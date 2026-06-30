from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class Memory:
    id: int
    type: str
    scope: str
    content: str
    source: str | None
    created_at: str
    updated_at: str


def _row_to_memory(row: sqlite3.Row) -> Memory:
    return Memory(
        id=row["id"],
        type=row["type"],
        scope=row["scope"],
        content=row["content"],
        source=row["source"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def insert(
    conn: sqlite3.Connection,
    type: str,
    content: str,
    scope: str = "global",
    source: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO memories (type, content, scope, source) VALUES (?, ?, ?, ?)",
        (type, content, scope, source),
    )
    conn.commit()
    return cur.lastrowid


def get(conn: sqlite3.Connection, memory_id: int) -> Memory | None:
    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    return _row_to_memory(row) if row else None


def list_all(
    conn: sqlite3.Connection,
    scope: str | None = None,
    type: str | None = None,
) -> list[Memory]:
    query = "SELECT * FROM memories WHERE 1=1"
    params: list = []
    if scope is not None:
        query += " AND scope = ?"
        params.append(scope)
    if type is not None:
        query += " AND type = ?"
        params.append(type)
    query += " ORDER BY id"
    rows = conn.execute(query, params).fetchall()
    return [_row_to_memory(r) for r in rows]


def update(conn: sqlite3.Connection, memory_id: int, content: str) -> None:
    conn.execute(
        "UPDATE memories SET content = ?, updated_at = datetime('now') WHERE id = ?",
        (content, memory_id),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, memory_id: int) -> None:
    conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
    conn.commit()


def search_substring(
    conn: sqlite3.Connection, query: str, limit: int = 5
) -> list[Memory]:
    rows = conn.execute(
        "SELECT * FROM memories WHERE content LIKE ? ORDER BY id LIMIT ?",
        (f"%{query}%", limit),
    ).fetchall()
    return [_row_to_memory(r) for r in rows]
