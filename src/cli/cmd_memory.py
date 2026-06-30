from __future__ import annotations

import json as _json
import re

import click

from src.core.logger import get_logger
from src.core.project import get_project_paths
from src.db import memory as mem_db
from src.db import searches as search_db
from src.db import vectors as vec_db
from src.db.connection import get_connection
from src.db.schema import migrate
from src.embeddings.provider import get_provider

_KNOWN_PREFIXES = re.compile(
    r"^(ALWAYS|NEVER|CHECK|DECIDED|AVOID)\s*:|^WHEN\b", re.IGNORECASE
)

_PREFIX_TEMPLATES = {
    "constraint": "ALWAYS: {content}",
    "pattern": "WHEN <condition> DO: {content}",
    "decision": "DECIDED: {content}",
}


def _suggest_prefix(mem_type: str, content: str) -> str | None:
    if _KNOWN_PREFIXES.match(content.strip()):
        return None
    template = _PREFIX_TEMPLATES.get(mem_type)
    if template is None:
        return None
    return template.format(content=content)


def _highlight_content(content: str) -> str:
    m = _KNOWN_PREFIXES.match(content.strip())
    if not m:
        return content
    prefix_end = m.end()
    prefix = content[:prefix_end]
    rest = content[prefix_end:]
    return f"[{prefix}]{rest}"


def _get_conn():
    paths = get_project_paths()
    if not paths.db_path.exists():
        raise click.ClickException(
            ".specify/ não inicializado. Execute `specify init` primeiro."
        )
    conn = get_connection(paths.db_path)
    migrate(conn)
    return conn


def _format_memory(
    m: mem_db.Memory, *, as_json: bool = False, highlight: bool = False
) -> str:
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
    content = _highlight_content(m.content) if highlight else m.content
    return f"[{m.id}] ({m.type}/{m.scope}){src}\n    {content}"


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
    suggestion = _suggest_prefix(mem_type, content)
    if suggestion:
        click.echo(f"  sugestão de formato: {suggestion}", err=False)


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
            click.echo(_format_memory(m, highlight=True))


@cmd_memory.command("search")
@click.argument("query")
@click.option("--limit", default=5, show_default=True)
@click.option(
    "--source", default=None, help="Origem da busca (ex: specify.plan, specify.new)"
)
@click.option("--json", "as_json", is_flag=True)
def cmd_search(query: str, limit: int, source: str | None, as_json: bool) -> None:
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

    search_db.log_search(conn, query=query, results_count=len(memories), source=source)
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


@cmd_memory.command("stats")
@click.option("--json", "as_json", is_flag=True)
def cmd_stats(as_json: bool) -> None:
    """Exibe estatísticas de uso de memórias (criações e buscas)."""
    conn = _get_conn()
    data = search_db.stats(conn)
    total_memories = len(mem_db.list_all(conn))
    conn.close()

    data["total_memories"] = total_memories

    if as_json:
        click.echo(_json.dumps(data, indent=2))
        return

    click.echo(f"memórias salvas : {total_memories}")
    click.echo(f"buscas totais   : {data['total_searches']}")
    click.echo(f"buscas sem resultado: {data['zero_result_searches']}")

    if data["by_source"]:
        click.echo("\nbuscas por origem:")
        for row in data["by_source"]:
            src = row["source"] or "(sem source)"
            click.echo(f"  {src:<30} {row['count']}")

    if data["top_queries"]:
        click.echo("\nqueries mais frequentes:")
        for row in data["top_queries"]:
            click.echo(f"  [{row['count']}x] {row['query']}")

    if data["recent"]:
        click.echo("\núltimas buscas:")
        for row in data["recent"]:
            src = f" [{row['source']}]" if row["source"] else ""
            click.echo(
                f"  {row['searched_at']}{src} → {row['results_count']} resultado(s): {row['query']}"
            )


@cmd_memory.command("reformat")
@click.option(
    "--id", "memory_id", type=int, default=None, help="ID da memória a reformatar"
)
@click.option("--dry-run", is_flag=True, help="Exibe mudanças sem alterar o banco")
def cmd_reformat(memory_id: int | None, dry_run: bool) -> None:
    """Reformata memórias sem prefixo para o padrão prescritivo."""
    conn = _get_conn()

    if memory_id is not None:
        memories = [mem_db.get(conn, memory_id)]
        if memories[0] is None:
            conn.close()
            raise click.ClickException(f"memória [{memory_id}] não encontrada")
    else:
        memories = mem_db.list_all(conn)

    to_reformat = [
        (m, _suggest_prefix(m.type, m.content))
        for m in memories
        if m is not None and _suggest_prefix(m.type, m.content) is not None
    ]

    if not to_reformat:
        conn.close()
        click.echo("nenhuma memória sem prefixo encontrada")
        return

    if dry_run:
        for m, suggestion in to_reformat:
            click.echo(f"[{m.id}] ({m.type}) →")
            click.echo(f"  antes:  {m.content}")
            click.echo(f"  depois: {suggestion}")
        conn.close()
        return

    if len(to_reformat) > 5:
        click.echo(f"{len(to_reformat)} memórias serão reformatadas.")
        if not click.confirm("Prosseguir?"):
            conn.close()
            click.echo("cancelado")
            return

    for m, suggestion in to_reformat:
        mem_db.update(conn, m.id, suggestion)
        click.echo(f"[{m.id}] atualizado")

    conn.close()


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


@cmd_memory.command("link")
@click.option("--kind", required=True, help="Tipo do link (ex: not-applicable)")
@click.option("--memory", "memory_id", required=True, type=int, help="ID da memória")
@click.option("--task", "task_slug", required=True, help="Slug da task")
@click.option("--note", default=None, help="Razão obrigatória para o link")
def cmd_link(kind: str, memory_id: int, task_slug: str, note: str | None) -> None:
    """Cria um link entre memória e task (ex: not-applicable)."""
    if note is None or not note.strip():
        raise click.ClickException("--note é obrigatório para memory link")

    conn = _get_conn()
    from src.db import links as links_db
    from src.db import tasks as task_db

    if mem_db.get(conn, memory_id) is None:
        conn.close()
        raise click.ClickException(f"memória [{memory_id}] não encontrada")

    if task_db.get(conn, task_slug) is None:
        conn.close()
        raise click.ClickException(f"task '{task_slug}' não encontrada")

    try:
        lid = links_db.insert(
            conn, memory_id=memory_id, task_slug=task_slug, kind=kind, note=note
        )
    except ValueError as e:
        conn.close()
        raise click.ClickException(str(e))

    conn.close()
    click.echo(f"link [{lid}] salvo: [{memory_id}] → {task_slug} ({kind})")


# late import to avoid circular
from src.cli.cmd_harvest import cmd_harvest  # noqa: E402

cmd_memory.add_command(cmd_harvest)
