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
| public native object | `uuidv7.uuid7_obj()` | 25,666,120 | 39.0 | 1,000,000 | C generation plus compact native object allocation |
| C extension output | `generate_uuid7_bytes()` | 24,501,293 | 40.8 | 1,000,000 | C generation plus PyBytes allocation without public wrapper |
| public raw output | `uuidv7.uuid7_bytes()` | 24,014,543 | 41.6 | 1,000,000 | C generation plus PyBytes allocation |
| C extension output | `generate_uuid7_int()` | 22,333,564 | 44.8 | 1,000,000 | C generation plus 128-bit PyLong conversion |
| C extension output | `generate_uuid7()` | 20,555,639 | 48.6 | 1,000,000 | C generation, manual hex encoding, PyUnicode allocation without public wrapper |
| public string output | `uuidv7.uuid7_str()` | 20,408,595 | 49.0 | 1,000,000 | C generation, manual hex encoding, PyUnicode allocation |
| native string output | `str(uuidv7.uuid7_obj())` | 14,710,885 | 68.0 | 1,000,000 | uuid7_obj() plus native formatter |
| C extension output | `uuidv7 C uuid7()` | 12,683,485 | 78.8 | 1,000,000 | C generation, PyLong conversion, _UUID7 allocation, direct slot writes |
| public uuid object | `uuidv7.uuid7()` | 11,182,660 | 89.4 | 1,000,000 | C generation, PyLong conversion, _UUID7 allocation, direct slot writes |
| Python object construction | `_uuid7_from_int(fixed_int)` | 5,124,190 | 195.2 | 1,000,000 | _UUID7 allocation and direct int/is_safe attribute writes |
| uuid object split | `generate_uuid7_int() + _uuid7_from_int(value)` | 4,659,842 | 214.6 | 1,000,000 | same pieces as uuid7(), called explicitly from Python |
| Python string formatting | `str(fixed_uuid)` | 2,807,030 | 356.2 | 1,000,000 | UUID.__str__ formatting from an existing UUID object |
| Python object construction | `uuid.UUID(int=fixed_int)` | 2,648,080 | 377.6 | 1,000,000 | stdlib UUID constructor from an existing int |
| Python object construction | `uuid.UUID(bytes=fixed_bytes)` | 2,174,535 | 459.9 | 1,000,000 | stdlib UUID constructor from existing 16 bytes |
| convenience string output | `str(uuidv7.uuid7())` | 2,143,816 | 466.5 | 1,000,000 | uuid7() plus UUID.__str__ formatting |

## Derived Reads

| Estimate | Delta |
| --- | ---: |
| `uuid7()` over direct `generate_uuid7_int()` | +44.6 ns/op |
| `uuid7()` over `_uuid7_from_int(fixed_int)` | -105.7 ns/op |
| `uuid7_str()` over `uuid7_bytes()` | +7.4 ns/op |
| `str(uuid7())` over `uuid7()` | +377.0 ns/op |
| public `uuid7()` wrapper over explicit split call | -125.2 ns/op |
| public `uuid7()` alias over direct C object call | +10.6 ns/op |
| public `uuid7_bytes()` wrapper over direct extension call | +0.8 ns/op |
| public `uuid7_str()` wrapper over direct extension call | +0.4 ns/op |

These deltas are directional microbenchmark reads, not strict additive profiling. They are useful for choosing the next optimization target.
