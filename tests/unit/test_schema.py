import sqlite3
from pathlib import Path

import pytest

from src.db.connection import get_connection
from src.db.schema import CURRENT_VERSION, migrate


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    yield c
    c.close()


def _tables(conn) -> set[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {r[0] for r in rows}


def test_migrate_creates_all_tables(conn):
    migrate(conn)
    tables = _tables(conn)
    assert "memories" in tables
    assert "tasks" in tables
    assert "gates" in tables
    assert "loop_iterations" in tables


def test_migrate_sets_user_version(conn):
    migrate(conn)
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == CURRENT_VERSION


def test_migrate_is_idempotent(conn):
    migrate(conn)
    migrate(conn)
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    assert version == CURRENT_VERSION
    assert len(_tables(conn)) >= 4


def test_tasks_slug_unique(conn):
    migrate(conn)
    conn.execute("INSERT INTO tasks (slug, title) VALUES ('foo', 'Foo')")
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO tasks (slug, title) VALUES ('foo', 'Foo2')")
        conn.commit()
