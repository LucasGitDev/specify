from __future__ import annotations

from pathlib import Path

import click

from src.core.project import get_project_paths
from src.db import memory as mem_db
from src.db import tasks as task_db
from src.db import vectors as vec_db
from src.db.connection import get_connection
from src.db.schema import migrate
from src.embeddings.provider import get_provider

# vec_db.search returns L2 distance — lower is more similar (0.0 = identical)
_DISTANCE_MAX = 0.4
_LIMIT = 8


def _get_conn():
    paths = get_project_paths()
    if not paths.db_path.exists():
        raise click.ClickException(
            ".specify/ não inicializado. Execute `specify init` primeiro."
        )
    conn = get_connection(paths.db_path)
    migrate(conn)
    return conn


@click.command("context")
@click.argument("slug")
def cmd_context(slug: str) -> None:
    """Exibe memórias relevantes para uma task (constraints e decisions)."""
    conn = _get_conn()

    task = task_db.get(conn, slug)
    if task is None:
        conn.close()
        raise click.ClickException(f"task '{slug}' não encontrada")

    query_parts = [task.title]
    if task.spec_path:
        spec = Path(task.spec_path)
        if spec.exists():
            query_parts.append(spec.read_text()[:2000])
    query = " ".join(query_parts)

    provider = get_provider(warn=False)
    memories: list[mem_db.Memory] = []

    if provider.available():
        embedding = provider.embed(query)
        if embedding:
            results = vec_db.search(conn, embedding, limit=_LIMIT)
            for mid, dist in results:
                if dist <= _DISTANCE_MAX:
                    m = mem_db.get(conn, mid)
                    if m is not None and m.type in ("constraint", "decision"):
                        memories.append(m)
    else:
        # fallback: substring match against task title keywords
        keywords = [w for w in query.lower().split() if len(w) > 3]
        candidates = mem_db.list_all(conn, type="constraint") + mem_db.list_all(
            conn, type="decision"
        )
        memories = [
            m for m in candidates if any(kw in m.content.lower() for kw in keywords)
        ][:_LIMIT]

    conn.close()

    click.echo(f"## Context — {slug}\n")

    constraints = [m for m in memories if m.type == "constraint"]
    decisions = [m for m in memories if m.type == "decision"]

    if constraints:
        click.echo("### Known constraints\n")
        for m in constraints:
            click.echo(f"  [{m.id}] {m.content}")
        click.echo("")

    if decisions:
        click.echo("### Relevant decisions\n")
        for m in decisions:
            click.echo(f"  [{m.id}] {m.content}")
        click.echo("")

    if not memories:
        click.echo("(no relevant memories found)")
