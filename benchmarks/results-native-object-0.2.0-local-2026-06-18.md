# UUIDv7 Benchmark Results

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Implementation | Version | UUIDs/sec | ns/op | Iterations |
| --- | ---: | ---: | ---: | ---: |
| fastuuid7 0.2.0 candidate: uuid7_bytes() -> bytes | 0.2.0 | 25,363,925 | 39.4 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_obj() -> native object | 0.2.0 | 25,316,887 | 39.5 | 1,000,000 |
| fastuuidv7 uuid7() | 0.1.5 | 24,216,757 | 41.3 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_str() -> str | 0.2.0 | 20,418,277 | 49.0 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7() -> uuid.UUID | 0.2.0 | 12,963,659 | 77.1 | 1,000,000 |
| uuid-utils uuid7() | 0.16.1 | 11,684,266 | 85.6 | 1,000,000 |
| fastuuid7 0.2.0 candidate: str(uuid7()) | 0.2.0 | 1,958,759 | 510.5 | 1,000,000 |
| uuid7 package uuid_extensions.uuid7() | 0.1.0 | 787,759 | 1,269.4 | 1,000,000 |

## Skipped

- Python stdlib uuid.uuid7()
- published fastuuid7 0.1.0: uuid7() -> str
