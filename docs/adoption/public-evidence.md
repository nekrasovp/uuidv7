# Public evidence of external use

Review date: **2026-09-18 Europe/Moscow** (public reads on 2026-09-17 UTC,
approximately 21:45–22:15 UTC). This is a bounded discovery snapshot, not a
census. Only public search, GitHub GET APIs, source files, and PyPI metadata
were used. No maintainers were contacted and no third-party code was executed.

## What was confirmed

**Two application code scenarios** have both a dependency on this distribution
and identifiable call sites. A **third scenario is a source-packaging recipe**
for this repository's C core, not a Python application. **Zero installed
environments and zero production deployments were independently verified.**
External benchmark references are recorded separately below. None of these
counts is a count of users, companies, customers, or endorsements.

Classification used here:

| Evidence | What it establishes | What it cannot establish alone |
| --- | --- | --- |
| Manifest / lockfile | Declared dependency / resolved artifact identity | Installation, execution, current deployed version |
| Application call site | A concrete integration in public source | Successful execution or production use |
| Packaging recipe | A plan to build specified upstream sources | Successful build, published binaries, downstream use |
| Benchmark / example | Evaluation or illustrative code | Application adoption, comparable guarantees, operator experience |
| Issue / pull request | A report or proposed change, attributed to its author | Deployment, acceptance, or human demand when bot-generated |
| Operator report / runtime evidence | Only the workload, version, period and results actually evidenced | General reliability or all users' outcomes |

## 1. SQLAlchemy identifiers in an identity service

Repository: `ystdn-exp/identity-service`; reviewed commit
[`08beb5d36ee95cde0db3d99208879537d946f361`](https://github.com/ystdn-exp/identity-service/commit/08beb5d36ee95cde0db3d99208879537d946f361),
committer timestamp **2026-07-20T14:44:18Z**. Observed on the review date above.

- [Manifest](https://github.com/ystdn-exp/identity-service/blob/08beb5d36ee95cde0db3d99208879537d946f361/pyproject.toml)
  declares `fastuuid7>=0.3.0`.
- [Lockfile](https://github.com/ystdn-exp/identity-service/blob/08beb5d36ee95cde0db3d99208879537d946f361/uv.lock#L655-L659)
  resolves **fastuuid7 0.3.0** from PyPI. Its source-archive SHA-256 is
  `893fe116ec005da1ba54bffa4011f0beaae3b031892e0651b512dbf4a8d3163f`.
  This matches the [PyPI 0.3.0 metadata](https://pypi.org/pypi/fastuuid7/0.3.0/json),
  whose project URL is `nekrasovp/uuidv7`.
- [Shared model](https://github.com/ystdn-exp/identity-service/blob/08beb5d36ee95cde0db3d99208879537d946f361/app/modules/shared/models.py#L1-L29)
  imports `uuid7` from `fastuuid7` and uses the callable as the default of a
  SQLAlchemy UUID primary key. The
  [User model](https://github.com/ystdn-exp/identity-service/blob/08beb5d36ee95cde0db3d99208879537d946f361/app/modules/users/models.py#L1-L12)
  inherits that mixin.

**Classification:** declared and locked dependency plus application code.
**Limit:** no install log, database execution, deployment, operator testimony,
volume, or latency evidence was examined. This does not establish use of 0.4.0
or 0.5.0. The commit date is the reviewed snapshot's date, not the adoption date.

## 2. RabbitMQ message identifiers in S.L.O.T.H

Repository: `ISCOUTB/S.L.O.T.H`; reviewed commit
[`d06c31aa8e62f46f0aad4f5778de33ee108f5909`](https://github.com/ISCOUTB/S.L.O.T.H/commit/d06c31aa8e62f46f0aad4f5778de33ee108f5909),
committer timestamp **2026-05-07T22:26:44Z**. Observed on the review date above.

- The messaging utilities
  [manifest](https://github.com/ISCOUTB/S.L.O.T.H/blob/d06c31aa8e62f46f0aad4f5778de33ee108f5909/packages/messaging-utils/messaging-utils-py/pyproject.toml)
  declares `fastuuid7>=0.1.0`; its
  [lockfile](https://github.com/ISCOUTB/S.L.O.T.H/blob/d06c31aa8e62f46f0aad4f5778de33ee108f5909/packages/messaging-utils/messaging-utils-py/uv.lock#L204-L210)
  resolves **fastuuid7 0.1.0**. The source-archive SHA-256
  `e88e6fc79e894e3c3974acfffb98f90c6edeae6665a3fc5e27b2d86851b92ee3`
  matches [PyPI 0.1.0 metadata](https://pypi.org/pypi/fastuuid7/0.1.0/json),
  which links to this repository.
- The [publisher](https://github.com/ISCOUTB/S.L.O.T.H/blob/d06c31aa8e62f46f0aad4f5778de33ee108f5909/packages/messaging-utils/messaging-utils-py/src/messaging_utils/messaging/publishers.py#L25)
  imports through the legacy `uuidv7` path. Its
  [validation message path](https://github.com/ISCOUTB/S.L.O.T.H/blob/d06c31aa8e62f46f0aad4f5778de33ee108f5909/packages/messaging-utils/messaging-utils-py/src/messaging_utils/messaging/publishers.py#L286-L323)
  generates `str(uuid7())` when a task ID is absent and supplies the resulting
  value to the payload and RabbitMQ `message_id`.
- [Dependabot PR #208](https://github.com/ISCOUTB/S.L.O.T.H/pull/208), created
  **2026-08-28T22:43:27Z**, proposes 0.1.0 → 0.3.0 and directly links our
  repository. It was **open, unmerged, authored by `dependabot[bot]`** when
  checked. This is dependency-maintenance activity, not a user's testimonial.

**Classification:** declared and locked dependency plus application code.
**Limit:** the old lock is not a production inventory; even the later bot PR
does not prove an upgrade. Version 0.1.0 predates the CSPRNG/fork reset changes
in 0.3.0. This scenario provides **no confirmation of 0.4.0/0.5.0 behavior**
and is not a recommendation to use the old release. See the
[security policy](../../SECURITY.md) before planning an upgrade.

## 3. Windows packaging of the C core

Repository: `brechtsanders/winlibs_recipes`; reviewed
[recipe at `d37a463c6832650db1e5dd9b76c9c642d10de004`](https://github.com/brechtsanders/winlibs_recipes/blob/d37a463c6832650db1e5dd9b76c9c642d10de004/recipes/uuidv7.winlib).
Observed on the review date above; the recipe itself records
`VERSION=0.4.0` and `VERSIONDATE=20260917`.

It names `https://github.com/nekrasovp/uuidv7`, downloads that repository's
version tag, compiles `uuidv7/uuidv7_impl/src/uuid7_gen.c`, and describes static
and Windows DLL packaging. Python-install commands are commented out.

**Classification:** external source-packaging recipe for this C core.
**Limit:** no build was run or artifact inspected. This is not proof of a
working Windows package, Python-wheel installation, stable public C ABI, or
production consumption. The recipe's date is not a verified build date.

## Other references and rejected matches

| Source, observed on the review date | Exact basis and classification | Limitation |
| --- | --- | --- |
| [lava-sh/uuid7-rs manifest](https://github.com/lava-sh/uuid7-rs/blob/fe98d368cfdc1a1997bf21422d587e7a0098bc2b/pyproject.toml#L70-L80) and [benchmark](https://github.com/lava-sh/uuid7-rs/blob/fe98d368cfdc1a1997bf21422d587e7a0098bc2b/benchmark/run.py#L143-L164) | Benchmark dependency `fastuuid7`, calls through `uuidv7`; commit dated 2026-09-06T02:22:16Z | Version is unpinned there; one case calls private `_uuid7_python`. Evaluation code, no application/production claim or imported performance endorsement |
| [marcomq/fast-uuid-v7 benchmark](https://github.com/marcomq/fast-uuid-v7/blob/8bc95e8e4799550596cbbed6b7b31a62745d358c/python/bench/bench.py#L75-L87) | Optional comparison case for `fastuuid7` | The author's product is **fastuuidv7**, a different distribution. Presence in a comparison does not mean it is a runtime dependency or that the optional case executed |
| [STomoya/nekomata helper](https://github.com/STomoya/nekomata/blob/95fcba5c2b1c7f3e5efe45158ca7706a5566b533/src/nekomata/utils/uuid.py) | Function named `fastuuid7`, imported generator from `fastuuid` | Rejected: different package |
| [fastuuid/fastuuid test](https://github.com/fastuuid/fastuuid/blob/d33252258c7e9d2ece27fa18f5beca5ad71d9d55/tests/test_benchmarks.py#L13-L17) | Alias `from fastuuid import uuid7 as fastuuid7` | Rejected: different package |
| [PyDigger metadata mirror](https://github.com/szabgab/pydigger-data/blob/5806f74180c476538d4b40d9ebee4f2276418c69/data/pypi/fa/fastuuid7.json) | Search hit for a registry metadata file | Discovery signal only; not application execution |

## Search method and coverage

The target identity is the **PyPI distribution `fastuuid7`**, owned by
`nekrasovp`, with repository `nekrasovp/uuidv7`. `uuidv7` imports alone are
ambiguous: link them to an exact dependency, artifact or source URL before
counting them. Registry listings, the author's own site, downloads, stars,
automated updates and duplicated benchmark charts are not user counts.

GitHub REST searches used GET, `per_page=100`, page 1. Results are indexed
snapshots; the search service reported `incomplete_results=false`, which does
not make coverage exhaustive.

| Search endpoint / query | Returned total | Review coverage |
| --- | ---: | --- |
| `/search/code`: `fastuuid7 -user:nekrasovp` | 573 | First page of 100 retrieved; repeated benchmark charts prompted the filtered query below, not a count of consumers |
| `/search/code`: `fastuuid7 -user:nekrasovp -repo:lava-sh/benchmarks` | 15 | All 15 paths triaged; candidate source and dependency files opened at returned SHAs |
| `/search/code`: `"nekrasovp/uuidv7" -user:nekrasovp -repo:lava-sh/benchmarks` | 3 | All 3 paths triaged; packaging recipe inspected |
| `/search/code`: `uuidv7 repo:ISCOUTB/S.L.O.T.H` | 4 | Located legacy call sites; messaging path inspected with its lockfile |
| `/search/issues`: `"fastuuid7" -user:nekrasovp` | 11 | Returned PR metadata reviewed; #208 inspected. Bot updates, not eleven independent reports |

General web queries included `"fastuuid7" dependency github`,
`"fastuuid7" "production"`, `"fastuuid7" "requirements.txt"`,
`"fastuuid7" "pyproject.toml"` and `"nekrasovp/uuidv7"`.
They primarily surfaced project/registry material and comparisons; they
provided no independently verified production case. Private repositories,
unindexed files, deleted code, and actual deployed states are outside coverage.

Reproduce discovery with an authenticated GitHub CLI (read access only):

```sh
gh api -X GET search/code \
  -f q='fastuuid7 -user:nekrasovp -repo:lava-sh/benchmarks' \
  -f per_page=100 --jq '{total_count,incomplete_results,items:[.items[]|{path,html_url}]}'
gh api -X GET search/issues \
  -f q='"fastuuid7" -user:nekrasovp' \
  -f per_page=100 --jq '{total_count,incomplete_results,items:[.items[]|{html_url,title}]}'
```

Future searches can return different counts. Preserve the reviewed source SHA,
check the package identity again, and record dates and limits. Promote a source
example to operational evidence only after obtaining attributable, concrete
runtime information. No such promotion is justified by this review.
