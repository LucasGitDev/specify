from __future__ import annotations

import json as _json

import click

from src.core.project import find_project_root, get_project_paths
from src.core import worktree as wt
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
            "worktree_path": t.worktree_path,
            "worktree_branch": t.worktree_branch,
            "created_at": t.created_at,
        })
    spec = f" [{t.spec_path}]" if t.spec_path else ""
    wt_info = f" [worktree: {t.worktree_branch}]" if t.worktree_branch else ""
    return f"[{t.slug}] {t.status}{spec}{wt_info}\n    {t.title}"


@click.group("task")
def cmd_task() -> None:
    """Gerencia tasks do projeto."""


@cmd_task.command("create")
@click.option("--slug", required=True, help="Identificador único da task")
@click.option("--title", required=True, help="Título da task")
@click.option("--spec", "spec_path", default=None, help="Caminho para spec.md")
@click.option("--worktree", is_flag=True, help="Criar worktree isolado para esta task")
def cmd_create(slug: str, title: str, spec_path: str | None, worktree: bool) -> None:
    """Cria uma nova task."""
    conn = _get_conn()
    worktree_path: str | None = None
    worktree_branch: str | None = None

    if worktree:
        root = find_project_root()
        if root is None:
            conn.close()
            raise click.ClickException("Raiz do projeto não encontrada.")
        try:
            info = wt.create(root, slug)
            worktree_path = str(info.path)
            worktree_branch = info.branch
        except RuntimeError as e:
            conn.close()
            raise click.ClickException(f"Erro ao criar worktree: {e}")

    try:
        task_id = task_db.create(
            conn,
            slug=slug,
            title=title,
            spec_path=spec_path,
            worktree_path=worktree_path,
            worktree_branch=worktree_branch,
        )
        conn.close()
        click.echo(f"task '{slug}' criada (id={task_id})")
        if worktree_branch:
            click.echo(f"  worktree: {worktree_path}")
            click.echo(f"  branch:   {worktree_branch}")
            click.echo(f"  para entrar: claude --worktree {slug}")
    except ValueError as e:
        if worktree_path:
            # rollback: remover worktree criado
            try:
                from pathlib import Path
                wt.remove(find_project_root(), Path(worktree_path), force=True)
            except Exception:
                pass
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
@click.option("--remove-worktree", is_flag=True, help="Remover worktree após fechar")
def cmd_close(slug: str, remove_worktree: bool) -> None:
    """Fecha uma task (atalho para update --status closed)."""
    conn = _get_conn()
    t = task_db.get(conn, slug)
    if t is None:
        conn.close()
        raise click.ClickException(f"task '{slug}' não encontrada")
    task_db.update_status(conn, slug, "closed")
    conn.close()
    click.echo(f"task '{slug}' fechada")

    if t.worktree_path and remove_worktree:
        root = find_project_root()
        if root:
            try:
                from pathlib import Path
                wt.remove(root, Path(t.worktree_path))
                click.echo(f"  worktree removido: {t.worktree_path}")
            except RuntimeError as e:
                click.echo(f"  aviso: não foi possível remover worktree: {e}", err=True)
    elif t.worktree_path and not remove_worktree:
        click.echo(f"  worktree em: {t.worktree_path}")
        click.echo("  para remover: specify task close <slug> --remove-worktree")


@cmd_task.command("worktree-info")
@click.argument("slug")
def cmd_worktree_info(slug: str) -> None:
    """Exibe informações do worktree de uma task."""
    conn = _get_conn()
    t = task_db.get(conn, slug)
    conn.close()
    if t is None:
        raise click.ClickException(f"task '{slug}' não encontrada")
    if not t.worktree_path:
        click.echo(f"task '{slug}' não tem worktree associado")
        return
    click.echo(f"task:    {slug}")
    click.echo(f"path:    {t.worktree_path}")
    click.echo(f"branch:  {t.worktree_branch}")
