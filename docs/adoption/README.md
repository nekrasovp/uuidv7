# Adopting fastuuid7

These materials separate implementation advice, measured performance, and
evidence of external use. Prepared on 2026-09-18 (Europe/Moscow) for the 0.5.0
release cycle. Released examples and historical microbenchmarks are from
**0.4.0**, commit `0386e15dc32fb2658e33518be77bae330db6556f`; the guide also
documents accepted `uuid7_at_many()` from the **0.5.0 candidate** at
`aefda263cfb81f0439e0f0f6df4be0d6d1165ce8`, before release publication.

- [Choose a generator and an output representation](choosing-a-generator.md).
- [Executable framework and PostgreSQL integration suite](https://github.com/nekrasovp/uuidv7/blob/f0b81a046f0c4246d6ba04651d0eede279c1f337/docs/integration-testing.md),
  with its verified version/matrix boundaries.
- [Public evidence of external use](public-evidence.md): two application code
  scenarios, one source-packaging recipe, and **zero verified production
  deployments** in this review. These are different evidence categories.
- [Feedback template and proposed 1.0 readiness criteria](feedback-and-1.0.md).
- [Technical article draft](../articles/application-side-uuidv7.md).

The application examples establish public dependency and call-site evidence.
They do not establish installed environments, endorsement, workload size, or
use of 0.4.0/0.5.0. The article's published 0.4.0 figures are not measurements of
0.5.0. A separate PostgreSQL study from this release cycle is incorporated at
its measured source `032adad79e7f319139e093dbac8cd27c8402d5b8`, which still uses
the 0.4.0 generator. It motivates further historical-batch evaluation and does
not establish a future release's performance or external adoption.
