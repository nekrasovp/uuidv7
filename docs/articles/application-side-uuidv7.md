# UUIDv7 at the application boundary: choose the contract before the timer

**Technical article draft, 2026-09-18.** Intended for review during the fastuuid7
0.5.0 cycle; not yet published on an external platform. Released API examples
and published timings below refer to **fastuuid7 0.4.0**, source
`0386e15dc32fb2658e33518be77bae330db6556f`. No number below is a measurement of
0.5.0 or a production deployment.

A service may need an identifier before a database row exists. An API can
create an event, attach an ID to its durable outbox entry, then pass the same
ID to a worker and several stores. Another service can let its database own
the ID and retrieve it after insertion. Both are reasonable designs. The
useful first question is when the ID must exist; nanoseconds per call come
later.

UUIDv7 puts a millisecond timestamp near the front of the value. That gives
time-oriented keys without making a UUID a distributed sequence or a delivery
guarantee. Application clocks differ, retries happen, and a historical event
can be imported long after it occurred. Store the event's actual timestamp
and persist the generated ID across retries. A sortable identifier does not
replace those application decisions.

## Three places to start

Python 3.14 includes `uuid.uuid7()`, returning `uuid.UUID`. Its documented
counter preserves within-millisecond monotonicity. If that API meets the
application's needs, the standard library avoids an additional generator
dependency. [Python's UUID documentation](https://docs.python.org/3.14/library/uuid.html#uuid.uuid7).

PostgreSQL 18 offers `uuidv7()`, usable in a column default. With
`INSERT ... RETURNING id`, the database can generate and return the identifier
in the insert statement. It computes current time with sub-millisecond
information and randomness; an optional interval shifts the computed time.
This is a server-side generation contract, not a direct substitute for an ID
that must exist while the application is offline.
[PostgreSQL UUID functions](https://www.postgresql.org/docs/18/functions-uuid.html).

fastuuid7 supplies application-side generation for Python 3.9–3.14, plus
explicit text, bytes, native-object and batch paths. The PyPI name is
**fastuuid7** and the repository is **nekrasovp/uuidv7**. The legacy `uuidv7`
import is supported. **fastuuidv7**, from marcomq, is another project; similar
names are not evidence of shared behavior or users.

## Representation is part of the cost

An ORM's UUID field may expect a `uuid.UUID`. JSON needs text. A binary protocol
may want 16 bytes. These are different workloads: allocating an object and
formatting it later costs something that returning text directly can avoid.

In fastuuid7, `uuid7()` returns a standard-library-compatible UUID object;
`uuid7_obj()` returns a distinct native `UUID7Obj`. Its UUID-like interface
does not promise acceptance by an arbitrary validator or driver. Use the
compatibility object at those boundaries until adapter behavior is tested.
For a text-only boundary, `uuid7_str()` avoids a later object-to-text step.

```python
import uuid

from fastuuid7 import uuid7, uuid7_str

existing = uuid7()
payload_id = str(existing)  # same identifier, new representation
assert uuid.UUID(payload_id) == existing
new_payload_id = uuid7_str()  # a new identifier already in text form
assert uuid.UUID(new_payload_id).version == 7
```

The batch distinction is also concrete. `uuid7_many(n)` returns a list of
UUID objects, while `uuid7_bytes_many(n)` returns one `16*n` byte buffer.
Getting a buffer into the final consumer may require splitting, copying or
adapting it. Include that work in the measurement. The buffer alone is not a
database bulk-insert API.

## What the released 0.4.0 evidence says

The [0.4.0 release](https://github.com/nekrasovp/uuidv7/releases/tag/v0.4.0)
was published on 2026-09-17. Its
[benchmark run](https://github.com/nekrasovp/uuidv7/actions/runs/35191258668)
and [manifest](https://github.com/nekrasovp/uuidv7/releases/download/v0.4.0/benchmark-manifest.json)
identify source `0386e15dc32fb2658e33518be77bae330db6556f`.
The downloaded scalar and batch reports were checked against the manifest's
SHA-256 values during this review.

The scalar report records CPython **3.14.7**, Linux
`6.17.0-1022-azure-x86_64-with-glibc2.39`, one million iterations per round and
five rounds. Each case ran in a fresh worker process. These are the report's
environment values, not an inferred CPU model; no specific CPU model is
provided there.

| Scalar case | Return shape | Median ns/UUID |
| --- | --- | ---: |
| fastuuid7 0.3.0 `uuid7()` | `uuid.UUID` subclass | 282.1 |
| fastuuid7 0.4.0 `uuid7()` | `uuid.UUID` subclass | 289.4 |
| CPython 3.14.7 `uuid.uuid7()` | `uuid.UUID` | 1590.3 |
| fastuuid7 0.4.0 `uuid7_str()` | canonical text | 210.5 |
| fastuuid7 0.4.0 `str(uuid7())` | canonical text, including conversion | 838.8 |

Source: [published scalar report](https://github.com/nekrasovp/uuidv7/releases/download/v0.4.0/benchmark-results.md).
The secure 0.3.0 and 0.4.0 compatibility paths are close in this run; it does
not support a blanket speedup claim over 0.3.0. The two text rows demonstrate
why conversion belongs in a benchmark. The stdlib comparison is narrower than
a universal replacement claim: its fork guarantee was explicitly **not
verified** by this harness. The report labels OS entropy and process-local
ordering separately; a small uniqueness sample cannot establish RNG strength
or fork correctness.

The separate [batch report](https://github.com/nekrasovp/uuidv7/releases/download/v0.4.0/batch-results.md)
used batches of 10,000, five rounds, on the same reported Python/Linux family:

| Shape | Python loop median ns/UUID | C batch median ns/UUID | Reported ratio |
| --- | ---: | ---: | ---: |
| `uuid.UUID` list | 337.4 | 317.7 | 1.06× |
| canonical text list | 213.5 | 182.3 | 1.17× |
| contiguous bytes | 223.5 | 157.3 | 1.42× |

The bytes baseline joins scalar byte results into one buffer, matching the
batch output shape. These modest, shape-dependent ratios are more useful than
comparing raw native bytes with a Python UUID object. Batch and scalar runners
have different loop and allocation boundaries; do not combine their rows into
one ranking. Neither runner measures SQL insertion, JSON response latency,
peak resident memory or production throughput.

## Reproduce the evidence, then measure your boundary

Use a fresh directory, Git, uv, a supported C build toolchain and network
access to the pinned packages. Python 3.14 is needed for the stdlib comparison.
The recipe fixes the source revision; rerunning on another machine does not
reproduce the original timing values or necessarily its Python patch version.

```sh
git clone https://github.com/nekrasovp/uuidv7.git fastuuid7-040-review
cd fastuuid7-040-review
git checkout --detach 0386e15dc32fb2658e33518be77bae330db6556f
git rev-parse HEAD
git status --short
uv sync --python 3.14 --extra dev --locked
uv run --extra dev --locked pytest
mkdir -p /tmp/fastuuid7-040-review
uv --version
uv run --extra dev --locked python -VV
uv run --extra dev --locked python benchmarks/benchmark.py \
  --rounds 5 --output /tmp/fastuuid7-040-review/scalar.md
uv run --extra dev --locked python benchmarks/benchmark_competitors.py \
  --install-optional --rounds 5 --output /tmp/fastuuid7-040-review/competitors.md
uv run --extra dev --locked python benchmarks/benchmark_batch.py \
  --count 10000 --rounds 5 --output /tmp/fastuuid7-040-review/batch.md
```

Run timing commands sequentially on an otherwise quiet machine. The scalar
and competitor runners use temporary environments for published packages;
`--install-optional` permits their installation. Pins and primary-source
guarantee labels live in
[`competitors.json` at the release commit](https://github.com/nekrasovp/uuidv7/blob/0386e15dc32fb2658e33518be77bae330db6556f/benchmarks/competitors.json).
Retain Markdown and JSON sidecars, exit codes and every skip/rejection reason.
An unavailable wheel, failed conformance sample or skipped case is not a pass.
See the [release benchmark methodology](https://github.com/nekrasovp/uuidv7/blob/0386e15dc32fb2658e33518be77bae330db6556f/benchmarks/README.md).

To check the original report bytes independently of a rerun, this Python code
downloads only three public release assets and verifies both the expected
manifest and the two report hashes. It does not execute downloaded code:

```python
import hashlib
import json
import urllib.request

base = "https://github.com/nekrasovp/uuidv7/releases/download/v0.4.0/"
with urllib.request.urlopen(base + "benchmark-manifest.json", timeout=30) as response:
    manifest_bytes = response.read()
assert hashlib.sha256(manifest_bytes).hexdigest() == (
    "a284c1977837146bb3825be39dfcf08d8045717629d04485c6979f638eadf533"
)
manifest = json.loads(manifest_bytes)
assert manifest["source_commit"] == "0386e15dc32fb2658e33518be77bae330db6556f"
digests = {report["filename"]: report["sha256"] for report in manifest["reports"]}
for name in ("benchmark-results.md", "batch-results.md"):
    with urllib.request.urlopen(base + name, timeout=30) as response:
        data = response.read()
    assert hashlib.sha256(data).hexdigest() == digests[name], name
    print(name, "verified", digests[name])
```

For an application comparison, use the same payloads and resulting UUID type,
then include serialization, validation, adaptation, insertion and read-back.
Hold transaction size, indexes, connection setup and concurrency constant.
Compare server defaults inside actual insert transactions; an isolated SQL
function call and a Python generator loop have different costs. Report memory
as well as latency and throughput. A generator that occupies 5% of a request
cannot remove the other 95% of its work.

## Historical data has a different contract

Live fastuuid7 APIs advance a process-local monotonic generator. A historical
import instead needs the event's timestamp preserved exactly, even when it is
older than the last generated live ID. `uuid7_at()` was introduced for that
case:

```python
from fastuuid7 import uuid7_at

historical = uuid7_at(unix_ms=1_645_557_742_123)
assert historical.time == 1_645_557_742_123
assert historical.version == 7
```

The argument is an integer number of Unix milliseconds in `0..2**48-1`.
The remaining 74 bits use fresh OS randomness, without changing the live
generator's counter. Repeating the timestamp does not reconstruct the same ID
and does not order records within that millisecond. Persist the assigned value
with the source key so an interrupted migration can resume. Preserve a
separate sequence when the source order matters.
[Historical API contract](https://github.com/nekrasovp/uuidv7/blob/0386e15dc32fb2658e33518be77bae330db6556f/docs/api.md#historical-records).

## What external use currently tells us

The [public-source review](../adoption/public-evidence.md) found two application
code scenarios: SQLAlchemy primary keys in `ystdn-exp/identity-service`, locked
to 0.3.0, and RabbitMQ message IDs in `ISCOUTB/S.L.O.T.H`, locked to **0.1.0**
at the reviewed commit. A Windows source-packaging recipe also names this
repository and 0.4.0. Those are identifiable source facts. They are not
deployment confirmations or endorsements; **zero production deployments were
independently verified**. The old S.L.O.T.H lock cannot validate the entropy,
fork behavior or API of 0.4.0/0.5.0.

External benchmark harnesses reference this package too, while several search
hits were aliases for another library named `fastuuid`. Package identity must
be checked before making adoption claims. Download totals and stars do not
repair missing operational evidence.

Application-side IDs, direct output shapes and backfills are concrete things
to evaluate. How much they matter to real operators remains a question for
reproducible integrations and voluntary feedback. The
[adoption guide](../adoption/choosing-a-generator.md) gives practical choices,
and the [feedback template](../adoption/feedback-and-1.0.md) makes both a useful
improvement and a decision to retain stdlib or database generation recordable.

## Editorial state for the 0.5.0 cycle

At this draft's current evidence boundary, no verified 0.5.0 application report
has been incorporated. Before adding such findings, record the measured
commit, versions, exact commands, sample sizes, output shapes, all failure/skip
states and persistent report links. Explain what the complete workload
measures. Keep the published 0.4.0 table labeled as historical evidence; do not
relabel it or infer a 0.5.0 speedup from unchanged source.
