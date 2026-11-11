# UUID formatting, parsing and FastAPI/Pydantic comparison

This benchmark compares an **installed candidate wheel**, published fastuuid7
**0.6.0** (`d733169281a1d8039a891e6334aa6281007fd638`), and uuid-utils **1.2.0**.
It does not install a framework adapter into either production library.

## Protocol (declared before the measurements)

- Use the same interpreter, CPU and `uv.lock` dependencies for every variant.
  The baseline environment resolves PyPI 0.6.0; the candidate environment starts
  from the identical lock, then replaces only fastuuid7 with the built wheel.
  The candidate version is read from that installed wheel; only fastuuid7's
  version may differ from the baseline, while all other packages remain identical.
  Check every installed candidate runtime file against that wheel. Record wheel,
  native-extension, Python wrapper, harness, corpus and lock hashes.
- Run five independent processes/repeats, sequentially, with deterministic
  randomized provider/case order. Never run two measured providers concurrently.
  Interleave baseline/candidate UUID workers within each repeat. Preserve all
  results, including losses, failed runs and scheduler overload.
- UUID microbenchmarks use the existing lifetime/output-shape protocol, adding
  pure formatting of pre-created native UUIDs and `format_uuid(uuid4/7())`.
  Median process means and ranges retain the five independent worker values.
- Pydantic cases separately measure JSON validation, serialization of an already
  parsed model, the full validate-and-dump path, and invalid input. Payload sizes
  are 1, 64 and 1,000 UUIDs; inputs contain deterministic, varied v4/v7 values.
  Each case warms/calibrates to >=25 ms and takes three timed values per process.
- HTTP uses a separate uvicorn process, one worker, asyncio/h11 and actual TCP
  bound only to `127.0.0.1` through an inherited socket. Startup and warmup are
  outside timing. A separate client offers fixed rates, checks every response,
  and records scheduled-to-response p50/p95/p99 latency and scheduling lag.
  Server CPU/request excludes the client's CPU. RSS is a lifetime high-water
  mark, not allocation or server-only UUID memory. Metrics endpoint overhead
  remains in server CPU and is shared by all variants.
- HTTP scenarios: UUID path parameter, JSON body with 1 or 1,000 UUIDs, a prepared
  1,000-UUID response, invalid UUID (422 and exact error location), and generation
  of 64 UUIDv4 or UUIDv7 values through model defaults and a response model.
  There are two predeclared rates per scenario, 0.25 s warmup and 1 s measurement
  per repeat. These are fixed-load latency/CPU observations, not capacity RPS.
- Mark a repeat with p99 client scheduling lag >100 ms as overloaded. Keep it in
  the data and do not use it to claim application improvement. Tail estimates
  from small request counts are exploratory. Bootstrap paired repeat/process
  means (5,000 resamples) for exploratory 95% intervals; no multiple-comparison
  correction or production statistical significance is claimed.
- Keep core optimizations only after negative/property/sanitizer checks and a
  repeatable targeted microbenchmark improvement. Recommend a framework adapter
  for speed only after a >=10% server CPU reduction repeats across measured
  configurations/rates, intervals exclude zero, and latency does not regress.
  Otherwise report the application result as inconclusive or a regression.

## Variants and equivalence

| Variant | Parsing / serialization | Generation | Python values |
|---|---|---|---|
| baseline-default | Built-in Pydantic UUID handling | fastuuid7 0.6.0 | stdlib-compatible UUID |
| candidate-default | Built-in Pydantic UUID handling | Candidate | stdlib-compatible UUID |
| baseline-explicit | Benchmark-only scalar/bulk parser and formatter callbacks | fastuuid7 0.6.0 | stdlib UUID |
| candidate-explicit | Same explicit callbacks | Candidate | stdlib UUID |
| uuid-utils-compat | Built-in Pydantic UUID handling | uuid-utils.compat | stdlib UUID |
| uuid-utils-native | Benchmark-only native parser and string serializer | uuid-utils | native UUID |

The native row has equivalent canonical JSON, **not** an interchangeable Python
type or full strict-mode/driver contract. Fastuuid7's strict text grammar is not
the entire Pydantic/stdlib constructor grammar. Explicit adapters fall back to
Pydantic for unsupported inputs and preserve tested errors/strict modes; they
are comparison fixtures, not a supported public integration. Contract tests
also cover malformed JSON, invalid path parameters and UUID version/layout.

## Reproduce

POSIX host with CPython 3.12 or 3.14; run from a clean recorded commit:

```sh
uv build --python 3.14 --wheel
uv sync --project benchmarks/api --python 3.14 --locked
uv export --project benchmarks/api --locked --no-dev --format requirements-txt --output-file /tmp/uuid-api-requirements.txt > /dev/null
uv venv --python 3.14 /tmp/uuid-api-candidate
uv pip sync --python /tmp/uuid-api-candidate/bin/python --require-hashes /tmp/uuid-api-requirements.txt
uv pip install --python /tmp/uuid-api-candidate/bin/python --reinstall-package fastuuid7 --no-deps dist/*.whl
```

From a directory outside the checkout, run `test_contracts.py` in both environments
with `python -m pytest --import-mode=importlib /checkout/benchmarks/api/test_contracts.py`.
Then run `micro_compare.py` and `run.py` **sequentially**, using the same arguments:

```text
--candidate-python /tmp/uuid-api-candidate/bin/python
--baseline-python /checkout/benchmarks/api/.venv/bin/python
--candidate-wheel /checkout/dist/fastuuid7-<candidate-version>-<wheel-tags>.whl
--work-dir /tmp
--output /tmp/<micro-or-api>.json
```

Use the baseline interpreter to run the harness. Run `analyze.py --api
/tmp/api.json --micro /tmp/micro.json --output /tmp/summary.json` to reproduce
the JSON/Markdown summary. Analysis refuses incomplete or dirty-source results.
The `API and UUID comparison` workflow repeats this on Linux 3.12 and 3.14 and
retains raw reports plus server logs even when a job fails. The lock's published
0.6.0 reference must remain independent from the candidate checkout.
