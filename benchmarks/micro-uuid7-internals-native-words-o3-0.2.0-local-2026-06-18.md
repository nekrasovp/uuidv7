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
| public native object | `uuidv7.uuid7_obj()` | 27,877,343 | 35.9 | 1,000,000 | C generation plus compact native object allocation |
| C extension output | `generate_uuid7_bytes()` | 25,681,742 | 38.9 | 1,000,000 | C generation plus PyBytes allocation without public wrapper |
| public raw output | `uuidv7.uuid7_bytes()` | 24,669,206 | 40.5 | 1,000,000 | C generation plus PyBytes allocation |
| C extension output | `generate_uuid7_int()` | 23,782,540 | 42.0 | 1,000,000 | C generation plus 128-bit PyLong conversion |
| public string output | `uuidv7.uuid7_str()` | 20,627,501 | 48.5 | 1,000,000 | C generation, manual hex encoding, PyUnicode allocation |
| C extension output | `generate_uuid7()` | 20,319,705 | 49.2 | 1,000,000 | C generation, manual hex encoding, PyUnicode allocation without public wrapper |
| native string output | `str(uuidv7.uuid7_obj())` | 15,464,153 | 64.7 | 1,000,000 | uuid7_obj() plus native formatter |
| public uuid object | `uuidv7.uuid7()` | 12,650,165 | 79.1 | 1,000,000 | C generation, PyLong conversion, _UUID7 allocation, direct slot writes |
| C extension output | `uuidv7 C uuid7()` | 12,177,300 | 82.1 | 1,000,000 | C generation, PyLong conversion, _UUID7 allocation, direct slot writes |
| Python object construction | `_uuid7_from_int(fixed_int)` | 6,166,351 | 162.2 | 1,000,000 | _UUID7 allocation and direct int/is_safe attribute writes |
| uuid object split | `generate_uuid7_int() + _uuid7_from_int(value)` | 4,840,781 | 206.6 | 1,000,000 | same pieces as uuid7(), called explicitly from Python |
| Python object construction | `uuid.UUID(int=fixed_int)` | 2,742,747 | 364.6 | 1,000,000 | stdlib UUID constructor from an existing int |
| Python string formatting | `str(fixed_uuid)` | 2,713,982 | 368.5 | 1,000,000 | UUID.__str__ formatting from an existing UUID object |
| Python object construction | `uuid.UUID(bytes=fixed_bytes)` | 2,207,736 | 453.0 | 1,000,000 | stdlib UUID constructor from existing 16 bytes |
| convenience string output | `str(uuidv7.uuid7())` | 2,122,959 | 471.0 | 1,000,000 | uuid7() plus UUID.__str__ formatting |

## Derived Reads

| Estimate | Delta |
| --- | ---: |
| `uuid7()` over direct `generate_uuid7_int()` | +37.0 ns/op |
| `uuid7()` over `_uuid7_from_int(fixed_int)` | -83.1 ns/op |
| `uuid7_str()` over `uuid7_bytes()` | +7.9 ns/op |
| `str(uuid7())` over `uuid7()` | +392.0 ns/op |
| public `uuid7()` wrapper over explicit split call | -127.5 ns/op |
| public `uuid7()` alias over direct C object call | -3.1 ns/op |
| public `uuid7_bytes()` wrapper over direct extension call | +1.6 ns/op |
| public `uuid7_str()` wrapper over direct extension call | -0.7 ns/op |

These deltas are directional microbenchmark reads, not strict additive profiling. They are useful for choosing the next optimization target.
