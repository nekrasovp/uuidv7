# UUIDv7 Benchmark Results

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Implementation | Version | UUIDs/sec | ns/op | Iterations |
| --- | ---: | ---: | ---: | ---: |
| fastuuid7 0.2.0 candidate: uuid7_bytes() -> bytes | 0.2.0 | 25,219,473 | 39.7 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_str() -> str | 0.2.0 | 20,907,138 | 47.8 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7() -> uuid.UUID | 0.2.0 | 10,878,619 | 91.9 | 1,000,000 |
| fastuuid7 0.2.0 candidate: str(uuid7()) | 0.2.0 | 2,044,476 | 489.1 | 1,000,000 |

## Skipped

- Python stdlib uuid.uuid7()
- uuid-utils uuid7()
- fastuuidv7 uuid7()
- uuid7 package uuid_extensions.uuid7()
- published fastuuid7 0.1.0: uuid7() -> str
