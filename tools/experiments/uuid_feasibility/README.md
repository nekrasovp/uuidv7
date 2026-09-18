# UUID feasibility laboratory

This directory is an isolated experiment. It does not change the installed
fastuuid7 API. Read [PROTOCOL.md](PROTOCOL.md) before interpreting a result.
All Python dependencies are in this directory's `uv.lock`.

```sh
cd tools/experiments/uuid_feasibility
uv sync --locked --python 3.14
.venv/bin/python build.py
.venv/bin/python -m pytest -q -o addopts='' test_contract.py
.venv/bin/python micro.py --prototype --processes 5 --values 3 --warmups 1 --min-time 0.05 -o /tmp/micro.json
.venv/bin/python http_bench.py --rounds 5 --duration 2 --output /tmp/http.json
.venv/bin/python extras.py memory --rounds 3 --output /tmp/memory.json
.venv/bin/python extras.py threads --rounds 5 --output /tmp/threads.json
.venv/bin/python extras.py profile --output /tmp/profile.json
```

For existing-library-only measurements omit `--prototype`. `micro.py` reports
scalar ns/UUID (32 varied inputs per timed function with inner-loop normalization)
and batch/model time per whole batch. `uuid_utils.compat.UUID` is stdlib's UUID
class, so the stdlib row covers it; explicit native-to-stdlib rows include the
conversion cost. Do not compare native and standard objects as identical APIs.

`http_bench.py` launches one uvicorn process at a time, with an independent
open-loop HTTP client, local proxy bypass, reusable connections and full response
checks. Fixed rates: path 300/900, batch and response 40/120, invalid 150/450
requests/s. Each variant/case gets a 0.5-second warmup, then the configured
measurement, five independently randomized repeats by default. Latency includes
time since the scheduled request, not just time after actual dispatch. The
reported client scheduling lag can identify measurements limited by the load
generator. Server CPU includes the final metrics request and has no subtraction;
low-volume absolute CPU measurements should be interpreted cautiously. Native
model rows implement an explicitly narrower integration (not full strict-mode
or universal Pydantic/ORM compatibility).

COPY requires a disposable database named `fastuuid7_feasibility*`; the harness
creates/drops only its own unique schema. For example with local PostgreSQL:

```sh
export UUID_LAB_DSN=postgresql://workload:disposable-workload-only@127.0.0.1:55333/fastuuid7_feasibility_local
.venv/bin/python extras.py copy --rounds 5 --rows 100000 --output /tmp/copy.json
```

Every row is reread after commit. Text input, native/packed conversion,
COPY adaptation, transport and commit are all in elapsed time; connection/DDL,
input creation and verification are outside it. Each sample uses a fresh process
and table. Server CPU and production concurrency are not measured.

Sanitizer fuzzing (clang with libFuzzer):

```sh
mkdir -p /tmp/uuid-fuzz-corpus
printf '01900000-0000-7000-8000-000000000001' > /tmp/uuid-fuzz-corpus/valid
clang -O1 -g -fsanitize=fuzzer,address,undefined fuzz.c -o /tmp/uuid-fuzz
/tmp/uuid-fuzz -runs=200000 -seed=9562 /tmp/uuid-fuzz-corpus
```

This covers the shared C text parser/formatter, not the entire CPython runtime.
Hypothesis tests cover bindings and adapter behavior. `NativeUUID` is immutable
and compares/hashes by value but does not implement the complete stdlib UUID
surface, pickle, subclassing or every driver integration. The module requires
the GIL and does not claim subinterpreter/free-threaded support. Releasing the
GIL for an owned batch buffer is not a declaration of free-threaded compatibility.
Private CPython integer construction is used; this prototype is not abi3.

UUIDv4 has two experiments: C object creation after a normal `os.urandom` call,
and direct Linux `getrandom` / macOS `arc4random_buf`. The latter have different
platform plumbing; neither uses an application-maintained entropy buffer.
Other generators' entropy/fork properties are not established by speed or small
uniqueness samples. No Windows direct-entropy implementation is included.

`packed_copy.py` is a separately identified consumer experiment using psycopg's
public binary Dumper API, scoped to each disposable connection. It compares
standard-object COPY with direct 16-byte UUID values, including slicing/framing
costs, and verifies every persisted row. It avoids assuming that packed values
must be converted back into stdlib UUIDs. Five randomized repeats plus a warmup
are fixed before its first run. Run with the same disposable `UUID_LAB_DSN`:

```sh
.venv/bin/python packed_copy.py --output /tmp/packed-copy.json
```

The direct-core supplement separates public TypeAdapter call overhead from
Pydantic's native schema validator, with the same standard UUID outputs:

```sh
.venv/bin/python core_baseline.py --processes 5 --values 3 --warmups 1 --min-time 0.05 -o /tmp/core-baseline.json
```

Memory RSS and tracemalloc runs use separate fresh processes so instrumentation
does not inflate the reported untraced RSS measurement.

The dedicated `UUID feasibility research` workflow is manually dispatched:
`full` reproduces the main Linux Python 3.12/3.14 matrix, while `supplement`
runs the direct-core and direct binary COPY consumers on Python 3.14. The
completed study originally ran from the two recorded research branches; the
final workflow is manual to avoid repeating long measurements on report edits.
Source identity, package versions and lock/source/extension hashes are embedded
in results. Run heavy measurements sequentially on a quiet machine.

The [decision report](../../../docs/design/uuid-feasibility.md) explains outcomes
and limitations. Retained raw evidence is under `results/`; regenerate the
deterministic summary without rerunning measurements:

```sh
python3 analyze.py results /tmp/uuid-summary.json
cmp results/summary.json /tmp/uuid-summary.json
```
