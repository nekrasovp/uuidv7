# Adopting fastuuid7

These materials separate implementation advice, measured performance, and
evidence of external use. Prepared on 2026-09-18 (Europe/Moscow) for the 0.5.0
release cycle; the documented released API and historical measurements are
from **0.4.0**, commit `0386e15dc32fb2658e33518be77bae330db6556f`.

- [Choose a generator and an output representation](choosing-a-generator.md).
- [Public evidence of external use](public-evidence.md): two application code
  scenarios, one source-packaging recipe, and **zero verified production
  deployments** in this review. These are different evidence categories.
- [Feedback template and proposed 1.0 readiness criteria](feedback-and-1.0.md).
- [Technical article draft](../articles/application-side-uuidv7.md).

The application examples establish public dependency and call-site evidence.
They do not establish installed environments, endorsement, workload size, or
use of 0.4.0/0.5.0. The article's published 0.4.0 figures are not measurements of
0.5.0. New application measurements must be attached to their own exact source
commit and environment before making release claims.
