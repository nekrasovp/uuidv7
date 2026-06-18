# Docker Benchmark

- Docker image: `python:3.14-bookworm`
- Profile: `uuidv7`
- Iterations per case: 1000000
- Benchmark command: `python benchmarks/benchmark.py --iterations "${BENCHMARK_ITERATIONS}" ${BENCHMARK_EXTRA_ARGS}`

Python/runtime: Python 3.14.6
## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.36
- Machine: x86_64
- CPU: unknown
- Python: 3.14.6

## Results

| Implementation | Version | UUIDs/sec | ns/op | Iterations |
| --- | ---: | ---: | ---: | ---: |
| fastuuid7 0.2.0 candidate: uuid7_bytes() -> bytes | 0.2.0 | 12,675,497 | 78.9 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_str() -> str | 0.2.0 | 10,919,733 | 91.6 | 1,000,000 |
| published fastuuid7 0.1.0: uuid7() -> str | 0.1.0 | 3,198,539 | 312.6 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7() -> uuid.UUID | 0.2.0 | 1,999,356 | 500.2 | 1,000,000 |
| fastuuid7 0.2.0 candidate: str(uuid7()) | 0.2.0 | 1,037,730 | 963.6 | 1,000,000 |
| Python stdlib uuid.uuid7() | 3.14.6 | 626,633 | 1,595.8 | 1,000,000 |

## Skipped

- uuid-utils uuid7()
- fastuuidv7 uuid7()
- uuid7 package uuid_extensions.uuid7()
