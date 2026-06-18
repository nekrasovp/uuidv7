# Docker Benchmark

- Docker image: `python:3.12-bookworm`
- Profile: `uuidv7`
- Iterations per case: 1000000
- Benchmark command: `python benchmarks/micro_uuid7_internals.py --iterations 1000000`

Python/runtime: Python 3.12.13
# UUIDv7 Internals Microbenchmark

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.36
- Machine: x86_64
- CPU: unknown
- Python: 3.12.13
- fastuuid7: 0.2.0

## Results

| Group | Case | ops/sec | ns/op | Iterations | Includes |
| --- | --- | ---: | ---: | ---: | --- |
| C extension output | `generate_uuid7_bytes()` | 13,396,803 | 74.6 | 1,000,000 | C generation plus PyBytes allocation without public wrapper |
| C extension output | `generate_uuid7_int()` | 13,340,266 | 75.0 | 1,000,000 | C generation plus 128-bit PyLong conversion |
| C extension output | `generate_uuid7()` | 11,836,401 | 84.5 | 1,000,000 | C generation, manual hex encoding, PyUnicode allocation without public wrapper |
| public raw output | `uuidv7.uuid7_bytes()` | 10,182,905 | 98.2 | 1,000,000 | C generation plus PyBytes allocation |
| public string output | `uuidv7.uuid7_str()` | 9,146,983 | 109.3 | 1,000,000 | C generation, manual hex encoding, PyUnicode allocation |
| Python object construction | `_uuid7_from_int(fixed_int)` | 2,193,790 | 455.8 | 1,000,000 | _UUID7 allocation and direct int/is_safe attribute writes |
| public uuid object | `uuidv7.uuid7()` | 2,031,221 | 492.3 | 1,000,000 | C generation, PyLong conversion, _UUID7 allocation, attribute writes |
| uuid object split | `generate_uuid7_int() + _uuid7_from_int(value)` | 1,999,534 | 500.1 | 1,000,000 | same pieces as uuid7(), called explicitly from Python |
| Python string formatting | `str(fixed_uuid)` | 1,650,082 | 606.0 | 1,000,000 | UUID.__str__ formatting from an existing UUID object |
| Python object construction | `uuid.UUID(int=fixed_int)` | 1,336,266 | 748.4 | 1,000,000 | stdlib UUID constructor from an existing int |
| Python object construction | `uuid.UUID(bytes=fixed_bytes)` | 1,082,670 | 923.6 | 1,000,000 | stdlib UUID constructor from existing 16 bytes |
| convenience string output | `str(uuidv7.uuid7())` | 897,185 | 1,114.6 | 1,000,000 | uuid7() plus UUID.__str__ formatting |

## Derived Reads

| Estimate | Delta |
| --- | ---: |
| `uuid7()` over direct `generate_uuid7_int()` | +417.4 ns/op |
| `uuid7()` over `_uuid7_from_int(fixed_int)` | +36.5 ns/op |
| `uuid7_str()` over `uuid7_bytes()` | +11.1 ns/op |
| `str(uuid7())` over `uuid7()` | +622.3 ns/op |
| public `uuid7()` wrapper over explicit split call | -7.8 ns/op |
| public `uuid7_bytes()` wrapper over direct extension call | +23.6 ns/op |
| public `uuid7_str()` wrapper over direct extension call | +24.8 ns/op |

These deltas are directional microbenchmark reads, not strict additive profiling. They are useful for choosing the next optimization target.
