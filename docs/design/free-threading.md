# ADR: free-threaded UUIDv7 generation

Status: **research complete; production integration not accepted**.
Scope: fastuuid7 0.5.0 research/tools, based on 0.4.0 commit
`0386e15dc32fb2658e33518be77bae330db6556f`. Production C/Python files,
dependency metadata, and release configuration are unchanged by this research.

## Decision

Retain the production GIL requirement. Recommend a future architecture with
one synchronized native sequence/entropy domain and separately owned Python
module state. The executable POSIX prototype supports investigation of that
architecture; it does not establish that the production extension is safe
without the GIL. Its measured scalar cost and contention do not justify
immediately integrating it. No free-threaded wheel, classifier, support claim,
or `Py_MOD_GIL_NOT_USED` declaration is added to the shipped extension.

## Baseline inventory

The inspected production files are `uuidv7/uuidv7_impl/src/uuid7_gen.c`,
`uuidv7/uuidv7_impl/uuid7_gen.c`, and `uuidv7/__init__.py` at the base above.

| State / operation | Current ownership and protection | Consequence without GIL |
| --- | --- | --- |
| `last_ms`, `counter`, `initialized` | Process static; no native lock | Lost updates, duplicate reservations, ordering violations |
| `process_id`, reset | PID comparison and state reset on each generation | Reset races with generation; PID detection alone cannot repair an inherited locked mutex |
| `entropy_pool[4096]`, `entropy_offset` | Shared by live and historical generation | Refill/read races, repeated or partially filled entropy |
| `urandom_fd` | Lazy process static on POSIX; retained across PID reset | Open/refill needs serialization; descriptor lifecycle needs an explicit owner |
| Windows precise-clock resolution flags/function pointer | Lazy static locals | Initialization also needs synchronization; absent from POSIX experiment |
| `uuid7_type`, `uuid7_safe_uuid`, `uuid_int_attr`, `uuid_is_safe_attr` | Static `PyObject*`, replaced/initialized globally | Interpreter ownership violation and configuration/reference races |
| `NativeUUID7Type` | Static Python type | Requires separate heap-type/lifetime review |
| Private PyLong digits, generic allocation, direct bytes/Unicode writes | GIL paths and unpublished results | Requires exact-version C API/allocation audit; this prototype does not port those paths |
| Scalar and batches | GIL held by production C calls; no explicit thread detachment | Existing serialization cannot be inferred when forcibly disabling GIL |

The production module uses single-phase initialization and `m_size=-1`.
Python-level `_UUID7`, `_SAFE_UUID_UNKNOWN`, and factory helpers are per
interpreter, but `_configure_uuid7()` copies their references into C globals.
One mutex around those globals would not make foreign-interpreter objects
valid. The current API explicitly declines cross-interpreter ordering support.

Baseline validation on ordinary CPython 3.14.6: all 65 repository tests passed.
The unmodified extension was separately compiled for CPython 3.14.6t. A fresh
default-mode process reported GIL **off before import, on after import**, with
the expected runtime warning; 1,000 generated values were unique and increasing.
This is a GIL fallback observation, not production no-GIL validation. The
baseline compiler also emitted the existing `_PyLong_New` deprecation warning.

## API guidance and implications

CPython's [free-threaded extension guide](https://docs.python.org/3.14/howto/free-threading-extensions.html)
requires an explicit support declaration; otherwise imports can enable the GIL.
Native shared state needs synchronization. Attached thread state still matters
with GIL disabled; blocking native work should detach. Critical sections around
Python objects can be suspended and are not a substitute for an uninterrupted
native reservation mutex. Borrowed references and direct object-field access
need review; mutable caches cannot simply be relabeled safe. Free-threaded
extensions require matching builds, without the regular stable ABI assumption.

The [extension isolation guide](https://docs.python.org/3.14/howto/isolating-extensions.html)
supports putting owned Python references into per-module state, using
multi-phase initialization and traverse/clear/free hooks. Truly native process
state is a deliberate exception requiring its own ownership design. The
[module C API](https://docs.python.org/3.14/c-api/module.html) distinguishes
free-threaded capability from multiple-interpreter capability: both declarations
need evidence, and neither declaration supplies synchronization.

Python [documents limitations of fork with threads](https://docs.python.org/3.14/library/os.html#os.fork),
including deprecation warnings for detected multithreaded `fork()` and macOS
restrictions. Passing an isolated atfork test cannot upgrade that platform
contract. These official sources were checked on 2026-09-18.

## Ordering contract to preserve

1. A live UUID reservation has a linearization point at the native commit of
   `(last_ms, counter)`, after all entropy reads for that item succeed.
2. Values increase in reservation order across scalar and batch live APIs,
   even with a fixed timestamp, backward clock movement, and counter carry.
   Reservations from one successful batch remain contiguous under one lock.
3. If call A completes before call B starts, B's values exceed A's. Concurrent
   calls may acquire the lock in either order. Allocation, GIL reattachment,
   OS scheduling, or caller work may invert their observed completion order.
   Sorting a shared append log by completion is not a linearizability test.
4. The prototype records sequence tickets under the same lock and checks both
   ticket/value agreement and real-time precedence. A pipe deliberately delays
   one call **after unlock but before return**: a later reservation completes
   first, while UUID value order remains correct. Negative controls reject
   duplicates, overlapping tickets, inverted values, and precedence violations.
5. Failure exposes no partial batch. Earlier committed items can leave gaps;
   failed entropy reads never commit the failing item. A later Python allocation
   failure may consume a full reservation. Rollback of published/native sequence
   state is forbidden. Historical UUIDs retain their exact timestamp and share
   entropy synchronization, without entering the live ordering contract.

This preserves a process sequence, not a per-thread or per-interpreter one.
It neither promises cross-process ordering after fork nor turns random UUID
uniqueness across processes into a mathematical guarantee.

## Alternatives

| Option | Ordering/ownership implications | Decision |
| --- | --- | --- |
| Keep required GIL | Preserves current supported behavior and cost | Retain in production |
| Only declare `Py_MOD_GIL_NOT_USED` | Adds no protection for native or Python globals | Reject |
| Per-thread or per-interpreter generators | Removes much contention, but independent counters can produce decreasing values when callers switch domains | Reject for existing live API; would require a separately named, explicitly weaker contract |
| Thread-local entropy with global sequence reservation | Could shorten the lock, but refill/fork lifecycle and committing failed reservations become more complex | Future optimization after a correct common sequencer; not measured here |
| Reserve counter ranges for later generation | Non-overlapping ranges alone do not preserve real-time order when an older range is used after a newer call finishes; timestamp/entropy and failure semantics also change | Not accepted without a new proof; not implemented |
| One mutex plus module-owned Python objects | Keeps one sequence and separates interpreter ownership | Recommended starting point, prototyped; throughput limited by shared state |
| Lock-free multiword sequence | Requires atomic timestamp/counter transition, entropy ownership, overflow and fork protocol | Defer; no executable evidence |

The comparisons for unimplemented alternatives are architectural reasoning,
not benchmark results. We did not trade away process-wide ordering to obtain
thread-scaling numbers.

## Executable prototype

The [harness](../../tools/experiments/free_threading/README.md) compiles a distinct
`_ft_uuid7` module. It includes the checked-out production generator source
without editing it, substituting only an entropy-read fault wrapper. The
original source and header digests are recorded with each run. It never imports
the production extension into the no-GIL correctness-test process.

A native pthread mutex spans PID checks, clock sampling per item, entropy
refill, sequence commits, and the full batch. The extension detaches thread
state before waiting/acquiring and unlocks before reattachment. No Python API,
Python callback, allocation, or refcount operation occurs while holding the
mutex. Packed bytes are allocated while attached and filled privately before
publication. All inputs are validated before generation.

The only Python cache is a strong reference to that module's `uuid.UUID` class,
initialized once using multi-phase execution and cleared by module lifetime
hooks. `as_uuid()` constructs objects outside the native mutex. Tests create
two interpreters concurrently, verify each cached type against its own `uuid`
module, generate 6,002 values in a shared reservation domain across repeated
create/destroy cycles, and check ordering, uniqueness, and main-interpreter
survival. This validates the prototype's ownership design; the production
`UUID7Obj` and `_UUID7` optimizations are not ported or accepted by that test.

Native process state survives module unload; it is not owned by one interpreter.
Atfork handlers are registered once per loaded image. Prepare acquires the
mutex, parent releases it, and child clears inherited counter/entropy state
before release. Child entropy failure proves inherited cached bytes are not
used. The inherited read-only random-device descriptor remains open, as in
baseline. These handlers allocate nothing and call no Python API. Their
lifetime, platform semantics, and interaction with other native libraries need
production review. A second copy of the shared library, embedding/reinitializing
Python, asynchronous cancellation, and third-party fork handlers are outside
the tested domain.

## Results

Local raw measurements and contract logs are captured under
`tools/experiments/free_threading/results/`. The reproduction driver records
compiler commands, exact source hashes, Python build, observed post-import GIL,
CPU/OS, iteration count, all timing samples, and skips separately.

The measured host was Apple M3 Pro, 12 logical CPUs, macOS arm64, using Apple
clang 21 with `-O3`, and uv-provided CPython 3.14.6 / 3.14.6t. Each throughput
cell uses the median of five 262,144-UUID rounds after warmup; APIs return packed
bytes, batch size 1 or 64. Thread creation is outside the timed region; barrier
release, scheduling, and result collection are inside. These are local
exploratory measurements without affinity or frequency control, not a portable
performance budget or an isolated estimate of mutex instruction cost.

| Packed-byte API / runtime | 1 thread | 2 threads | 4 threads | 8 threads |
| --- | ---: | ---: | ---: | ---: |
| Production baseline / regular GIL / batch 1 | 48.4 | 47.4 | 46.3 | 47.5 |
| Production baseline / t-build GIL fallback / batch 1 | 46.9 | 47.2 | 47.1 | 47.1 |
| Mutex prototype / regular GIL / batch 1 | 96.8 | 190.3 | 519.6 | 2882.8 |
| Mutex prototype / t-build no GIL / batch 1 | 82.3 | 123.3 | 178.9 | 284.9 |
| Production baseline / regular GIL / batch 64 | 32.8 | 33.0 | 32.9 | 32.2 |
| Production baseline / t-build GIL fallback / batch 64 | 32.0 | 31.7 | 32.0 | 32.2 |
| Mutex prototype / regular GIL / batch 64 | 34.1 | 41.5 | 58.9 | 60.7 |
| Mutex prototype / t-build no GIL / batch 64 | 34.2 | 42.5 | 56.7 | 59.4 |

Units: **ns per UUID**, lower is faster. Raw rounds and source digests:
[local evidence](../../tools/experiments/free_threading/results/macos-arm64-2026-09-18.json).

The single-thread scalar prototype costs 2.00x the regular baseline and
1.75x the t-build baseline with its GIL enabled. This includes argument
parsing, mutex, detach/reattach, and wrapper differences; it is not a pure lock
overhead measurement. With eight no-GIL threads and batch 64, instrumented
waiting accounts for 90.4% of summed native wait-plus-hold time;
p95 mutex wait is 190.2 microseconds. One thread is faster than eight
for this shared generator on this host. Batching amortizes Python-call cost,
but it does not provide parallel sequence generation.

Contention instrumentation runs separately and uses `CLOCK_MONOTONIC_RAW` where
available, recording its nominal resolution. A first exploratory run used
macOS `CLOCK_MONOTONIC`, whose quantization produced zero-duration samples for
short holds; the retained measurements use the raw clock. Instrumentation still
adds clock-call overhead and observed wait includes descheduling. Baseline has
no native wait counters; its throughput already includes GIL serialization.

The contract suite runs **18 tests**, with 135,000 mixed scalar/batch live UUIDs
across 1/2/4/8 threads, plus failure, historical, fork, and subinterpreter cases.
No duplicate or ordering violation was found in these executed samples.
This is finite test evidence, not a proof that races cannot exist.

## Remaining work before production acceptance

- Port and review every public scalar/batch/object path, private PyLong usage,
  `_configure_uuid7` replacement semantics, heap type creation, module teardown,
  and allocator-domain behavior. The prototype covers bytes and a simple UUID
  factory, not the complete production API.
- Add Windows synchronization/clock/entropy initialization and establish exact
  supported CPython/platform/wheel matrices. Local Windows and 3.13t runs,
  sanitizer/TSAN builds, debug allocator exhaustion, and long-duration stress
  were **not run** for this study. CI evidence, if available, is separate from
  local evidence and does not fill these gaps automatically.
- Establish race-detector and stress evidence for sequence, entropy, object
  lifetime, repeated imports and interpreter destruction; include malformed
  input and error paths. The simulated allocation failure is not real OOM.
- Resolve native singleton ownership on duplicate library loads and embedding
  lifetimes; define supported fork contexts and review handler ordering.
  No arbitrary multithreaded-fork safety claim follows from the diagnostic test.
- Measure representative object APIs, fairness/tail latency of large batches,
  unbounded entropy blocking, and single-thread overhead on Linux, macOS and
  Windows. Agree an explicit performance budget before changing the default.
- Require the coordinator's separate integration acceptance on the full shipped
  extension, installed wheels and source archive. Only then consider support
  declarations and packaging for free-threaded Python.

The research outcome is independently reviewable and complete with these
limitations. Future integration is a separate task, not a condition requiring
this study to wait for future users or claim unexecuted gates passed.
