from __future__ import annotations

import json as _json

import click

from src.core.project import get_project_paths
from src.db import tasks as task_db
from src.db.connection import get_connection
from src.db.schema import migrate

_VALID_STATUSES = ["planned", "in_progress", "review", "closed"]


def _get_conn():
    paths = get_project_paths()
    if not paths.db_path.exists():
        raise click.ClickException(
            ".specify/ não inicializado. Execute `specify init` primeiro."
        )
    conn = get_connection(paths.db_path)
    migrate(conn)
    return conn


def _format_task(t: task_db.Task, *, as_json: bool = False) -> str:
    if as_json:
        return _json.dumps({
            "slug": t.slug,
            "title": t.title,
            "status": t.status,
            "spec_path": t.spec_path,
            "created_at": t.created_at,
        })
    spec = f" [{t.spec_path}]" if t.spec_path else ""
    return f"[{t.slug}] {t.status}{spec}\n    {t.title}"


@click.group("task")
def cmd_task() -> None:
    """Gerencia tasks do projeto."""


@cmd_task.command("create")
@click.option("--slug", required=True, help="Identificador único da task")
@click.option("--title", required=True, help="Título da task")
@click.option("--spec", "spec_path", default=None, help="Caminho para spec.md")
def cmd_create(slug: str, title: str, spec_path: str | None) -> None:
    """Cria uma nova task."""
    conn = _get_conn()
    try:
        task_id = task_db.create(conn, slug=slug, title=title, spec_path=spec_path)
        conn.close()
        click.echo(f"task '{slug}' criada (id={task_id})")
    except ValueError as e:
        conn.close()
        raise click.ClickException(str(e))


@cmd_task.command("list")
@click.option(
    "--status",
    default=None,
    type=click.Choice(_VALID_STATUSES),
    help="Filtrar por status",
)
@click.option("--json", "as_json", is_flag=True)
def cmd_list(status: str | None, as_json: bool) -> None:
    """Lista tasks do projeto."""
    conn = _get_conn()
    tasks = task_db.list_all(conn, status=status)
    conn.close()
    if not tasks:
        click.echo("nenhuma task encontrada")
        return
    if as_json:
        click.echo(_json.dumps([_json.loads(_format_task(t, as_json=True)) for t in tasks], indent=2))
    else:
        for t in tasks:
            click.echo(_format_task(t))


@cmd_task.command("status")
@click.argument("slug")
@click.option("--json", "as_json", is_flag=True)
def cmd_status(slug: str, as_json: bool) -> None:
    """Exibe detalhes de uma task."""
    conn = _get_conn()
    t = task_db.get(conn, slug)
    conn.close()
    if t is None:
        raise click.ClickException(f"task '{slug}' não encontrada")
    click.echo(_format_task(t, as_json=as_json))


@cmd_task.command("update")
@click.argument("slug")
@click.option(
    "--status",
    required=True,
    type=click.Choice(_VALID_STATUSES),
    help="Novo status",
)
def cmd_update(slug: str, status: str) -> None:
    """Atualiza o status de uma task."""
    conn = _get_conn()
    if task_db.get(conn, slug) is None:
        conn.close()
        raise click.ClickException(f"task '{slug}' não encontrada")
    task_db.update_status(conn, slug, status)
    conn.close()
    click.echo(f"task '{slug}' → {status}")


@cmd_task.command("close")
@click.argument("slug")
def cmd_close(slug: str) -> None:
    """Fecha uma task (atalho para update --status closed)."""
    conn = _get_conn()
    if task_db.get(conn, slug) is None:
        conn.close()
        raise click.ClickException(f"task '{slug}' não encontrada")
    task_db.update_status(conn, slug, "closed")
    conn.close()
    click.echo(f"task '{slug}' fechada")
