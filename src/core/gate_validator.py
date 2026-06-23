from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from src.core.lang_detector import LangConfig


@dataclass
class GateResult:
    gate_type: str
    passed: bool
    output: str
    duration_ms: int
    command: str


def run_gate(cmd: str, cwd: Path, gate_type: str = "custom", timeout: int = 120) -> GateResult:
    """Executa um comando e retorna GateResult. Nunca levanta exceção."""
    start = time.monotonic()
    try:
        result = subprocess.run(
            shlex.split(cmd),
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        output = (result.stdout + result.stderr).strip()
        return GateResult(
            gate_type=gate_type,
            passed=result.returncode == 0,
            output=output,
            duration_ms=duration_ms,
            command=cmd,
        )
    except FileNotFoundError:
        duration_ms = int((time.monotonic() - start) * 1000)
        return GateResult(
            gate_type=gate_type,
            passed=False,
            output=f"comando não encontrado: {cmd.split()[0]}",
            duration_ms=duration_ms,
            command=cmd,
        )
    except subprocess.TimeoutExpired:
        duration_ms = int((time.monotonic() - start) * 1000)
        return GateResult(
            gate_type=gate_type,
            passed=False,
            output=f"timeout após {timeout}s: {cmd}",
            duration_ms=duration_ms,
            command=cmd,
        )


def run_tests(config: LangConfig, cwd: Path, timeout: int = 300) -> GateResult:
    return run_gate(config.test_cmd, cwd, gate_type="tests", timeout=timeout)


def run_lint(config: LangConfig, cwd: Path) -> GateResult:
    return run_gate(config.lint_cmd, cwd, gate_type="lint")


def run_fmt_check(config: LangConfig, cwd: Path) -> GateResult:
    return run_gate(config.fmt_cmd, cwd, gate_type="fmt")
