"""RED — tests for prescriptive memory format (memory-format spec)."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from src.cli.cmd_memory import cmd_memory, _suggest_prefix
from src.db.connection import get_connection
from src.db.memory import insert, get
from src.db.schema import migrate


@pytest.fixture
def db(tmp_path):
    c = get_connection(tmp_path / "test.db")
    migrate(c)
    yield c
    c.close()


@pytest.fixture
def project(tmp_path):
    """Minimal git project with specify initialized."""
    import subprocess

    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "t@t.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "T"],
        check=True,
        capture_output=True,
    )
    specify_dir = tmp_path / ".specify"
    specify_dir.mkdir()
    db_path = specify_dir / "specify.db"
    conn = get_connection(db_path)
    migrate(conn)
    conn.close()
    return tmp_path


@pytest.fixture
def runner(project, monkeypatch):
    """CLI runner with an initialized project."""
    monkeypatch.chdir(project)
    with patch("src.cli.cmd_memory.get_provider") as mock_provider:
        mock_provider.return_value.available.return_value = False
        yield CliRunner()


# ─── _suggest_prefix unit tests ────────────────────────────────────────────


class TestSuggestPrefix:
    def test_constraint_without_prefix_suggests_always(self):
        suggestion = _suggest_prefix("constraint", "run go build ./... before gating")
        assert suggestion is not None
        assert any(p in suggestion for p in ("ALWAYS:", "NEVER:", "CHECK:"))

    def test_pattern_without_prefix_suggests_when_do(self):
        suggestion = _suggest_prefix("pattern", "testar módulo legado por último")
        assert suggestion is not None
        assert "WHEN" in suggestion

    def test_decision_without_prefix_suggests_decided(self):
        suggestion = _suggest_prefix("decision", "toolchain permanece em 1.22")
        assert suggestion is not None
        assert "DECIDED:" in suggestion

    def test_already_prefixed_always_returns_none(self):
        assert _suggest_prefix("constraint", "ALWAYS: run go build ./...") is None

    def test_already_prefixed_never_returns_none(self):
        assert _suggest_prefix("constraint", "NEVER: go get -u geral") is None

    def test_already_prefixed_check_returns_none(self):
        assert _suggest_prefix("constraint", "CHECK: go mod verify") is None

    def test_already_prefixed_when_returns_none(self):
        assert _suggest_prefix("pattern", "WHEN módulo legado DO testar último") is None

    def test_already_prefixed_decided_returns_none(self):
        assert _suggest_prefix("decision", "DECIDED: usar JWT para auth") is None

    def test_already_prefixed_avoid_returns_none(self):
        assert _suggest_prefix("constraint", "AVOID: go get -u") is None

    def test_partial_prefix_without_colon_not_recognized(self):
        # "ALWAYS" without colon is not a valid prefix
        suggestion = _suggest_prefix("constraint", "ALWAYS run build before gate")
        assert suggestion is not None

    def test_prefix_case_insensitive_recognition(self):
        # lowercase prefix should still be recognized
        suggestion = _suggest_prefix("constraint", "always: run build")
        assert suggestion is None


# ─── cmd_set suggestion output tests ───────────────────────────────────────


class TestCmdSetSuggestion:
    def test_set_constraint_without_prefix_prints_suggestion(self, runner):
        result = runner.invoke(
            cmd_memory,
            ["set", "--type", "constraint", "--content", "go build deve passar"],
        )
        assert result.exit_code == 0
        assert "memória" in result.output
        assert any(
            p in result.output
            for p in ("ALWAYS:", "NEVER:", "CHECK:", "sugestão", "Sugestão")
        )

    def test_set_pattern_without_prefix_prints_suggestion(self, runner):
        result = runner.invoke(
            cmd_memory,
            ["set", "--type", "pattern", "--content", "testar legado por último"],
        )
        assert result.exit_code == 0
        assert "WHEN" in result.output or "sugestão" in result.output.lower()

    def test_set_decision_without_prefix_prints_suggestion(self, runner):
        result = runner.invoke(
            cmd_memory,
            ["set", "--type", "decision", "--content", "manter toolchain 1.22"],
        )
        assert result.exit_code == 0
        assert "DECIDED:" in result.output or "sugestão" in result.output.lower()

    def test_set_with_prefix_no_suggestion(self, runner):
        result = runner.invoke(
            cmd_memory,
            ["set", "--type", "constraint", "--content", "ALWAYS: run go build ./..."],
        )
        assert result.exit_code == 0
        # no suggestion line when already prefixed
        assert "sugestão" not in result.output.lower()
        assert "suggestion" not in result.output.lower()

    def test_set_is_non_blocking_regardless_of_format(self, runner):
        result = runner.invoke(
            cmd_memory,
            ["set", "--type", "constraint", "--content", "sem prefixo algum aqui"],
        )
        assert result.exit_code == 0
        assert "memória" in result.output and "salva" in result.output


# ─── cmd_reformat tests ────────────────────────────────────────────────────


class TestCmdReformat:
    def test_reformat_dry_run_does_not_alter_db(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        mid = insert(conn, type="constraint", content="go build deve passar")
        original = get(conn, mid).content
        conn.close()

        result = runner.invoke(cmd_memory, ["reformat", "--id", str(mid), "--dry-run"])

        assert result.exit_code == 0
        conn2 = get_connection(db_path)
        assert get(conn2, mid).content == original
        conn2.close()

    def test_reformat_single_id_updates_content(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        mid = insert(conn, type="constraint", content="go build deve passar")
        conn.close()

        result = runner.invoke(cmd_memory, ["reformat", "--id", str(mid)])

        assert result.exit_code == 0
        conn2 = get_connection(db_path)
        updated = get(conn2, mid).content
        conn2.close()
        assert any(updated.startswith(p) for p in ("ALWAYS:", "NEVER:", "CHECK:"))

    def test_reformat_all_skips_already_prefixed(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        mid_prefixed = insert(conn, type="constraint", content="ALWAYS: run build")
        mid_unprefixed = insert(
            conn, type="constraint", content="go mod verify deve passar"
        )
        conn.close()

        result = runner.invoke(cmd_memory, ["reformat"])

        assert result.exit_code == 0
        conn2 = get_connection(db_path)
        assert get(conn2, mid_prefixed).content == "ALWAYS: run build"
        updated = get(conn2, mid_unprefixed).content
        conn2.close()
        assert any(updated.startswith(p) for p in ("ALWAYS:", "NEVER:", "CHECK:"))

    def test_reformat_bulk_confirms_when_more_than_5(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        for i in range(6):
            insert(conn, type="constraint", content=f"constraint sem prefixo {i}")
        conn.close()

        result = runner.invoke(cmd_memory, ["reformat"], input="n\n")

        assert result.exit_code == 0
        assert (
            "abort" in result.output.lower()
            or "cancelado" in result.output.lower()
            or "n" in result.output.lower()
        )

    def test_reformat_dry_run_prints_proposed_changes(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        mid = insert(conn, type="decision", content="manter toolchain 1.22")
        conn.close()

        result = runner.invoke(cmd_memory, ["reformat", "--id", str(mid), "--dry-run"])

        assert result.exit_code == 0
        assert "DECIDED:" in result.output


# ─── cmd_list highlight tests ──────────────────────────────────────────────


class TestCmdListHighlight:
    def test_list_shows_prefix_distinctly(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        insert(conn, type="constraint", content="ALWAYS: run go build ./...")
        insert(conn, type="constraint", content="sem prefixo aqui")
        conn.close()

        result = runner.invoke(cmd_memory, ["list"])

        assert result.exit_code == 0
        assert "ALWAYS:" in result.output
