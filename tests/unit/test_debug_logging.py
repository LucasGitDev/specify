"""Tests for expanded debug logging across CLI commands."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

import src.core.logger as _logger_mod
from src.cli.main import cli


def _setup_project(tmp_path: Path) -> Path:
    """Create a minimal .specify/ project in tmp_path."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    specify = tmp_path / ".specify"
    specify.mkdir()
    (specify / "INDEX.md").write_text("# Index\n")
    return tmp_path


def _fresh_logger():
    """Reset singleton so next get_logger() picks up current env vars."""
    _logger_mod.reset()
    return _logger_mod


# ── Critério 1 — artifact save loga path + primeiros 200 chars do content ──


def test_artifact_save_logs_path_and_content_preview(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    root = _setup_project(tmp_path)
    monkeypatch.chdir(root)

    from src.db.connection import get_connection
    from src.db.schema import migrate

    conn = get_connection(root / ".specify" / "specify.db")
    migrate(conn)
    conn.close()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "artifact",
            "save",
            "--task",
            "t1",
            "--type",
            "spec",
            "--content",
            "hello world spec content",
        ],
    )
    assert result.exit_code == 0

    content = log_file.read_text()
    assert "artifact save" in content
    assert "hello world spec content" in content


def test_artifact_save_truncates_content_at_200_chars(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    root = _setup_project(tmp_path)
    monkeypatch.chdir(root)

    from src.db.connection import get_connection
    from src.db.schema import migrate

    conn = get_connection(root / ".specify" / "specify.db")
    migrate(conn)
    conn.close()

    long_content = "x" * 500
    runner = CliRunner()
    runner.invoke(
        cli,
        [
            "artifact",
            "save",
            "--task",
            "t1",
            "--type",
            "spec",
            "--content",
            long_content,
        ],
    )

    log_content = log_file.read_text()
    assert "x" * 200 in log_content
    assert "x" * 201 not in log_content


# ── Critério 3 — gate record loga task/phase/type/status ──


def test_gate_record_logs_details(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    root = _setup_project(tmp_path)
    monkeypatch.chdir(root)

    from src.db.connection import get_connection
    from src.db.schema import migrate

    conn = get_connection(root / ".specify" / "specify.db")
    migrate(conn)
    conn.close()

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "gate",
            "record",
            "--task",
            "mytask",
            "--phase",
            "green",
            "--type",
            "tests",
            "--status",
            "pass",
        ],
    )
    assert result.exit_code == 0

    log_content = log_file.read_text()
    assert "mytask" in log_content
    assert "green" in log_content
    assert "pass" in log_content


# ── Critério 4 — task create/update/close loga slug + mudança de status ──


def test_task_create_logs_slug(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    root = _setup_project(tmp_path)
    monkeypatch.chdir(root)

    from src.db.connection import get_connection
    from src.db.schema import migrate

    conn = get_connection(root / ".specify" / "specify.db")
    migrate(conn)
    conn.close()

    runner = CliRunner()
    result = runner.invoke(
        cli, ["task", "create", "--slug", "my-slug", "--title", "My Task"]
    )
    assert result.exit_code == 0

    log_content = log_file.read_text()
    assert "my-slug" in log_content


def test_task_update_logs_status_change(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    root = _setup_project(tmp_path)
    monkeypatch.chdir(root)

    from src.db.connection import get_connection
    from src.db.schema import migrate
    from src.db import tasks as task_db

    conn = get_connection(root / ".specify" / "specify.db")
    migrate(conn)
    task_db.create(conn, slug="my-slug", title="My Task")
    conn.close()

    runner = CliRunner()
    result = runner.invoke(
        cli, ["task", "update", "my-slug", "--status", "in_progress"]
    )
    assert result.exit_code == 0

    log_content = log_file.read_text()
    assert "my-slug" in log_content
    assert "in_progress" in log_content


def test_task_close_logs_slug(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    root = _setup_project(tmp_path)
    monkeypatch.chdir(root)

    from src.db.connection import get_connection
    from src.db.schema import migrate
    from src.db import tasks as task_db

    conn = get_connection(root / ".specify" / "specify.db")
    migrate(conn)
    task_db.create(conn, slug="close-slug", title="Task To Close")
    conn.close()

    runner = CliRunner()
    result = runner.invoke(cli, ["task", "close", "close-slug"])
    assert result.exit_code == 0

    log_content = log_file.read_text()
    assert "close-slug" in log_content


# ── Critério 5 — memory search loga query + N resultados ──


def test_memory_search_logs_query_and_count(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    root = _setup_project(tmp_path)
    monkeypatch.chdir(root)

    from src.db.connection import get_connection
    from src.db.schema import migrate

    conn = get_connection(root / ".specify" / "specify.db")
    migrate(conn)
    conn.close()

    runner = CliRunner()
    runner.invoke(cli, ["memory", "search", "some query term"])

    log_content = log_file.read_text()
    assert "some query term" in log_content
    assert "result" in log_content


# ── Critério 2 — gate run loga comando, duração, status, output ──


def test_gate_run_logs_details(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    root = _setup_project(tmp_path)
    monkeypatch.chdir(root)

    from src.db.connection import get_connection
    from src.db.schema import migrate
    from src.core.gate_validator import GateResult

    conn = get_connection(root / ".specify" / "specify.db")
    migrate(conn)
    conn.close()

    fake_result = GateResult(
        gate_type="tests",
        passed=True,
        output="5 passed",
        duration_ms=42,
        command="pytest tests/",
    )

    import src.cli.cmd_gate as cmd_gate_mod

    monkeypatch.setattr(cmd_gate_mod, "run_tests", lambda lang, cwd, **kw: fake_result)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["gate", "run", "--task", "my-task", "--phase", "tests"],
        catch_exceptions=False,
    )
    assert result.exit_code == 0

    log_content = log_file.read_text()
    assert "gate run" in log_content
    assert "my-task" in log_content
    assert "pass" in log_content
    assert "42" in log_content
    assert "pytest" in log_content


# ── Critérios 8+9 — specify log tail / clear ──


def test_log_tail_prints_last_n_lines(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    lines = [f"line {i}" for i in range(100)]
    log_file.write_text("\n".join(lines) + "\n")

    runner = CliRunner()
    result = runner.invoke(cli, ["log", "tail", "--lines", "10"])
    assert result.exit_code == 0
    output_lines = [line for line in result.output.splitlines() if line.strip()]
    assert len(output_lines) == 10
    assert "line 99" in result.output


def test_log_tail_default_50_lines(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    lines = [f"line {i}" for i in range(100)]
    log_file.write_text("\n".join(lines) + "\n")

    runner = CliRunner()
    result = runner.invoke(cli, ["log", "tail"])
    assert result.exit_code == 0
    output_lines = [line for line in result.output.splitlines() if line.strip()]
    assert len(output_lines) == 50


def test_log_tail_missing_file_shows_empty(monkeypatch, tmp_path):
    log_file = tmp_path / "nonexistent.log"
    monkeypatch.delenv("SPECIFY_DEBUG", raising=False)
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    runner = CliRunner()
    result = runner.invoke(cli, ["log", "tail"])
    assert result.exit_code == 0
    assert "vazio" in result.output


def test_log_clear_deletes_file(monkeypatch, tmp_path):
    log_file = tmp_path / "specify.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    log_file.write_text("some log content\n")
    assert log_file.exists()

    runner = CliRunner()
    result = runner.invoke(cli, ["log", "clear"])
    assert result.exit_code == 0
    assert not log_file.exists()


def test_log_clear_missing_file_is_noop(monkeypatch, tmp_path):
    log_file = tmp_path / "nonexistent.log"
    monkeypatch.setenv("SPECIFY_DEBUG", "1")
    monkeypatch.setenv("SPECIFY_LOG_PATH", str(log_file))
    _fresh_logger()

    runner = CliRunner()
    result = runner.invoke(cli, ["log", "clear"])
    assert result.exit_code == 0
