from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.db.connection import get_connection
from src.db.schema import migrate
from src.db import tasks as tasks_db
from src.db.memory import insert as insert_memory


@pytest.fixture
def db_conn(tmp_path):
    c = get_connection(tmp_path / "test.db", check_same_thread=False)
    migrate(c)
    yield c
    c.close()


@pytest.fixture
def client(db_conn, monkeypatch):
    from src.studio import app as studio_app

    monkeypatch.setattr(studio_app, "_get_conn", lambda: db_conn)
    # prevent StaticFiles from mounting (no static dir in test env)
    monkeypatch.setattr(studio_app.app, "router", studio_app.app.router)

    from src.studio.app import app

    return TestClient(app, raise_server_exceptions=True)


# ── GET /api/tasks/{slug} ─────────────────────────────────────────────────────


def test_get_task_not_found(client):
    res = client.get("/api/tasks/missing")
    assert res.status_code == 404


def test_get_task_returns_fields(db_conn, client):
    tasks_db.create(db_conn, slug="feat-x", title="Feature X", spec_path="spec.md")
    res = client.get("/api/tasks/feat-x")
    assert res.status_code == 200
    data = res.json()
    assert data["slug"] == "feat-x"
    assert data["title"] == "Feature X"
    assert data["id"] == "t:feat-x"
    assert data["status"] == "planned"
    assert data["spec_path"] == "spec.md"
    assert isinstance(data["gates"], list)
    assert data["result_path"] is None


def test_get_task_gates_use_correct_columns(db_conn, client):
    tasks_db.create(db_conn, slug="feat-y", title="Feature Y")
    db_conn.execute(
        "INSERT INTO gates (task_slug, phase, gate_type, status, output)"
        " VALUES (?, ?, ?, ?, ?)",
        ("feat-y", "green", "tests", "pass", "24 passed"),
    )
    db_conn.commit()
    res = client.get("/api/tasks/feat-y")
    assert res.status_code == 200
    gates = res.json()["gates"]
    assert len(gates) == 1
    assert gates[0]["phase"] == "green"
    assert gates[0]["result"] == "pass"
    assert "recorded_at" in gates[0]


# ── GET /api/graph includes tasks ─────────────────────────────────────────────


def test_graph_includes_task_nodes(db_conn, client):
    tasks_db.create(db_conn, slug="my-task", title="My Task")
    res = client.get("/api/graph")
    assert res.status_code == 200
    data = res.json()
    task_nodes = [n for n in data["nodes"] if n["type"] == "task"]
    assert len(task_nodes) == 1
    assert task_nodes[0]["id"] == "t:my-task"


def test_graph_scope_links_in_edges(db_conn, client):
    tasks_db.create(db_conn, slug="task-a", title="Task A")
    insert_memory(db_conn, type="decision", content="some decision", scope="task-a")
    res = client.get("/api/graph")
    assert res.status_code == 200
    scope_edges = [e for e in res.json()["edges"] if e.get("kind") == "scope"]
    assert len(scope_edges) == 1
    assert scope_edges[0]["source"] == "t:task-a"
