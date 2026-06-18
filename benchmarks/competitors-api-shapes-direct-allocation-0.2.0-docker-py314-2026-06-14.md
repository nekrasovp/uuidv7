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
| custom default object | `c_uuid_v7.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 12,635,411 | 79.1 | 1,000,000 |
| custom default object | `uuid7_rs.uuid7()` | `uuid7-rs` | 0.0.9 | `_UUID` | 12,560,411 | 79.6 | 1,000,000 |
| bytes | `uuidv7.uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 11,686,920 | 85.6 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 11,148,687 | 89.7 | 1,000,000 |
| string/default | `uuidv7.uuid7_str()` | `fastuuid7` | 0.2.0 | `str` | 10,778,903 | 92.8 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_int()` | `fastuuid7` | 0.2.0 | `int` | 10,533,500 | 94.9 | 1,000,000 |
| string/default | `fastuuidv7.uuid7()` | `fastuuidv7` | 0.1.5 | `str` | 10,408,855 | 96.1 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7()` | `fastuuid7` | 0.2.0 | `str` | 9,416,788 | 106.2 | 1,000,000 |
| materialized string | `str(uuid7_rs.uuid7())` | `uuid7-rs` | 0.0.9 | `str` | 7,565,537 | 132.2 | 1,000,000 |
| uuid/custom object | `uuid_utils.uuid7()` | `uuid-utils` | 0.16.0 | `UUID` | 7,248,743 | 138.0 | 1,000,000 |
| materialized string | `str(c_uuid_v7.uuid7())` | `c_uuid_v7` | 0.0.11 | `str` | 7,175,211 | 139.4 | 1,000,000 |
| materialized string | `str(uuid_utils.uuid7())` | `uuid-utils` | 0.16.0 | `str` | 3,931,194 | 254.4 | 1,000,000 |
| uuid.UUID compat | `uuidv7.uuid7()` | `fastuuid7` | 0.2.0 | `_UUID7` | 1,949,208 | 513.0 | 1,000,000 |
| uuid.UUID compat | `uuid7_rs.compat.uuid7()` | `uuid7-rs` | 0.0.9 | `UUID` | 1,914,172 | 522.4 | 1,000,000 |
| uuid.UUID compat | `c_uuid_v7.compat.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 1,812,321 | 551.8 | 1,000,000 |
| convenience string | `str(uuidv7.uuid7())` | `fastuuid7` | 0.2.0 | `str` | 985,369 | 1,014.8 | 1,000,000 |
| uuid.UUID compat | `stdlib uuid.uuid7()` | `python` | 3.14.6 | `UUID` | 611,881 | 1,634.3 | 1,000,000 |
| uuid.UUID compat | `uuid_extensions.uuid7()` | `uuid7` | 0.1.0 | `UUID` | 470,433 | 2,125.7 | 1,000,000 |
| uuid.UUID compat | `uuid6.uuid7()` | `uuid6` | 2025.0.1 | `UUID` | 456,319 | 2,191.4 | 1,000,000 |

## By API Shape

### C extension output

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7 C generate_uuid7_bytes()` | 11,148,687 | 89.7 | `bytes` |
| `uuidv7 C generate_uuid7_int()` | 10,533,500 | 94.9 | `int` |
| `uuidv7 C generate_uuid7()` | 9,416,788 | 106.2 | `str` |

### bytes

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_bytes()` | 11,686,920 | 85.6 | `bytes` |

### convenience string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuidv7.uuid7())` | 985,369 | 1,014.8 | `str` |

### custom default object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `c_uuid_v7.uuid7()` | 12,635,411 | 79.1 | `UUID` |
| `uuid7_rs.uuid7()` | 12,560,411 | 79.6 | `_UUID` |

### materialized string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuid7_rs.uuid7())` | 7,565,537 | 132.2 | `str` |
| `str(c_uuid_v7.uuid7())` | 7,175,211 | 139.4 | `str` |
| `str(uuid_utils.uuid7())` | 3,931,194 | 254.4 | `str` |

### string/default

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_str()` | 10,778,903 | 92.8 | `str` |
| `fastuuidv7.uuid7()` | 10,408,855 | 96.1 | `str` |

### uuid.UUID compat

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7()` | 1,949,208 | 513.0 | `_UUID7` |
| `uuid7_rs.compat.uuid7()` | 1,914,172 | 522.4 | `UUID` |
| `c_uuid_v7.compat.uuid7()` | 1,812,321 | 551.8 | `UUID` |
| `stdlib uuid.uuid7()` | 611,881 | 1,634.3 | `UUID` |
| `uuid_extensions.uuid7()` | 470,433 | 2,125.7 | `UUID` |
| `uuid6.uuid7()` | 456,319 | 2,191.4 | `UUID` |

### uuid/custom object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuid_utils.uuid7()` | 7,248,743 | 138.0 | `UUID` |

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
