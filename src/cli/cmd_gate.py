from __future__ import annotations

import json as _json
from pathlib import Path

import click

from src.core.gate_validator import run_fmt_check, run_lint, run_tests
from src.core.lang_detector import detect
from src.core.logger import get_logger
from src.core.project import get_project_paths
from src.db import gates as gate_db
from src.db.connection import get_connection
from src.db.schema import migrate

_PHASES = ["red", "green", "refactor", "review", "close"]
_GATE_TYPES = ["tests", "lint", "fmt", "coverage", "adversarial"]
_STATUSES = ["pass", "fail", "skip"]
_RUN_PHASES = ["tests", "lint", "fmt"]


def _get_conn():
    paths = get_project_paths()
    if not paths.db_path.exists():
        raise click.ClickException(
            ".specify/ não inicializado. Execute `specify init` primeiro."
        )
    conn = get_connection(paths.db_path)
    migrate(conn)
    return conn


def _format_gate(g: gate_db.Gate, *, as_json: bool = False) -> str:
    if as_json:
        return _json.dumps(
            {
                "id": g.id,
                "task_slug": g.task_slug,
                "phase": g.phase,
                "gate_type": g.gate_type,
                "status": g.status,
                "iteration": g.iteration,
                "created_at": g.created_at,
            }
        )
    symbol = "✓" if g.status == "pass" else ("⊘" if g.status == "skip" else "✗")
    return f"{symbol} [{g.phase}/{g.gate_type}] iter={g.iteration}  {g.status}  ({g.created_at})"


@click.group("gate")
def cmd_gate() -> None:
    """Gerencia gates de validação."""


@cmd_gate.command("record")
@click.option("--task", "task_slug", required=True, help="Slug da task")
@click.option("--phase", required=True, type=click.Choice(_PHASES))
@click.option("--type", "gate_type", required=True, type=click.Choice(_GATE_TYPES))
@click.option("--status", required=True, type=click.Choice(_STATUSES))
@click.option("--output", "output_text", default=None, help="Output do comando")
@click.option("--iteration", default=1, type=int)
def cmd_record(
    task_slug: str,
    phase: str,
    gate_type: str,
    status: str,
    output_text: str | None,
    iteration: int,
) -> None:
    """Registra um gate manualmente."""
    conn = _get_conn()
    gid = gate_db.record(
        conn,
        task_slug=task_slug,
        phase=phase,
        gate_type=gate_type,
        status=status,
        output=output_text,
        iteration=iteration,
    )
    conn.close()
    symbol = "✓" if status == "pass" else "✗"
    get_logger().debug(
        "gate record: %s/%s/%s → %s", task_slug, phase, gate_type, status
    )
    click.echo(
        f"{symbol} gate [{gid}] registrado: {task_slug}/{phase}/{gate_type} → {status}"
    )


@cmd_gate.command("run")
@click.option("--task", "task_slug", required=True, help="Slug da task")
@click.option("--phase", required=True, type=click.Choice(_RUN_PHASES))
@click.option(
    "--cwd", "cwd_path", default=None, help="Diretório do projeto (padrão: CWD)"
)
@click.option("--iteration", default=1, type=int)
def cmd_run(task_slug: str, phase: str, cwd_path: str | None, iteration: int) -> None:
    """Executa um gate e registra o resultado no DB."""
    cwd = Path(cwd_path) if cwd_path else Path.cwd()
    lang = detect(cwd)
    if lang is None:
        raise click.ClickException(
            f"linguagem não detectada em '{cwd}'. "
            "Verifique se há go.mod, pyproject.toml ou package.json."
        )

    click.echo(f"executando {phase} ({lang.language}) em {cwd}...")

    if phase == "tests":
        result = run_tests(lang, cwd)
    elif phase == "lint":
        result = run_lint(lang, cwd)
    else:  # fmt
        result = run_fmt_check(lang, cwd)

    status = "pass" if result.passed else "fail"
    symbol = "✓" if result.passed else "✗"

    conn = _get_conn()
    gate_db.record(
        conn,
        task_slug=task_slug,
        phase=phase,
        gate_type=result.gate_type,
        status=status,
        output=result.output[:4000] if result.output else None,
        iteration=iteration,
    )
    conn.close()

    get_logger().debug(
        "gate run: %s/%s → %s (%dms) cmd=%r output=%r",
        task_slug,
        phase,
        status,
        result.duration_ms,
        result.command,
        (result.output or "")[:2000],
    )
    click.echo(f"{symbol} {phase}: {status} ({result.duration_ms}ms)")
    click.echo(f"  cmd: {result.command}")
    if result.output:
        # exibir últimas linhas do output para não poluir terminal
        lines = result.output.splitlines()
        preview = "\n".join(lines[-10:]) if len(lines) > 10 else result.output
        click.echo(f"  output:\n{preview}")


@cmd_gate.command("history")
@click.option("--task", "task_slug", required=True)
@click.option("--phase", default=None, type=click.Choice(_PHASES))
@click.option("--json", "as_json", is_flag=True)
def cmd_history(task_slug: str, phase: str | None, as_json: bool) -> None:
    """Exibe histórico de gates de uma task."""
    conn = _get_conn()
    gates = gate_db.history(conn, task_slug, phase=phase)
    conn.close()
    if not gates:
        click.echo("nenhum gate registrado")
        return
    if as_json:
        click.echo(
            _json.dumps(
                [_json.loads(_format_gate(g, as_json=True)) for g in gates], indent=2
            )
        )
    else:
        for g in gates:
            click.echo(_format_gate(g))


@cmd_gate.command("last")
@click.option("--task", "task_slug", required=True)
@click.option("--phase", required=True, type=click.Choice(_PHASES))
@click.option("--type", "gate_type", required=True, type=click.Choice(_GATE_TYPES))
@click.option("--json", "as_json", is_flag=True)
def cmd_last(task_slug: str, phase: str, gate_type: str, as_json: bool) -> None:
    """Exibe o último gate para uma combinação task/phase/type."""
    conn = _get_conn()
    g = gate_db.last(conn, task_slug, phase, gate_type)
    conn.close()
    if g is None:
        raise click.ClickException(
            f"nenhum gate encontrado para {task_slug}/{phase}/{gate_type}"
        )
    click.echo(_format_gate(g, as_json=as_json))
