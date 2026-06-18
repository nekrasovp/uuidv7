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
| string/default | `c_uuid_v7.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 12,841,182 | 77.9 | 1,000,000 |
| string/default | `uuid7_rs.uuid7()` | `uuid7-rs` | 0.0.9 | `_UUID` | 12,666,765 | 78.9 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_int()` | `fastuuid7` | 0.2.0 | `int` | 11,369,935 | 88.0 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 11,158,834 | 89.6 | 1,000,000 |
| string/default | `fastuuidv7.uuid7()` | `fastuuidv7` | 0.1.5 | `str` | 10,295,248 | 97.1 | 1,000,000 |
| bytes | `uuidv7.uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 9,320,427 | 107.3 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7()` | `fastuuid7` | 0.2.0 | `str` | 8,983,080 | 111.3 | 1,000,000 |
| string/default | `uuidv7.uuid7_str()` | `fastuuid7` | 0.2.0 | `str` | 8,550,878 | 116.9 | 1,000,000 |
| uuid/custom object | `uuid_utils.uuid7()` | `uuid-utils` | 0.16.0 | `UUID` | 7,632,296 | 131.0 | 1,000,000 |
| uuid.UUID compat | `uuidv7.uuid7()` | `fastuuid7` | 0.2.0 | `_UUID7` | 2,016,870 | 495.8 | 1,000,000 |
| uuid.UUID compat | `uuid7_rs.compat.uuid7()` | `uuid7-rs` | 0.0.9 | `UUID` | 1,993,016 | 501.8 | 1,000,000 |
| uuid.UUID compat | `c_uuid_v7.compat.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 1,883,636 | 530.9 | 1,000,000 |
| convenience string | `str(uuidv7.uuid7())` | `fastuuid7` | 0.2.0 | `str` | 1,041,466 | 960.2 | 1,000,000 |
| uuid.UUID compat | `stdlib uuid.uuid7()` | `python` | 3.14.6 | `UUID` | 618,537 | 1,616.7 | 1,000,000 |
| uuid.UUID compat | `uuid6.uuid7()` | `uuid6` | 2025.0.1 | `UUID` | 518,901 | 1,927.2 | 1,000,000 |
| uuid.UUID compat | `uuid_extensions.uuid7()` | `uuid7` | 0.1.0 | `UUID` | 506,340 | 1,975.0 | 1,000,000 |

## By API Shape

### C extension output

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7 C generate_uuid7_int()` | 11,369,935 | 88.0 | `int` |
| `uuidv7 C generate_uuid7_bytes()` | 11,158,834 | 89.6 | `bytes` |
| `uuidv7 C generate_uuid7()` | 8,983,080 | 111.3 | `str` |

### bytes

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_bytes()` | 9,320,427 | 107.3 | `bytes` |

### convenience string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuidv7.uuid7())` | 1,041,466 | 960.2 | `str` |

### string/default

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `c_uuid_v7.uuid7()` | 12,841,182 | 77.9 | `UUID` |
| `uuid7_rs.uuid7()` | 12,666,765 | 78.9 | `_UUID` |
| `fastuuidv7.uuid7()` | 10,295,248 | 97.1 | `str` |
| `uuidv7.uuid7_str()` | 8,550,878 | 116.9 | `str` |

### uuid.UUID compat

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7()` | 2,016,870 | 495.8 | `_UUID7` |
| `uuid7_rs.compat.uuid7()` | 1,993,016 | 501.8 | `UUID` |
| `c_uuid_v7.compat.uuid7()` | 1,883,636 | 530.9 | `UUID` |
| `stdlib uuid.uuid7()` | 618,537 | 1,616.7 | `UUID` |
| `uuid6.uuid7()` | 518,901 | 1,927.2 | `UUID` |
| `uuid_extensions.uuid7()` | 506,340 | 1,975.0 | `UUID` |

### uuid/custom object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuid_utils.uuid7()` | 7,632,296 | 131.0 | `UUID` |

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
