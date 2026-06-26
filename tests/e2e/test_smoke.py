"""Smoke tests end-to-end: testa o fluxo CLI completo num projeto Go temporário."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

SPECIFY = str(Path(__file__).resolve().parent.parent.parent / ".venv" / "bin" / "specify")


@pytest.fixture
def go_project(tmp_path):
    """Projeto Go mínimo com git init."""
    (tmp_path / "go.mod").write_text("module example.com/smoke\n\ngo 1.21\n")
    subprocess.run(["git", "init", str(tmp_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@test.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "init"],
        check=True, capture_output=True,
    )
    return tmp_path


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [SPECIFY, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_init_creates_specify_dir(go_project):
    result = _run(["init"], go_project)
    assert result.returncode == 0, result.stderr
    assert (go_project / ".specify").is_dir()
    assert (go_project / ".specify" / "specify.db").exists()
    assert (go_project / ".specify" / "INDEX.md").exists()


def test_init_detects_go_language(go_project):
    result = _run(["init"], go_project)
    assert "go" in result.stdout


def test_init_adds_to_gitignore(go_project):
    _run(["init"], go_project)
    gitignore = (go_project / ".gitignore").read_text()
    assert "specify.db" in gitignore
    assert ".claude/worktrees/" in gitignore


def test_memory_set_and_list(go_project):
    _run(["init"], go_project)
    result = _run(
        ["memory", "set", "--type", "decision", "--content", "usar JWT para auth"],
        go_project,
    )
    assert result.returncode == 0, result.stderr
    assert "salva" in result.stdout

    result = _run(["memory", "list", "--type", "decision"], go_project)
    assert result.returncode == 0
    assert "JWT" in result.stdout


def test_memory_search_substring_fallback(go_project):
    _run(["init"], go_project)
    _run(["memory", "set", "--type", "pattern", "--content", "handlers em api/"], go_project)
    result = _run(["memory", "search", "handlers"], go_project)
    assert result.returncode == 0
    assert "handlers" in result.stdout


def test_task_create_and_list(go_project):
    _run(["init"], go_project)
    result = _run(
        ["task", "create", "--slug", "add-health", "--title", "Add healthcheck"],
        go_project,
    )
    assert result.returncode == 0, result.stderr
    assert "add-health" in result.stdout

    result = _run(["task", "list"], go_project)
    assert result.returncode == 0
    assert "add-health" in result.stdout


def test_task_update_status(go_project):
    _run(["init"], go_project)
    _run(["task", "create", "--slug", "add-health", "--title", "Add healthcheck"], go_project)
    result = _run(["task", "update", "add-health", "--status", "in_progress"], go_project)
    assert result.returncode == 0

    result = _run(["task", "status", "add-health"], go_project)
    assert "in_progress" in result.stdout


def test_gate_record_and_history(go_project):
    _run(["init"], go_project)
    _run(["task", "create", "--slug", "add-health", "--title", "Add healthcheck"], go_project)
    result = _run(
        ["gate", "record",
         "--task", "add-health",
         "--phase", "green",
         "--type", "tests",
         "--status", "pass"],
        go_project,
    )
    assert result.returncode == 0, result.stderr

    result = _run(["gate", "history", "--task", "add-health"], go_project)
    assert result.returncode == 0
    assert "green" in result.stdout
    assert "pass" in result.stdout


def test_task_close(go_project):
    _run(["init"], go_project)
    _run(["task", "create", "--slug", "add-health", "--title", "Add healthcheck"], go_project)
    result = _run(["task", "close", "add-health"], go_project)
    assert result.returncode == 0

    result = _run(["task", "list", "--status", "closed"], go_project)
    assert "add-health" in result.stdout


def test_task_worktree_info_without_worktree(go_project):
    _run(["init"], go_project)
    _run(["task", "create", "--slug", "add-health", "--title", "Add healthcheck"], go_project)
    result = _run(["task", "worktree-info", "add-health"], go_project)
    assert result.returncode == 0
    assert "não tem worktree" in result.stdout


def test_init_idempotent_with_force(go_project):
    _run(["init"], go_project)
    result = _run(["init", "--force"], go_project)
    assert result.returncode == 0


def test_memory_delete(go_project):
    _run(["init"], go_project)
    _run(["memory", "set", "--type", "decision", "--content", "remover isso"], go_project)
    result = _run(["memory", "list"], go_project)
    # formato: "[1] (decision/global)\n    remover isso"
    # o id fica na linha "[N] ..." e o conteúdo na linha seguinte indentada
    mid = None
    lines = result.stdout.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("[") and i + 1 < len(lines) and "remover isso" in lines[i + 1]:
            mid = line[1:line.index("]")]
            break
    assert mid is not None, f"id não encontrado em: {result.stdout!r}"
    result = _run(["memory", "delete", mid], go_project)
    assert result.returncode == 0
    result = _run(["memory", "list"], go_project)
    assert "remover isso" not in result.stdout
