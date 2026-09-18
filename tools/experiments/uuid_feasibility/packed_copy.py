"""Supplement: public psycopg binary adapter avoids materializing stdlib UUIDs.

Fixed before this consumer's first measurement. Same persisted values, framing,
payload and verification as the original COPY study. Six variants, five repeats
plus warmup, 100k rows. Original micro/HTTP/COPY code is unchanged.
"""

import argparse
import json
import os
import random
import subprocess
import sys
import time
import uuid

import _uuid_lab as lab
import fastuuid
import psycopg
import uuid_utils
from common import HERE, identity, save
from consumers import ADAPTER
from psycopg import sql
from psycopg.adapt import Dumper
from psycopg.pq import Format


class UUIDBytesDumper(Dumper):
    oid = 2950
    format = Format.BINARY

    def dump(self, value):
        if not isinstance(value, bytes) or len(value) != 16:
            raise ValueError("UUID binary value must be exactly 16 bytes")
        return value


def packed_rows(texts):
    raw = lab.parse_many_bytes(texts)
    return [raw[i : i + 16] for i in range(0, len(raw), 16)]


VARIANTS = {
    "pydantic_uuids": ADAPTER.validate_python,
    "c_uuids": lab.parse_many,
    "pydantic_bytes": lambda v: [x.bytes for x in ADAPTER.validate_python(v)],
    "uuid_utils_bytes": lambda v: [uuid_utils.UUID(x).bytes for x in v],
    "fastuuid_bytes": lambda v: [fastuuid.UUID(x).bytes for x in v],
    "c_packed": packed_rows,
}


def worker(variant):
    dsn = os.environ["UUID_LAB_DSN"]
    if (
        not psycopg.conninfo.conninfo_to_dict(dsn)
        .get("dbname", "")
        .startswith("fastuuid7_feasibility")
    ):
        raise ValueError("disposable study database required")
    rng = random.Random(9562)
    inputs = [str(uuid.UUID(int=rng.getrandbits(128))) for _ in range(100000)]
    schema = "packed_" + uuid.uuid4().hex
    with psycopg.connect(dsn) as conn:
        if not variant.endswith("uuids"):
            conn.adapters.register_dumper(bytes, UUIDBytesDumper)
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        conn.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
        conn.execute("CREATE TABLE records (seq bigint PRIMARY KEY,id uuid NOT NULL,payload text)")
        conn.commit()
        try:
            start, cpu = time.perf_counter(), time.process_time()
            with conn.cursor().copy(
                "COPY records (seq,id,payload) FROM STDIN (FORMAT BINARY)"
            ) as copy:
                copy.set_types(["int8", "uuid", "text"])
                for offset in range(0, len(inputs), 1000):
                    values = VARIANTS[variant](inputs[offset : offset + 1000])
                    for index, value in enumerate(values, offset):
                        copy.write_row((index, value, "x" * 128))
            conn.commit()
            elapsed, cpu = time.perf_counter() - start, time.process_time() - cpu
            count = 0
            with conn.cursor(name="verify") as cur:
                cur.execute("SELECT seq,id,payload FROM records ORDER BY seq")
                for seq, value, payload in cur:
                    assert seq == count and str(value) == inputs[count] and payload == "x" * 128
                    count += 1
            assert count == len(inputs)
            return {
                "variant": variant,
                "elapsed": elapsed,
                "cpu": cpu,
                "rows": count,
                "verified_all_rows": True,
                "postgres": conn.execute("SHOW server_version").fetchone()[0],
            }
        finally:
            conn.rollback()
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            conn.commit()


def main(args):
    if args.worker:
        print(json.dumps(worker(args.worker)))
        return
    out = {"identity": identity(), "kind": "packed_copy", "samples": []}
    rng = random.Random(9562)
    for repeat in range(-1, 5):
        names = list(VARIANTS)
        rng.shuffle(names)
        for name in names:
            row = json.loads(
                subprocess.check_output(
                    [sys.executable, str(HERE / "packed_copy.py"), "--worker", name],
                    cwd=HERE,
                    text=True,
                )
            )
            row.update(repeat=repeat, warmup=repeat == -1)
            out["samples"].append(row)
            save(args.output, out)
            print(name, repeat, row["elapsed"], flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", choices=list(VARIANTS))
    parser.add_argument("--output")
    main(parser.parse_args())
