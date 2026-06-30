from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass

from src.db.memory import list_all
from src.db.tasks import list_all as list_all_tasks


@dataclass
class GraphNode:
    id: str
    label: str
    type: str
    scope: str
    source: str | None


@dataclass
class TaskNode:
    id: str
    label: str
    type: str
    status: str


@dataclass
class GraphEdge:
    source: str
    target: str
    weight: float


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def build_graph(
    conn: sqlite3.Connection,
    embeddings: dict[int, list[float]],
    threshold: float = 0.7,
    top_k: int = 3,
) -> dict:
    memories = list_all(conn)
    tasks = list_all_tasks(conn)

    memory_nodes = [
        {
            "id": str(m.id),
            "label": m.content,
            "type": m.type,
            "scope": m.scope,
            "source": m.source,
        }
        for m in memories
    ]

    task_nodes = [
        {
            "id": f"t:{t.slug}",
            "label": t.title,
            "type": "task",
            "status": t.status,
        }
        for t in tasks
    ]

    edges: list[dict] = []

    # scope-link: task → memory when memory.scope matches task.slug
    task_slugs = {t.slug for t in tasks}
    for m in memories:
        if m.scope and m.scope != "global" and m.scope in task_slugs:
            edges.append(
                {
                    "source": f"t:{m.scope}",
                    "target": str(m.id),
                    "kind": "scope",
                }
            )

    # semantic edges
    seen: set[tuple[str, str]] = set()
    ids = [m.id for m in memories if m.id in embeddings]

    for mid_a in ids:
        neighbors: list[tuple[float, int]] = []
        for mid_b in ids:
            if mid_a == mid_b:
                continue
            sim = cosine_similarity(embeddings[mid_a], embeddings[mid_b])
            if sim >= threshold:
                neighbors.append((sim, mid_b))

        neighbors.sort(reverse=True)
        for sim, mid_b in neighbors[:top_k]:
            key = (min(str(mid_a), str(mid_b)), max(str(mid_a), str(mid_b)))
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                {
                    "source": str(mid_a),
                    "target": str(mid_b),
                    "weight": sim,
                    "kind": "semantic",
                }
            )

    return {
        "nodes": memory_nodes + task_nodes,
        "edges": edges,
    }
