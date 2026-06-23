import pytest

from src.db.connection import get_connection
from src.db.memory import Memory, delete, get, insert, list_all, search_substring, update
from src.db.schema import migrate


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    migrate(c)
    yield c
    c.close()


def test_insert_returns_int(conn):
    mid = insert(conn, type="decision", content="usar JWT")
    assert isinstance(mid, int)
    assert mid > 0


def test_get_returns_memory(conn):
    mid = insert(conn, type="decision", content="usar JWT", scope="global", source="spec.md")
    m = get(conn, mid)
    assert isinstance(m, Memory)
    assert m.id == mid
    assert m.type == "decision"
    assert m.content == "usar JWT"
    assert m.scope == "global"
    assert m.source == "spec.md"


def test_get_returns_none_for_missing(conn):
    assert get(conn, 9999) is None


def test_list_all_returns_all(conn):
    insert(conn, type="decision", content="A")
    insert(conn, type="pattern", content="B")
    insert(conn, type="constraint", content="C")
    result = list_all(conn)
    assert len(result) == 3


def test_list_all_filter_scope(conn):
    insert(conn, type="decision", content="A", scope="global")
    insert(conn, type="decision", content="B", scope="task-1")
    result = list_all(conn, scope="global")
    assert len(result) == 1
    assert result[0].scope == "global"


def test_list_all_filter_type(conn):
    insert(conn, type="decision", content="A")
    insert(conn, type="pattern", content="B")
    result = list_all(conn, type="decision")
    assert len(result) == 1
    assert result[0].type == "decision"


def test_update_changes_content(conn):
    mid = insert(conn, type="decision", content="original")
    update(conn, mid, "atualizado")
    m = get(conn, mid)
    assert m.content == "atualizado"


def test_delete_removes_memory(conn):
    mid = insert(conn, type="decision", content="remover")
    delete(conn, mid)
    assert get(conn, mid) is None


def test_search_substring_case_insensitive(conn):
    insert(conn, type="decision", content="Usar JWT para autenticação")
    insert(conn, type="pattern", content="handlers no pacote api")
    result = search_substring(conn, "jwt")
    assert len(result) == 1
    assert "JWT" in result[0].content
