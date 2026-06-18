# UUIDv7 Competitor Benchmark

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Shape | Case | Package | Version | Return type | ops/sec | ns/op | Iterations |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| custom default object | `c_uuid_v7.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 28,810,871 | 34.7 | 1,000,000 |
| custom default object | `uuid7_rs.uuid7()` | `uuid7-rs` | 0.0.9 | `_UUID` | 27,754,339 | 36.0 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 24,246,698 | 41.2 | 1,000,000 |
| custom native object | `uuidv7.uuid7_obj()` | `fastuuid7` | 0.2.0 | `UUID7Obj` | 23,901,294 | 41.8 | 1,000,000 |
| string/default | `fastuuidv7.uuid7()` | `fastuuidv7` | 0.1.5 | `str` | 23,586,496 | 42.4 | 1,000,000 |
| bytes | `uuidv7.uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 23,064,536 | 43.4 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_int()` | `fastuuid7` | 0.2.0 | `int` | 21,762,025 | 46.0 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7()` | `fastuuid7` | 0.2.0 | `str` | 20,138,403 | 49.7 | 1,000,000 |
| string/default | `uuidv7.uuid7_str()` | `fastuuid7` | 0.2.0 | `str` | 18,900,102 | 52.9 | 1,000,000 |
| materialized string | `str(c_uuid_v7.uuid7())` | `c_uuid_v7` | 0.0.11 | `str` | 16,254,391 | 61.5 | 1,000,000 |
| materialized string | `str(uuid7_rs.uuid7())` | `uuid7-rs` | 0.0.9 | `str` | 14,433,957 | 69.3 | 1,000,000 |
| materialized string | `str(uuidv7.uuid7_obj())` | `fastuuid7` | 0.2.0 | `str` | 14,229,639 | 70.3 | 1,000,000 |
| uuid.UUID compat | `uuidv7.uuid7()` | `fastuuid7` | 0.2.0 | `_UUID7` | 12,682,084 | 78.9 | 1,000,000 |
| uuid/custom object | `uuid_utils.uuid7()` | `uuid-utils` | 0.16.1 | `UUID` | 11,889,960 | 84.1 | 1,000,000 |
| materialized string | `str(uuid_utils.uuid7())` | `uuid-utils` | 0.16.1 | `str` | 6,457,358 | 154.9 | 1,000,000 |
| uuid.UUID compat | `uuid7_rs.compat.uuid7()` | `uuid7-rs` | 0.0.9 | `UUID` | 3,171,403 | 315.3 | 1,000,000 |
| uuid.UUID compat | `c_uuid_v7.compat.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 2,789,118 | 358.5 | 1,000,000 |
| convenience string | `str(uuidv7.uuid7())` | `fastuuid7` | 0.2.0 | `str` | 1,965,018 | 508.9 | 1,000,000 |
| uuid.UUID compat | `uuid6.uuid7()` | `uuid6` | 2025.0.1 | `UUID` | 826,290 | 1,210.2 | 1,000,000 |
| uuid.UUID compat | `uuid_extensions.uuid7()` | `uuid7` | 0.1.0 | `UUID` | 790,553 | 1,264.9 | 1,000,000 |

## By API Shape

### C extension output

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7 C generate_uuid7_bytes()` | 24,246,698 | 41.2 | `bytes` |
| `uuidv7 C generate_uuid7_int()` | 21,762,025 | 46.0 | `int` |
| `uuidv7 C generate_uuid7()` | 20,138,403 | 49.7 | `str` |

### bytes

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_bytes()` | 23,064,536 | 43.4 | `bytes` |

### convenience string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuidv7.uuid7())` | 1,965,018 | 508.9 | `str` |

### custom default object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `c_uuid_v7.uuid7()` | 28,810,871 | 34.7 | `UUID` |
| `uuid7_rs.uuid7()` | 27,754,339 | 36.0 | `_UUID` |

### custom native object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_obj()` | 23,901,294 | 41.8 | `UUID7Obj` |

### materialized string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(c_uuid_v7.uuid7())` | 16,254,391 | 61.5 | `str` |
| `str(uuid7_rs.uuid7())` | 14,433,957 | 69.3 | `str` |
| `str(uuidv7.uuid7_obj())` | 14,229,639 | 70.3 | `str` |
| `str(uuid_utils.uuid7())` | 6,457,358 | 154.9 | `str` |

### string/default

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `fastuuidv7.uuid7()` | 23,586,496 | 42.4 | `str` |
| `uuidv7.uuid7_str()` | 18,900,102 | 52.9 | `str` |

### uuid.UUID compat

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7()` | 12,682,084 | 78.9 | `_UUID7` |
| `uuid7_rs.compat.uuid7()` | 3,171,403 | 315.3 | `UUID` |
| `c_uuid_v7.compat.uuid7()` | 2,789,118 | 358.5 | `UUID` |
| `uuid6.uuid7()` | 826,290 | 1,210.2 | `UUID` |
| `uuid_extensions.uuid7()` | 790,553 | 1,264.9 | `UUID` |

### uuid/custom object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuid_utils.uuid7()` | 11,889,960 | 84.1 | `UUID` |

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
