"""Measure committed PostgreSQL workloads, with one fresh process per sample."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import random
import statistics
import subprocess
import sys
import time
import traceback
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PINS = {"fastuuid7": "0.4.0", "uuid-utils": "1.0.0", "uuid6": "2025.0.1"}
HISTORY_START_MS = 1_577_836_800_000
PAYLOAD = "x" * 128
SCENARIOS = ("sqlalchemy", "copy", "historical")


@dataclass(frozen=True)
class Case:
    name: str
    group: str
    historical: bool = False
    batch: bool = False


def cases_for(scenario, include_historical_batch=False):
    if scenario == "historical":
        return (
            [Case("checkout_at_batch", "client_uuid7", True, True)]
            if include_historical_batch
            else []
        ) + [
            Case("checkout_at", "client_uuid7", True),
            Case("published_at", "client_uuid7", True),
            Case("uuid_utils_at", "client_uuid7", True),
            Case("rfc_random_at", "reference_strategy", True),
        ]
    if scenario not in SCENARIOS:
        raise ValueError("unknown scenario")
    return [
        Case("checkout_scalar", "client_uuid7"),
        Case("checkout_batch", "client_uuid7", batch=True),
        Case("published_scalar", "client_uuid7"),
        Case("published_batch", "client_uuid7", batch=True),
        Case("stdlib_uuid7", "client_uuid7"),
        Case("uuid_utils", "client_uuid7"),
        Case("uuid6", "client_uuid7"),
        Case("stdlib_uuid4", "uuid4_control"),
        Case("postgres_uuid7", "server_strategy"),
    ]


def historical_ms(index):
    # Eight events per millisecond, then out-of-order timestamps within a week.
    return HISTORY_START_MS + ((index // 8) * 104_729) % (7 * 86_400_000)


def random_at(unix_ms):
    """RFC 9562 v7 reference: exact timestamp and 74 OS-random bits; no counter."""
    raw = int.from_bytes(os.urandom(10), "big")
    value = (unix_ms << 80) | (raw & ((1 << 76) - 1))
    value = (value & ~(3 << 62)) | (7 << 76) | (2 << 62)
    return uuid.UUID(int=value)


def validate_uuid(value, *, version=7, exact_ms=None, lower_ms=None, upper_ms=None):
    if not isinstance(value, uuid.UUID):
        raise ValueError("ID must be a stdlib uuid.UUID instance")
    if value.version != version or value.variant != uuid.RFC_4122:
        raise ValueError("invalid UUID version/variant")
    timestamp = value.int >> 80
    if exact_ms is not None and timestamp != exact_ms:
        raise ValueError("historical timestamp mismatch")
    if lower_ms is not None and not lower_ms <= timestamp <= upper_ms:
        raise ValueError("timestamp outside permitted clock window")
    return timestamp


def check_config(rows, batch_size, rounds, database):
    if min(rows, batch_size, rounds) < 1:
        raise ValueError("rows, batch size and rounds must be positive")
    if not database.startswith("fastuuid7_workloads_") or not database.isidentifier():
        raise ValueError("database must have disposable prefix fastuuid7_workloads_")


def generator_for(case):
    name = case.name
    if name.startswith(("checkout", "published")):
        if name.startswith("checkout"):
            sys.path.insert(0, str(ROOT))
        module = importlib.import_module("fastuuid7")
        origin = Path(module.__file__).resolve()
        if name.startswith("checkout"):
            if origin != ROOT / "fastuuid7" / "__init__.py":
                raise ValueError("checkout import escaped repository")
            impl = importlib.import_module("uuidv7.uuidv7_impl.uuid7_gen")
            if ROOT not in Path(impl.__file__).resolve().parents:
                raise ValueError("checkout extension escaped repository")
        elif origin == ROOT / "fastuuid7" / "__init__.py":
            raise ValueError("published import shadowed by checkout")
        elif importlib.metadata.version("fastuuid7") != PINS["fastuuid7"]:
            raise ValueError("published version mismatch")
        version = module.__version__
        if case.historical and case.batch:
            function = module.uuid7_at_many  # Missing API is a failure, never a skip.
            return lambda times: function(unix_ms=times), version
        if case.historical:
            return lambda times: [module.uuid7_at(unix_ms=t) for t in times], version
        if case.batch:
            return lambda times: module.uuid7_many(len(times)), version
        return lambda times: [module.uuid7() for _ in times], version
    if name.startswith("uuid_utils"):
        if importlib.metadata.version("uuid-utils") != PINS["uuid-utils"]:
            raise ValueError("uuid-utils pin mismatch")
        module = importlib.import_module("uuid_utils.compat")
        if case.historical:
            return lambda times: [module.uuid7(nanoseconds=t * 1_000_000) for t in times], PINS[
                "uuid-utils"
            ]
        return lambda times: [module.uuid7() for _ in times], PINS["uuid-utils"]
    if name == "uuid6":
        module = importlib.import_module("uuid6")
        if importlib.metadata.version("uuid6") != PINS["uuid6"]:
            raise ValueError("uuid6 pin mismatch")
        return lambda times: [module.uuid7() for _ in times], PINS["uuid6"]
    if name == "rfc_random_at":
        return lambda times: [random_at(t) for t in times], platform.python_version()
    if name == "postgres_uuid7":
        return None, "server"
    function = {"stdlib_uuid4": uuid.uuid4, "stdlib_uuid7": uuid.uuid7}[name]
    return lambda times: [function() for _ in times], platform.python_version()


def rss_bytes():
    import resource

    # macOS reports bytes; Linux reports KiB. Lifetime high-water, not a delta.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if sys.platform == "darwin" else 1024
    )


def verify_rows(connection, table, case, rows, lower_ms, upper_ms):
    from psycopg import sql

    counts = connection.execute(
        sql.SQL("SELECT count(*), count(DISTINCT id) FROM {}").format(table)
    ).fetchone()
    if counts != (rows, rows):
        raise ValueError(f"persisted row/unique counts differ: {counts}")
    minimum, maximum = (1 << 48), 0
    count = 0
    with connection.cursor(name="verify_workload") as cursor:
        cursor.execute(
            sql.SQL("SELECT seq, id, event_ms, payload FROM {} ORDER BY seq").format(table)
        )
        for seq, value, event_ms, payload in cursor:
            if seq != count or event_ms != historical_ms(seq) or payload != PAYLOAD:
                raise ValueError("persisted sequence/event/payload differs")
            ts = validate_uuid(
                value,
                version=4 if case.group == "uuid4_control" else 7,
                exact_ms=event_ms if case.historical else None,
                lower_ms=lower_ms
                if not case.historical and case.group != "uuid4_control"
                else None,
                upper_ms=upper_ms,
            )
            minimum, maximum = min(minimum, ts), max(maximum, ts)
            count += 1
    if count != rows:
        raise ValueError("verification stream was incomplete")
    return {
        "rows": count,
        "distinct_ids": counts[1],
        "all_rows_layout_checked": True,
        "min_uuid_ms": minimum if case.group != "uuid4_control" else None,
        "max_uuid_ms": maximum if case.group != "uuid4_control" else None,
    }


def measure(args, case):
    import psycopg
    from psycopg import sql
    from sqlalchemy import (
        BigInteger,
        Column,
        MetaData,
        String,
        Table,
        Uuid,
        create_engine,
        insert,
        text,
    )
    from sqlalchemy.orm import Session, registry

    generate, version = generator_for(case)
    # Probe before timing, including timestamp layout; uuid6 may advance its
    # logical clock by one millisecond per subsequent call under high load.
    before = time.time_ns() // 1_000_000
    if generate:
        sample = generate([HISTORY_START_MS])[0]
        validate_uuid(
            sample,
            version=4 if case.group == "uuid4_control" else 7,
            exact_ms=HISTORY_START_MS if case.historical else None,
            lower_ms=before - 100
            if not case.historical and case.group != "uuid4_control"
            else None,
            upper_ms=time.time_ns() // 1_000_000 + 100,
        )
    schema = "wl_" + uuid.uuid4().hex
    table = sql.Identifier(schema, "events")
    dsn = os.environ["WORKLOAD_DSN"]
    conn = psycopg.connect(dsn, dbname=args.database)
    engine = None
    session = None
    schema_created = False
    try:
        if conn.info.server_version < 180000:
            raise ValueError("PostgreSQL 18 or newer required for the full matrix")
        server_version = conn.execute("SELECT version()").fetchone()[0]
        settings = {
            key: conn.execute(sql.SQL("SHOW {}").format(sql.Identifier(key))).fetchone()[0]
            for key in ("fsync", "synchronous_commit", "shared_buffers", "max_wal_size")
        }
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        conn.execute(
            sql.SQL(
                "CREATE TABLE {} (id uuid PRIMARY KEY DEFAULT uuidv7(), "
                "seq bigint NOT NULL, event_ms bigint NOT NULL, payload text NOT NULL)"
            ).format(table)
        )
        conn.commit()
        schema_created = True
        phases = {"generation_s": 0.0, "row_build_s": 0.0, "execute_s": 0.0, "commit_s": 0.0}
        session = None
        if args.scenario == "sqlalchemy":
            engine = create_engine(
                "postgresql+psycopg://", creator=lambda: psycopg.connect(dsn, dbname=args.database)
            )
            mapper = registry()
            relation = Table(
                "events",
                MetaData(),
                Column("id", Uuid, primary_key=True, server_default=text("uuidv7()")),
                Column("seq", BigInteger),
                Column("event_ms", BigInteger),
                Column("payload", String),
                schema=schema,
            )

            class Event:
                pass

            mapper.map_imperatively(Event, relation)
            statement = insert(Event)
            session = Session(engine)
            session.connection()  # Connection/pool setup is excluded.
        else:
            statement = sql.SQL("COPY {} ({}) FROM STDIN (FORMAT BINARY)").format(
                table,
                sql.SQL("seq, event_ms, payload")
                if generate is None
                else sql.SQL("id, seq, event_ms, payload"),
            )
        server_start_ms = int(
            conn.execute("SELECT extract(epoch FROM clock_timestamp()) * 1000").fetchone()[0]
        )
        conn.commit()
        wall_start_ms = time.time_ns() // 1_000_000
        cpu_start = time.process_time()
        start = time.perf_counter()
        for offset in range(0, args.rows, args.batch_size):
            end = min(offset + args.batch_size, args.rows)
            t = time.perf_counter()
            times = [historical_ms(i) for i in range(offset, end)]
            phases["row_build_s"] += time.perf_counter() - t
            t = time.perf_counter()
            ids = generate(times) if generate else None
            phases["generation_s"] += time.perf_counter() - t
            t = time.perf_counter()
            if session:
                records = [
                    {
                        "seq": i,
                        "event_ms": times[i - offset],
                        "payload": PAYLOAD,
                        **({"id": ids[i - offset]} if ids is not None else {}),
                    }
                    for i in range(offset, end)
                ]
            else:
                records = [
                    ((ids[i - offset],) if ids is not None else ())
                    + (i, times[i - offset], PAYLOAD)
                    for i in range(offset, end)
                ]
            phases["row_build_s"] += time.perf_counter() - t
            t = time.perf_counter()
            if session:
                session.execute(statement, records)
            else:
                with conn.cursor().copy(statement) as copy:
                    copy.set_types((["uuid"] if ids is not None else []) + ["int8", "int8", "text"])
                    for record in records:
                        copy.write_row(record)
            phases["execute_s"] += time.perf_counter() - t
        t = time.perf_counter()
        if session:
            session.commit()
        else:
            conn.commit()
        phases["commit_s"] = time.perf_counter() - t
        elapsed = time.perf_counter() - start
        cpu = time.process_time() - cpu_start
        peak = rss_bytes()  # Before SELECT/validation allocates anything.
        wall_end_ms = time.time_ns() // 1_000_000
        server_end_ms = int(
            conn.execute("SELECT extract(epoch FROM clock_timestamp()) * 1000").fetchone()[0]
        )
        conn.commit()
        if session:
            session.close()
        lower = (server_start_ms if generate is None else wall_start_ms) - 100
        upper = (server_end_ms if generate is None else wall_end_ms) + 100
        if case.name == "uuid6":
            upper += args.rows + 1  # Explicit bounded logical-clock allowance.
        verified = verify_rows(conn, table, case, args.rows, lower, upper)
        conn.commit()
        relation_bytes = conn.execute(
            "SELECT pg_total_relation_size(%s::regclass)", (f"{schema}.events",)
        ).fetchone()[0]
        return {
            "scenario": args.scenario,
            "case": asdict(case),
            "version": version,
            "rows": args.rows,
            "batch_size": args.batch_size,
            "elapsed_s": elapsed,
            "throughput_rows_s": args.rows / elapsed,
            "client_cpu_s": cpu,
            "client_cpu_percent_one_core": cpu / elapsed * 100,
            "client_lifetime_peak_rss_bytes": peak,
            "phases": phases,
            "verification": verified,
            "postgres": server_version,
            "postgres_settings": settings,
            "relation_bytes": relation_bytes,
            "wall_end_ms": wall_end_ms,
            "final_clock_delta_ms": verified["max_uuid_ms"] - wall_end_ms
            if not case.historical and verified["max_uuid_ms"] is not None
            else None,
        }
    finally:
        if session:
            session.close()
        if engine:
            engine.dispose()
        conn.rollback()
        if schema_created:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            conn.commit()
        conn.close()


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def provenance():
    paths = [
        "fastuuid7/__init__.py",
        "uuidv7/__init__.py",
        "uuidv7/uuidv7_impl/src/uuid7_gen.c",
        "uuidv7/uuidv7_impl/uuid7_gen.c",
        "benchmarks/workloads/run.py",
        "benchmarks/workloads/uv.lock",
    ]
    return {
        "head": git("rev-parse", "HEAD"),
        "status": git("status", "--porcelain"),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": os.cpu_count(),
        "processor": platform.processor(),
        "packages": {
            p: importlib.metadata.version(p)
            for p in ("SQLAlchemy", "psycopg", "psycopg-binary", *PINS)
        },
        "sha256": {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths},
        "extension_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "uuidv7").rglob("*.so")
        },
        "postgres_image": os.environ.get("WORKLOAD_POSTGRES_IMAGE", "not recorded"),
    }


def summarize(samples):
    result = []
    for scenario in SCENARIOS:
        for case in cases_for(scenario, include_historical_batch=True):
            group = [
                s for s in samples if s["scenario"] == scenario and s["case"]["name"] == case.name
            ]
            if not group:
                continue
            result.append(
                {
                    "scenario": scenario,
                    "case": case.name,
                    "group": case.group,
                    "runs": len(group),
                    **{
                        key: statistics.median(s[key] for s in group)
                        for key in (
                            "elapsed_s",
                            "throughput_rows_s",
                            "client_cpu_s",
                            "client_lifetime_peak_rss_bytes",
                        )
                    },
                    "min_elapsed_s": min(s["elapsed_s"] for s in group),
                    "max_elapsed_s": max(s["elapsed_s"] for s in group),
                    "generation_percent": statistics.median(
                        100 * s["phases"]["generation_s"] / s["elapsed_s"] for s in group
                    ),
                }
            )
    return result


def markdown(data):
    lines = [
        "# PostgreSQL workload measurements",
        "",
        f"Source HEAD: `{data['provenance']['head']}`",
        f"Rows/sample: {data['rows']}; batch: {data['batch_size']}; measured rounds: {data['rounds']}; seed: {data['seed']}.",
        "One untimed, validated warmup per case precedes randomized measured rounds. Fresh process and table per sample.",
        "ID: stdlib uuid.UUID -> PostgreSQL uuid; 128-byte text payload + two bigint columns. Binary COPY uses write_row.",
        "Elapsed includes generation, row construction, adaptation, insertion and commit; excludes connection/DDL/verification.",
        "CPU is client process only. RSS is client lifetime high-water before verification, including imports. No server CPU/RSS measurement.",
        "",
        "| Scenario | Case | Group | Median s | Min–max s | Rows/s | Client CPU s | Peak MiB | Generate % |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for s in data["summary"]:
        lines.append(
            f"| {s['scenario']} | {s['case']} | {s['group']} | {s['elapsed_s']:.4f} | {s['min_elapsed_s']:.4f}–{s['max_elapsed_s']:.4f} | {s['throughput_rows_s']:,.0f} | {s['client_cpu_s']:.4f} | {s['client_lifetime_peak_rss_bytes'] / 2**20:.1f} | {s['generation_percent']:.2f} |"
        )
    lines += [
        "",
        "Every sample committed and passed full row count, uniqueness, payload, sequence, RFC layout and timestamp verification.",
        "UUIDv4 is a control, PostgreSQL uuidv7() is a server strategy, and rfc_random_at is an OS-random reference constructor; none is a competing live UUIDv7 library row.",
        "Historical comparison: fastuuid7 uuid7_at and uuid_utils.compat.uuid7(nanoseconds=...). No stdlib/uuid6 exact timestamp API is claimed.",
        "uuid6 may advance a logical millisecond per call; raw results record clock drift and an explicit rows+1 ms verification allowance.",
        "Shared host, small initially empty tables, one client, warm caches, no query/read or sustained-update workload; no statistical significance or production-scale index claim.",
        "Raw samples, phase timings, versions, settings, SHA and verification counts are in the adjacent JSON.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260918)
    parser.add_argument("--database", default="fastuuid7_workloads_run")
    parser.add_argument("--output", type=Path, default=Path("workloads.json"))
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--include-historical-batch", action="store_true")
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    parser.add_argument("--scenario", choices=SCENARIOS, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    check_config(args.rows, args.batch_size, args.rounds, args.database)
    if args.worker:
        case = next(
            c
            for c in cases_for(args.scenario, args.include_historical_batch)
            if c.name == args.worker
        )
        try:
            print(json.dumps(measure(args, case)))
            return 0
        except Exception as exc:
            # Driver exception messages can contain credentials. Only emit class
            # and code locations; retain neither DSN nor raw exception text.
            print(
                json.dumps(
                    {
                        "failure": {
                            "type": type(exc).__name__,
                            "locations": [
                                f"{Path(f.filename).name}:{f.lineno}:{f.name}"
                                for f in traceback.extract_tb(exc.__traceback__)
                            ],
                        }
                    }
                )
            )
            return 1
    if sys.version_info[:2] != (3, 14):
        raise ValueError("use the isolated Python 3.14 workload environment")
    meta = provenance()
    if meta["status"] and not args.allow_dirty:
        raise ValueError("commit changes before measurement, or explicitly use --allow-dirty")
    # Require a pre-created, dedicated disposable database. Never create/drop a database.
    import psycopg

    with psycopg.connect(os.environ["WORKLOAD_DSN"], dbname=args.database) as connection:
        if connection.info.dbname != args.database:
            raise ValueError("unexpected database")
        if connection.info.server_version < 180000:
            raise ValueError("PostgreSQL 18 or newer required")
    samples, warmups = [], []
    rng = random.Random(args.seed)
    matrix = [
        (scenario, c)
        for scenario in SCENARIOS
        for c in cases_for(scenario, args.include_historical_batch)
    ]
    for run in range(-1, args.rounds):
        order = list(matrix)
        rng.shuffle(order)
        for scenario, case in order:
            print(
                f"{'warmup' if run == -1 else f'round {run + 1}'}: {scenario}/{case.name}",
                file=sys.stderr,
                flush=True,
            )
            command = [
                sys.executable,
                "-I",
                str(HERE / "run.py"),
                "--worker",
                case.name,
                "--scenario",
                scenario,
                "--rows",
                str(args.rows),
                "--batch-size",
                str(args.batch_size),
                "--database",
                args.database,
            ]
            if args.include_historical_batch:
                command.append("--include-historical-batch")
            result = subprocess.run(command, cwd=HERE, text=True, capture_output=True, timeout=600)
            if result.returncode:
                # DB credentials can appear in driver exceptions; do not echo stderr.
                try:
                    failure = json.loads(result.stdout)["failure"]
                except (ValueError, KeyError):
                    failure = "worker terminated without structured diagnostic"
                raise RuntimeError(
                    f"{scenario}/{case.name} failed (exit {result.returncode}): {failure}; no PASS/report produced"
                )
            sample = json.loads(result.stdout)
            sample["round"] = run + 1
            (warmups if run == -1 else samples).append(sample)
    data = {
        "format_version": 1,
        "provenance": meta,
        "rows": args.rows,
        "batch_size": args.batch_size,
        "rounds": args.rounds,
        "seed": args.seed,
        "include_historical_batch": args.include_historical_batch,
        "samples": samples,
        "warmups": warmups,
        "summary": summarize(samples),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    args.output.with_suffix(".md").write_text(markdown(data))
    print(f"PASS: {len(samples)} measured + {len(warmups)} warmup samples, all rows verified")


if __name__ == "__main__":
    raise SystemExit(main())
