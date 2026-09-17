# Feedback and proposed 1.0 readiness criteria

The [public evidence review](public-evidence.md) establishes two application
code scenarios and a source-packaging recipe, with no independently verified
production deployment. This is enough to inform documentation; it does not
establish demand for batch generation, historical IDs, or a stable C ABI.

## A short feedback template

Use this in a voluntary report. A repository link is optional; a sanitized
reproducer is useful. Do not include credentials, user data or private logs.
Leave unknown fields unknown. Reporting results does not imply permission to
quote a person or name their organization publicly.

```text
Date and stage: evaluating / prototype / CI / deployed (period observed):
fastuuid7 version and source SHA; Python, OS, architecture:
Application boundary: ORM/driver/database/serializer versions and API used:
Why an ID is needed here; alternative considered (stdlib / PostgreSQL / other):
Evidence: dependency only / executed reproducer / measured workload / operator report:
Command or public immutable source; expected result; actual result:
Load: IDs/operation, concurrency, batch/transaction size, duration:
Result: latency/throughput/memory and failures, or "not measured":
Ordering, clock rollback, fork, retry and historical-data requirements:
Decision: adopted / declined / blocked / still evaluating; reason:
May this report be quoted publicly? No / exact approved excerpt and attribution:
```

A bug report should distinguish generator behavior from driver adaptation,
serialization, retries and database constraints. Negative results and choosing
the standard library are useful findings. Use the repository's existing
reporting channels voluntarily; this document does not initiate outreach.

## Facts, hypotheses and unverified demand

| Statement | Status | Evidence needed to change it |
| --- | --- | --- |
| Public source uses this distribution for ORM and message IDs | Observed, at the SHAs in the evidence review | New immutable source or attributable runtime evidence for stronger claims |
| A Windows recipe consumes the C source | Observed recipe only | Reproducible build logs and artifact identity before claiming working packaging |
| Explicit text/batch output may remove unnecessary conversions | Engineering hypothesis supported by version-bound microbenchmarks | Matched end-to-end workload with serialization/persistence and measured costs |
| Operators need exact historical timestamps | Supported API; market demand unverified | A concrete migration problem, executed backfill, retry behavior and operator feedback |
| Users require a stable native C ABI or free-threaded Python support | Unverified demand | Concrete compatibility requirements and a reviewed support proposal |
| 0.5.0 improves real application throughput | Unverified until measured | Candidate SHA, commands, raw results, environment and equivalent baseline |

## Proposed gates for 1.0

These are **proposed acceptance criteria**, not completed checks or an approved
release promise. A release owner should record a verdict and evidence URL for
each row on the actual 1.0 candidate. Technical success is separate from an
operator's adoption decision.

| Gate | Concrete acceptance evidence | Current status in this review |
| --- | --- | --- |
| Stable Python contract | Documented scalar/batch types, errors, ordering scope, timestamp units, historical/live isolation and legacy import policy; compatibility tests pass at the candidate SHA | 0.4.0 contract exists; 1.0 candidate not evaluated |
| Correctness and entropy | Installed-wheel tests exercise overflow, rollback, fork reset where supported, malformed inputs, packed layout and historical boundaries on all claimed platforms; no unresolved critical correctness/security defects | Prior 0.4.0 evidence exists; no 1.0 sign-off |
| Distribution and support | Explicit supported Python/OS/architectures; successful wheel installs and sdist builds, typing checks, artifact hashes and release provenance; unsupported targets explicitly listed | Must be checked on final 1.0 artifacts |
| Integration behavior | Reproducible create/serialize/validate/store/read/retry checks for at least two intended application boundaries, with exact dependency versions; documented native-object adapter limits | Public code is discovery evidence; it does not pass this gate |
| External feedback | At least two independent voluntary reports of executed application evaluation, with API, versions, observed period and outcome; a declined adoption can qualify as feedback | No such reports verified in this review |
| Honest performance claims | Exact-SHA reports for matched output types and generation guarantees; end-to-end time and memory where claimed; all skips/failures visible; no regression claim without comparable measurements | Published 0.4.0 microbenchmarks only in this document set |
| Operational documentation | Tested migration/rollback procedure, persisted IDs across retries/backfills, timestamp privacy and clock/process boundaries explained; compatibility policy for future changes | Draft guidance supplied; application acceptance remains separate |
| Maintainer decision | Named release owner records accepted support scope, open limitations and reviewed exceptions; stable C ABI/free-threading require separate explicit commitments if offered | Pending release-owner decision |

Download counts, stars, bot PRs and the existence of an example do not satisfy
the external-feedback gate. A 1.0 label must not silently add guarantees beyond
what was reviewed. A lack of external reports does not block publishing honest
pre-1.0 tools, documentation or the research findings.
