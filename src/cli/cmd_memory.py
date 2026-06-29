from __future__ import annotations

import json as _json

import click

from src.core.logger import get_logger
from src.core.project import get_project_paths
from src.db import memory as mem_db
from src.db import vectors as vec_db
from src.db.connection import get_connection
from src.db.schema import migrate
from src.embeddings.provider import get_provider


def _get_conn():
    paths = get_project_paths()
    if not paths.db_path.exists():
        raise click.ClickException(
            ".specify/ não inicializado. Execute `specify init` primeiro."
        )
    conn = get_connection(paths.db_path)
    migrate(conn)
    return conn


def _format_memory(m: mem_db.Memory, *, as_json: bool = False) -> str:
    if as_json:
        return _json.dumps(
            {
                "id": m.id,
                "type": m.type,
                "scope": m.scope,
                "content": m.content,
                "source": m.source,
                "created_at": m.created_at,
            }
        )
    src = f" [{m.source}]" if m.source else ""
    return f"[{m.id}] ({m.type}/{m.scope}){src}\n    {m.content}"


@click.group("memory")
def cmd_memory() -> None:
    """Gerencia memórias do projeto."""


@cmd_memory.command("set")
@click.option(
    "--type",
    "mem_type",
    required=True,
    type=click.Choice(["decision", "pattern", "constraint"]),
    help="Tipo da memória",
)
@click.option("--content", required=True, help="Conteúdo da memória")
@click.option("--scope", default="global", help="Escopo: 'global' ou slug da task")
@click.option("--source", default=None, help="Arquivo ou skill de origem")
def cmd_set(mem_type: str, content: str, scope: str, source: str | None) -> None:
    """Persiste uma nova memória."""
    conn = _get_conn()
    memory_id = mem_db.insert(
        conn, type=mem_type, content=content, scope=scope, source=source
    )

    provider = get_provider(warn=True)
    if provider.available():
        embedding = provider.embed(content)
        if embedding:
            vec_db.upsert_embedding(conn, memory_id, embedding)

    conn.close()
    click.echo(f"memória [{memory_id}] salva ({mem_type}/{scope})")


@cmd_memory.command("get")
@click.argument("memory_id", type=int)
@click.option("--json", "as_json", is_flag=True)
def cmd_get(memory_id: int, as_json: bool) -> None:
    """Exibe uma memória pelo ID."""
    conn = _get_conn()
    m = mem_db.get(conn, memory_id)
    conn.close()
    if m is None:
        raise click.ClickException(f"memória [{memory_id}] não encontrada")
    click.echo(_format_memory(m, as_json=as_json))


@cmd_memory.command("list")
@click.option("--scope", default=None, help="Filtrar por escopo")
@click.option("--type", "mem_type", default=None, help="Filtrar por tipo")
@click.option("--json", "as_json", is_flag=True)
def cmd_list(scope: str | None, mem_type: str | None, as_json: bool) -> None:
    """Lista memórias do projeto."""
    conn = _get_conn()
    memories = mem_db.list_all(conn, scope=scope, type=mem_type)
    conn.close()
    if not memories:
        click.echo("nenhuma memória encontrada")
        return
    if as_json:
        click.echo(
            _json.dumps(
                [_json.loads(_format_memory(m, as_json=True)) for m in memories],
                indent=2,
            )
        )
    else:
        for m in memories:
            click.echo(_format_memory(m))


@cmd_memory.command("search")
@click.argument("query")
@click.option("--limit", default=5, show_default=True)
@click.option("--json", "as_json", is_flag=True)
def cmd_search(query: str, limit: int, as_json: bool) -> None:
    """Busca memórias por similaridade semântica (ou substring como fallback)."""
    conn = _get_conn()
    provider = get_provider(warn=False)

    if provider.available():
        embedding = provider.embed(query)
        if embedding:
            results = vec_db.search(conn, embedding, limit=limit)
            memories = [mem_db.get(conn, mid) for mid, _ in results]
            memories = [m for m in memories if m is not None]
        else:
            memories = mem_db.search_substring(conn, query, limit=limit)
    else:
        click.echo("aviso: busca vetorial indisponível, usando substring", err=True)
        memories = mem_db.search_substring(conn, query, limit=limit)

    conn.close()
    get_logger().debug("memory search: query=%r results=%d", query, len(memories))
    if not memories:
        click.echo("nenhum resultado")
        return
    if as_json:
        click.echo(
            _json.dumps(
                [_json.loads(_format_memory(m, as_json=True)) for m in memories],
                indent=2,
            )
        )
    else:
        for m in memories:
            click.echo(_format_memory(m))


@cmd_memory.command("delete")
@click.argument("memory_id", type=int)
def cmd_delete(memory_id: int) -> None:
    """Remove uma memória pelo ID."""
    conn = _get_conn()
    if mem_db.get(conn, memory_id) is None:
        conn.close()
        raise click.ClickException(f"memória [{memory_id}] não encontrada")
    vec_db.delete_embedding(conn, memory_id)
    mem_db.delete(conn, memory_id)
    conn.close()
    click.echo(f"memória [{memory_id}] removida")


# late import to avoid circular
from src.cli.cmd_harvest import cmd_harvest  # noqa: E402

cmd_memory.add_command(cmd_harvest)
