# Free-threading research harness

This is an isolated experiment, **not a fastuuid7 runtime or supported API**.
It builds `_ft_uuid7` outside both shipped packages. `setup.py` never builds it.
The unchanged production extension is built into a separate baseline import
root. No additional Python dependencies are needed.

See the [architecture decision](../../../docs/design/free-threading.md)
for the state inventory, ordering contract, results, limitations, and integration
criteria. The harness targets POSIX CPython 3.13+ and a C11 compiler with pthreads;
the complete subinterpreter checks require Python 3.14.

## Reproduce

From a Git checkout or a source distribution containing these tools:

```sh
uv sync --extra dev --locked
uv run --extra dev --locked pytest
uv run --extra dev --locked python tools/experiments/free_threading/run.py \
  --output /tmp/uuid7-experiment-gil

uv python install 3.14t
"$(uv python find 3.14t)" tools/experiments/free_threading/run.py \
  --output /tmp/uuid7-experiment-free
```

Run these two measurements **sequentially** on an otherwise idle host. The
default is five rounds of 262,144 UUIDs for each 1/2/4/8-thread and 1/64-item
batch combination. Each throughput sample excludes contention instrumentation;
native mutex wait/hold samples are collected separately. Thread startup occurs
before a barrier; releasing the barrier, scheduling, and collecting futures are
included. No affinity, frequency, thermal, or external-load control is imposed.
`CC` may select the C compiler. Output paths should be outside the source tree.

`--no-benchmark` executes the contracts and production import probe only.
`--rounds 3 --uuids 65536` provides a shorter CI measurement. A Python 3.13 run
reports its missing public subinterpreter API as a **skip**, never a full pass.
Do not set `PYTHON_GIL`, use `-X gil=0`, or use `-O`: the driver rejects these.
GIL state is checked after imports. Baseline probing is isolated in a different
process, where the production extension may enable the GIL on a t build.

The output directory contains `build.log`, `checks.log`, `summary.json`, a
baseline import warning log, two benchmark JSON files, and compiler/source
provenance in `build/build.json`. Child processes have explicit timeouts; any
failure aborts the driver. Read logs before interpreting an incomplete output
directory. A successful benchmark alone says nothing about correctness.

## Files and boundaries

- `prototype.c`: includes the checked-out production algorithm without editing
  it; protects its native state with a process mutex and keeps its UUID class in
  per-module state. Test hooks inject entropy failures and controlled completion
  inversions. Hooks must never be copied into a production API.
- `build.py`: compiles the prototype with `-O3 -Wall -Wextra -Werror` and an
  unchanged baseline, recording source digests and exact compiler commands.
- `check.py`: stdlib-only concurrency, ordering, failure, ownership, and fork
  tests, including negative controls for the ordering oracle.
- `measure.py`: packed-bytes throughput and separate mutex contention samples.
- `run.py`: bounded build/check/probe/measure orchestration.
- `results/`: captured local evidence, including raw benchmark rounds.

`generate(count=1, timestamp=-1, audit=False, fail_pack=False,
historical=False, return_gate_fd=-1)` returns packed bytes, or
`(first_ticket, bytes, wait_ns, hold_ns)` in audit mode. A ticket is assigned under
the native mutex; it is an observation tool, not part of UUIDv7. `timestamp=-1`
samples the wall clock for **each item**. Historical generation uses the shared
entropy buffer but leaves the live counter/tickets unchanged.

The mutex spans every item of a batch. Object allocation happens before or
after this region, with no Python calls or refcount changes inside it. Failed
batches expose no prefix, but successful earlier reservations remain consumed.
The `fail_pack` hook simulates a result-allocation failure; it does not prove
actual allocator exhaustion behavior under all CPython allocators.

The native singleton is per loaded shared-library image. This experiment never
shares the prototype's counter with the production extension. Loading duplicate
copies of the shared library is outside the claimed process-sequence domain.
Fork checks use child processes: one after joined workers, and one diagnostic
case with the native mutex held. The latter is not a general guarantee for
forking arbitrary multithreaded Python programs.
