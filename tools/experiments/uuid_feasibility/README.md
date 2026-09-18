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

The dedicated `UUID feasibility research` workflow reproduces Linux Python
3.12/3.14. Source identity, package versions and lock/source/extension hashes
are embedded in results. Run heavy measurements sequentially on a quiet machine.
