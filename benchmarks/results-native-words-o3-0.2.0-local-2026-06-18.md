# UUIDv7 Benchmark Results

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Implementation | Version | UUIDs/sec | ns/op | Iterations |
| --- | ---: | ---: | ---: | ---: |
| fastuuid7 0.2.0 candidate: uuid7_obj() -> native object | 0.2.0 | 28,398,880 | 35.2 | 1,000,000 |
| fastuuidv7 uuid7() | 0.1.5 | 24,959,993 | 40.1 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_bytes() -> bytes | 0.2.0 | 23,621,190 | 42.3 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7_str() -> str | 0.2.0 | 18,596,358 | 53.8 | 1,000,000 |
| uuid-utils uuid7() | 0.16.1 | 12,262,839 | 81.5 | 1,000,000 |
| fastuuid7 0.2.0 candidate: uuid7() -> uuid.UUID | 0.2.0 | 12,084,179 | 82.8 | 1,000,000 |
| fastuuid7 0.2.0 candidate: str(uuid7()) | 0.2.0 | 2,091,423 | 478.1 | 1,000,000 |
| uuid7 package uuid_extensions.uuid7() | 0.1.0 | 792,951 | 1,261.1 | 1,000,000 |

## Skipped

- Python stdlib uuid.uuid7()
- published fastuuid7 0.1.0: uuid7() -> str
