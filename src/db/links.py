from __future__ import annotations

import sqlite3
from dataclasses import dataclass

_VALID_KINDS = {"not-applicable"}


@dataclass
class MemoryLink:
    id: int
    memory_id: int
    task_slug: str
    kind: str
    note: str
    created_at: str


def insert(
    conn: sqlite3.Connection,
    memory_id: int,
    task_slug: str,
    kind: str,
    note: str,
) -> int:
    if kind not in _VALID_KINDS:
        raise ValueError(
            f"invalid kind '{kind}', must be one of: {sorted(_VALID_KINDS)}"
        )
    cur = conn.execute(
        "INSERT INTO memory_links (memory_id, task_slug, kind, note) VALUES (?, ?, ?, ?)",
        (memory_id, task_slug, kind, note),
    )
    conn.commit()
    return cur.lastrowid


def exists(
    conn: sqlite3.Connection,
    memory_id: int,
    task_slug: str,
    kind: str,
) -> bool:
    row = conn.execute(
        "SELECT 1 FROM memory_links WHERE memory_id = ? AND task_slug = ? AND kind = ?",
        (memory_id, task_slug, kind),
    ).fetchone()
    return row is not None


def list_for_task(
    conn: sqlite3.Connection,
    task_slug: str,
    kind: str | None = None,
) -> list[MemoryLink]:
    query = "SELECT * FROM memory_links WHERE task_slug = ?"
    params: list = [task_slug]
    if kind is not None:
        query += " AND kind = ?"
        params.append(kind)
    rows = conn.execute(query, params).fetchall()
    return [
        MemoryLink(
            id=r["id"],
            memory_id=r["memory_id"],
            task_slug=r["task_slug"],
            kind=r["kind"],
            note=r["note"],
            created_at=r["created_at"],
        )
        for r in rows
    ]
