# Integration and UUID compatibility tests

The recipes in [integrations.md](integrations.md) are exercised by real framework
and database dependencies. These are test extras; the library still has no
runtime dependencies and retains Python 3.9 support.

## Suites and dependency boundaries

| Suite | Extra | Python in dedicated CI | Contract |
| --- | --- | --- | --- |
| Core | `dev` | Existing CI: 3.9–3.14 | No frameworks or database required |
| UUID properties | `dev,properties` | 3.9, 3.10, 3.14 | Compare each public UUID result with a stdlib UUID of the same value |
| Frameworks | `dev,integrations` | 3.10, 3.12, 3.14 | SQLAlchemy 2, Django 5.2 LTS, Pydantic 2, FastAPI, psycopg 3 and PostgreSQL 17 |

`uv.lock` records the exact dependency versions, including the Python 3.9
compatible Hypothesis resolution. Integration requirements have Python >=3.10
markers; installing that extra on 3.9 does not install frameworks. The `dev` and
`release` requirement lists are unchanged. Django 5.2.8 or later supports the
framework matrix, including Python 3.14 ([Django release notes](https://docs.djangoproject.com/en/5.2/releases/5.2/)).

Run the usual suite without integration dependencies or a database:

```sh
uv sync --extra dev --locked
uv run --extra dev --locked pytest
```

Without `properties`, pytest reports the property module as **skipped**. This is
not property coverage. Integration modules are not collected unless
`FASTUUID7_RUN_INTEGRATIONS=1`; ordinary test discovery does not import frameworks.

## UUID properties

```sh
uv sync --extra dev --extra properties --locked
uv run --extra dev --extra properties --locked pytest tests/test_uuid_compat_properties.py
```

Hypothesis exercises historical timestamps across the full accepted range,
explicit endpoint examples, scalar and batch results, and comparisons with
arbitrary stdlib UUID values. Each generated UUID is reconstructed with
`uuid.UUID(int=value.int)`. Checks cover bytes, little-endian bytes, text, fields,
hash/equality, dictionary/set interchangeability, all rich comparisons, mixed
ordering, and every pickle protocol supported by the interpreter.

The Hypothesis input sequence is deterministic (`derandomize=True`, 75 examples,
no timing deadline). Generator OS entropy remains random: IDs from independent
generation calls are never expected to have identical bits. No private generator
hooks or copied generation algorithms are used. The `.time` differential only
runs on Python 3.14+, because older stdlib UUIDs expose UUIDv1 time semantics.
Historical outputs independently retain their requested millisecond value.

Native `UUID7Obj` tests cover documented properties, immutability, hashing and
ordering among native objects. They do not claim native/stdlib equality, shared
hash values, pickle support, or automatic framework/driver adaptation.

## Local PostgreSQL and frameworks

Use Python 3.10+ and a disposable test database. This command runs the same pinned
PostgreSQL image as CI and exposes it only on loopback:

```sh
docker run --detach --name fastuuid7-test-integrations \
  --env POSTGRES_DB=fastuuid7_test \
  --env POSTGRES_USER=fastuuid7_test \
  --env POSTGRES_PASSWORD=fastuuid7_test \
  --publish 127.0.0.1:55437:5432 \
  postgres:17@sha256:ebba4f4de37f08f138f97c1443c987a435e783177afedcc4aaf2da1930fbc37a
docker exec fastuuid7-test-integrations pg_isready -U fastuuid7_test -d fastuuid7_test

uv sync --extra dev --extra integrations --locked
export FASTUUID7_RUN_INTEGRATIONS=1
export FASTUUID7_TEST_POSTGRES_DSN=postgresql://fastuuid7_test:fastuuid7_test@127.0.0.1:55437/fastuuid7_test
uv run --extra dev --extra integrations --locked pytest tests/integration

docker rm --force --volumes fastuuid7-test-integrations
unset FASTUUID7_RUN_INTEGRATIONS FASTUUID7_TEST_POSTGRES_DSN
```

Wait for `pg_isready` to report readiness before running pytest. The DSN is
required, connections have a five-second timeout, and database names must start
with `fastuuid7_test`. Each database module creates a unique test schema and
drops that schema in fixture teardown; connections use that schema as their
search path. Tables, Django app labels, HTTP routes and local container names
are test-specific. A missing dependency, DSN or unavailable database fails an
enabled integration run rather than skipping it.

The checks exercise:

- SQLAlchemy's `Uuid(as_uuid=True)` primary key and `default=uuid7` on both SQLite
  and PostgreSQL: distinct per-row defaults, explicit historical IDs, commit,
  reload in a new session, lookup, ordering and duplicate-key rejection.
- Django's `UUIDField(default=uuid7)`: generation before save, validation,
  PostgreSQL save/read through a new connection, text lookup, JSON serialization
  and duplicate-key rejection. Django settings are configured only for this test
  process; pytest-django and migrations are not needed for the disposable model.
- Pydantic's `Field(default_factory=uuid7)`: UUID/text/bytes inputs, strict UUID
  acceptance, JSON serialization and validation, invalid input rejection; real
  FastAPI TestClient request/response and path-parameter validation.
- psycopg's native UUID adaptation in text and binary result modes: `INSERT
  RETURNING`, committed reads through a new connection, primary-key lookup,
  PostgreSQL ordering, JSONB payloads and invalid/duplicate value rejection.

These checks establish the tested combinations, not every framework version or
database backend. UUID values retain their bits after storage; on Python <3.14 a
driver-loaded stdlib UUID does not acquire fastuuid7's `.time` override. The
FastAPI app exercises validation/serialization, not a persistent HTTP service.

## CI reproduction

`.github/workflows/integrations.yml` uses pinned action commits, uv 0.11.28,
`uv sync --locked`, explicit Python matrices and a digest-pinned PostgreSQL
service with a health check. It runs on pull requests, main pushes and manual
dispatch. The property job explicitly selects its module, so missing Hypothesis
cannot yield a successful empty test run. Framework dependencies are imported
normally in the enabled suite. A skipped local suite or a CI job that never
starts is not a passing integration gate.

The workflows pin Python minor lines and the Ubuntu runner image family; patch
releases and hosted-runner updates may still change. The PostgreSQL digest and
lock should be refreshed intentionally alongside another complete integration
run. The service uses application-generated IDs, without database extensions or
server-side UUIDv7 generation.
