# Workload task scope

Base: `0386e15dc32fb2658e33518be77bae330db6556f` (fastuuid7 0.4.0).
Branch: `codex/workloads-fastuuid7-050`; initially clean, dedicated worktree.

Owned: `benchmarks/workloads/**`, `.github/workflows/workloads.yml`,
`tests/test_workload_contract.py`, `docs/performance-workloads.md`.
Authorized: implementation, disposable local database, tests, commit, push,
draft PR and relevant GitHub Actions runs. Terminal result: verified draft PR,
real workload evidence and exact-head clean-clone handoff to the coordinator.

Excluded: C core, existing microbenchmarks, library runtime dependencies,
root pyproject/lock, README, CHANGELOG, SECURITY, releasing documentation,
merge, package versions, tags, releases, publication, paid resources and outreach.
Historical batch APIs remain a separate task; this runner uses the 0.4.0 scalar
contract and documents the extension boundary explicitly.
