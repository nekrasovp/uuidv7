# UUIDv7 Competitor Benchmark

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Shape | Case | Package | Version | Return type | ops/sec | ns/op | Iterations |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| C extension output | `uuidv7 C generate_uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 24,508,268 | 40.8 | 300,000 |
| bytes | `uuidv7.uuid7_bytes()` | `fastuuid7` | 0.2.0 | `bytes` | 23,737,978 | 42.1 | 300,000 |
| C extension output | `uuidv7 C generate_uuid7_int()` | `fastuuid7` | 0.2.0 | `int` | 23,360,267 | 42.8 | 300,000 |
| C extension output | `uuidv7 C generate_uuid7()` | `fastuuid7` | 0.2.0 | `str` | 20,450,638 | 48.9 | 300,000 |
| string/default | `uuidv7.uuid7_str()` | `fastuuid7` | 0.2.0 | `str` | 19,844,252 | 50.4 | 300,000 |
| uuid.UUID compat | `uuidv7.uuid7()` | `fastuuid7` | 0.2.0 | `_UUID7` | 8,215,975 | 121.7 | 300,000 |
| convenience string | `str(uuidv7.uuid7())` | `fastuuid7` | 0.2.0 | `str` | 2,073,709 | 482.2 | 300,000 |

## By API Shape

### C extension output

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7 C generate_uuid7_bytes()` | 24,508,268 | 40.8 | `bytes` |
| `uuidv7 C generate_uuid7_int()` | 23,360,267 | 42.8 | `int` |
| `uuidv7 C generate_uuid7()` | 20,450,638 | 48.9 | `str` |

### bytes

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_bytes()` | 23,737,978 | 42.1 | `bytes` |

### convenience string

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `str(uuidv7.uuid7())` | 2,073,709 | 482.2 | `str` |

### string/default

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7_str()` | 19,844,252 | 50.4 | `str` |

### uuid.UUID compat

| Case | ops/sec | ns/op | Return type |
| --- | ---: | ---: | --- |
| `uuidv7.uuid7()` | 8,215,975 | 121.7 | `_UUID7` |

## Skipped

| Case | Package | Reason | Source |
| --- | --- | --- | --- |
| `stdlib uuid.uuid7()` | `python` | not available on this Python runtime | https://docs.python.org/3/library/uuid.html#uuid.uuid7 |
| `c_uuid_v7.uuid7()` | `c_uuid_v7` | import failed: No module named 'c_uuid_v7' | https://github.com/lava-sh/c_uuid_v7 |
| `c_uuid_v7.compat.uuid7()` | `c_uuid_v7` | import failed: No module named 'c_uuid_v7' | https://github.com/lava-sh/c_uuid_v7 |
| `uuid7_rs.uuid7()` | `uuid7-rs` | import failed: No module named 'uuid7_rs' | https://github.com/lava-sh/uuid7-rs |
| `uuid7_rs.compat.uuid7()` | `uuid7-rs` | import failed: No module named 'uuid7_rs' | https://github.com/lava-sh/uuid7-rs |
| `fastuuidv7.uuid7()` | `fastuuidv7` | import failed: No module named 'fastuuidv7' | https://pypi.org/project/fastuuidv7/ |
| `uuid_utils.uuid7()` | `uuid-utils` | import failed: No module named 'uuid_utils' | https://pypi.org/project/uuid-utils/ |
| `uuid_extensions.uuid7()` | `uuid7` | import failed: No module named 'uuid_extensions' | https://pypi.org/project/uuid7/ |
| `uuid_v7.uuid7()` | `uuid-v7` | import failed: No module named 'uuid_v7' | https://pypi.org/project/uuid-v7/ |
| `uuid6.uuid7()` | `uuid6` | import failed: No module named 'uuid6' | https://pypi.org/project/uuid6/ |
| `str(c_uuid_v7.uuid7())` | `c_uuid_v7` | import failed: No module named 'c_uuid_v7' | https://github.com/lava-sh/c_uuid_v7 |
| `str(uuid7_rs.uuid7())` | `uuid7-rs` | import failed: No module named 'uuid7_rs' | https://github.com/lava-sh/uuid7-rs |
| `str(uuid_utils.uuid7())` | `uuid-utils` | import failed: No module named 'uuid_utils' | https://pypi.org/project/uuid-utils/ |

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
