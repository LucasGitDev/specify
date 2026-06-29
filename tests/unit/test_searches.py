import pytest

from src.db.connection import get_connection
from src.db.schema import migrate
from src.db.searches import log_search, stats


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    migrate(c)
    yield c
    c.close()


def test_log_search_persists(conn):
    log_search(conn, query="auth pattern", results_count=3, source="specify.new")
    data = stats(conn)
    assert data["total_searches"] == 1
    assert data["recent"][0]["query"] == "auth pattern"
    assert data["recent"][0]["results_count"] == 3
    assert data["recent"][0]["source"] == "specify.new"


def test_log_search_without_source(conn):
    log_search(conn, query="cache", results_count=0)
    data = stats(conn)
    assert data["total_searches"] == 1
    assert data["recent"][0]["source"] is None


def test_zero_result_searches_count(conn):
    log_search(conn, query="x", results_count=0)
    log_search(conn, query="y", results_count=2)
    log_search(conn, query="z", results_count=0)
    data = stats(conn)
    assert data["zero_result_searches"] == 2


def test_by_source_groups(conn):
    log_search(conn, query="a", results_count=1, source="specify.plan")
    log_search(conn, query="b", results_count=1, source="specify.plan")
    log_search(conn, query="c", results_count=1, source="specify.new")
    data = stats(conn)
    sources = {r["source"]: r["count"] for r in data["by_source"]}
    assert sources["specify.plan"] == 2
    assert sources["specify.new"] == 1


def test_top_queries_deduplicates(conn):
    for _ in range(3):
        log_search(conn, query="redis", results_count=1)
    log_search(conn, query="other", results_count=1)
    data = stats(conn)
    top = {r["query"]: r["count"] for r in data["top_queries"]}
    assert top["redis"] == 3
    assert top["other"] == 1


def test_stats_empty_db(conn):
    data = stats(conn)
    assert data["total_searches"] == 0
    assert data["zero_result_searches"] == 0
    assert data["by_source"] == []
    assert data["top_queries"] == []
    assert data["recent"] == []


def test_recent_capped_at_20(conn):
    for i in range(25):
        log_search(conn, query=f"q{i}", results_count=1)
    data = stats(conn)
    assert len(data["recent"]) == 20
