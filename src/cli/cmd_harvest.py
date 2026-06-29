from __future__ import annotations

import re
from pathlib import Path

import click

from src.core.project import get_project_paths
from src.db import memory as mem_db
from src.db import vectors as vec_db
from src.db.connection import get_connection
from src.db.schema import migrate
from src.embeddings.provider import get_provider

_TYPES = ["decision", "pattern", "constraint"]

# Patterns that signal a candidate line worth harvesting
_CANDIDATE_RE = re.compile(
    r"""
    ^\s*[-*]\s+(?:\[x\]\s+)?       # bullet, optional checkbox
    (?:✓\s+)?                       # optional checkmark
    (.{10,})$                       # content, min 10 chars
    """,
    re.VERBOSE,
)

_SKIP_RE = re.compile(
    r"^\s*[-*]\s+(?:\[x\]\s+)?(?:✓\s+)?"
    r"(gate|status|data|iter|arquivo|tests?|lint|fmt|coverage|pass|fail|n/a)",
    re.IGNORECASE,
)

_SECTION_DECISION = re.compile(
    r"^#{1,3}\s+(decisão|decision|arquitetura|estratégia|restrição|restrições|constraint)",
    re.IGNORECASE,
)

_SECTION_SKIP = re.compile(
    r"^#{1,3}\s+(gate|arquivo|modificado|entregue|worktree|ciclo|commits?|fora de escopo|out of scope)",
    re.IGNORECASE,
)


def _extract_candidates(path: Path, slug: str) -> list[dict]:
    if not path.exists():
        return []
    text = path.read_text()
    lines = text.splitlines()
    candidates = []
    in_skip_section = False
    in_decision_section = False

    for line in lines:
        if re.match(r"^#{1,3}\s+", line):
            in_skip_section = bool(_SECTION_SKIP.match(line))
            in_decision_section = bool(_SECTION_DECISION.match(line))
            continue

        if in_skip_section:
            continue

        m = _CANDIDATE_RE.match(line)
        if not m:
            continue
        if _SKIP_RE.match(line):
            continue

        content = m.group(1).strip()
        # strip trailing markdown like "→ pass", "| ✓", etc.
        content = re.sub(r"\s*[→|]\s*.*$", "", content).strip()
        # keep backtick content but strip the backticks themselves
        content = re.sub(r"`([^`]+)`", r"\1", content).strip()
        content = re.sub(r"\s+", " ", content)
        if len(content) < 20:
            continue

        guessed_type = "decision" if in_decision_section else _guess_type(content)
        candidates.append(
            {
                "content": content,
                "type": guessed_type,
                "source": f"{slug}/{path.name}",
            }
        )

    return candidates


def _guess_type(content: str) -> str:
    low = content.lower()
    if any(
        w in low
        for w in [
            "sem ",
            "não ",
            "proibido",
            "nunca",
            "apenas",
            "somente",
            "fixo",
            "obrigat",
        ]
    ):
        return "constraint"
    if any(
        w in low
        for w in ["usar ", "utilizar ", "padrão", "convençã", "ao invés", "em vez"]
    ):
        return "decision"
    return "pattern"


def _already_exists(conn, content: str) -> bool:
    needle = content[:60].lower()
    rows = conn.execute(
        "SELECT content FROM memories WHERE lower(substr(content,1,60)) = ?",
        (needle,),
    ).fetchall()
    return len(rows) > 0


def _insert_memory(conn, content: str, mem_type: str, source: str) -> int:
    mid = mem_db.insert(
        conn, type=mem_type, content=content, scope="global", source=source
    )
    provider = get_provider(warn=False)
    if provider.available():
        emb = provider.embed(content)
        if emb:
            vec_db.upsert_embedding(conn, mid, emb)
    return mid


@click.command("harvest")
@click.option("--task", "task_slug", default=None, help="Processar só esta task")
@click.option(
    "--all",
    "all_tasks",
    is_flag=True,
    default=False,
    help="Processar todas as tasks (default)",
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Mostrar candidatos sem inserir"
)
def cmd_harvest(task_slug: str | None, all_tasks: bool, dry_run: bool) -> None:
    """Extrai memórias de artifacts de tasks e popula o banco interativamente."""
    paths = get_project_paths()
    if not paths.db_path.exists():
        raise click.ClickException(".specify/ não inicializado.")

    conn = get_connection(paths.db_path)
    migrate(conn)

    tasks_dir = paths.tasks_dir
    if task_slug:
        slugs = [task_slug]
    else:
        slugs = sorted(p.name for p in tasks_dir.iterdir() if p.is_dir())

    if not slugs:
        click.echo("nenhuma task encontrada")
        conn.close()
        return

    total_inserted = 0
    total_skipped = 0

    for slug in slugs:
        task_dir = tasks_dir / slug
        candidates: list[dict] = []
        for fname in ("spec.md", "plan.md", "result.md"):
            candidates.extend(_extract_candidates(task_dir / fname, slug))

        if not candidates:
            continue

        click.echo(f"\n{'─' * 52}")
        click.echo(f"  task: {slug}  ({len(candidates)} candidatos)")
        click.echo(f"{'─' * 52}")

        for c in candidates:
            if _already_exists(conn, c["content"]):
                click.echo(f"  [já existe] {c['content'][:70]}")
                total_skipped += 1
                continue

            click.echo(f"\n  fonte:    {c['source']}")
            click.echo(f"  tipo:     {c['type']}")
            click.echo(f"  conteúdo: {c['content']}")

            if dry_run:
                click.echo("  → [dry-run] não inserido")
                continue

            prompt = "\n  [d]ecision  [p]attern  [c]onstraint  [s]kip  [e]dit  [q]uit? "
            while True:
                choice = (
                    click.prompt(prompt, default="s", prompt_suffix="").strip().lower()
                )

                if choice == "q":
                    conn.close()
                    click.echo(
                        f"\n✓ {total_inserted} inseridas, {total_skipped} puladas"
                    )
                    return
                elif choice == "s":
                    total_skipped += 1
                    break
                elif choice in ("d", "p", "c"):
                    mem_type = {"d": "decision", "p": "pattern", "c": "constraint"}[
                        choice
                    ]
                    mid = _insert_memory(conn, c["content"], mem_type, c["source"])
                    click.echo(f"  ✓ inserida [{mid}] ({mem_type})")
                    total_inserted += 1
                    break
                elif choice == "e":
                    new_content = click.prompt("  novo conteúdo", default=c["content"])
                    type_choice = click.prompt(
                        "  tipo", type=click.Choice(_TYPES), default=c["type"]
                    )
                    mid = _insert_memory(conn, new_content, type_choice, c["source"])
                    click.echo(f"  ✓ inserida [{mid}] ({type_choice})")
                    total_inserted += 1
                    break
                else:
                    click.echo("  opção inválida")

    conn.close()
    click.echo(f"\n✓ {total_inserted} inseridas, {total_skipped} puladas")
