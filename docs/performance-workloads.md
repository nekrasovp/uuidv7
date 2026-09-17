# PostgreSQL application workloads

This independent harness measures SQLAlchemy ORM bulk INSERT, psycopg binary
COPY, and historical import through COPY. It uses PostgreSQL 18 and Python 3.14.
Dependencies live in `benchmarks/workloads/pyproject.toml` and its own `uv.lock`;
the library gains no runtime dependencies. Existing microbenchmarks are unchanged.

## Reproduce

Use a committed checkout and a dedicated disposable PostgreSQL database whose
name starts with `fastuuid7_workloads_`. The runner creates a unique schema per
sample and drops only that schema in `finally`. It does not create/drop databases.
The database role needs CREATE privileges only inside this disposable database.

```sh
uv sync --extra dev --locked
uv sync --project benchmarks/workloads --locked
# Example disposable server (remove this task-owned container after the run):
docker run --name fastuuid7-workloads-pg --rm -d -p 127.0.0.1:55432:5432 \
  -e POSTGRES_USER=workload -e POSTGRES_PASSWORD=disposable-workload-only \
  -e POSTGRES_DB=fastuuid7_workloads_run postgres:18.3
# Wait until docker exec fastuuid7-workloads-pg pg_isready -U workload succeeds.
export WORKLOAD_DSN=postgresql://workload:disposable-workload-only@127.0.0.1:55432/fastuuid7_workloads_run
export WORKLOAD_POSTGRES_IMAGE="$(docker image inspect postgres:18.3 --format '{{index .RepoDigests 0}}')"
benchmarks/workloads/.venv/bin/python -I benchmarks/workloads/run.py \
  --rows 100000 --batch-size 1000 --rounds 3 --output /tmp/workloads.json
docker stop fastuuid7-workloads-pg
```

The separate `PostgreSQL workloads` Actions workflow provides the same disposable
service and uploads raw JSON plus a Markdown report, named with the tested HEAD.
A missing competitor, wheel, API, database or failed verification fails the run;
there are no successful SKIP rows. Worker isolation (`-I`, fresh interpreter per
sample) prevents checkout shadowing of published fastuuid7 0.4.0 and avoids
cross-library process state. The candidate C extension must first be built by
the root `uv sync`; its location and digest are checked/recorded.

## Matrix and interpretation

Live UUIDv7 rows compare current checkout and published 0.4.0 scalar `uuid7()`
and `uuid7_many()`, Python 3.14 `uuid.uuid7()`, uuid-utils 1.0.0's stdlib-compatible
API, and uuid6 2025.0.1. All client IDs are stdlib UUID instances (subclasses
accepted), stored in a native PostgreSQL `uuid` primary key. No custom native
objects are silently treated as driver-compatible UUIDs. All conversion costs
for this representation are inside the measurement.

UUIDv4 is a separate control; its difference includes RNG/generation costs as
well as index locality. It cannot establish a UUIDv7-library speedup or isolate
index effects. PostgreSQL `uuidv7()` is a separate server strategy: INSERT/COPY
omits the ID column and the server fills the default. It sends fewer bytes and
moves generation CPU to PostgreSQL. This is not a client library comparison.

Historical rows import scrambled timestamps from a week in January 2020, with
eight records per millisecond. Current and published `uuid7_at(unix_ms=...)`
are compared with `uuid_utils.compat.uuid7(nanoseconds=...)`. A separately labeled
reference constructor uses Python `uuid.UUID` and 74 OS-random bits. It is **not**
a stdlib `uuid7` historical API. stdlib and uuid6 have no exact historical API in
this matrix. Entropy/counter/fork guarantees differ between libraries; small
uniqueness samples do not prove cryptographic or fork safety equivalence.

The historical generation adapter is the extension point for the separately
implemented `uuid7_at_many(*, unix_ms: Iterable[int])`. Future measurements must
use `--include-historical-batch` to add `checkout_at_batch` separately and run on the merged exact commit;
this task does not emulate it or claim results for unreleased code.

## Measurement contract

Each of 22 cases gets one full validated warmup and three measured runs, in
seeded random order. Each sample uses a fresh process, table and UUID index.
100,000 rows contain a UUID primary key, two bigint fields (source sequence and
event timestamp), and a fixed 128-byte text payload. Batches are 1,000 rows, one
transaction per complete sample. SQLAlchemy uses ORM `Session.execute(insert,
list_of_dicts)` without RETURNING; COPY uses psycopg binary `write_row` with
explicit UUID/int8/text types. The historical path is the same COPY path.

Elapsed time starts before generation/row construction and ends after commit.
Generation, row construction, execute/adaptation and commit phases are recorded.
Imports, connection setup, schema/table creation and verification are excluded.
Throughput is rows/elapsed. CPU is `process_time` for the client only; PostgreSQL
CPU is not measured. RSS is the fresh client's lifetime high-water read directly
after commit, before verification, including Python/import/connection baseline;
it is neither an allocation delta nor server memory. macOS bytes and Linux KiB
are normalized. This is a streaming-batch workload, not whole-import buffering.

After commit, SQL count/distinct count and a streamed reread of **every row**
verify row count, uniqueness, sequence, payload, version/variant and the 48-bit
millisecond layout. Historical timestamps must equal each source row exactly.
Live timestamps use a 100 ms clock tolerance; uuid6's documented logical clock
gets an explicit additional rows+1 ms allowance and its final clock lead is
reported. An initial generator sample must use the current wall timestamp.
Server UUIDs use server-side clock bounds, not a synchronized-clock assumption.

JSON records every sample, warmup, runtime/platform, pinned package versions,
PostgreSQL version/settings/image identity, source HEAD/status, source/lock and
compiled-extension hashes, volume, representation and repetition counts. Reports
include median and min/max, without unsupported statistical significance claims.

## Limitations and buffer decision

These initially empty tables, one client, warm caches and fixed-size payload do
not represent saturated storage, a growing production index, mixed reads/writes,
WAN connections or concurrent writers. Server CPU/RSS and isolated index-locality
benefits are unmeasured. Small apparent differences can be run-to-run noise.

Generation-phase share provides an optimistic bound on eliminating generation
cost entirely; it is not proof that a caller-owned UUID buffer saves that cost.
Driver adaptation and COPY framing remain in execute time. A buffer proposal
needs its own equivalent-representation, equivalent-guarantee benchmark including
framing and persistence verification. The present task adds no buffer API.

## Primary references

- [SQLAlchemy ORM bulk INSERT](https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#orm-bulk-insert-statements)
- [psycopg COPY and binary type adaptation](https://www.psycopg.org/psycopg3/docs/basic/copy.html)
- [PostgreSQL 18 UUID generation and extraction](https://www.postgresql.org/docs/18/functions-uuid.html)
- [Python 3.14 UUID API](https://docs.python.org/3.14/library/uuid.html)
- [uuid-utils 1.0.0](https://github.com/aminalaee/uuid-utils/tree/1.0.0)
- [uuid6 implementation](https://github.com/oittaa/uuid6-python)
