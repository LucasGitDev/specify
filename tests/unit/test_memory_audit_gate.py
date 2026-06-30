"""RED — tests for memory-audit gate phase."""
from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from src.cli.cmd_gate import cmd_gate
from src.cli.cmd_memory import cmd_memory
from src.db import memory as mem_db
from src.db import vectors as vec_db
from src.db.connection import get_connection
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


def _make_task(conn, slug="my-task", title="fix build failures"):
    from src.db import tasks as task_db
    task_db.create(conn, slug=slug, title=title)


def _insert_constraint(conn, content, similar=True):
    mid = mem_db.insert(conn, type="constraint", content=content)
    if similar:
        # identical embedding to mock query → distance 0.0
        vec_db.upsert_embedding(conn, mid, [1.0] + [0.0] * 383)
    else:
        # orthogonal → high distance
        vec_db.upsert_embedding(conn, mid, [0.0, 1.0] + [0.0] * 382)
    return mid


def _mock_provider(return_vec=None):
    p = MagicMock()
    p.available.return_value = True
    p.embed.return_value = return_vec or ([1.0] + [0.0] * 383)
    return p


# ─── gate run --phase memory-audit ─────────────────────────────────────────


class TestMemoryAuditGate:
    def test_memory_audit_pass_when_no_relevant_constraints(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _make_task(conn, "my-task")
        # constraint with orthogonal embedding — below threshold
        _insert_constraint(conn, "ALWAYS: run go build", similar=False)
        conn.close()

        with patch("src.cli.cmd_gate.get_provider", return_value=_mock_provider([1.0] + [0.0] * 383)):
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--phase", "memory-audit"]
            )

        assert result.exit_code == 0
        assert "PASS" in result.output or "pass" in result.output.lower()
        # no noise when nothing relevant
        assert "not-applicable" not in result.output

    def test_memory_audit_fail_when_unaddressed_constraint(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _make_task(conn, "my-task", "fix build failures")
        mid = _insert_constraint(conn, "ALWAYS: run go build before gating")
        conn.close()

        with patch("src.cli.cmd_gate.get_provider", return_value=_mock_provider()):
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--phase", "memory-audit"]
            )

        assert result.exit_code != 0 or "FAIL" in result.output
        assert str(mid) in result.output
        assert "go build" in result.output
        assert "not-applicable" in result.output  # shows remediation command

    def test_memory_audit_fail_output_includes_remediation_command(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _make_task(conn, "my-task")
        mid = _insert_constraint(conn, "ALWAYS: run go build before gating")
        conn.close()

        with patch("src.cli.cmd_gate.get_provider", return_value=_mock_provider()):
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--phase", "memory-audit"]
            )

        assert f"--memory {mid}" in result.output
        assert "--task my-task" in result.output
        assert "--note" in result.output

    def test_memory_audit_pass_when_constraint_terms_in_modified_files(
        self, runner, project
    ):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _make_task(conn, "my-task")
        _insert_constraint(conn, "ALWAYS: run go build before gating")
        conn.close()

        # create a file with the constraint terms
        (project / "main.go").write_text("// go build before gating\npackage main\n")
        subprocess.run(["git", "-C", str(project), "add", "main.go"], check=True, capture_output=True)
        subprocess.run(
            ["git", "-C", str(project), "commit", "-m", "add main.go"],
            check=True,
            capture_output=True,
        )

        with patch("src.cli.cmd_gate.get_provider", return_value=_mock_provider()):
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--phase", "memory-audit"]
            )

        assert result.exit_code == 0
        assert "PASS" in result.output or "pass" in result.output.lower()

    def test_memory_audit_pass_when_not_applicable_link_exists(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _make_task(conn, "my-task")
        mid = _insert_constraint(conn, "ALWAYS: run go build before gating")
        conn.close()

        # register not-applicable link first
        with patch("src.cli.cmd_memory.get_provider") as mp:
            mp.return_value.available.return_value = False
            runner.invoke(
                cmd_memory,
                [
                    "link",
                    "--kind", "not-applicable",
                    "--memory", str(mid),
                    "--task", "my-task",
                    "--note", "Python project, no go build needed",
                ],
            )

        with patch("src.cli.cmd_gate.get_provider", return_value=_mock_provider()):
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--phase", "memory-audit"]
            )

        assert result.exit_code == 0
        assert "PASS" in result.output or "pass" in result.output.lower()

    def test_memory_audit_gate_recorded_in_history(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _make_task(conn, "my-task")
        conn.close()

        with patch("src.cli.cmd_gate.get_provider") as mp:
            mp.return_value.available.return_value = False
            runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--phase", "memory-audit"]
            )

        result = runner.invoke(cmd_gate, ["history", "--task", "my-task"])
        assert result.exit_code == 0
        assert "memory-audit" in result.output


# ─── memory link command ────────────────────────────────────────────────────


class TestMemoryLinkCommand:
    def test_link_not_applicable_requires_note(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        mid = mem_db.insert(conn, type="constraint", content="ALWAYS: run build")
        _make_task(conn, "my-task")
        conn.close()

        with patch("src.cli.cmd_memory.get_provider") as mp:
            mp.return_value.available.return_value = False
            result = runner.invoke(
                cmd_memory,
                [
                    "link",
                    "--kind", "not-applicable",
                    "--memory", str(mid),
                    "--task", "my-task",
                ],
            )

        assert result.exit_code != 0
        assert "note" in result.output.lower() or "required" in result.output.lower()

    def test_link_not_applicable_persists(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        mid = mem_db.insert(conn, type="constraint", content="ALWAYS: run build")
        _make_task(conn, "my-task")
        conn.close()

        with patch("src.cli.cmd_memory.get_provider") as mp:
            mp.return_value.available.return_value = False
            result = runner.invoke(
                cmd_memory,
                [
                    "link",
                    "--kind", "not-applicable",
                    "--memory", str(mid),
                    "--task", "my-task",
                    "--note", "Python project, not applicable",
                ],
            )

        assert result.exit_code == 0
        assert "link" in result.output.lower() or "salvo" in result.output.lower() or str(mid) in result.output

    def test_link_unknown_kind_rejected(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        mid = mem_db.insert(conn, type="constraint", content="ALWAYS: run build")
        conn.close()

        with patch("src.cli.cmd_memory.get_provider") as mp:
            mp.return_value.available.return_value = False
            result = runner.invoke(
                cmd_memory,
                [
                    "link",
                    "--kind", "unknown-kind",
                    "--memory", str(mid),
                    "--task", "my-task",
                    "--note", "some note",
                ],
            )

        assert result.exit_code != 0


# ─── gate run pipeline (no --phase) ────────────────────────────────────────


class TestGateRunPipeline:
    def _make_run_result(self, gate_type="tests"):
        from src.core.gate_validator import GateResult
        return GateResult(
            passed=True, gate_type=gate_type,
            command="pytest", output="1 passed", duration_ms=50,
        )

    def test_gate_run_without_phase_runs_memory_audit_first(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _make_task(conn, "my-task")
        conn.close()

        with (
            patch("src.cli.cmd_gate.get_provider") as mp,
            patch("src.cli.cmd_gate.run_tests", return_value=self._make_run_result()),
            patch("src.cli.cmd_gate.detect") as mock_detect,
        ):
            mp.return_value.available.return_value = False
            mock_detect.return_value = MagicMock(language="python")
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task"]
            )

        assert result.exit_code == 0
        # memory-audit should appear before tests in output
        assert "memory-audit" in result.output or "audit" in result.output.lower()

    def test_gate_run_skip_memory_audit_flag(self, runner, project):
        db_path = project / ".specify" / "specify.db"
        conn = get_connection(db_path)
        _make_task(conn, "my-task")
        mid = _insert_constraint(conn, "ALWAYS: run go build before gating")
        conn.close()

        with (
            patch("src.cli.cmd_gate.get_provider", return_value=_mock_provider()),
            patch("src.cli.cmd_gate.run_tests", return_value=self._make_run_result()),
            patch("src.cli.cmd_gate.detect") as mock_detect,
        ):
            mock_detect.return_value = MagicMock(language="python")
            result = runner.invoke(
                cmd_gate, ["run", "--task", "my-task", "--skip-memory-audit"]
            )

        assert result.exit_code == 0
        # skipped — no FAIL from the unaddressed constraint
        assert "FAIL" not in result.output
