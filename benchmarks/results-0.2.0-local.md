# UUIDv7 Benchmark Results

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Implementation | Version | UUIDs/sec | ns/op | Iterations |
| --- | ---: | ---: | ---: | ---: |
| fastuuidv7 uuid7() | 0.1.5 | 23,095,658 | 43.3 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_bytes() -> bytes | 0.2.0 | 18,203,404 | 54.9 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_str() -> str | 0.2.0 | 13,880,113 | 72.0 | 1,000,000 |
| uuid-utils uuid7() | 0.16.0 | 12,186,695 | 82.1 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7() -> uuid.UUID | 0.2.0 | 4,366,928 | 229.0 | 1,000,000 |
| published fastuuid7 0.1.0: uuid7() -> str | 0.1.0 | 4,298,579 | 232.6 | 1,000,000 |
| fastuuid7 0.2.0 candidate: str(uuid7()) | 0.2.0 | 1,479,025 | 676.1 | 1,000,000 |
| uuid7 package uuid_extensions.uuid7() | 0.1.0 | 762,942 | 1,310.7 | 1,000,000 |

## Skipped

- Python stdlib uuid.uuid7()
