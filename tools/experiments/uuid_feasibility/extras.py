"""Separate-process memory, threads, profile and PostgreSQL measurements."""

import argparse
import concurrent.futures
import cProfile
import json
import os
import random
import resource
import subprocess
import sys
import time
import uuid

import _uuid_lab as lab
import psycopg
from common import HERE, RAW, TEXTS, digest, identity, save
from consumers import CONSUMERS
from psycopg import sql


def worker(args):
    if args.kind == "memory":
        import gc
        import tracemalloc

        count = 100_000
        inputs = [TEXTS[i % len(TEXTS)] for i in range(count)]
        gc.collect()
        tracemalloc.start()
        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        fn = {**CONSUMERS, "native": lab.parse_many_native, "packed": lab.parse_many_bytes}[
            args.variant
        ]
        result = fn(inputs)
        current, peak = tracemalloc.get_traced_memory()
        after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        assert len(result) == count * (16 if args.variant == "packed" else 1)
        return {
            "variant": args.variant,
            "count": count,
            "traced_current": current,
            "traced_peak": peak,
            "rss_before": before,
            "rss_after": after,
            "rss_unit": "bytes" if sys.platform == "darwin" else "KiB",
            "note": "tracemalloc tracks Python allocator traffic, not every external native allocation; RSS is lifetime high-water",
        }
    if args.kind == "copy":
        dsn = os.environ["UUID_LAB_DSN"]
        params = psycopg.conninfo.conninfo_to_dict(dsn)
        if not params.get("dbname", "").startswith("fastuuid7_feasibility"):
            raise ValueError("dedicated disposable database required")
        rng = random.Random(9562)
        inputs = [str(uuid.UUID(int=rng.getrandbits(128))) for _ in range(args.rows)]
        schema = "study_" + uuid.uuid4().hex
        with psycopg.connect(dsn) as conn:
            conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
            conn.execute(
                "CREATE TABLE records (seq bigint PRIMARY KEY, id uuid NOT NULL, payload text)"
            )
            conn.commit()
            try:
                start = time.perf_counter()
                cpu = time.process_time()
                parse_seconds = 0
                with conn.cursor().copy(
                    "COPY records (seq,id,payload) FROM STDIN (FORMAT BINARY)"
                ) as copy:
                    copy.set_types(["int8", "uuid", "text"])
                    for offset in range(0, len(inputs), 1000):
                        tick = time.perf_counter()
                        values = CONSUMERS[args.variant](inputs[offset : offset + 1000])
                        parse_seconds += time.perf_counter() - tick
                        for i, value in enumerate(values, offset):
                            copy.write_row((i, value, "x" * 128))
                conn.commit()
                elapsed, cpu = time.perf_counter() - start, time.process_time() - cpu
                rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                count = 0
                with conn.cursor(name="verify") as cur:
                    cur.execute("SELECT seq,id,payload FROM records ORDER BY seq")
                    for seq, value, payload in cur:
                        assert seq == count and str(value) == inputs[count] and payload == "x" * 128
                        count += 1
                assert count == len(inputs)
                version = conn.execute("SHOW server_version").fetchone()[0]
                return {
                    "variant": args.variant,
                    "rows": count,
                    "elapsed": elapsed,
                    "cpu": cpu,
                    "parse_seconds": parse_seconds,
                    "rss": rss,
                    "postgres": version,
                    "verified_all_rows": True,
                    "server_cpu_measured": False,
                }
            finally:
                conn.rollback()
                conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
                conn.commit()


def main(args):
    if args.worker:
        print(json.dumps(worker(args)))
        return
    out = {
        "identity": identity(),
        "extension_sha256": digest(lab.__file__),
        "kind": args.kind,
        "samples": [],
    }
    rng = random.Random(9562)
    if args.kind in ("memory", "copy"):
        variants = list(CONSUMERS)
        if args.kind == "memory":
            variants += ["native", "packed"]
        for repeat in range(-1 if args.kind == "copy" else 0, args.rounds):
            rng.shuffle(variants)
            for variant in variants:
                cmd = [
                    sys.executable,
                    str(HERE / "extras.py"),
                    args.kind,
                    "--worker",
                    "--variant",
                    variant,
                    "--rows",
                    str(args.rows),
                ]
                row = json.loads(subprocess.check_output(cmd, cwd=HERE, text=True))
                row.update(repeat=repeat, warmup=repeat == -1)
                out["samples"].append(row)
                save(args.output, out)
                print(
                    args.kind,
                    variant,
                    repeat,
                    row.get("elapsed", row.get("traced_current")),
                    flush=True,
                )
    elif args.kind == "threads":
        values = TEXTS * 64
        expected = b"".join(RAW) * 64
        cases = [
            (fn, workers)
            for fn in ("parse_many_bytes", "parse_many_bytes_detach")
            for workers in (1, 2, 4)
        ]
        for repeat in range(-1, args.rounds):
            rng.shuffle(cases)
            for fn, workers in cases:
                with concurrent.futures.ThreadPoolExecutor(workers) as pool:
                    # Fixed total work (16 batches) at each worker count.
                    list(pool.map(lambda _: None, range(workers)))
                    start = time.perf_counter()
                    cpu = time.process_time()
                    results = list(pool.map(getattr(lab, fn), [values] * 16))
                    elapsed, cpu = time.perf_counter() - start, time.process_time() - cpu
                assert all(r == expected for r in results)
                out["samples"].append(
                    {
                        "fn": fn,
                        "workers": workers,
                        "repeat": repeat,
                        "warmup": repeat == -1,
                        "elapsed": elapsed,
                        "cpu": cpu,
                        "uuids": len(values) * 16,
                    }
                )
        save(args.output, out)
    elif args.kind == "profile":
        from integration import StandardModel

        data = json.dumps({"ids": TEXTS[:1000], "label": "sample"})
        profile = cProfile.Profile()
        profile.enable()
        for _ in range(1000):
            StandardModel.model_validate_json(data).model_dump_json()
        profile.disable()
        profile.dump_stats(args.output + ".pstats")
        out["note"] = (
            "Python call attribution only: native UUID and JSON costs are not separated; profiling is not timing evidence."
        )
        save(args.output, out)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("kind", choices=["memory", "copy", "threads", "profile"])
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--variant")
    parser.add_argument("--rows", type=int, default=100000)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--output")
    main(parser.parse_args())
