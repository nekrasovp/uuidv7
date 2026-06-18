# Docker Benchmark

- Docker image: `python:3.14-bookworm`
- Profile: `uuidv7`
- Iterations per case: 1000000
- Benchmark command: `python benchmarks/benchmark_competitors.py --install-optional --iterations 1000000`

Python/runtime: Python 3.14.6
# UUIDv7 Competitor Benchmark

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.36
- Machine: x86_64
- CPU: unknown
- Python: 3.14.6

## Results

| Shape | Case | Package | Version | Return type | ops/sec | ns/op | Iterations |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| custom default object | `c_uuid_v7.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 13,208,788 | 75.7 | 1,000,000 |
| custom default object | `uuid7_rs.uuid7()` | `uuid7-rs` | 0.0.9 | `_UUID` | 12,949,484 | 77.2 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_int()` | `fastuuid7` | 0.2.0 | `int` | 11,753,316 | 85.1 | 1,000,000 |
| string/default | `fastuuidv7.uuid7()` | `fastuuidv7` | 0.1.5 | `str` | 10,408,459 | 96.1 | 1,000,000 |
| bytes | `uuidv7.uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 10,174,225 | 98.3 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 10,088,801 | 99.1 | 1,000,000 |
| string/default | `uuidv7.uuid7_str()` | `fastuuid7` | 0.2.0 | `str` | 9,909,917 | 100.9 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7()` | `fastuuid7` | 0.2.0 | `str` | 9,104,335 | 109.8 | 1,000,000 |
| materialized string | `str(uuid7_rs.uuid7())` | `uuid7-rs` | 0.0.9 | `str` | 7,617,938 | 131.3 | 1,000,000 |
| uuid/custom object | `uuid_utils.uuid7()` | `uuid-utils` | 0.16.0 | `UUID` | 7,557,612 | 132.3 | 1,000,000 |
| materialized string | `str(c_uuid_v7.uuid7())` | `c_uuid_v7` | 0.0.11 | `str` | 7,485,563 | 133.6 | 1,000,000 |
| materialized string | `str(uuid_utils.uuid7())` | `uuid-utils` | 0.16.0 | `str` | 4,023,152 | 248.6 | 1,000,000 |
| uuid.UUID compat | `uuidv7.uuid7()` | `fastuuid7` | 0.2.0 | `_UUID7` | 2,030,683 | 492.4 | 1,000,000 |
| uuid.UUID compat | `uuid7_rs.compat.uuid7()` | `uuid7-rs` | 0.0.9 | `UUID` | 1,955,296 | 511.4 | 1,000,000 |
| uuid.UUID compat | `c_uuid_v7.compat.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 1,880,969 | 531.6 | 1,000,000 |
| convenience string | `str(uuidv7.uuid7())` | `fastuuid7` | 0.2.0 | `str` | 1,034,088 | 967.0 | 1,000,000 |
| uuid.UUID compat | `stdlib uuid.uuid7()` | `python` | 3.14.6 | `UUID` | 635,828 | 1,572.8 | 1,000,000 |
| uuid.UUID compat | `uuid6.uuid7()` | `uuid6` | 2025.0.1 | `UUID` | 500,973 | 1,996.1 | 1,000,000 |
| uuid.UUID compat | `uuid_extensions.uuid7()` | `uuid7` | 0.1.0 | `UUID` | 497,905 | 2,008.4 | 1,000,000 |

## By API Shape

### C extension output

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7 C generate_uuid7_int()` | 11,753,316 | 85.1 | `int` |
| `uuidv7 C generate_uuid7_bytes()` | 10,088,801 | 99.1 | `bytes` |
| `uuidv7 C generate_uuid7()` | 9,104,335 | 109.8 | `str` |

### bytes

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_bytes()` | 10,174,225 | 98.3 | `bytes` |

### convenience string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuidv7.uuid7())` | 1,034,088 | 967.0 | `str` |

### custom default object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `c_uuid_v7.uuid7()` | 13,208,788 | 75.7 | `UUID` |
| `uuid7_rs.uuid7()` | 12,949,484 | 77.2 | `_UUID` |

### materialized string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuid7_rs.uuid7())` | 7,617,938 | 131.3 | `str` |
| `str(c_uuid_v7.uuid7())` | 7,485,563 | 133.6 | `str` |
| `str(uuid_utils.uuid7())` | 4,023,152 | 248.6 | `str` |

### string/default

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `fastuuidv7.uuid7()` | 10,408,459 | 96.1 | `str` |
| `uuidv7.uuid7_str()` | 9,909,917 | 100.9 | `str` |

### uuid.UUID compat

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7()` | 2,030,683 | 492.4 | `_UUID7` |
| `uuid7_rs.compat.uuid7()` | 1,955,296 | 511.4 | `UUID` |
| `c_uuid_v7.compat.uuid7()` | 1,880,969 | 531.6 | `UUID` |
| `stdlib uuid.uuid7()` | 635,828 | 1,572.8 | `UUID` |
| `uuid6.uuid7()` | 500,973 | 1,996.1 | `UUID` |
| `uuid_extensions.uuid7()` | 497,905 | 2,008.4 | `UUID` |

### uuid/custom object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuid_utils.uuid7()` | 7,557,612 | 132.3 | `UUID` |

## Skipped

| Case | Package | Reason | Source |
| --- | --- | --- | --- |
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
