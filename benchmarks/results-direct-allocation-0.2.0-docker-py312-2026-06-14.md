# Docker Benchmark

- Docker image: `python:3.12-bookworm`
- Profile: `uuidv7`
- Iterations per case: 1000000
- Benchmark command: `python benchmarks/benchmark.py --iterations "${BENCHMARK_ITERATIONS}" ${BENCHMARK_EXTRA_ARGS}`

Python/runtime: Python 3.12.13
## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.36
- Machine: x86_64
- CPU: unknown
- Python: 3.12.13

## Results

| Implementation | Version | UUIDs/sec | ns/op | Iterations |
| --- | ---: | ---: | ---: | ---: |
| fastuuid7 0.2.0 candidate: uuid7_bytes() -> bytes | 0.2.0 | 14,909,443 | 67.1 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_str() -> str | 0.2.0 | 12,421,879 | 80.5 | 1,000,000 |
| published fastuuid7 0.1.0: uuid7() -> str | 0.1.0 | 3,368,888 | 296.8 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7() -> uuid.UUID | 0.2.0 | 2,022,605 | 494.4 | 1,000,000 |
| fastuuid7 0.2.0 candidate: str(uuid7()) | 0.2.0 | 895,277 | 1,117.0 | 1,000,000 |

## Skipped

- Python stdlib uuid.uuid7()
- uuid-utils uuid7()
- fastuuidv7 uuid7()
- uuid7 package uuid_extensions.uuid7()
