import pytest

from src.db.connection import get_connection
from src.db.memory import insert as mem_insert
from src.db.schema import migrate
from src.db.vectors import delete_embedding, search, upsert_embedding

_VEC_A = [1.0, 0.0, 0.0, 0.0] + [0.0] * 380  # 384 dims
_VEC_B = [0.0, 1.0, 0.0, 0.0] + [0.0] * 380
_VEC_C = [0.9, 0.1, 0.0, 0.0] + [0.0] * 380


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    migrate(c)
    yield c
    c.close()


@pytest.fixture
def conn_with_memories(conn):
    id1 = mem_insert(conn, type="decision", content="A")
    id2 = mem_insert(conn, type="decision", content="B")
    id3 = mem_insert(conn, type="decision", content="C")
    return conn, id1, id2, id3


def test_upsert_inserts_without_error(conn):
    mid = mem_insert(conn, type="decision", content="X")
    upsert_embedding(conn, mid, _VEC_A)
    results = search(conn, _VEC_A, limit=1)
    assert len(results) == 1
    assert results[0][0] == mid


def test_upsert_replaces_existing(conn):
    mid = mem_insert(conn, type="decision", content="X")
    upsert_embedding(conn, mid, _VEC_A)
    upsert_embedding(conn, mid, _VEC_B)
    results = search(conn, _VEC_B, limit=1)
    assert results[0][0] == mid
    assert results[0][1] < 0.01  # distância próxima de 0


def test_search_returns_ordered_by_distance(conn_with_memories):
    conn, id1, id2, id3 = conn_with_memories
    upsert_embedding(conn, id1, _VEC_A)
    upsert_embedding(conn, id2, _VEC_B)
    upsert_embedding(conn, id3, _VEC_C)
    results = search(conn, _VEC_A, limit=3)
    ids = [r[0] for r in results]
    # id1 (VEC_A) e id3 (VEC_C, próximo de A) devem vir antes de id2 (VEC_B)
    assert ids.index(id1) < ids.index(id2)


def test_search_empty_table(conn):
    results = search(conn, _VEC_A, limit=5)
    assert results == []


def test_delete_embedding_removes(conn):
    mid = mem_insert(conn, type="decision", content="X")
    upsert_embedding(conn, mid, _VEC_A)
    delete_embedding(conn, mid)
    results = search(conn, _VEC_A, limit=5)
    assert all(r[0] != mid for r in results)


def test_search_after_delete_excludes_deleted(conn_with_memories):
    conn, id1, id2, id3 = conn_with_memories
    upsert_embedding(conn, id1, _VEC_A)
    upsert_embedding(conn, id2, _VEC_B)
    delete_embedding(conn, id1)
    results = search(conn, _VEC_A, limit=5)
    assert all(r[0] != id1 for r in results)
