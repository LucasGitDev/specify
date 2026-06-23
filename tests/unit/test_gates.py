import pytest

from src.db.connection import get_connection
from src.db.gates import Gate, history, iterations, last, record, record_iteration
from src.db.schema import migrate


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    migrate(c)
    yield c
    c.close()


def test_record_returns_int(conn):
    gid = record(conn, task_slug="t1", phase="green", gate_type="tests", status="pass")
    assert isinstance(gid, int)
    assert gid > 0


def test_history_returns_all_for_task(conn):
    record(conn, "t1", "red", "tests", "fail")
    record(conn, "t1", "green", "tests", "pass")
    record(conn, "t2", "green", "tests", "pass")
    result = history(conn, "t1")
    assert len(result) == 2
    assert all(g.task_slug == "t1" for g in result)


def test_history_filter_phase(conn):
    record(conn, "t1", "red", "tests", "fail")
    record(conn, "t1", "green", "tests", "pass")
    result = history(conn, "t1", phase="green")
    assert len(result) == 1
    assert result[0].phase == "green"


def test_history_empty_for_unknown_task(conn):
    assert history(conn, "nao-existe") == []


def test_last_returns_most_recent(conn):
    record(conn, "t1", "green", "tests", "fail", iteration=1)
    record(conn, "t1", "green", "tests", "pass", iteration=2)
    g = last(conn, "t1", "green", "tests")
    assert g is not None
    assert g.status == "pass"
    assert g.iteration == 2


def test_last_returns_none_if_missing(conn):
    assert last(conn, "t1", "green", "tests") is None


def test_record_iteration_and_query(conn):
    record_iteration(conn, "t1", "red", 1, "escreveu testes", "3 testes criados")
    record_iteration(conn, "t1", "red", 2, "corrigiu testes", None)
    result = iterations(conn, "t1")
    assert len(result) == 2
    assert result[0]["action"] == "escreveu testes"
    assert result[0]["result"] == "3 testes criados"


def test_iterations_filter_phase(conn):
    record_iteration(conn, "t1", "red", 1, "acao-red")
    record_iteration(conn, "t1", "green", 1, "acao-green")
    result = iterations(conn, "t1", phase="red")
    assert len(result) == 1
    assert result[0]["phase"] == "red"
