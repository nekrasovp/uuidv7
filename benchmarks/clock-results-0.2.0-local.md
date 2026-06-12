# UUIDv7 Clock Source Benchmark

## Environment

- OS: Linux-5.15.167.4-microsoft-standard-WSL2-x86_64-with-glibc2.39
- Machine: x86_64
- CPU: x86_64
- Python: 3.12.3

## Results

| Clock source | ns/call | Iterations |
| --- | ---: | ---: |
| clock_gettime(CLOCK_REALTIME_COARSE) | 2.910 | 10,000,000 |
| clock_gettime(CLOCK_REALTIME) | 14.538 | 10,000,000 |
