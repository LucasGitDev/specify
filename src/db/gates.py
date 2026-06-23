from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class Gate:
    id: int
    task_slug: str
    phase: str
    gate_type: str
    status: str
    output: str | None
    iteration: int
    created_at: str


def _row_to_gate(row: sqlite3.Row) -> Gate:
    return Gate(
        id=row["id"],
        task_slug=row["task_slug"],
        phase=row["phase"],
        gate_type=row["gate_type"],
        status=row["status"],
        output=row["output"],
        iteration=row["iteration"],
        created_at=row["created_at"],
    )


def record(
    conn: sqlite3.Connection,
    task_slug: str,
    phase: str,
    gate_type: str,
    status: str,
    output: str | None = None,
    iteration: int = 1,
) -> int:
    cur = conn.execute(
        "INSERT INTO gates (task_slug, phase, gate_type, status, output, iteration)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (task_slug, phase, gate_type, status, output, iteration),
    )
    conn.commit()
    return cur.lastrowid


def history(
    conn: sqlite3.Connection,
    task_slug: str,
    phase: str | None = None,
    gate_type: str | None = None,
) -> list[Gate]:
    query = "SELECT * FROM gates WHERE task_slug = ?"
    params: list = [task_slug]
    if phase is not None:
        query += " AND phase = ?"
        params.append(phase)
    if gate_type is not None:
        query += " AND gate_type = ?"
        params.append(gate_type)
    query += " ORDER BY id"
    return [_row_to_gate(r) for r in conn.execute(query, params).fetchall()]


def last(
    conn: sqlite3.Connection,
    task_slug: str,
    phase: str,
    gate_type: str,
) -> Gate | None:
    row = conn.execute(
        "SELECT * FROM gates WHERE task_slug = ? AND phase = ? AND gate_type = ?"
        " ORDER BY id DESC LIMIT 1",
        (task_slug, phase, gate_type),
    ).fetchone()
    return _row_to_gate(row) if row else None


def record_iteration(
    conn: sqlite3.Connection,
    task_slug: str,
    phase: str,
    iteration: int,
    action: str,
    result: str | None = None,
) -> int:
    cur = conn.execute(
        "INSERT INTO loop_iterations (task_slug, phase, iteration, action, result)"
        " VALUES (?, ?, ?, ?, ?)",
        (task_slug, phase, iteration, action, result),
    )
    conn.commit()
    return cur.lastrowid


def iterations(
    conn: sqlite3.Connection,
    task_slug: str,
    phase: str | None = None,
) -> list[dict]:
    query = "SELECT * FROM loop_iterations WHERE task_slug = ?"
    params: list = [task_slug]
    if phase is not None:
        query += " AND phase = ?"
        params.append(phase)
    query += " ORDER BY id"
    rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]
