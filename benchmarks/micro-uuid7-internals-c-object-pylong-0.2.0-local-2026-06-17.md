# UUIDv7 Internals Microbenchmark

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3
- fastuuid7: 0.2.0

## Results

| Group | Case | ops/sec | ns/op | Iterations | Includes |
| --- | --- | ---: | ---: | ---: | --- |
| public raw output | `uuidv7.uuid7_bytes()` | 25,708,756 | 38.9 | 1,000,000 | C generation plus PyBytes allocation |
| C extension output | `generate_uuid7_bytes()` | 25,389,096 | 39.4 | 1,000,000 | C generation plus PyBytes allocation without public wrapper |
| C extension output | `generate_uuid7_int()` | 23,206,471 | 43.1 | 1,000,000 | C generation plus 128-bit PyLong conversion |
| public string output | `uuidv7.uuid7_str()` | 21,245,244 | 47.1 | 1,000,000 | C generation, manual hex encoding, PyUnicode allocation |
| C extension output | `generate_uuid7()` | 20,281,493 | 49.3 | 1,000,000 | C generation, manual hex encoding, PyUnicode allocation without public wrapper |
| public uuid object | `uuidv7.uuid7()` | 12,907,367 | 77.5 | 1,000,000 | C generation, PyLong conversion, _UUID7 allocation, direct slot writes |
| C extension output | `uuidv7 C uuid7()` | 12,595,845 | 79.4 | 1,000,000 | C generation, PyLong conversion, _UUID7 allocation, direct slot writes |
| Python object construction | `_uuid7_from_int(fixed_int)` | 6,197,391 | 161.4 | 1,000,000 | _UUID7 allocation and direct int/is_safe attribute writes |
| uuid object split | `generate_uuid7_int() + _uuid7_from_int(value)` | 4,225,573 | 236.7 | 1,000,000 | same pieces as uuid7(), called explicitly from Python |
| Python string formatting | `str(fixed_uuid)` | 2,713,589 | 368.5 | 1,000,000 | UUID.__str__ formatting from an existing UUID object |
| Python object construction | `uuid.UUID(int=fixed_int)` | 2,668,062 | 374.8 | 1,000,000 | stdlib UUID constructor from an existing int |
| Python object construction | `uuid.UUID(bytes=fixed_bytes)` | 2,171,614 | 460.5 | 1,000,000 | stdlib UUID constructor from existing 16 bytes |
| convenience string output | `str(uuidv7.uuid7())` | 1,987,949 | 503.0 | 1,000,000 | uuid7() plus UUID.__str__ formatting |

## Derived Reads

| Estimate | Delta |
| --- | ---: |
| `uuid7()` over direct `generate_uuid7_int()` | +34.4 ns/op |
| `uuid7()` over `_uuid7_from_int(fixed_int)` | -83.9 ns/op |
| `uuid7_str()` over `uuid7_bytes()` | +8.2 ns/op |
| `str(uuid7())` over `uuid7()` | +425.6 ns/op |
| public `uuid7()` wrapper over explicit split call | -159.2 ns/op |
| public `uuid7()` alias over direct C object call | -1.9 ns/op |
| public `uuid7_bytes()` wrapper over direct extension call | -0.5 ns/op |
| public `uuid7_str()` wrapper over direct extension call | -2.2 ns/op |

These deltas are directional microbenchmark reads, not strict additive profiling. They are useful for choosing the next optimization target.
