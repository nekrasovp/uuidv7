# API reference

All functions are available from both `fastuuid7` and `uuidv7`. New code should
use `fastuuid7`, which matches the distribution name.

## Scalar generation

| Function | Return type | Intended use |
| --- | --- | --- |
| `uuid7()` | `uuid.UUID` | Standard-library-compatible application API |
| `uuid7_obj()` | `UUID7Obj` | Lowest-overhead object with UUID-like properties |
| `uuid7_str()` | `str` | Canonical lowercase UUID text |
| `uuid7_bytes()` | `bytes` | One 16-byte big-endian UUID |

`UUID7Obj` is immutable, hashable, and orderable with other `UUID7Obj` values.
It exposes `int`, `bytes`, `bytes_le`, `hex`, `time`, `timestamp`, `urn`,
`version`, `variant`, and `fields` properties.

## Batch generation

| Function | Return type | Allocation shape |
| --- | --- | --- |
| `uuid7_many(count)` | `list[uuid.UUID]` | One list plus one object per UUID |
| `uuid7_obj_many(count)` | `list[UUID7Obj]` | One list plus one native object per UUID |
| `uuid7_str_many(count)` | `list[str]` | One list plus one string per UUID |
| `uuid7_bytes_many(count)` | `bytes` | One contiguous `count * 16` byte buffer |

Split a contiguous batch without copying by using a `memoryview`:

```python
from fastuuid7 import uuid7_bytes_many

raw = memoryview(uuid7_bytes_many(1_000))
first = raw[:16]
second = raw[16:32]
```

`count` must be a non-negative integer. A zero count returns an empty list or
`b""`, depending on the output shape. Negative counts raise `ValueError` and
non-integer counts raise `TypeError`.

## Ordering and time

UUIDs produced by the live scalar and batch APIs in one process are strictly increasing, including multiple
calls within the same millisecond and observed wall-clock rollback. The `time`
property is the embedded Unix timestamp in milliseconds.

Ordering is local to a generator process. UUIDv7 does not provide total
ordering between independent hosts or processes with unsynchronized clocks.

If advancing the counter would exhaust the 48-bit timestamp, generation raises
`OverflowError`; a batch returns no partial result. A failed batch may have
consumed counter values for earlier items before the error. Each item in a batch samples
the wall clock. These APIs currently require the GIL; free-threaded performance
or cross-interpreter ordering is not claimed.

## Historical records

```python
from fastuuid7 import uuid7_at

record_id = uuid7_at(unix_ms=1_645_557_742_123)
assert record_id.time == 1_645_557_742_123
```

`uuid7_at(*, unix_ms: int) -> uuid.UUID` preserves exactly the supplied Unix
timestamp in milliseconds. The argument is keyword-only to make units explicit.
Integers from `0` through `2**48 - 1` are accepted. Booleans and non-integers raise
`TypeError`; negative or out-of-range integers raise `ValueError`.

The remaining 74 bits are freshly drawn from the operating-system CSPRNG.
Calls at the same timestamp are unique with probabilistic UUID guarantees,
not deterministic or monotonically ordered. Different timestamps sort by their
embedded millisecond value. Historical calls do not read or advance the live
generator's timestamp/counter, even if the supplied timestamp is in the future.
They share the fork-aware entropy buffer and retain the same PID reset behavior.
Mixing historical and live results does not preserve call-order monotonicity.
