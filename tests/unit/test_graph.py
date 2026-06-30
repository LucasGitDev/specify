from __future__ import annotations

import math

import pytest

from src.db.connection import get_connection
from src.db.memory import insert
from src.db.schema import migrate
from src.studio.graph import (
    GraphEdge,
    GraphNode,
    build_graph,
    cosine_similarity,
)


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    migrate(c)
    yield c
    c.close()


# ── cosine_similarity ────────────────────────────────────────────────────────

def test_cosine_identical_vectors():
    v = [1.0, 0.0, 0.0]
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_orthogonal_vectors():
    a = [1.0, 0.0]
    b = [0.0, 1.0]
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_cosine_opposite_vectors():
    a = [1.0, 0.0]
    b = [-1.0, 0.0]
    assert cosine_similarity(a, b) == pytest.approx(-1.0)


def test_cosine_arbitrary():
    a = [1.0, 1.0, 0.0]
    b = [1.0, 0.0, 0.0]
    expected = 1.0 / math.sqrt(2)
    assert cosine_similarity(a, b) == pytest.approx(expected)


def test_cosine_zero_vector_returns_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == pytest.approx(0.0)


# ── build_graph ──────────────────────────────────────────────────────────────

def _make_embedding(dim: int = 4, val: float = 1.0) -> list[float]:
    v = [0.0] * dim
    v[0] = val
    return v


def test_build_graph_empty_db(conn):
    graph = build_graph(conn, embeddings={})
    assert graph["nodes"] == []
    assert graph["edges"] == []


def test_build_graph_nodes_include_all_memories(conn):
    insert(conn, type="decision", content="usar JWT")
    insert(conn, type="pattern", content="handlers no api/")
    insert(conn, type="constraint", content="sem deps externas")

    graph = build_graph(conn, embeddings={})

    assert len(graph["nodes"]) == 3
    types = {n["type"] for n in graph["nodes"]}
    assert types == {"decision", "pattern", "constraint"}


def test_build_graph_node_fields(conn):
    mid = insert(conn, type="decision", content="usar JWT", scope="global", source="spec.md")
    graph = build_graph(conn, embeddings={})
    node = graph["nodes"][0]

    assert node["id"] == str(mid)
    assert node["label"] == "usar JWT"
    assert node["type"] == "decision"
    assert node["scope"] == "global"
    assert node["source"] == "spec.md"


def test_build_graph_no_edges_without_embeddings(conn):
    insert(conn, type="decision", content="A")
    insert(conn, type="pattern", content="B")
    graph = build_graph(conn, embeddings={})
    assert graph["edges"] == []


def test_build_graph_edge_above_threshold(conn):
    mid1 = insert(conn, type="decision", content="A")
    mid2 = insert(conn, type="pattern", content="B")
    # identical direction → similarity = 1.0
    embeddings = {mid1: [1.0, 0.0, 0.0], mid2: [1.0, 0.0, 0.0]}

    graph = build_graph(conn, embeddings=embeddings, threshold=0.7, top_k=3)

    assert len(graph["edges"]) == 1
    edge = graph["edges"][0]
    assert {edge["source"], edge["target"]} == {str(mid1), str(mid2)}
    assert edge["weight"] == pytest.approx(1.0)


def test_build_graph_edge_below_threshold_excluded(conn):
    mid1 = insert(conn, type="decision", content="A")
    mid2 = insert(conn, type="pattern", content="B")
    embeddings = {mid1: [1.0, 0.0], mid2: [0.0, 1.0]}  # similarity = 0.0

    graph = build_graph(conn, embeddings=embeddings, threshold=0.7, top_k=3)

    assert graph["edges"] == []


def test_build_graph_top_k_limits_edges_per_node(conn):
    anchor = insert(conn, type="decision", content="anchor")
    others = [insert(conn, type="pattern", content=f"p{i}") for i in range(5)]

    embeddings = {anchor: [1.0, 0.0, 0.0]}
    for mid in others:
        embeddings[mid] = [1.0, 0.0, 0.0]

    graph = build_graph(conn, embeddings=embeddings, threshold=0.5, top_k=2)

    # anchor should have at most top_k=2 edges
    anchor_edges = [e for e in graph["edges"] if e["source"] == str(anchor) or e["target"] == str(anchor)]
    assert len(anchor_edges) <= 2


def test_build_graph_edges_are_deduplicated(conn):
    mid1 = insert(conn, type="decision", content="A")
    mid2 = insert(conn, type="pattern", content="B")
    embeddings = {mid1: [1.0, 0.0], mid2: [1.0, 0.0]}

    graph = build_graph(conn, embeddings=embeddings, threshold=0.5, top_k=3)

    # A→B and B→A should collapse to one undirected edge
    assert len(graph["edges"]) == 1


def test_build_graph_node_type_preserved(conn):
    insert(conn, type="constraint", content="no external deps")
    graph = build_graph(conn, embeddings={})
    assert graph["nodes"][0]["type"] == "constraint"


def test_graphnode_is_dataclass():
    n = GraphNode(id="1", label="x", type="decision", scope="global", source=None)
    assert n.id == "1"


def test_graphedge_is_dataclass():
    e = GraphEdge(source="1", target="2", weight=0.9)
    assert e.weight == 0.9


# ── TaskNode ─────────────────────────────────────────────────────────────────

def test_tasknode_is_dataclass():
    from src.studio.graph import TaskNode
    t = TaskNode(id="t:feat-auth", label="feat-auth", type="task", status="in_progress")
    assert t.id == "t:feat-auth"
    assert t.type == "task"


# ── build_graph with tasks ────────────────────────────────────────────────────

def test_build_graph_includes_task_nodes(conn):
    from src.db.tasks import create as create_task
    create_task(conn, slug="feat-auth", title="Auth feature")

    graph = build_graph(conn, embeddings={})

    task_nodes = [n for n in graph["nodes"] if n["type"] == "task"]
    assert len(task_nodes) == 1
    assert task_nodes[0]["id"] == "t:feat-auth"
    assert task_nodes[0]["label"] == "Auth feature"


def test_build_graph_task_without_memories_is_isolated(conn):
    from src.db.tasks import create as create_task
    create_task(conn, slug="orphan-task", title="Orphan")

    graph = build_graph(conn, embeddings={})

    task_nodes = [n for n in graph["nodes"] if n["type"] == "task"]
    assert len(task_nodes) == 1
    scope_edges = [e for e in graph["edges"] if e.get("kind") == "scope"]
    assert scope_edges == []


def test_build_graph_scope_link_memory_to_task(conn):
    from src.db.tasks import create as create_task
    create_task(conn, slug="feat-x", title="Feature X")
    insert(conn, type="decision", content="use redis", scope="feat-x")

    graph = build_graph(conn, embeddings={})

    scope_edges = [e for e in graph["edges"] if e.get("kind") == "scope"]
    assert len(scope_edges) == 1
    assert scope_edges[0]["source"] == "t:feat-x"
    assert scope_edges[0]["target"] != "t:feat-x"


def test_build_graph_global_memory_has_no_scope_link(conn):
    from src.db.tasks import create as create_task
    create_task(conn, slug="feat-y", title="Feature Y")
    insert(conn, type="decision", content="global decision", scope="global")

    graph = build_graph(conn, embeddings={})

    scope_edges = [e for e in graph["edges"] if e.get("kind") == "scope"]
    assert scope_edges == []


def test_build_graph_multiple_memories_same_task(conn):
    from src.db.tasks import create as create_task
    create_task(conn, slug="feat-z", title="Feature Z")
    insert(conn, type="decision", content="decision A", scope="feat-z")
    insert(conn, type="pattern", content="pattern B", scope="feat-z")

    graph = build_graph(conn, embeddings={})

    scope_edges = [e for e in graph["edges"] if e.get("kind") == "scope"]
    assert len(scope_edges) == 2
    for e in scope_edges:
        assert e["source"] == "t:feat-z"


def test_build_graph_semantic_edges_have_kind_semantic(conn):
    mid1 = insert(conn, type="decision", content="A")
    mid2 = insert(conn, type="pattern", content="B")
    embeddings = {mid1: [1.0, 0.0], mid2: [1.0, 0.0]}

    graph = build_graph(conn, embeddings=embeddings, threshold=0.5)

    semantic_edges = [e for e in graph["edges"] if e.get("kind") == "semantic"]
    assert len(semantic_edges) == 1
    assert semantic_edges[0]["weight"] == pytest.approx(1.0)


def test_build_graph_task_node_fields(conn):
    from src.db.tasks import create as create_task
    create_task(conn, slug="my-task", title="My Task", spec_path="spec.md")

    graph = build_graph(conn, embeddings={})

    task_nodes = [n for n in graph["nodes"] if n["type"] == "task"]
    assert len(task_nodes) == 1
    node = task_nodes[0]
    assert node["id"] == "t:my-task"
    assert node["label"] == "My Task"
    assert node["status"] == "planned"
