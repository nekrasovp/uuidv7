"""Fixed offered load from a process separate from uvicorn, with lag accounting."""

import argparse
import asyncio
import json
import math
import os
import random
import socket
import subprocess
import sys
import time

import httpx
from common import HERE, TEXTS, identity, save


def percentile(values, fraction):
    return sorted(values)[min(len(values) - 1, math.ceil(len(values) * fraction) - 1)]


async def load(client, scenario, rate, duration):
    values = []
    lags = []
    errors = []
    start = time.perf_counter()
    encoded = json.dumps({"ids": TEXTS[:1000], "label": "sample"}).encode()
    invalid = json.dumps({"ids": [TEXTS[0], "bad"], "label": "sample"}).encode()

    async def request(index, scheduled):
        sent = time.perf_counter()
        lags.append(sent - scheduled)
        try:
            if scenario == "path":
                text = TEXTS[index % len(TEXTS)]
                r = await client.get("/item/" + text)
                assert r.status_code == 200 and r.json() == {"id": text}
            elif scenario == "response":
                r = await client.get("/response")
                assert r.status_code == 200 and r.json() == {"ids": TEXTS[:1000], "label": "sample"}
            elif scenario == "invalid":
                r = await client.post(
                    "/batch", content=invalid, headers={"content-type": "application/json"}
                )
                assert r.status_code == 422
                assert r.json()["detail"][0]["loc"] == ["body", "ids", 1]
            else:
                r = await client.post(
                    "/batch", content=encoded, headers={"content-type": "application/json"}
                )
                assert r.status_code == 200 and r.json() == {"ids": TEXTS[:1000], "label": "sample"}
            # Scheduled-to-completion latency includes client scheduling delays.
            values.append(time.perf_counter() - scheduled)
        except Exception as exc:
            errors.append(repr(exc))

    tasks = []
    for i in range(round(rate * duration)):
        scheduled = start + i / rate
        await asyncio.sleep(max(0, scheduled - time.perf_counter()))
        tasks.append(asyncio.create_task(request(i, scheduled)))
    await asyncio.gather(*tasks)
    elapsed = time.perf_counter() - start
    if errors:
        raise RuntimeError(f"{len(errors)} failed requests: {errors[:3]}")
    return {
        "requests": len(values),
        "elapsed": elapsed,
        "rps": len(values) / elapsed,
        "latency_ms": {f"p{p}": percentile(values, p / 100) * 1000 for p in (50, 95, 99)},
        "scheduling_lag_p99_ms": percentile(lags, 0.99) * 1000,
        "max_scheduling_lag_ms": max(lags) * 1000,
        "errors": len(errors),
    }


async def main(args):
    out = {
        "identity": identity(),
        "duration": args.duration,
        "rounds": args.rounds,
        "rates": {
            "path": [300, 900],
            "batch": [40, 120],
            "response": [40, 120],
            "invalid": [150, 450],
        },
        "samples": [],
    }
    rng = random.Random(9562)
    variants = args.variants.split(",")
    for repeat in range(args.rounds):
        rng.shuffle(variants)
        for variant in variants:
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            env = dict(os.environ, UUID_LAB_VARIANT=variant)
            server = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--no-access-log",
                    "--log-level",
                    "error",
                ],
                cwd=HERE,
                env=env,
                stdout=subprocess.DEVNULL,
            )
            try:
                async with httpx.AsyncClient(
                    base_url=f"http://127.0.0.1:{port}",
                    timeout=20,
                    trust_env=False,
                    limits=httpx.Limits(max_connections=256, max_keepalive_connections=64),
                ) as client:
                    for _ in range(100):
                        try:
                            if (await client.get("/health")).status_code == 200:
                                break
                        except httpx.ConnectError:
                            pass
                        if server.poll() is not None:
                            raise RuntimeError("uvicorn exited during startup")
                        await asyncio.sleep(0.05)
                    else:
                        raise RuntimeError("uvicorn did not start")
                    cases = [(s, rate) for s, rates in out["rates"].items() for rate in rates]
                    rng.shuffle(cases)
                    for scenario, rate in cases:
                        await load(client, scenario, rate, 0.5)
                        before = (await client.get("/metrics")).json()
                        result = await load(client, scenario, rate, args.duration)
                        after = (await client.get("/metrics")).json()
                        result.update(
                            variant=variant,
                            scenario=scenario,
                            rate=rate,
                            repeat=repeat,
                            server_cpu_per_request_us=(after["cpu"] - before["cpu"])
                            / result["requests"]
                            * 1e6,
                            server_rss=after["rss"],
                            rss_unit="bytes" if sys.platform == "darwin" else "KiB",
                        )
                        out["samples"].append(result)
                        save(args.output, out)
                        print(
                            variant,
                            scenario,
                            rate,
                            repeat,
                            round(result["server_cpu_per_request_us"], 1),
                            flush=True,
                        )
            finally:
                server.terminate()
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--duration", type=float, default=2)
    parser.add_argument("--variants", default="standard,scalar,bulk,native")
    parser.add_argument("--output", required=True)
    asyncio.run(main(parser.parse_args()))
