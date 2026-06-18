# Docker Benchmark

- Docker image: `python:3.12-bookworm`
- Profile: `uuidv7`
- Iterations per case: 1000000
- Benchmark command: `python benchmarks/benchmark_competitors.py --install-optional --iterations 1000000`

Python/runtime: Python 3.12.13
# UUIDv7 Competitor Benchmark

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.36
- Machine: x86_64
- CPU: unknown
- Python: 3.12.13

## Results

| Shape | Case | Package | Version | Return type | ops/sec | ns/op | Iterations |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| custom default object | `uuid7_rs.uuid7()` | `uuid7-rs` | 0.0.9 | `_UUID` | 16,302,353 | 61.3 | 1,000,000 |
| custom default object | `c_uuid_v7.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 16,278,576 | 61.4 | 1,000,000 |
| string/default | `fastuuidv7.uuid7()` | `fastuuidv7` | 0.1.5 | `str` | 13,712,741 | 72.9 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_int()` | `fastuuid7` | 0.2.0 | `int` | 13,150,732 | 76.0 | 1,000,000 |
| bytes | `uuidv7.uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 12,847,690 | 77.8 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 12,253,494 | 81.6 | 1,000,000 |
| string/default | `uuidv7.uuid7_str()` | `fastuuid7` | 0.2.0 | `str` | 11,866,739 | 84.3 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7()` | `fastuuid7` | 0.2.0 | `str` | 11,455,883 | 87.3 | 1,000,000 |
| uuid/custom object | `uuid_utils.uuid7()` | `uuid-utils` | 0.16.0 | `UUID` | 8,593,774 | 116.4 | 1,000,000 |
| materialized string | `str(uuid7_rs.uuid7())` | `uuid7-rs` | 0.0.9 | `str` | 8,361,312 | 119.6 | 1,000,000 |
| materialized string | `str(c_uuid_v7.uuid7())` | `c_uuid_v7` | 0.0.11 | `str` | 8,235,990 | 121.4 | 1,000,000 |
| materialized string | `str(uuid_utils.uuid7())` | `uuid-utils` | 0.16.0 | `str` | 4,591,091 | 217.8 | 1,000,000 |
| uuid.UUID compat | `uuidv7.uuid7()` | `fastuuid7` | 0.2.0 | `_UUID7` | 2,065,888 | 484.1 | 1,000,000 |
| uuid.UUID compat | `uuid7_rs.compat.uuid7()` | `uuid7-rs` | 0.0.9 | `UUID` | 1,514,742 | 660.2 | 1,000,000 |
| uuid.UUID compat | `c_uuid_v7.compat.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 1,397,904 | 715.4 | 1,000,000 |
| convenience string | `str(uuidv7.uuid7())` | `fastuuid7` | 0.2.0 | `str` | 868,692 | 1,151.2 | 1,000,000 |
| uuid.UUID compat | `uuid6.uuid7()` | `uuid6` | 2025.0.1 | `UUID` | 507,346 | 1,971.0 | 1,000,000 |
| uuid.UUID compat | `uuid_extensions.uuid7()` | `uuid7` | 0.1.0 | `UUID` | 472,799 | 2,115.1 | 1,000,000 |

## By API Shape

### C extension output

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7 C generate_uuid7_int()` | 13,150,732 | 76.0 | `int` |
| `uuidv7 C generate_uuid7_bytes()` | 12,253,494 | 81.6 | `bytes` |
| `uuidv7 C generate_uuid7()` | 11,455,883 | 87.3 | `str` |

### bytes

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_bytes()` | 12,847,690 | 77.8 | `bytes` |

### convenience string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuidv7.uuid7())` | 868,692 | 1,151.2 | `str` |

### custom default object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuid7_rs.uuid7()` | 16,302,353 | 61.3 | `_UUID` |
| `c_uuid_v7.uuid7()` | 16,278,576 | 61.4 | `UUID` |

### materialized string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuid7_rs.uuid7())` | 8,361,312 | 119.6 | `str` |
| `str(c_uuid_v7.uuid7())` | 8,235,990 | 121.4 | `str` |
| `str(uuid_utils.uuid7())` | 4,591,091 | 217.8 | `str` |

### string/default

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `fastuuidv7.uuid7()` | 13,712,741 | 72.9 | `str` |
| `uuidv7.uuid7_str()` | 11,866,739 | 84.3 | `str` |

### uuid.UUID compat

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7()` | 2,065,888 | 484.1 | `_UUID7` |
| `uuid7_rs.compat.uuid7()` | 1,514,742 | 660.2 | `UUID` |
| `c_uuid_v7.compat.uuid7()` | 1,397,904 | 715.4 | `UUID` |
| `uuid6.uuid7()` | 507,346 | 1,971.0 | `UUID` |
| `uuid_extensions.uuid7()` | 472,799 | 2,115.1 | `UUID` |

### uuid/custom object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuid_utils.uuid7()` | 8,593,774 | 116.4 | `UUID` |

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
