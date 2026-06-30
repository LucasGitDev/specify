"""RED — tests for contextual injection at phase transition points."""
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.cmd_gate import cmd_gate
from src.cli.cmd_task import cmd_task
from src.db.connection import get_connection
from src.db.memory import insert
from src.db.schema import migrate


@pytest.fixture
def project(tmp_path):
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
    monkeypatch.chdir(project)
    return CliRunner()


def _mock_provider(similarity: float = 0.8):
    """Return a mock embedding provider with fixed similarity."""
    provider = MagicMock()
    provider.available.return_value = True
    provider.embed.return_value = [1.0] + [0.0] * 383
    return provider


def _insert_memory_with_embedding(conn, db_path, mem_type, content, sim=0.8):
    """Insert memory and mock its embedding (unit vector scaled by sim)."""
    mid = insert(conn, type=mem_type, content=content)
    from src.db import vectors as vec_db

    # embedding identical to query mock → cosine sim = 1.0
    vec_db.upsert_embedding(conn, mid, [1.0] + [0.0] * 383)
    return mid


# ─── task create: Relevant prior knowledge ─────────────────────────────────


class TestTaskCreateInjection:
    def test_create_shows_relevant_knowledge_when_memories_exist(
        self, runner, project
    ):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _insert_memory_with_embedding(
            conn, db_path, "constraint", "ALWAYS: run go build before gating"
        )
        conn.close()

        with patch("src.cli.cmd_task.get_provider", return_value=_mock_provider()):
            result = runner.invoke(
                cmd_task,
                ["create", "--slug", "my-task", "--title", "fix go build failures"],
            )

        assert result.exit_code == 0
        assert "Relevant prior knowledge" in result.output
        assert "go build" in result.output

    def test_create_omits_section_when_no_relevant_memories(self, runner, project):
        with patch(
            "src.cli.cmd_task.get_provider", return_value=_mock_provider()
        ) as mp:
            # embed returns zero vector → no similarity
            mp.return_value.embed.return_value = [0.0] * 384
            result = runner.invoke(
                cmd_task,
                ["create", "--slug", "my-task", "--title", "completely unrelated topic"],
            )

        assert result.exit_code == 0
        assert "Relevant prior knowledge" not in result.output
        assert "nenhuma" not in result.output.lower() or "knowledge" not in result.output

    def test_create_omits_section_when_provider_unavailable(self, runner, project):
        with patch("src.cli.cmd_task.get_provider") as mp:
            mp.return_value.available.return_value = False
            result = runner.invoke(
                cmd_task,
                ["create", "--slug", "my-task", "--title", "some task"],
            )

        assert result.exit_code == 0
        assert "Relevant prior knowledge" not in result.output

    def test_create_with_no_search_flag_suppresses_search(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _insert_memory_with_embedding(conn, db_path, "constraint", "ALWAYS: run build")
        conn.close()

        with patch("src.cli.cmd_task.get_provider", return_value=_mock_provider()):
            result = runner.invoke(
                cmd_task,
                [
                    "create",
                    "--slug",
                    "my-task",
                    "--title",
                    "run build",
                    "--no-search",
                ],
            )

        assert result.exit_code == 0
        assert "Relevant prior knowledge" not in result.output

    def test_create_shows_at_most_5_memories(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        for i in range(8):
            _insert_memory_with_embedding(
                conn, db_path, "constraint", f"ALWAYS: constraint {i}"
            )
        conn.close()

        with patch("src.cli.cmd_task.get_provider", return_value=_mock_provider()):
            result = runner.invoke(
                cmd_task,
                ["create", "--slug", "my-task", "--title", "constraint related task"],
            )

        assert result.exit_code == 0
        lines = [l for l in result.output.splitlines() if "ALWAYS:" in l or "constraint" in l.lower()]
        assert len(lines) <= 5

    def test_create_output_does_not_exceed_15_lines_for_knowledge_section(
        self, runner, project
    ):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        for i in range(5):
            _insert_memory_with_embedding(
                conn, db_path, "constraint", f"ALWAYS: constraint number {i} with long content here"
            )
        conn.close()

        with patch("src.cli.cmd_task.get_provider", return_value=_mock_provider()):
            result = runner.invoke(
                cmd_task,
                ["create", "--slug", "my-task", "--title", "constraint related"],
            )

        assert result.exit_code == 0
        if "Relevant prior knowledge" in result.output:
            start = result.output.index("Relevant prior knowledge")
            section = result.output[start:]
            assert len(section.splitlines()) <= 15


# ─── specify context <slug> ────────────────────────────────────────────────


class TestContextCommand:
    def test_context_command_exists(self, runner):
        from src.cli.main import cli

        result = runner.invoke(cli, ["context", "--help"])
        assert result.exit_code == 0

    def test_context_returns_relevant_constraints(self, runner, project):
        from src.cli.main import cli

        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        # create a task
        from src.db import tasks as task_db

        task_db.create(conn, slug="my-task", title="fix go build failures")
        _insert_memory_with_embedding(
            conn, db_path, "constraint", "ALWAYS: run go build before gating"
        )
        conn.close()

        with patch("src.cli.cmd_context.get_provider", return_value=_mock_provider()):
            result = runner.invoke(cli, ["context", "my-task"])

        assert result.exit_code == 0
        assert "Known constraints" in result.output or "constraint" in result.output.lower()
        assert "go build" in result.output

    def test_context_works_without_spec_file(self, runner, project):
        from src.cli.main import cli

        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        from src.db import tasks as task_db

        task_db.create(conn, slug="no-spec-task", title="task without spec")
        _insert_memory_with_embedding(
            conn, db_path, "decision", "DECIDED: use JWT for auth"
        )
        conn.close()

        with patch("src.cli.cmd_context.get_provider", return_value=_mock_provider()):
            result = runner.invoke(cli, ["context", "no-spec-task"])

        assert result.exit_code == 0

    def test_context_task_not_found_returns_error(self, runner, project):
        from src.cli.main import cli

        with patch("src.cli.cmd_context.get_provider", return_value=_mock_provider()):
            result = runner.invoke(cli, ["context", "nonexistent-slug"])

        assert result.exit_code != 0


# ─── gate run: pre-gate checklist ──────────────────────────────────────────


class TestGateRunChecklist:
    def _make_gate_run_mock(self):
        """Mock run_tests to avoid needing a real project."""
        from src.core.gate_validator import GateResult

        mock_result = GateResult(
            passed=True,
            gate_type="tests",
            command="pytest",
            output="1 passed",
            duration_ms=100,
        )
        return mock_result

    def test_gate_run_tests_prints_checklist_before_result(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        from src.db import tasks as task_db

        task_db.create(conn, slug="my-task", title="fix build")
        _insert_memory_with_embedding(
            conn, db_path, "constraint", "ALWAYS: run go build before gating"
        )
        conn.close()

        with (
            patch("src.cli.cmd_gate.get_provider", return_value=_mock_provider()),
            patch(
                "src.cli.cmd_gate.run_tests", return_value=self._make_gate_run_mock()
            ),
            patch("src.cli.cmd_gate.detect") as mock_detect,
        ):
            mock_detect.return_value = MagicMock(language="python")
            result = runner.invoke(
                cmd_gate,
                ["run", "--task", "my-task", "--phase", "tests"],
            )

        assert result.exit_code == 0
        # checklist appears before gate result
        output = result.output
        assert "go build" in output
        checklist_pos = output.find("go build")
        result_pos = output.find("tests:")
        assert checklist_pos < result_pos

    def test_gate_run_tests_checklist_does_not_block(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        from src.db import tasks as task_db

        task_db.create(conn, slug="my-task", title="fix build")
        _insert_memory_with_embedding(
            conn, db_path, "constraint", "ALWAYS: run go build"
        )
        conn.close()

        with (
            patch("src.cli.cmd_gate.get_provider", return_value=_mock_provider()),
            patch(
                "src.cli.cmd_gate.run_tests", return_value=self._make_gate_run_mock()
            ),
            patch("src.cli.cmd_gate.detect") as mock_detect,
        ):
            mock_detect.return_value = MagicMock(language="python")
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--phase", "tests"]
            )

        assert result.exit_code == 0
        assert "pass" in result.output

    def test_gate_run_lint_does_not_show_checklist(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        from src.db import tasks as task_db

        task_db.create(conn, slug="my-task", title="fix build")
        _insert_memory_with_embedding(
            conn, db_path, "constraint", "ALWAYS: run go build"
        )
        conn.close()

        from src.core.gate_validator import GateResult

        lint_result = GateResult(
            passed=True,
            gate_type="lint",
            command="ruff check",
            output="",
            duration_ms=50,
        )

        with (
            patch("src.cli.cmd_gate.get_provider", return_value=_mock_provider()),
            patch("src.cli.cmd_gate.run_lint", return_value=lint_result),
            patch("src.cli.cmd_gate.detect") as mock_detect,
        ):
            mock_detect.return_value = MagicMock(language="python")
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--phase", "lint"]
            )

        assert result.exit_code == 0
        assert "Constraint checklist" not in result.output
        assert "go build" not in result.output

    def test_gate_run_omits_checklist_when_no_relevant_constraints(
        self, runner, project
    ):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        from src.db import tasks as task_db

        task_db.create(conn, slug="my-task", title="fix build")
        conn.close()

        with (
            patch("src.cli.cmd_gate.get_provider") as mp,
            patch(
                "src.cli.cmd_gate.run_tests", return_value=self._make_gate_run_mock()
            ),
            patch("src.cli.cmd_gate.detect") as mock_detect,
        ):
            mp.return_value.available.return_value = False
            mock_detect.return_value = MagicMock(language="python")
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--phase", "tests"]
            )

        assert result.exit_code == 0
        assert "Constraint checklist" not in result.output
