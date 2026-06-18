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
| string/default | `c_uuid_v7.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 16,601,571 | 60.2 | 1,000,000 |
| string/default | `uuid7_rs.uuid7()` | `uuid7-rs` | 0.0.9 | `_UUID` | 15,909,782 | 62.9 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 13,245,199 | 75.5 | 1,000,000 |
| string/default | `fastuuidv7.uuid7()` | `fastuuidv7` | 0.1.5 | `str` | 12,885,638 | 77.6 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7_int()` | `fastuuid7` | 0.2.0 | `int` | 12,180,615 | 82.1 | 1,000,000 |
| C extension output | `uuidv7 C generate_uuid7()` | `fastuuid7` | 0.2.0 | `str` | 10,633,234 | 94.0 | 1,000,000 |
| bytes | `uuidv7.uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 9,747,668 | 102.6 | 1,000,000 |
| uuid/custom object | `uuid_utils.uuid7()` | `uuid-utils` | 0.16.0 | `UUID` | 8,816,635 | 113.4 | 1,000,000 |
| string/default | `uuidv7.uuid7_str()` | `fastuuid7` | 0.2.0 | `str` | 8,790,135 | 113.8 | 1,000,000 |
| uuid.UUID compat | `uuidv7.uuid7()` | `fastuuid7` | 0.2.0 | `_UUID7` | 2,025,760 | 493.6 | 1,000,000 |
| uuid.UUID compat | `uuid7_rs.compat.uuid7()` | `uuid7-rs` | 0.0.9 | `UUID` | 1,507,064 | 663.5 | 1,000,000 |
| uuid.UUID compat | `c_uuid_v7.compat.uuid7()` | `c_uuid_v7` | 0.0.11 | `UUID` | 1,373,862 | 727.9 | 1,000,000 |
| convenience string | `str(uuidv7.uuid7())` | `fastuuid7` | 0.2.0 | `str` | 862,462 | 1,159.5 | 1,000,000 |
| uuid.UUID compat | `uuid6.uuid7()` | `uuid6` | 2025.0.1 | `UUID` | 500,010 | 2,000.0 | 1,000,000 |
| uuid.UUID compat | `uuid_extensions.uuid7()` | `uuid7` | 0.1.0 | `UUID` | 478,579 | 2,089.5 | 1,000,000 |

## By API Shape

### C extension output

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7 C generate_uuid7_bytes()` | 13,245,199 | 75.5 | `bytes` |
| `uuidv7 C generate_uuid7_int()` | 12,180,615 | 82.1 | `int` |
| `uuidv7 C generate_uuid7()` | 10,633,234 | 94.0 | `str` |

### bytes

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_bytes()` | 9,747,668 | 102.6 | `bytes` |

### convenience string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuidv7.uuid7())` | 862,462 | 1,159.5 | `str` |

### string/default

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `c_uuid_v7.uuid7()` | 16,601,571 | 60.2 | `UUID` |
| `uuid7_rs.uuid7()` | 15,909,782 | 62.9 | `_UUID` |
| `fastuuidv7.uuid7()` | 12,885,638 | 77.6 | `str` |
| `uuidv7.uuid7_str()` | 8,790,135 | 113.8 | `str` |

### uuid.UUID compat

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7()` | 2,025,760 | 493.6 | `_UUID7` |
| `uuid7_rs.compat.uuid7()` | 1,507,064 | 663.5 | `UUID` |
| `c_uuid_v7.compat.uuid7()` | 1,373,862 | 727.9 | `UUID` |
| `uuid6.uuid7()` | 500,010 | 2,000.0 | `UUID` |
| `uuid_extensions.uuid7()` | 478,579 | 2,089.5 | `UUID` |

### uuid/custom object

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuid_utils.uuid7()` | 8,816,635 | 113.4 | `UUID` |

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
