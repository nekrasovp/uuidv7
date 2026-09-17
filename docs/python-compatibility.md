# Python compatibility and integer conversion

This work tests CPython **3.15.0rc2**, the prerelease available on 2026-09-18.
It is not a claim about an untested final Python 3.15 release. The stable release
matrix and package classifiers remain Python 3.9–3.14. The separate
`python-prerelease.yml` workflow pins `3.15.0-rc.2` on Linux, macOS, and Windows,
reports the interpreter, runs locked tests, and builds artifacts without publishing.
A failing prerelease job is not suppressed with `continue-on-error`.

## C API choices

| Build | Conversion path |
| --- | --- |
| Full CPython C API, 3.14+ | Public `PyLongWriter` after checking the documented native layout |
| Unrecognized writer layout | Public unsigned native bytes conversion |
| Full CPython C API, 3.9–3.13, 30-bit digits | Existing `_PyLong_New` path, bounded to these versions |
| Other legacy digit layouts or an older Limited API floor | Public integer construction, shift, and OR |
| Limited API floor 3.14+ | Public unsigned native bytes conversion |

`PyLong_FromUnsignedNativeBytes` was added in 3.13 and entered the Stable ABI in
3.14. `PyLongWriter` was added in 3.14. Its layout API describes digit width,
size, order, and endianness; the optimized path checks all four before use.
The writer and layout APIs enter the Stable ABI in 3.15. See the official
[integer API documentation](https://docs.python.org/3.15/c-api/long.html) and
[3.13 API documentation](https://docs.python.org/3.13/c-api/long.html).

`_PyLong_New` is deprecated starting in 3.14, as shown by the
[3.15.0rc2 CPython header](https://github.com/python/cpython/blob/v3.15.0rc2/Include/cpython/longintrepr.h).
The 3.14+ helper does not access `PyLongObject` digits or call private integer
functions. `_PyLong_FromByteArray` is removed entirely. Older CPython versions
retain the direct allocation path because they lack the public writer; adopting
the bytes API alone on 3.13 adds conversion overhead without this benefit.

All packing uses unsigned 64-bit operands with shift counts below 64. Byte reads
and writes are alignment independent. The writer buffer receives five initialized
30-bit digits via `memcpy`; `PyLongWriter_Finish` normalizes zero and leading zeros.
A failed writer allocation returns the existing Python exception. The fallback
keeps all 128 bits unsigned, including bit 127, and releases temporary objects
on every arithmetic error path.

## Verification

`tests/test_int_conversion.py` compiles a temporary extension from the **same
production header**, using the project's existing isolated build backend. Tests
therefore require `uv` and a C compiler. A missing compiler or failed build fails
the test instead of skipping it. The installed library gains no test methods or
runtime dependencies. One harness uses the full C API; another compiles against
a Python 3.9 Limited API floor to exercise the arithmetic fallback.

Coverage includes zero, `2**128 - 1`, each bit boundary and its neighbors, 4,096
fixed-seed random values, asymmetric byte patterns, offset byte buffers, and
integer arithmetic/hash/byte round trips. On 3.14+ it also forces each writer
layout mismatch and a writer allocation failure. Public live and historical UUID
outputs are checked against `int.from_bytes` at timestamp/sign-bit boundaries.

The implementation was tested in separate `git clone --no-local` checkouts on
macOS 26.6.2 arm64. All listed tests executed with no skips:

| Interpreter | Full suite | Focused conversion tests |
| --- | ---: | ---: |
| CPython 3.9.25 | 456 passed | 391 |
| CPython 3.10.20 | 456 passed | 391 |
| CPython 3.11.15 | 456 passed | 391 |
| CPython 3.12.13 | 456 passed | 391 |
| CPython 3.13.14 | 456 passed | 391 |
| CPython 3.14.6 | 461 passed | 396 |
| CPython 3.15.0rc2 | 461 passed | 396 |

The five additional tests on 3.14+ exercise writer layout and allocation errors.
A separate 3.15.0rc2 build with `-fsanitize=undefined`,
`-fno-sanitize-recover=all`, and `-Werror=deprecated-declarations` also passes all
461 tests, including the instrumented conversion harness, without sanitizer
diagnostics. Ruff, formatting, mypy, and actionlint pass.
The 3.15 interpreter is a normal GIL build compiled with Apple Clang 21.0.0,
without PGO. The official source archive SHA-256 is
`8d93af5eaaaea5adfd41bd786a7ba3f03f2ad1ab57c6a65e0b963deab91d5ad7`,
verified against the [Python 3.15.0rc2 release page](https://www.python.org/downloads/release/python-3150rc2/).

Reproduce the standard checks with:

```bash
uv sync --extra dev --locked --python /path/to/python
uv run --extra dev --locked pytest
uv run --extra dev --locked ruff check .
uv run --extra dev --locked ruff format --check .
uv run --extra dev --locked mypy
uv build --python /path/to/python
```

When editing C sources in an existing editable environment, add
`--reinstall-package fastuuid7` to `uv sync` to force a rebuild. Check the loaded
extension path and symbols before measuring; dependency freshness alone does not
prove that an editable native extension was rebuilt.

## Performance evidence

Before: `0386e15dc32fb2658e33518be77bae330db6556f` (0.4.0).
After: the integer helper in this change. Both use the same CPython 3.14.6 binary,
Apple M3 Pro, macOS 26.6.2 arm64, and setuptools `-O3` build configuration. Each
row compares the same result representation. Nine paired subprocess samples
alternate before/after order; the table reports medians in ns per UUID.

| Operation / result | Before | After | Time change |
| --- | ---: | ---: | ---: |
| `generate_uuid7_int()` / int | 49.09 | 46.97 | -4.3% |
| Existing native UUID `.int` / int | 19.65 | 19.03 | -3.1% |
| `uuid7()` / UUID | 90.12 | 85.25 | -5.4% |
| `uuid7_at(unix_ms=1700000000000)` / UUID | 475.70 | 486.12 | +2.2% |
| `uuid7_many(1024)` / list of UUIDs | 79.82 | 73.48 | -7.9% |

These are local timings, not portable speedup promises. The historical case is
2.2% slower in this sample; the measured public writer does not cause a material
regression in the other measured paths. An exploratory fixed-constant C wrapper
on the same Python took 15.69 ns using the old allocator, 17.90 ns using the
writer, and 24.11 ns using only the bytes API (11 interleaved samples of two
million calls). That isolated comparison motivated the writer over bytes-only
conversion; it is not an end-to-end UUID throughput claim.

For a paired reproduction, build before and after in separate checkouts with the
same interpreter and forced rebuilds. Save this script as `/tmp/bench-int-api.py`:

```python
import json
import sys
import timeit

sys.path.insert(0, sys.argv[1])
import fastuuid7 as f
from uuidv7.uuidv7_impl.uuid7_gen import generate_uuid7_int

obj = f.uuid7_obj()
assert obj.int == int.from_bytes(obj.bytes, "big")
cases = {
    "generate_uuid7_int": ("generate_uuid7_int()", 1000000, 1),
    "native_obj.int": ("obj.int", 2000000, 1),
    "uuid7": ("f.uuid7()", 500000, 1),
    "uuid7_at": ("f.uuid7_at(unix_ms=1700000000000)", 500000, 1),
    "uuid7_many_1024": ("f.uuid7_many(1024)", 1000, 1024),
}
print(json.dumps({
    name: timeit.timeit(stmt, globals=globals(), number=n) * 1e9 / (n * size)
    for name, (stmt, n, size) in cases.items()
}))
```

Use that same Python executable to invoke the script with each checkout's absolute
path. Run nine pairs, reversing order on alternate pairs, and take each operation's
median for each checkout. Avoid simultaneous benchmark jobs. These measurements
do not compare 3.14 with a differently built 3.15 interpreter.

## Limits

This is not an ABI3 migration. The Limited API harness covers only the conversion
helper; the complete extension still uses static types and other full C API
facilities. This work does not claim GIL-free or free-threaded support.
The layout fallback is injected in tests; native big-endian hardware and a
15-bit-digit CPython build have not been executed locally. Hosted prerelease
results and remaining platform gates must be checked on the exact PR head.
