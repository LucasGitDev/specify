from __future__ import annotations

import sqlite3
from dataclasses import dataclass

_VALID_STATUSES = {"planned", "in_progress", "review", "closed"}


@dataclass
class Task:
    id: int
    slug: str
    title: str
    status: str
    spec_path: str | None
    worktree_path: str | None
    worktree_branch: str | None
    created_at: str
    updated_at: str


def _row_to_task(row: sqlite3.Row) -> Task:
    return Task(
        id=row["id"],
        slug=row["slug"],
        title=row["title"],
        status=row["status"],
        spec_path=row["spec_path"],
        worktree_path=row["worktree_path"],
        worktree_branch=row["worktree_branch"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create(
    conn: sqlite3.Connection,
    slug: str,
    title: str,
    spec_path: str | None = None,
    worktree_path: str | None = None,
    worktree_branch: str | None = None,
) -> int:
    if get(conn, slug) is not None:
        raise ValueError(f"task '{slug}' já existe")
    cur = conn.execute(
        "INSERT INTO tasks (slug, title, spec_path, worktree_path, worktree_branch)"
        " VALUES (?, ?, ?, ?, ?)",
        (slug, title, spec_path, worktree_path, worktree_branch),
    )
    conn.commit()
    return cur.lastrowid


def get(conn: sqlite3.Connection, slug: str) -> Task | None:
    row = conn.execute("SELECT * FROM tasks WHERE slug = ?", (slug,)).fetchone()
    return _row_to_task(row) if row else None


def list_all(conn: sqlite3.Connection, status: str | None = None) -> list[Task]:
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list = []
    if status is not None:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY id"
    return [_row_to_task(r) for r in conn.execute(query, params).fetchall()]


def update_status(conn: sqlite3.Connection, slug: str, status: str) -> None:
    if status not in _VALID_STATUSES:
        raise ValueError(f"status inválido: '{status}'. Válidos: {_VALID_STATUSES}")
    conn.execute(
        "UPDATE tasks SET status = ?, updated_at = datetime('now') WHERE slug = ?",
        (status, slug),
    )
    conn.commit()


def delete(conn: sqlite3.Connection, slug: str) -> None:
    conn.execute("DELETE FROM tasks WHERE slug = ?", (slug,))
    conn.commit()
