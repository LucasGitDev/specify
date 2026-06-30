import pytest

from src.db.connection import get_connection
from src.db.schema import migrate
from src.db.tasks import Task, create, delete, get, list_all, update_status


@pytest.fixture
def conn(tmp_path):
    c = get_connection(tmp_path / "test.db")
    migrate(c)
    yield c
    c.close()


def test_create_returns_int(conn):
    tid = create(conn, slug="feat-x", title="Feature X")
    assert isinstance(tid, int)
    assert tid > 0


def test_create_duplicate_slug_raises(conn):
    create(conn, slug="feat-x", title="Feature X")
    with pytest.raises(ValueError, match="já existe"):
        create(conn, slug="feat-x", title="Feature X dup")


def test_get_returns_task(conn):
    create(
        conn,
        slug="feat-x",
        title="Feature X",
        spec_path=".specify/tasks/feat-x/spec.md",
    )
    t = get(conn, "feat-x")
    assert isinstance(t, Task)
    assert t.slug == "feat-x"
    assert t.title == "Feature X"
    assert t.status == "planned"
    assert t.spec_path == ".specify/tasks/feat-x/spec.md"


def test_get_returns_none_for_missing(conn):
    assert get(conn, "nao-existe") is None


def test_list_all_returns_all(conn):
    create(conn, slug="a", title="A")
    create(conn, slug="b", title="B")
    create(conn, slug="c", title="C")
    assert len(list_all(conn)) == 3


def test_list_all_filter_status(conn):
    create(conn, slug="a", title="A")
    create(conn, slug="b", title="B")
    update_status(conn, "b", "in_progress")
    result = list_all(conn, status="planned")
    assert len(result) == 1
    assert result[0].slug == "a"


def test_update_status_changes_value(conn):
    create(conn, slug="feat-x", title="X")
    update_status(conn, "feat-x", "in_progress")
    assert get(conn, "feat-x").status == "in_progress"


def test_update_status_invalid_raises(conn):
    create(conn, slug="feat-x", title="X")
    with pytest.raises(ValueError, match="inválido"):
        update_status(conn, "feat-x", "nao-existe")


def test_delete_removes_task(conn):
    create(conn, slug="feat-x", title="X")
    delete(conn, "feat-x")
    assert get(conn, "feat-x") is None
