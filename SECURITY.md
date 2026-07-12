# Security policy

## Supported versions

| Version | Supported |
| --- | --- |
| 0.3.x | Yes |
| 0.2.x and earlier | No |

Versions through 0.2.x used a non-cryptographic process-local PRNG and could
inherit duplicate generator state after a process fork. Upgrade to 0.3.0 or
newer before using the library in multi-process applications. Python 3.8 users
must also upgrade Python; otherwise package resolvers can keep selecting the
unsupported 0.2.x line.

## Reporting a vulnerability

Please report suspected vulnerabilities privately to `nekrasovp@gmail.com`.
Include the affected version, platform, reproduction steps, and potential
impact. Do not open a public issue until a fix or coordinated disclosure plan is
available.

## UUID security properties

`fastuuid7` obtains UUID random fields from the operating system CSPRNG and
discards buffered entropy and generator counters when it detects a process
fork. UUIDv7 values still reveal their Unix timestamp by design and must not be
treated as secrets, authentication credentials, or authorization tokens.
