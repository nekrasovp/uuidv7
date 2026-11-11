"""Sequential baseline/candidate/reference measurements over real loopback HTTP.

The offered-load design is adapted from the repository's September feasibility
study; these are new production-wheel measurements with separate source identity.
"""

import argparse
import asyncio
import hashlib
import json
import math
import os
import random
import socket
import subprocess
import time
import uuid
import zipfile
from pathlib import Path

import httpx
from common import BASE_SHA, HERE, ROOT, TEXTS, VARIANTS, digest, save

RATES = {
    "path": [100, 300],
    "body-1": [100, 300],
    "body-1000": [20, 60],
    "response": [20, 60],
    "invalid": [100, 300],
    "generate-v4": [40, 120],
    "generate-v7": [40, 120],
}


def percentile(values, fraction):
    return sorted(values)[min(len(values) - 1, math.ceil(len(values) * fraction) - 1)]


def request_data(scenario, index=0):
    headers = {"content-type": "application/json"}
    if scenario == "path":
        return "GET", "/item/" + TEXTS[index % len(TEXTS)], None, headers
    if scenario == "response":
        return "GET", "/response", None, headers
    if scenario.startswith("generate-v"):
        return "GET", "/generate/" + scenario[-1], None, headers
    ids = [TEXTS[0], "bad"] if scenario == "invalid" else TEXTS[: int(scenario.split("-")[1])]
    return "POST", "/batch", json.dumps({"ids": ids, "label": "sample"}).encode(), headers


def validate_response(scenario, index, response):
    data = response.json()
    if scenario == "invalid":
        assert response.status_code == 422 and data["detail"][0]["loc"] == ["body", "ids", 1]
        return
    assert response.status_code == 200
    if scenario == "path":
        assert data == {"id": TEXTS[index % len(TEXTS)]}
    elif scenario.startswith("generate-v"):
        values = [uuid.UUID(text) for text in data["ids"]]
        assert data["label"] == "sample" and len(values) == len(set(values)) == 64
        assert all(v.version == int(scenario[-1]) and v.variant == uuid.RFC_4122 for v in values)
        assert [str(v) for v in values] == data["ids"]
    else:
        size = 1000 if scenario == "response" else int(scenario.split("-")[1])
        assert data == {"ids": TEXTS[:size], "label": "sample"}


async def load(client, scenario, rate, duration):
    count = max(1, round(rate * duration))
    requests = [request_data(scenario, i) for i in range(count)]
    latency, service, lag, errors = [], [], [], []
    start = time.perf_counter()

    async def request(index, scheduled):
        sent = time.perf_counter()
        lag.append(sent - scheduled)
        try:
            method, url, content, headers = requests[index]
            response = await client.request(method, url, content=content, headers=headers)
            completed = time.perf_counter()
            validate_response(scenario, index, response)
            latency.append(completed - scheduled)
            service.append(completed - sent)
        except Exception as error:
            errors.append(repr(error))

    tasks = []
    for i in range(count):
        scheduled = start + i / rate
        await asyncio.sleep(max(0, scheduled - time.perf_counter()))
        tasks.append(asyncio.create_task(request(i, scheduled)))
    await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start
    if errors:
        raise RuntimeError(f"{len(errors)} failed responses: {errors[:3]}")
    return {
        "requests": count,
        "elapsed_s": elapsed,
        "completed_rps": count / elapsed,
        "latency_ms": {f"p{p}": percentile(latency, p / 100) * 1000 for p in (50, 95, 99)},
        "service_ms": {f"p{p}": percentile(service, p / 100) * 1000 for p in (50, 95, 99)},
        "scheduling_lag_p99_ms": percentile(lag, 0.99) * 1000,
        "max_scheduling_lag_ms": max(lag) * 1000,
        "scheduling_overload": percentile(lag, 0.99) > 0.1,
        "errors": 0,
    }


def clean_env(variant):
    env = dict(os.environ, UUID_BENCH_VARIANT=variant, PYTHONNOUSERSITE="1")
    env.pop("PYTHONPATH", None)
    return env


def check_wheel(python, wheel):
    # Compare every installed runtime file, including Python wrappers, to the
    # exact candidate wheel. Version strings alone cannot distinguish the build.
    with zipfile.ZipFile(wheel) as archive:
        expected = {
            name: hashlib.sha256(archive.read(name)).hexdigest()
            for name in archive.namelist()
            if not name.endswith("/") and name.split("/")[0] in ("fastuuid7", "uuidv7")
        }
    script = """import fastuuid7,hashlib,json,pathlib,sys
root=pathlib.Path(fastuuid7.__file__).parent.parent
assert root.resolve().is_relative_to(pathlib.Path(sys.prefix).resolve())
expected=json.load(sys.stdin)
for name,digest in expected.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
print(json.dumps({'files':len(expected),'version':fastuuid7.__version__}))
"""
    result = subprocess.run(
        [python, "-I", "-c", script],
        input=json.dumps(expected),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


async def http_round(python, variant, repeat, args, rng, output):
    log_path = Path(args.output).with_suffix("").with_name(Path(args.output).stem + "-logs")
    log_path.mkdir(parents=True, exist_ok=True)
    with socket.socket() as sock, (log_path / f"{variant}-{repeat}.log").open("w") as log:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = subprocess.Popen(
            [
                python,
                "-I",
                "-m",
                "uvicorn",
                "app:create_app",
                "--factory",
                "--app-dir",
                str(HERE),
                "--fd",
                str(sock.fileno()),
                "--loop",
                "asyncio",
                "--http",
                "h11",
                "--no-access-log",
                "--log-level",
                "error",
            ],
            cwd=args.work_dir,
            env=clean_env(variant),
            pass_fds=(sock.fileno(),),
            stdout=log,
            stderr=log,
        )
    try:
        async with httpx.AsyncClient(
            base_url=f"http://127.0.0.1:{port}",
            timeout=20,
            trust_env=False,
            limits=httpx.Limits(max_connections=256, max_keepalive_connections=64),
        ) as client:
            for _ in range(200):
                try:
                    health = await client.get("/health")
                    if health.status_code == 200:
                        info = health.json()
                        assert info["variant"] == variant
                        output["identities"].setdefault(variant, info["identity"])
                        break
                except httpx.ConnectError:
                    pass
                if server.poll() is not None:
                    raise RuntimeError(f"server exited; see {log_path}")
                await asyncio.sleep(0.05)
            else:
                raise RuntimeError("server startup timeout")
            cases = [(scenario, rate) for scenario, rates in RATES.items() for rate in rates]
            rng.shuffle(cases)
            for scenario, rate in cases:
                await load(client, scenario, rate, args.warmup)
                before = (await client.get("/metrics")).json()
                result = await load(client, scenario, rate, args.duration)
                after = (await client.get("/metrics")).json()
                result.update(
                    variant=variant,
                    scenario=scenario,
                    rate=rate,
                    repeat=repeat,
                    server_cpu_us=(after["cpu"] - before["cpu"]) / result["requests"] * 1e6,
                    server_peak_rss_bytes=after["rss_bytes"],
                )
                output["http"].append(result)
                save(args.output, output)
            print(f"HTTP {variant} repeat {repeat + 1} complete", flush=True)
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


async def run(args):
    if args.rounds < 3 or args.duration <= 0 or args.warmup <= 0:
        raise ValueError("require >=3 rounds and positive duration/warmup")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT, text=True
    ).strip()
    output = {
        "protocol": "uuid-api-v1",
        "harness_commit": head,
        "source_dirty": dirty,
        "baseline_source": BASE_SHA,
        "candidate_source": head,
        "candidate_wheel_sha256": digest(args.candidate_wheel),
        "installed_candidate": check_wheel(args.candidate_python, args.candidate_wheel),
        "rounds": args.rounds,
        "duration_s": args.duration,
        "warmup_s": args.warmup,
        "rates": RATES,
        "identities": {},
        "pydantic": [],
        "http": [],
        "complete": False,
        "limits": [
            "same-host loopback, one uvicorn worker, asyncio/h11; no TLS/proxy/database",
            "fixed offered rates, not saturation throughput; inspect scheduling lag and tails",
            "p99 scheduling lag >100ms is flagged, never dropped",
            "native variant returns a different Python type; only JSON outputs are equivalent",
            "explicit adapters are benchmark-only opt-ins, not installed framework integrations",
            "HTTP latency ends at response receipt; correctness validation runs in the load client",
            "server CPU includes metrics endpoint overhead; RSS is process lifetime high-water",
            "Pydantic timing disables GC; HTTP uses normal GC; five repeats are exploratory",
        ],
    }
    rng = random.Random(9562)
    variants = list(VARIANTS)
    save(args.output, output)
    for repeat in range(args.rounds):
        rng.shuffle(variants)
        for variant in variants:
            python = (
                args.candidate_python if variant.startswith("candidate-") else args.baseline_python
            )
            if not args.http_only:
                result = subprocess.run(
                    [
                        python,
                        str(HERE / "pydantic_bench.py"),
                        "--variant",
                        variant,
                        "--seed",
                        str(9562 + repeat),
                    ],
                    cwd=args.work_dir,
                    env=clean_env(variant),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                measured = json.loads(result.stdout)
                measured["repeat"] = repeat
                output["pydantic"].append(measured)
                save(args.output, output)
            if not args.pydantic_only:
                await http_round(python, variant, repeat, args, rng, output)
    # Pins and interpreter must be identical for every variant; extension/wrapper
    # hashes intentionally distinguish the baseline and candidate builds.
    identities = list(output["identities"].values()) or [v["identity"] for v in output["pydantic"]]
    for value in identities:
        assert value["packages"]["fastuuid7"] == "0.6.0"
        assert value["packages"] == identities[0]["packages"]
        assert value["python"] == identities[0]["python"]
        assert value["lock_sha256"] == identities[0]["lock_sha256"]
    output["complete"] = True
    save(args.output, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-python", required=True)
    parser.add_argument("--baseline-python", required=True)
    parser.add_argument("--candidate-wheel", required=True)
    parser.add_argument(
        "--work-dir", required=True, help="existing directory outside the source checkout"
    )
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--duration", type=float, default=1)
    parser.add_argument("--warmup", type=float, default=0.25)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--http-only", action="store_true")
    mode.add_argument("--pydantic-only", action="store_true")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    args.candidate_python = str(Path(args.candidate_python).absolute())
    args.baseline_python = str(Path(args.baseline_python).absolute())
    args.work_dir = str(Path(args.work_dir).resolve())
    if Path(args.work_dir).is_relative_to(ROOT):
        parser.error("work directory must be outside the source checkout")
    asyncio.run(run(args))
