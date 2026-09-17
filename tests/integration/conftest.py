"""Explicit integration opt-in and isolated PostgreSQL test schemas."""

import os
import uuid

import pytest

# The ordinary dev suite does not import frameworks or require a running database.
# Explicit integration runs import dependencies normally, so missing extras fail.
collect_ignore_glob = [] if os.environ.get("FASTUUID7_RUN_INTEGRATIONS") == "1" else ["test_*.py"]


@pytest.fixture(scope="module")
def postgres_dsn():
    import psycopg
    from psycopg import sql
    from psycopg.conninfo import conninfo_to_dict, make_conninfo

    dsn = os.environ.get("FASTUUID7_TEST_POSTGRES_DSN")
    if not dsn:
        pytest.fail("FASTUUID7_TEST_POSTGRES_DSN is required for PostgreSQL integration tests")
    if not conninfo_to_dict(dsn).get("dbname", "").startswith("fastuuid7_test"):
        pytest.fail("PostgreSQL database name must start with fastuuid7_test")
    schema = "fastuuid7_test_" + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True, connect_timeout=5) as admin:
        admin.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        try:
            yield make_conninfo(dsn, options=f"-csearch_path={schema}", connect_timeout=5)
        finally:
            admin.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
