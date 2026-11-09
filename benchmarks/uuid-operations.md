# UUID operation comparisons

`uuid_operations.py` measures scalar v4/v7 creation with immediate discard,
retention in a 64-element list, and conversion to canonical strings. These
lifetimes distinguish native sole-owner object reuse from real retained values.
Parsing covers standard and native objects, conversion back to stdlib objects,
packed output and batch APIs. Format cases distinguish object and byte inputs.

Every case checks output type, version/variant or parsed value outside timing.
The harness runs five independent processes in deterministic randomized case
order, calibrates each case to at least 25 ms, warms it up, and records three
samples per process. Report the median of process means and their range. GC is
disabled by timeit; input creation/validation is outside timing, result allocation
and deallocation are included. No microbenchmark proves HTTP or DB throughput.

References: uuid-utils **1.2.0**, legacy **0.19.0** in a separate environment,
fastuuidv7 **0.1.10**, fastuuid **0.14.0**. Native result types are not equivalent
to `uuid.UUID`; fastuuidv7 also uses non-cryptographic randomness. Comparing
strings equalizes representation, not entropy or ordering guarantees.

Build a wheel from a recorded source commit, create a dedicated Python 3.14
environment, install that wheel plus those pinned references, then run outside
the checkout:

```sh
/path/to/env/bin/python /path/to/repo/benchmarks/uuid_operations.py \
  --source-sha COMMIT --processes 5 --output /tmp/current.json
```

Repeat in a separate environment with uuid-utils 0.19.0. For a v7 regression
comparison, install fastuuid7 0.5.0 into another environment with otherwise
identical dependencies and the same interpreter. The harness omits unsupported
new operations on that baseline. Do not run competing measurements concurrently.

JSON retains interpreter identity, installed packages, extension/harness hashes,
individual timings, summaries and caveats. The `UUID operation benchmarks`
workflow repeats current/legacy comparisons on Linux Python 3.12 and 3.14 using
the PR head, independently from functional CI. Published reports must identify
the CPU and cannot attribute cross-runner differences solely to Python versions.
September research and prior report files remain unchanged.
