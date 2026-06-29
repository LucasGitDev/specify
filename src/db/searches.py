from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class SearchEvent:
    id: int
    query: str
    results_count: int
    source: str | None
    searched_at: str


def log_search(
    conn: sqlite3.Connection,
    query: str,
    results_count: int,
    source: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO memory_searches (query, results_count, source) VALUES (?, ?, ?)",
        (query, results_count, source),
    )
    conn.commit()


def stats(conn: sqlite3.Connection) -> dict:
    total = conn.execute("SELECT COUNT(*) FROM memory_searches").fetchone()[0]
    by_source = conn.execute(
        "SELECT source, COUNT(*) FROM memory_searches GROUP BY source ORDER BY COUNT(*) DESC"
    ).fetchall()
    zero_results = conn.execute(
        "SELECT COUNT(*) FROM memory_searches WHERE results_count = 0"
    ).fetchone()[0]
    top_queries = conn.execute(
        "SELECT query, COUNT(*) as n FROM memory_searches GROUP BY query ORDER BY n DESC LIMIT 10"
    ).fetchall()
    recent = conn.execute(
        "SELECT query, results_count, source, searched_at FROM memory_searches ORDER BY id DESC LIMIT 20"
    ).fetchall()
    return {
        "total_searches": total,
        "zero_result_searches": zero_results,
        "by_source": [{"source": r[0], "count": r[1]} for r in by_source],
        "top_queries": [{"query": r[0], "count": r[1]} for r in top_queries],
        "recent": [
            {
                "query": r[0],
                "results_count": r[1],
                "source": r[2],
                "searched_at": r[3],
            }
            for r in recent
        ],
    }
