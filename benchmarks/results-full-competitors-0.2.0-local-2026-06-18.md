# UUIDv7 Benchmark Results

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Implementation | Version | UUIDs/sec | ns/op | Iterations |
| --- | ---: | ---: | ---: | ---: |
| fastuuid7 0.2.0 candidate: uuid7_bytes() -> bytes | 0.2.0 | 25,631,593 | 39.0 | 1,000,000 |
| fastuuidv7 uuid7() | 0.1.5 | 25,122,862 | 39.8 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_str() -> str | 0.2.0 | 20,633,217 | 48.5 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7() -> uuid.UUID | 0.2.0 | 12,996,491 | 76.9 | 1,000,000 |
| uuid-utils uuid7() | 0.16.1 | 12,173,931 | 82.1 | 1,000,000 |
| published fastuuid7 0.1.0: uuid7() -> str | 0.1.0 | 4,443,417 | 225.1 | 1,000,000 |
| fastuuid7 0.2.0 candidate: str(uuid7()) | 0.2.0 | 2,071,144 | 482.8 | 1,000,000 |
| uuid7 package uuid_extensions.uuid7() | 0.1.0 | 798,187 | 1,252.8 | 1,000,000 |

## Skipped

- Python stdlib uuid.uuid7()
