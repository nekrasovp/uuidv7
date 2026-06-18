# UUIDv7 Competitor Benchmark

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Shape | Case | Package | Version | Return type | ops/sec | best ns/op | median ns/op | Iterations | Rounds |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| custom default object | `c_uuid_v7.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 29,313,107 | 34.1 | 34.9 | 1,000,000 | 5 |
| custom default object | `uuid7_rs.uuid7()` | `uuid7-rs` | 0.0.9 | `_UUID` | 28,611,589 | 35.0 | 35.1 | 1,000,000 | 5 |
| custom native object | `uuidv7.uuid7_obj()` | `fastuuid7` | 0.2.0 | `UUID7Obj` | 28,056,053 | 35.6 | 36.2 | 1,000,000 | 5 |
| C extension output | `uuidv7 C generate_uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 25,873,666 | 38.6 | 39.7 | 1,000,000 | 5 |
| bytes | `uuidv7.uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 25,474,951 | 39.3 | 39.5 | 1,000,000 | 5 |
| string/default | `fastuuidv7.uuid7()` | `fastuuidv7` | 0.1.5 | `str` | 24,702,409 | 40.5 | 40.5 | 1,000,000 | 5 |
| C extension output | `uuidv7 C generate_uuid7_int()` | `fastuuid7` | 0.2.0 | `int` | 23,365,454 | 42.8 | 43.4 | 1,000,000 | 5 |
| string/default | `uuidv7.uuid7_str()` | `fastuuid7` | 0.2.0 | `str` | 20,895,972 | 47.9 | 48.8 | 1,000,000 | 5 |
| C extension output | `uuidv7 C generate_uuid7()` | `fastuuid7` | 0.2.0 | `str` | 20,749,939 | 48.2 | 49.0 | 1,000,000 | 5 |
| materialized string | `str(c_uuid_v7.uuid7())` | `c_uuid_v7` | 0.0.11 | `str` | 17,052,904 | 58.6 | 59.4 | 1,000,000 | 5 |
| materialized string | `str(uuid7_rs.uuid7())` | `uuid7-rs` | 0.0.9 | `str` | 16,622,199 | 60.2 | 60.6 | 1,000,000 | 5 |
| materialized string | `str(uuidv7.uuid7_obj())` | `fastuuid7` | 0.2.0 | `str` | 15,249,755 | 65.6 | 67.0 | 1,000,000 | 5 |
| uuid.UUID compat | `uuidv7.uuid7()` | `fastuuid7` | 0.2.0 | `_UUID7` | 13,328,017 | 75.0 | 75.6 | 1,000,000 | 5 |
| uuid/custom object | `uuid_utils.uuid7()` | `uuid-utils` | 0.16.1 | `UUID` | 12,215,938 | 81.9 | 82.8 | 1,000,000 | 5 |
| materialized string | `str(uuid_utils.uuid7())` | `uuid-utils` | 0.16.1 | `str` | 6,931,823 | 144.3 | 146.3 | 1,000,000 | 5 |
| uuid.UUID compat | `uuid7_rs.compat.uuid7()` | `uuid7-rs` | 0.0.9 | `UUID` | 3,258,733 | 306.9 | 310.2 | 1,000,000 | 5 |
| uuid.UUID compat | `c_uuid_v7.compat.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 2,852,392 | 350.6 | 354.5 | 1,000,000 | 5 |
| convenience string | `str(uuidv7.uuid7())` | `fastuuid7` | 0.2.0 | `str` | 2,147,728 | 465.6 | 467.7 | 1,000,000 | 5 |
| uuid.UUID compat | `uuid6.uuid7()` | `uuid6` | 2025.0.1 | `UUID` | 857,892 | 1,165.6 | 1,177.5 | 1,000,000 | 5 |
| uuid.UUID compat | `uuid_extensions.uuid7()` | `uuid7` | 0.1.0 | `UUID` | 815,292 | 1,226.6 | 1,246.9 | 1,000,000 | 5 |

## By API Shape

### C extension output

| Case | ops/sec | best ns/op | median ns/op | Return type |
| --- | ---: | ---: | ---: | --- |
| `uuidv7 C generate_uuid7_bytes()` | 25,873,666 | 38.6 | 39.7 | `bytes` |
| `uuidv7 C generate_uuid7_int()` | 23,365,454 | 42.8 | 43.4 | `int` |
| `uuidv7 C generate_uuid7()` | 20,749,939 | 48.2 | 49.0 | `str` |

### bytes

| Case | ops/sec | best ns/op | median ns/op | Return type |
| --- | ---: | ---: | ---: | --- |
| `uuidv7.uuid7_bytes()` | 25,474,951 | 39.3 | 39.5 | `bytes` |

### convenience string

| Case | ops/sec | best ns/op | median ns/op | Return type |
| --- | ---: | ---: | ---: | --- |
| `str(uuidv7.uuid7())` | 2,147,728 | 465.6 | 467.7 | `str` |

### custom default object

| Case | ops/sec | best ns/op | median ns/op | Return type |
| --- | ---: | ---: | ---: | --- |
| `c_uuid_v7.uuid7()` | 29,313,107 | 34.1 | 34.9 | `UUID` |
| `uuid7_rs.uuid7()` | 28,611,589 | 35.0 | 35.1 | `_UUID` |

### custom native object

| Case | ops/sec | best ns/op | median ns/op | Return type |
| --- | ---: | ---: | ---: | --- |
| `uuidv7.uuid7_obj()` | 28,056,053 | 35.6 | 36.2 | `UUID7Obj` |

### materialized string

| Case | ops/sec | best ns/op | median ns/op | Return type |
| --- | ---: | ---: | ---: | --- |
| `str(c_uuid_v7.uuid7())` | 17,052,904 | 58.6 | 59.4 | `str` |
| `str(uuid7_rs.uuid7())` | 16,622,199 | 60.2 | 60.6 | `str` |
| `str(uuidv7.uuid7_obj())` | 15,249,755 | 65.6 | 67.0 | `str` |
| `str(uuid_utils.uuid7())` | 6,931,823 | 144.3 | 146.3 | `str` |

### string/default

| Case | ops/sec | best ns/op | median ns/op | Return type |
| --- | ---: | ---: | ---: | --- |
| `fastuuidv7.uuid7()` | 24,702,409 | 40.5 | 40.5 | `str` |
| `uuidv7.uuid7_str()` | 20,895,972 | 47.9 | 48.8 | `str` |

### uuid.UUID compat

| Case | ops/sec | best ns/op | median ns/op | Return type |
| --- | ---: | ---: | ---: | --- |
| `uuidv7.uuid7()` | 13,328,017 | 75.0 | 75.6 | `_UUID7` |
| `uuid7_rs.compat.uuid7()` | 3,258,733 | 306.9 | 310.2 | `UUID` |
| `c_uuid_v7.compat.uuid7()` | 2,852,392 | 350.6 | 354.5 | `UUID` |
| `uuid6.uuid7()` | 857,892 | 1,165.6 | 1,177.5 | `UUID` |
| `uuid_extensions.uuid7()` | 815,292 | 1,226.6 | 1,246.9 | `UUID` |

### uuid/custom object

| Case | ops/sec | best ns/op | median ns/op | Return type |
| --- | ---: | ---: | ---: | --- |
| `uuid_utils.uuid7()` | 12,215,938 | 81.9 | 82.8 | `UUID` |

## Skipped

| Case | Package | Reason | Source |
| --- | --- | --- | --- |
| `stdlib uuid.uuid7()` | `python` | not available on this Python runtime | https://docs.python.org/3/library/uuid.html#uuid.uuid7 |
| `uuid_v7.uuid7()` | `uuid-v7` | uuid_v7.uuid7 not found | https://pypi.org/project/uuid-v7/ |

## Sources

| Package | Source |
| --- | --- |
| `c_uuid_v7` | https://github.com/lava-sh/c_uuid_v7 |
| `fastuuid7` | local candidate |
| `fastuuidv7` | https://pypi.org/project/fastuuidv7/ |
| `python` | https://docs.python.org/3/library/uuid.html#uuid.uuid7 |
| `uuid-utils` | https://pypi.org/project/uuid-utils/ |
| `uuid-v7` | https://pypi.org/project/uuid-v7/ |
| `uuid6` | https://pypi.org/project/uuid6/ |
| `uuid7` | https://pypi.org/project/uuid7/ |
| `uuid7-rs` | https://github.com/lava-sh/uuid7-rs |
