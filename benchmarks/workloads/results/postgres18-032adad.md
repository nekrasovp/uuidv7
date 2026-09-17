# PostgreSQL workload measurements

Source HEAD: `032adad79e7f319139e093dbac8cd27c8402d5b8`
Rows/sample: 100000; batch: 1000; measured rounds: 3; seed: 20260918.
One untimed, validated warmup per case precedes randomized measured rounds. Fresh process and table per sample.
ID: stdlib uuid.UUID -> PostgreSQL uuid; 128-byte text payload + two bigint columns. Binary COPY uses write_row.
Elapsed includes generation, row construction, adaptation, insertion and commit; excludes connection/DDL/verification.
CPU is client process only. RSS is client lifetime high-water before verification, including imports. No server CPU/RSS measurement.

| Scenario | Case | Group | Median s | Min–max s | Rows/s | Client CPU s | Peak MiB | Generate % |
|---|---|---|---:|---:|---:|---:|---:|---:|
| sqlalchemy | checkout_scalar | client_uuid7 | 3.9091 | 3.6530–4.1688 | 25,581 | 3.8966 | 68.8 | 1.24 |
| sqlalchemy | checkout_batch | client_uuid7 | 3.9555 | 3.8766–3.9999 | 25,281 | 3.9425 | 68.8 | 1.10 |
| sqlalchemy | published_scalar | client_uuid7 | 3.7671 | 3.7450–3.8471 | 26,546 | 3.7551 | 68.7 | 1.28 |
| sqlalchemy | published_batch | client_uuid7 | 3.8157 | 3.6880–3.8385 | 26,207 | 3.8042 | 68.7 | 1.13 |
| sqlalchemy | stdlib_uuid7 | client_uuid7 | 4.1306 | 3.9588–4.2581 | 24,209 | 4.1183 | 68.5 | 6.12 |
| sqlalchemy | uuid_utils | client_uuid7 | 3.8941 | 3.8842–4.1061 | 25,680 | 3.8831 | 69.0 | 1.84 |
| sqlalchemy | uuid6 | client_uuid7 | 4.1633 | 4.0437–4.2052 | 24,020 | 4.1503 | 68.9 | 7.60 |
| sqlalchemy | stdlib_uuid4 | uuid4_control | 3.9840 | 3.9775–4.0836 | 25,101 | 3.9704 | 68.4 | 4.27 |
| sqlalchemy | postgres_uuid7 | server_strategy | 3.4959 | 3.3035–3.5916 | 28,605 | 3.4808 | 68.3 | 0.00 |
| copy | checkout_scalar | client_uuid7 | 0.4835 | 0.4818–0.4874 | 206,838 | 0.2024 | 64.9 | 10.63 |
| copy | checkout_batch | client_uuid7 | 0.4865 | 0.4774–0.5070 | 205,555 | 0.1966 | 64.9 | 8.78 |
| copy | published_scalar | client_uuid7 | 0.4928 | 0.4857–0.5060 | 202,920 | 0.2042 | 64.9 | 10.13 |
| copy | published_batch | client_uuid7 | 0.4749 | 0.4739–0.5009 | 210,578 | 0.1918 | 64.8 | 8.96 |
| copy | stdlib_uuid7 | client_uuid7 | 0.6879 | 0.6862–0.7142 | 145,362 | 0.4045 | 64.8 | 37.05 |
| copy | uuid_utils | client_uuid7 | 0.5176 | 0.5074–0.5274 | 193,204 | 0.2284 | 65.3 | 14.38 |
| copy | uuid6 | client_uuid7 | 0.7593 | 0.7564–0.7781 | 131,707 | 0.4769 | 65.0 | 42.40 |
| copy | stdlib_uuid4 | uuid4_control | 0.6903 | 0.6590–0.7189 | 144,859 | 0.3296 | 64.8 | 25.29 |
| copy | postgres_uuid7 | server_strategy | 0.4475 | 0.4330–0.4556 | 223,460 | 0.1111 | 64.4 | 0.01 |
| historical | checkout_at | client_uuid7 | 0.6322 | 0.6318–0.6598 | 158,167 | 0.3366 | 64.9 | 29.20 |
| historical | published_at | client_uuid7 | 0.6409 | 0.6327–0.6421 | 156,041 | 0.3341 | 64.9 | 29.05 |
| historical | uuid_utils_at | client_uuid7 | 0.5310 | 0.5294–0.5713 | 188,319 | 0.2281 | 65.4 | 14.34 |
| historical | rfc_random_at | reference_strategy | 0.6739 | 0.6735–0.6741 | 148,392 | 0.3723 | 64.9 | 32.59 |

Every sample committed and passed full row count, uniqueness, payload, sequence, RFC layout and timestamp verification.
UUIDv4 is a control, PostgreSQL uuidv7() is a server strategy, and rfc_random_at is an OS-random reference constructor; none is a competing live UUIDv7 library row.
Historical comparison: fastuuid7 uuid7_at and uuid_utils.compat.uuid7(nanoseconds=...). No stdlib/uuid6 exact timestamp API is claimed.
uuid6 may advance a logical millisecond per call; raw results record clock drift and an explicit rows+1 ms verification allowance.
Shared host, small initially empty tables, one client, warm caches, no query/read or sustained-update workload; no statistical significance or production-scale index claim.
Raw samples, phase timings, versions, settings, SHA and verification counts are in the adjacent JSON.
