# UUID operations: 2026-11-09 measurements

Production source: `4e47ca2c8b7ed85e4b74cdbf06982322944563d7`.
Base release: `4d9912368da259590c31092837fc985bda8a3951` / fastuuid7 0.5.0.
The candidate still reports 0.5.0 until a release version is assigned; source SHA
and extension hash distinguish it from the published wheel. The later prototype
fork-handler fix and report updates do not change production code.

## Method and identities

See [the protocol](../../uuid-operations.md). Five independent processes, three
calibrated samples per case/process, 64 UUIDs per timed block, randomized case
order. Values below are medians of process means, in **ns per UUID**, including
loop/list allocation costs. Raw files include every sample, package and
interpreter identity, extension/harness hashes and process-mean ranges.
No timings are removed as outliers. Runs were sequential on each host.

| Environment | Interpreter | CPU | Visible CPUs |
| --- | --- | --- | ---: |
| macOS arm64 | 3.14.6 | Apple M3 Pro | 12 |
| Linux x86-64 A | 3.12.16 | AMD EPYC 9V45 96-Core Processor | 4 |
| Linux x86-64 B | 3.14.10 | AMD EPYC 7763 64-Core Processor | 4 |

Reference packages: uuid-utils 1.2.0, fastuuidv7 0.1.10, fastuuid 0.14.0.
The separate legacy runs use uuid-utils 0.19.0 with the same other packages.
Local Python is the same 3.14.6 interpreter used for the earlier study. Linux
3.12 and 3.14 ran on different CPU models: do not infer a Python-version effect.
Hosted results: [Linux run 42579480799](https://github.com/nekrasovp/uuidv7/actions/runs/42579480799).

## Equal standard-object output, retained in a list

| Environment | v4 candidate | v4 uuid-utils.compat | v4 ratio | v7 candidate | v7 uuid-utils.compat | v7 ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| macOS arm64 | 86.0 | 228.2 | 2.65× | 84.5 | 275.2 | 3.26× |
| Linux x86-64 A | 106.3 | 465.1 | 4.38× | 118.6 | 571.4 | 4.82× |
| Linux x86-64 B | 202.5 | 622.2 | 3.07× | 218.8 | 759.6 | 3.47× |

Ratios are competitor time / candidate time for the same representation and
lifetime, not universal performance guarantees. Both return standard UUIDs;
the measurements do not establish identical entropy/fork/ordering contracts.

Legacy uuid-utils 0.19.0 retained standard-object results:

| Environment | v4 candidate | v4 compat | v7 candidate | v7 compat |
| --- | ---: | ---: | ---: | ---: |
| macOS arm64 | 86.2 | 230.8 | 84.2 | 264.2 |
| Linux x86-64 A | 107.5 | 451.0 | 120.4 | 530.6 |
| Linux x86-64 B | 202.2 | 614.0 | 219.2 | 724.7 |

## Parsing and formatting

| Environment | parse → std UUID | stdlib constructor | parse_many → std UUID | parse_bytes_many | format UUID | str(UUID) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| macOS arm64 | 70.1 | 426.4 | 61.3 | 25.3 | 110.7 | 250.0 |
| Linux x86-64 A | 84.4 | 742.7 | 77.6 | 22.5 | 133.0 | 424.7 |
| Linux x86-64 B | 188.2 | 1059.6 | 168.0 | 57.1 | 273.3 | 629.8 |

Packed output is a different contract and should only be compared with the
`packed/*` cases in raw data. The constructor comparison uses canonical valid
text; fastuuid7 intentionally accepts a narrower grammar than uuid.UUID.
These gains do not supersede the September finding about FastAPI request costs:
no automatic Pydantic validator replacement or application throughput gain is
claimed. Invalid inputs are covered by tests/fuzzing, not timed here.

## Object lifetime and limits

On macOS, fastuuidv7 native v7 takes 14.1 ns with immediate discard versus 35.3 ns with retention. Its native result and non-cryptographic RNG differ from standard-object,
OS-CSPRNG generation. Native-output parsers can also be faster: macOS
uuid-utils/fastuuid parse takes 62.9/50.6 ns, while candidate parsing into stdlib UUID takes 70.1 ns.
The raw native-to-stdlib cases include conversion cost. No claim of being
fastest for every shape follows from the retained standard-object table.

The initial implementation still checked getpid on every UUID. Its raw files
(`before-hook-*`) are retained: v4 lost to uuid-utils.compat on one Linux 3.14
runner. Native pthread_atfork invalidation removes that per-call syscall,
retaining PID checking if registration fails. New Linux runners differ from
the initial runners, whose CPU models were not recorded: the tables above
support within-run competitor comparisons, not a precise before/after causal
speedup. They also do not establish Windows performance.

The released-0.5.0 macOS baseline used the same interpreter/reference pins.
Its retained v7 process means range from 84.8 to 147.9 ns (median 94.1), so no
small v7 regression/improvement claim is made from that noisy comparison.
The candidate passed ordering, clock, fork, and failure tests independently.

## Decision

Ship the bounded UUIDv4 and standard-object parsing/formatting APIs through
normal review/release checks. The current measurements support their value as
standalone operations. Keep native general UUID objects, ABI3 and free-threaded
production generation as separate projects; the existing UUID7Obj remains v7-only.
Explicit SDK run IDs are supported; SDK defaults are not patched.
