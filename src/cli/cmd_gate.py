from __future__ import annotations

import json as _json
from pathlib import Path

import click

from src.core.gate_validator import run_fmt_check, run_lint, run_tests
from src.core.lang_detector import detect
from src.core.logger import get_logger
from src.core.project import get_project_paths
from src.db import gates as gate_db
from src.db import links as links_db
from src.db import memory as mem_db
from src.db import tasks as task_db
from src.db import vectors as vec_db
from src.db.connection import get_connection
from src.db.schema import migrate
from src.embeddings.provider import get_provider

# vec_db.search returns L2 distance — lower is more similar (0.0 = identical)
_CHECKLIST_DISTANCE_MAX = 0.4
_CHECKLIST_LIMIT = 5
_AUDIT_DISTANCE_MAX = 0.25
_AUDIT_LIMIT = 20

_PHASES = ["red", "green", "refactor", "review", "close", "memory-audit"]
_GATE_TYPES = ["tests", "lint", "fmt", "coverage", "adversarial", "memory-audit"]
_STATUSES = ["pass", "fail", "skip"]
_RUN_PHASES = ["tests", "lint", "fmt", "memory-audit"]


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


def _print_constraint_checklist(conn, task_slug: str) -> None:
    task = task_db.get(conn, task_slug)
    query = task.title if task else task_slug

    provider = get_provider(warn=False)
    if not provider.available():
        return

    embedding = provider.embed(query)
    if not embedding:
        return

    results = vec_db.search(conn, embedding, limit=_CHECKLIST_LIMIT)
    constraints = []
    for mid, dist in results:
        if dist > _CHECKLIST_DISTANCE_MAX:
            continue
        m = mem_db.get(conn, mid)
        if m is not None and m.type == "constraint":
            constraints.append(m)

    if not constraints:
        return

    click.echo("Constraint checklist:")
    for m in constraints:
        click.echo(f"  [ ] {m.content}")
    click.echo("")


def _extract_keywords(content: str) -> list[str]:
    """Extract meaningful terms from constraint content for evidence matching."""
    import re

    # strip known prefixes
    content = re.sub(
        r"^(ALWAYS|NEVER|CHECK|DECIDED|AVOID|WHEN)\s*:?\s*",
        "",
        content,
        flags=re.IGNORECASE,
    )
    words = re.findall(r"[a-zA-Z0-9_./\-]{3,}", content)
    # filter stopwords
    stopwords = {
        "and",
        "the",
        "for",
        "with",
        "that",
        "this",
        "from",
        "are",
        "must",
        "not",
    }
    return [w.lower() for w in words if w.lower() not in stopwords]


def _has_evidence(keywords: list[str], task_slug: str, conn) -> bool:
    """Check if constraint keywords appear in git-modified files or plan.md."""
    import subprocess

    # check plan.md
    paths = get_project_paths()
    plan_path = paths.root / ".specify" / "tasks" / task_slug / "plan.md"
    if plan_path.exists():
        plan_text = plan_path.read_text().lower()
        if any(kw in plan_text for kw in keywords):
            return True

    # check git-modified files (working tree, staged, and last commit)
    try:
        cwd = str(paths.root)
        modified: list[str] = []
        for cmd in [
            ["git", "diff", "--name-only", "HEAD"],
            ["git", "diff", "--name-only", "--cached"],
            ["git", "show", "--name-only", "--format=", "HEAD"],
        ]:
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
            modified += r.stdout.splitlines()

        for fname in set(f for f in modified if f.strip()):
            fpath = paths.root / fname
            if fpath.exists() and fpath.stat().st_size < 500_000:
                try:
                    text = fpath.read_text(errors="ignore").lower()
                    if any(kw in text for kw in keywords):
                        return True
                except OSError:
                    pass
    except Exception:
        pass

    return False


def _run_memory_audit(conn, task_slug: str) -> tuple[str, str]:
    """
    Returns (status, output) where status is 'pass' or 'fail'.
    Checks relevant constraints against evidence in modified files and not-applicable links.
    """
    task = task_db.get(conn, task_slug)
    query = task.title if task else task_slug

    provider = get_provider(warn=False)
    if not provider.available():
        gate_db.record(
            conn,
            task_slug=task_slug,
            phase="memory-audit",
            gate_type="memory-audit",
            status="skip",
            output="embedding provider unavailable",
        )
        return "skip", "memory-audit: skip (provider unavailable)"

    embedding = provider.embed(query)
    if not embedding:
        gate_db.record(
            conn,
            task_slug=task_slug,
            phase="memory-audit",
            gate_type="memory-audit",
            status="skip",
            output="embed returned None",
        )
        return "skip", "memory-audit: skip (embed failed)"

    results = vec_db.search(conn, embedding, limit=_AUDIT_LIMIT)
    failing: list[mem_db.Memory] = []

    for mid, dist in results:
        if dist > _AUDIT_DISTANCE_MAX:
            continue
        m = mem_db.get(conn, mid)
        if m is None or m.type != "constraint":
            continue
        # check not-applicable exemption
        if links_db.exists(
            conn, memory_id=m.id, task_slug=task_slug, kind="not-applicable"
        ):
            continue
        # check evidence in modified files / plan
        keywords = _extract_keywords(m.content)
        if keywords and _has_evidence(keywords, task_slug, conn):
            continue
        failing.append(m)

    if not failing:
        gate_db.record(
            conn,
            task_slug=task_slug,
            phase="memory-audit",
            gate_type="memory-audit",
            status="pass",
        )
        return "pass", "✓ memory-audit: pass"

    lines = ["✗ MEMORY AUDIT FAILED", "─" * 50]
    for m in failing:
        src = f" [{m.source}]" if m.source else ""
        lines.append(f"\nConstraint [{m.id}]{src} not addressed:")
        lines.append(f"  {m.content}")
        lines.append(
            f"  → specify memory link --kind not-applicable "
            f'--memory {m.id} --task {task_slug} --note "<reason>"'
        )
    lines.append("")
    output = "\n".join(lines)

    gate_db.record(
        conn,
        task_slug=task_slug,
        phase="memory-audit",
        gate_type="memory-audit",
        status="fail",
        output=output[:4000],
    )
    return "fail", output


@cmd_gate.command("run")
@click.option("--task", "task_slug", required=True, help="Slug da task")
@click.option("--phase", default=None, type=click.Choice(_RUN_PHASES))
@click.option(
    "--skip-memory-audit", "skip_audit", is_flag=True, help="Suprimir memory-audit"
)
@click.option(
    "--cwd", "cwd_path", default=None, help="Diretório do projeto (padrão: CWD)"
)
@click.option("--iteration", default=1, type=int)
def cmd_run(
    task_slug: str,
    phase: str | None,
    skip_audit: bool,
    cwd_path: str | None,
    iteration: int,
) -> None:
    """Executa um gate e registra o resultado no DB."""
    # memory-audit only phase
    if phase == "memory-audit":
        conn = _get_conn()
        status, output = _run_memory_audit(conn, task_slug)
        conn.close()
        click.echo(output)
        if status == "fail":
            raise SystemExit(1)
        return

    # pipeline mode (no --phase): run memory-audit then tests
    if phase is None:
        conn = _get_conn()
        if not skip_audit:
            click.echo("running memory-audit...")
            status, output = _run_memory_audit(conn, task_slug)
            conn.close()
            click.echo(output)
            if status == "fail":
                raise SystemExit(1)
        else:
            gate_db.record(
                conn,
                task_slug=task_slug,
                phase="memory-audit",
                gate_type="memory-audit",
                status="skip",
                output="--skip-memory-audit flag",
            )
            conn.close()
            click.echo("memory-audit: skipped (--skip-memory-audit)")
        phase = "tests"

    cwd = Path(cwd_path) if cwd_path else Path.cwd()
    lang = detect(cwd)
    if lang is None:
        raise click.ClickException(
            f"linguagem não detectada em '{cwd}'. "
            "Verifique se há go.mod, pyproject.toml ou package.json."
        )

    conn = _get_conn()
    if phase == "tests":
        _print_constraint_checklist(conn, task_slug)
    conn.close()

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
