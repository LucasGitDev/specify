#!/usr/bin/env python3
"""SessionStart hook — injeta contexto do .specify/ na sessão do Claude."""
from __future__ import annotations

import sys
from pathlib import Path

# Garante que o src do plugin está no path quando invocado pelo hook
_plugin_root = Path(__file__).resolve().parent.parent.parent
if str(_plugin_root) not in sys.path:
    sys.path.insert(0, str(_plugin_root))

from src.core.project import find_project_root
from src.db import memory as mem_db
from src.db.connection import get_connection
from src.db.schema import migrate, CURRENT_VERSION


def _read_index(index_md: Path) -> str:
    try:
        return index_md.read_text().strip()
    except OSError:
        return "(INDEX.md não encontrado)"


def _get_active_tasks(conn) -> list[dict]:
    rows = conn.execute(
        "SELECT slug, title, status FROM tasks WHERE status != 'closed' ORDER BY id"
    ).fetchall()
    return [{"slug": r[0], "title": r[1], "status": r[2]} for r in rows]


def _get_recent_memories(conn) -> dict[str, list[mem_db.Memory]]:
    result: dict[str, list[mem_db.Memory]] = {}
    for mem_type in ("decision", "pattern", "constraint"):
        rows = mem_db.list_all(conn, type=mem_type)
        if rows:
            result[mem_type] = rows[-5:]  # últimas 5 por tipo
    return result


def main() -> None:
    root = find_project_root()
    if root is None:
        sys.exit(0)

    specify_dir = root / ".specify"
    if not specify_dir.exists():
        sys.exit(0)

    db_path = specify_dir / "specify.db"
    index_md = specify_dir / "INDEX.md"

    if not db_path.exists():
        print(
            f"## Specify — aviso\n\n"
            f"`.specify/` encontrado em `{root}` mas banco não inicializado.\n"
            f"Execute `specify init` para inicializar."
        )
        sys.exit(0)

    try:
        conn = get_connection(db_path)
        migrate(conn)
    except Exception as e:
        # falha silenciosa — não bloquear a sessão
        sys.exit(0)

    lines: list[str] = [f"## Specify Context — `{root.name}`\n"]

    # INDEX.md
    lines.append("### Stack (INDEX.md)\n")
    lines.append(_read_index(index_md))
    lines.append("")

    # Tasks ativas
    tasks = _get_active_tasks(conn)
    if tasks:
        lines.append("### Active Tasks\n")
        for t in tasks:
            lines.append(f"- `{t['slug']}` [{t['status']}]: {t['title']}")
        lines.append("")

    # Memórias recentes
    memories = _get_recent_memories(conn)
    if memories:
        lines.append("### Project Memory\n")
        for mem_type, items in memories.items():
            lines.append(f"**{mem_type.capitalize()}s:**")
            for m in items:
                scope = f" ({m.scope})" if m.scope != "global" else ""
                lines.append(f"- [{m.id}]{scope} {m.content}")
        lines.append("")

    lines.append("---")
    lines.append('Use `specify memory search "<query>"` para busca semântica.')
    if tasks:
        lines.append("Use `specify task list` para ver todas as tasks.")

    conn.close()
    print("\n".join(lines))


if __name__ == "__main__":
    main()
