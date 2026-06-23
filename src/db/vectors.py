from __future__ import annotations

import json
import sqlite3


def upsert_embedding(
    conn: sqlite3.Connection, memory_id: int, embedding: list[float]
) -> None:
    # vec0 não suporta INSERT OR REPLACE — DELETE + INSERT é o padrão correto
    vec_json = json.dumps(embedding)
    conn.execute("DELETE FROM vec_memories WHERE memory_id = ?", (memory_id,))
    conn.execute(
        "INSERT INTO vec_memories(memory_id, embedding) VALUES (?, ?)",
        (memory_id, vec_json),
    )
    conn.commit()


def search(
    conn: sqlite3.Connection, embedding: list[float], limit: int = 5
) -> list[tuple[int, float]]:
    vec_json = json.dumps(embedding)
    rows = conn.execute(
        "SELECT memory_id, distance FROM vec_memories WHERE embedding MATCH ? AND k = ?",
        (vec_json, limit),
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def delete_embedding(conn: sqlite3.Connection, memory_id: int) -> None:
    conn.execute("DELETE FROM vec_memories WHERE memory_id = ?", (memory_id,))
    conn.commit()
