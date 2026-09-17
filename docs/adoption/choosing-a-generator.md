# Choose where and how to generate UUIDv7

Start with where the identifier must exist, then choose its representation.
Python 3.14's standard library is a good default for application code that
needs `uuid.UUID`. PostgreSQL 18 can generate the value as part of an insert.
Use fastuuid7 when you need the same application API on older Python, explicit
output shapes, batches, or exact historical timestamps.

This guide covers the released **0.4.0** scalar/live-batch APIs, source
`0386e15dc32fb2658e33518be77bae330db6556f`, and the accepted **0.5.0 candidate**
historical-batch API from [PR #10](https://github.com/nekrasovp/uuidv7/pull/10),
source `aefda263cfb81f0439e0f0f6df4be0d6d1165ce8`.
`uuid7_at_many()` requires that candidate or the subsequent 0.5.0 release;
it is not available in the published 0.4.0 package. Candidate availability and
measured application performance are separate facts.

## Decide at the boundary

| Requirement | Starting choice | Tradeoff to verify |
| --- | --- | --- |
| Python 3.14+, ordinary `uuid.UUID`, no measured generator bottleneck | `uuid.uuid7()` | No third-party generator dependency; benchmark only if profiling justifies it |
| PostgreSQL 18 owns row creation; ID can be returned after insertion | Column `DEFAULT uuidv7()` with `RETURNING id` | Generation depends on database access; include the actual transaction in performance comparisons |
| ID needed before persistence, in a queue, offline, or across several stores | Application-side generator | Persist and reuse IDs across retries; do not regenerate an ID for the same logical operation |
| Python 3.9–3.13 with a UUIDv7 API | `fastuuid7.uuid7()` | Check wheel availability for the interpreter/OS/architecture; source builds require a C toolchain |
| Consumer expects UUID text, raw bytes, or large batches | Explicit fastuuid7 output API | Measure generation plus conversion, serialization and delivery to that consumer |
| Backfill must encode an exact event millisecond | `fastuuid7.uuid7_at(unix_ms=...)` | Fresh random IDs are not deterministic; historical records have no within-millisecond call ordering |
| Backfill a bounded collection of timestamps | 0.5.0 candidate `fastuuid7.uuid7_at_many(unix_ms=...)` | Eager input validation and one UUID per item; O(n) memory; no measured 0.5.0 application speedup yet |

Python added `uuid.uuid7()` in 3.14 and documents a 48-bit timestamp plus a
42-bit counter for within-millisecond monotonicity.
[Python 3.14 documentation](https://docs.python.org/3.14/library/uuid.html#uuid.uuid7).
PostgreSQL 18's `uuidv7()` combines the current millisecond time,
sub-millisecond information and randomness; its optional interval shifts the
computed time. That relative shift is not an exact absolute-millisecond input
contract like `uuid7_at()`.
[PostgreSQL 18 documentation](https://www.postgresql.org/docs/18/functions-uuid.html).

On Python 3.14, a simple application needs only:

```python
from uuid import UUID, uuid7

event_id = uuid7()
assert isinstance(event_id, UUID) and event_id.version == 7
```

For a mixed Python fleet that needs only the common scalar API:

```python
try:
    from uuid import uuid7
except ImportError:
    from fastuuid7 import uuid7

event_id = uuid7()
assert event_id.version == 7
```

A corresponding application dependency can use the marker
`fastuuid7>=0.4.0,<0.5; python_version < '3.14'` while evaluating the released
0.4 line. Lock the selected version. When using fastuuid7-specific APIs,
install the package on every target interpreter and import it explicitly;
the fallback does not provide those functions.

## Application-side identity and retries

Generate an identifier when creating the logical event, store it in a durable
outbox with the payload, and reuse it for retries. This lets the same ID appear
in an API response, a queue message and the database row without asking the
database for an ID first. The outbox transaction and the consumer's uniqueness
or idempotency checks provide delivery semantics; a UUID generator does not.

Pass `uuid7` as a callable to ORM defaults, not `uuid7()` as a shared value.
Use the standard `uuid.UUID` output first with UUID-aware ORM/driver fields.
See the [SQLAlchemy, Django and Pydantic recipes](../integrations.md).
Their suitability still depends on the versions and paths your application
actually uses. A passing isolated example does not verify your service.

The [executable integration suite](https://github.com/nekrasovp/uuidv7/blob/f0b81a046f0c4246d6ba04651d0eede279c1f337/docs/integration-testing.md)
from [PR #9](https://github.com/nekrasovp/uuidv7/pull/9), source
`f0b81a046f0c4246d6ba04651d0eede279c1f337`, passed
[run 35280759469](https://github.com/nekrasovp/uuidv7/actions/runs/35280759469).
It executes SQLAlchemy, Django, Pydantic/FastAPI and psycopg paths with real
PostgreSQL 17 on Python 3.10/3.12/3.14, plus a separate UUID property matrix.
It checks serialization, commit/read-back, lookups and rejected inputs or
duplicate keys. These results cover the pinned tested combinations, not every
driver version or the untested combined 0.5.0 candidate. Frameworks are test
extras; ordinary tests without the enabled integration suite are not evidence
of its success. Follow that source's disposable-database setup and commands.
On Python before 3.14, a driver-loaded stdlib UUID preserves the bits but does
not inherit fastuuid7's UUIDv7 `.time` override; use `value.int >> 80` when
extracting its millisecond timestamp after verifying version 7.

If PostgreSQL 18 owns generation, this transaction illustrates the alternative:

```sql
BEGIN;
CREATE TEMP TABLE adoption_event (
    id uuid PRIMARY KEY DEFAULT uuidv7(),
    payload jsonb NOT NULL
);
INSERT INTO adoption_event (payload)
VALUES ('{"kind":"created"}'::jsonb)
RETURNING id, uuid_extract_version(id);
ROLLBACK;
```

The SQL requires PostgreSQL 18; it is not a measured workload or evidence of
external deployment. With an application-generated ID, pass that value to a
native `uuid` column instead. Server defaults apply when the ID is omitted;
choose deliberately which layer supplies each record's ID.

## Match the consumer's representation

| Scalar / batch API | Result | Appropriate boundary |
| --- | --- | --- |
| `uuid7()` / `uuid7_many(n)` | `uuid.UUID` / list of UUID objects | UUID-aware validation and database adapters |
| `uuid7_obj()` / `uuid7_obj_many(n)` | `UUID7Obj` / list of native objects | Internal code that explicitly accepts this type |
| `uuid7_str()` / `uuid7_str_many(n)` | Canonical lowercase text / list of strings | JSON, logs, text protocols |
| `uuid7_bytes()` / `uuid7_bytes_many(n)` | 16 bytes / one contiguous `16*n` byte buffer | Consumers with an explicit binary UUID contract |

`UUID7Obj` is a distinct type; UUID-like properties do not make every ORM,
validator or serializer accept it. Use a native object only when that boundary
has been tested. Each generation call makes a new identifier: changing the
representation of an existing ID means converting that value, not calling
another generator.

```python
import uuid

from fastuuid7 import uuid7, uuid7_bytes_many, uuid7_str_many

event_id = uuid7()
text = str(event_id)
raw = event_id.bytes
assert uuid.UUID(text) == uuid.UUID(bytes=raw) == event_id

text_ids = uuid7_str_many(128)  # 128 new, unrelated IDs
assert len(text_ids) == 128
packed = uuid7_bytes_many(128)  # another 128 new IDs, not the IDs above
assert len(packed) == 128 * 16
view = memoryview(packed)
first_view = view[:16]  # view into the buffer; no slice copy
first_uuid = uuid.UUID(bytes=bytes(first_view))  # explicit conversion copies
assert first_uuid.version == 7
```

The packed result is not a list of `bytes`. Do not pass it to an ORM expecting
individual UUID values or confuse its big-endian encoding with `bytes_le`.
Chunk large inputs so a single batch does not exhaust memory. Batch APIs reduce
call/allocation overhead; they still sample the wall clock for each UUID and
currently require the GIL. They do not promise parallel generation or total
ordering across processes. See [full contracts](../api.md).

## Backfill exact historical milliseconds

Use an aware UTC time and integer arithmetic; reject ambiguous naive inputs in
your importer. This recipe deliberately floors sub-millisecond precision:

```python
from datetime import datetime, timezone

from fastuuid7 import uuid7_at

created_at = datetime(2022, 2, 22, 19, 22, 22, 123000, tzinfo=timezone.utc)
epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
delta = created_at - epoch
unix_ms = (delta.days * 86400 + delta.seconds) * 1000 + delta.microseconds // 1000
record_id = uuid7_at(unix_ms=unix_ms)
assert record_id.time == unix_ms == 1_645_557_742_123
```

The keyword-only integer must be in `0..2**48-1`; booleans are rejected. The
other 74 bits use fresh OS randomness. Store the generated ID with the source
record's stable key before marking it migrated: rerunning the call will not
reconstruct the same ID. Keep a sequence column if records within one
millisecond need a stable order. Historical calls leave the live counter alone;
mixing historical and live results does not preserve call order.

### Historical batches in the 0.5.0 candidate

The accepted signature is
`uuid7_at_many(*, unix_ms: Iterable[int]) -> list[uuid.UUID]`. For example:

```python
# Requires the 0.5.0 candidate at aefda263cfb81f0439e0f0f6df4be0d6d1165ce8.
from fastuuid7 import uuid7_at_many

timestamps = [1_645_557_742_123, 0, 1_645_557_742_123]
assigned = uuid7_at_many(unix_ms=iter(timestamps))
assert [value.time for value in assigned] == timestamps
assert all(value.version == 7 for value in assigned)
assert uuid7_at_many(unix_ms=[]) == []
```

The finite iterable is eagerly snapshotted, then every element is validated
before the function generates any IDs or consumes generator entropy. Accepted
elements are integers other than booleans in `0..2**48-1`; type/range failures
raise `TypeError`/`ValueError` with an input index. Input order is retained;
timestamps are not sorted. Repeated timestamps receive independent random
values, not a deterministic mapping or monotonically ordered IDs.

Materialization consumes one-shot iterators and propagates iterator errors
before element validation. Iterator side effects cannot be rolled back.
Entropy/allocation failures return no partial list but can consume entropy for
earlier items. The historical generator leaves the live counter alone and
retains normal fork reset behavior. Input and output take O(n) memory; use
bounded chunks and never an infinite iterable. This API allocates its output
and does not write to a user-supplied buffer.

For a related-record backfill, persist the old-key → new-UUID mapping and
dependent foreign keys in the same transaction. Resume from committed mappings
instead of regenerating IDs. The candidate's
[runnable SQLite migration](https://github.com/nekrasovp/uuidv7/blob/aefda263cfb81f0439e0f0f6df4be0d6d1165ce8/examples/historical_migration/README.md)
demonstrates interruption and resume; it is not a PostgreSQL migration test.
The [full batch contract](https://github.com/nekrasovp/uuidv7/blob/aefda263cfb81f0439e0f0f6df4be0d6d1165ce8/docs/api.md#historical-batches)
and [migration notes](https://github.com/nekrasovp/uuidv7/blob/aefda263cfb81f0439e0f0f6df4be0d6d1165ce8/docs/integrations.md#resumable-migration-of-related-historical-records)
define failure and concurrency boundaries.

Before release publication, build the accepted candidate in a fresh checkout
to run the batch example:

```sh
git clone https://github.com/nekrasovp/uuidv7.git fastuuid7-historical-review
cd fastuuid7-historical-review
git checkout --detach aefda263cfb81f0439e0f0f6df4be0d6d1165ce8
uv sync --extra dev --locked
uv run --extra dev --locked pytest tests/test_historical_batch.py
```

Live fastuuid7 ordering is local to one generator process, including observed
clock rollback. It is not a distributed transaction order or a substitute for
an event timestamp column. UUIDv7 reveals time and is not an authentication
token. Releases through 0.2.x have different entropy/fork behavior; do not
transfer modern guarantees to an old lockfile.
[API](../api.md) · [Security policy](../../SECURITY.md).

## Evaluate before adopting

First run the smallest real path: create, serialize, validate, insert, read
back, retry. Record package/driver/database versions and an immutable source
commit. Then profile the complete operation, changing one generator at a time
while holding output type, persistence, concurrency and transaction size
constant. Report throughput, latency distribution, memory and any failures.

If generation is only a small part of the operation, replacing it has a small
ceiling on overall benefit. For example, a hypothetical 5% generator share and
a 5× faster generator imply at most `1 / (0.95 + 0.05 / 5) ≈ 1.04×` overall
speedup when everything else is unchanged. This is an arithmetic illustration,
not a fastuuid7 measurement. Use the
[feedback template](feedback-and-1.0.md) to record the actual outcome, including
no benefit or a decision to keep stdlib/server-side generation.

The [database study incorporated in the article](../articles/application-side-uuidv7.md#a-separate-postgresql-study-from-this-release-cycle)
now supplies one concrete evaluation: at source
`032adad79e7f319139e093dbac8cd27c8402d5b8` with the 0.4.0 generator, generation
accounted for roughly 1.1% of SQLAlchemy bulk time, 8.8% of live COPY and 29.2%
of historical scalar import. Those figures support measuring the whole path
and investigating historical batching. They do not prove that a new buffer or
historical-batch API improves the application, or describe concurrent production
traffic. See the article for environment, source artifacts and excluded costs.
