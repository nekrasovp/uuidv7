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
uv sync --python 3.14 --extra dev --locked --reinstall-package fastuuid7
uv sync --project benchmarks/workloads --locked
# Example disposable server (remove this task-owned container after the run):
docker run --name fastuuid7-workloads-pg --rm -d -p 127.0.0.1:55432:5432 \
  -e POSTGRES_USER=workload -e POSTGRES_PASSWORD=disposable-workload-only \
  -e POSTGRES_DB=fastuuid7_workloads_run postgres:18.3@sha256:7e32e9833a6fb1c92c32552794cb6ed569d51b445a54907d35fc112ef39684db
# Wait until docker exec fastuuid7-workloads-pg pg_isready -U workload succeeds.
export WORKLOAD_DSN=postgresql://workload:disposable-workload-only@127.0.0.1:55432/fastuuid7_workloads_run
export WORKLOAD_POSTGRES_IMAGE="$(docker image inspect postgres:18.3@sha256:7e32e9833a6fb1c92c32552794cb6ed569d51b445a54907d35fc112ef39684db --format '{{index .RepoDigests 0}}')"
benchmarks/workloads/.venv/bin/python -I benchmarks/workloads/run.py \
  --rows 100000 --batch-size 1000 --rounds 3 --include-historical-batch --output /tmp/workloads.json
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

The `--include-historical-batch` flag adds the implemented
`uuid7_at_many(*, unix_ms: Iterable[int])` as `checkout_at_batch` on the combined
0.5.0 source. The release workflow enables it. The retained 0.4.0 evidence below
predates that API and must not be relabeled as a measurement of historical batches.

## Measurement contract

Each of 22 baseline cases (23 with historical batch) gets one full validated warmup and three measured runs, in
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

## Executed evidence: PostgreSQL 18.3, 2026-09-17 UTC

[Actions run 35280765719](https://github.com/nekrasovp/uuidv7/actions/runs/35280765719)
completed all 66 measured samples and 22 warmups: 8.8 million rows committed and
fully reread. The tested source was clean HEAD
`032adad79e7f319139e093dbac8cd27c8402d5b8`. Raw artifact bytes are retained in
[`postgres18-032adad.json`](../benchmarks/workloads/results/postgres18-032adad.json)
and the [complete table](../benchmarks/workloads/results/postgres18-032adad.md).
Later evidence/documentation commits do not change that measurement's identity.

Environment: Ubuntu 24.04 hosted runner, x86-64, four logical CPUs, Python 3.14.6,
PostgreSQL 18.3 (pinned image digest in the workflow/report), fsync and
synchronous_commit on, shared_buffers 128 MB. Dependency versions are in the
lock and report. Only Python/SQLAlchemy/driver CPU is measured.

| Path, 100,000 rows | Checkout median | Published 0.4.0 median | stdlib UUIDv7 median | Checkout generation share |
|---|---:|---:|---:|---:|
| SQLAlchemy bulk, uuid7_many | 3.9555 s | 3.8157 s | 4.1306 s | 1.10% |
| Binary COPY, uuid7_many | 0.4865 s | 0.4749 s | 0.6879 s | 8.78% |
| Historical COPY, scalar uuid7_at | 0.6322 s | 0.6409 s | unavailable | 29.20% |

The checkout still contains the 0.4.0 generator: these are **not** measurements
of the future 0.5.0 historical batch implementation. Checkout and PyPI build
results fluctuate in either direction; no checkout improvement over 0.4.0 is
established. The new `--include-historical-batch` case must be rerun by the release
coordinator on the combined exact commit.

SQLAlchemy bulk spends 97.38% of elapsed time in execute/adaptation and uses
3.9425 client CPU seconds over 3.9555 elapsed seconds, pointing to the client
ORM/driver path as the main bottleneck here. Live COPY spends 81.23% in the
execute phase and uses only 0.1966 client CPU seconds over 0.4865 elapsed seconds;
this phase includes driver work, transport and database waits, which these
measurements cannot separate. COPY's median throughput is 205,555 rows/s versus
25,281 rows/s for SQLAlchemy bulk with checkout batch generation.

The historical scalar path spends 29.20% in generation and 63.38% in execution.
The pinned uuid-utils historical path reaches 0.5310 s (188,319 rows/s), while
checkout scalar reaches 0.6322 s (158,167 rows/s). This makes historical batching
worth measuring; it does not establish identical entropy/counter guarantees or
predict the new API's result. The reference OS-random constructor takes 0.6739 s.

PostgreSQL server UUIDv7 has separate medians of 3.4959 s for bulk INSERT and
0.4475 s for COPY. The UUIDv4 control has medians of 3.9840 s and 0.6903 s.
These differences include representation/transport and generator costs; they
must not be advertised as the benefit of one UUIDv7 library or of index ordering
alone. Three runs and small empty tables do not establish production rankings.

**Buffer conclusion:** eliminating the entire checkout generation phase could
remove only about 1.1% of bulk INSERT or 8.8% of live COPY time in this setup.
A caller-owned buffer would retain RNG/layout work and might affect adaptation,
which was not isolated. There is no measured benefit sufficient to justify a
new buffer API from this evidence. A future prototype should compare complete
binary COPY framing/adaptation with equal UUID guarantees and retained-row
verification. Historical batch generation is the more clearly motivated next
measurement, with a 29.2% generation share; no gain is claimed in advance.
