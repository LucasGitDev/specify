from src.db.connection import get_connection
from pathlib import Path

_MIGRATION_1 = """
CREATE TABLE IF NOT EXISTS memories (
    id         INTEGER PRIMARY KEY,
    type       TEXT NOT NULL,
    scope      TEXT NOT NULL DEFAULT 'global',
    content    TEXT NOT NULL,
    source     TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY,
    slug       TEXT UNIQUE NOT NULL,
    title      TEXT NOT NULL,
    status     TEXT NOT NULL DEFAULT 'planned',
    spec_path  TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS gates (
    id         INTEGER PRIMARY KEY,
    task_slug  TEXT NOT NULL,
    phase      TEXT NOT NULL,
    gate_type  TEXT NOT NULL,
    status     TEXT NOT NULL,
    output     TEXT,
    iteration  INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS loop_iterations (
    id         INTEGER PRIMARY KEY,
    task_slug  TEXT NOT NULL,
    phase      TEXT NOT NULL,
    iteration  INTEGER NOT NULL,
    action     TEXT NOT NULL,
    result     TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_MIGRATION_2 = """
CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories USING vec0(
    memory_id INTEGER PRIMARY KEY,
    embedding  FLOAT[384]
);
"""

_MIGRATION_3 = """
ALTER TABLE tasks ADD COLUMN worktree_path TEXT;
ALTER TABLE tasks ADD COLUMN worktree_branch TEXT;
"""

_MIGRATION_4 = """
CREATE TABLE IF NOT EXISTS memory_searches (
    id           INTEGER PRIMARY KEY,
    query        TEXT NOT NULL,
    results_count INTEGER NOT NULL DEFAULT 0,
    source       TEXT,
    searched_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

MIGRATIONS: dict[int, str] = {
    1: _MIGRATION_1,
    2: _MIGRATION_2,
    3: _MIGRATION_3,
    4: _MIGRATION_4,
}

CURRENT_VERSION = 4


def migrate(conn) -> None:
    current = conn.execute("PRAGMA user_version").fetchone()[0]
    for version in sorted(v for v in MIGRATIONS if v > current):
        conn.executescript(MIGRATIONS[version])
        conn.execute(f"PRAGMA user_version = {version}")
    conn.commit()


def init_db(db_path: Path):
    conn = get_connection(db_path)
    migrate(conn)
    conn.close()
