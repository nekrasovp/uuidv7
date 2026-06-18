# UUIDv7 Competitor Benchmark

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Shape | Case | Package | Version | Return type | ops/sec | ns/op | Iterations |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| custom default object | `c_uuid_v7.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 29,358,518 | 34.1 | 1,000,000 |
| custom default object | `uuid7_rs.uuid7()` | `uuid7-rs` | 0.0.9 | `_UUID` | 27,899,254 | 35.8 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 24,914,274 | 40.1 | 1,000,000 |
| bytes | `uuidv7.uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 24,767,824 | 40.4 | 1,000,000 |
| string/default | `fastuuidv7.uuid7()` | `fastuuidv7` | 0.1.5 | `str` | 24,204,494 | 41.3 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_int()` | `fastuuid7` | 0.2.0 | `int` | 23,668,577 | 42.3 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7()` | `fastuuid7` | 0.2.0 | `str` | 20,518,870 | 48.7 | 1,000,000 |
| string/default | `uuidv7.uuid7_str()` | `fastuuid7` | 0.2.0 | `str` | 20,470,895 | 48.8 | 1,000,000 |
| materialized string | `str(c_uuid_v7.uuid7())` | `c_uuid_v7` | 0.0.11 | `str` | 15,493,042 | 64.5 | 1,000,000 |
| materialized string | `str(uuid7_rs.uuid7())` | `uuid7-rs` | 0.0.9 | `str` | 15,336,130 | 65.2 | 1,000,000 |
| uuid.UUID compat | `uuidv7.uuid7()` | `fastuuid7` | 0.2.0 | `_UUID7` | 12,343,105 | 81.0 | 1,000,000 |
| uuid/custom object | `uuid_utils.uuid7()` | `uuid-utils` | 0.16.1 | `UUID` | 12,160,981 | 82.2 | 1,000,000 |
| materialized string | `str(uuid_utils.uuid7())` | `uuid-utils` | 0.16.1 | `str` | 6,749,396 | 148.2 | 1,000,000 |
| uuid.UUID compat | `uuid7_rs.compat.uuid7()` | `uuid7-rs` | 0.0.9 | `UUID` | 3,197,012 | 312.8 | 1,000,000 |
| uuid.UUID compat | `c_uuid_v7.compat.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 2,801,785 | 356.9 | 1,000,000 |
| convenience string | `str(uuidv7.uuid7())` | `fastuuid7` | 0.2.0 | `str` | 2,085,975 | 479.4 | 1,000,000 |
| uuid.UUID compat | `uuid6.uuid7()` | `uuid6` | 2025.0.1 | `UUID` | 835,751 | 1,196.5 | 1,000,000 |
| uuid.UUID compat | `uuid_extensions.uuid7()` | `uuid7` | 0.1.0 | `UUID` | 804,177 | 1,243.5 | 1,000,000 |

## By API Shape

### C extension output

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7 C generate_uuid7_bytes()` | 24,914,274 | 40.1 | `bytes` |
| `uuidv7 C generate_uuid7_int()` | 23,668,577 | 42.3 | `int` |
| `uuidv7 C generate_uuid7()` | 20,518,870 | 48.7 | `str` |

### bytes

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_bytes()` | 24,767,824 | 40.4 | `bytes` |

### convenience string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuidv7.uuid7())` | 2,085,975 | 479.4 | `str` |

### custom default object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `c_uuid_v7.uuid7()` | 29,358,518 | 34.1 | `UUID` |
| `uuid7_rs.uuid7()` | 27,899,254 | 35.8 | `_UUID` |

### materialized string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(c_uuid_v7.uuid7())` | 15,493,042 | 64.5 | `str` |
| `str(uuid7_rs.uuid7())` | 15,336,130 | 65.2 | `str` |
| `str(uuid_utils.uuid7())` | 6,749,396 | 148.2 | `str` |

### string/default

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `fastuuidv7.uuid7()` | 24,204,494 | 41.3 | `str` |
| `uuidv7.uuid7_str()` | 20,470,895 | 48.8 | `str` |

### uuid.UUID compat

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7()` | 12,343,105 | 81.0 | `_UUID7` |
| `uuid7_rs.compat.uuid7()` | 3,197,012 | 312.8 | `UUID` |
| `c_uuid_v7.compat.uuid7()` | 2,801,785 | 356.9 | `UUID` |
| `uuid6.uuid7()` | 835,751 | 1,196.5 | `UUID` |
| `uuid_extensions.uuid7()` | 804,177 | 1,243.5 | `UUID` |

### uuid/custom object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuid_utils.uuid7()` | 12,160,981 | 82.2 | `UUID` |

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
