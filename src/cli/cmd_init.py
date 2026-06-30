from pathlib import Path

import click

from src.core.lang_detector import detect
from src.core.project import find_project_root, get_project_paths
from src.db.schema import init_db

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


def _read_template(name: str) -> str:
    return (_TEMPLATES_DIR / name).read_text()


def _write_index_md(path: Path, root: Path) -> None:
    lang = detect(root)
    if lang:
        content = _read_template("index_md.template").format(
            language=lang.language,
            test_cmd=lang.test_cmd,
            lint_cmd=lang.lint_cmd,
            fmt_cmd=lang.fmt_cmd,
        )
    else:
        content = _read_template("index_md_unknown.template")
    path.write_text(content)


def _ensure_gitignore(root: Path) -> None:
    gitignore = root / ".gitignore"
    entries = ["specify.db", ".claude/worktrees/"]
    existing = gitignore.read_text() if gitignore.exists() else ""
    additions = [e for e in entries if e not in existing]
    if additions:
        with gitignore.open("a") as f:
            f.write("\n".join(additions) + "\n")


@click.command("init")
@click.option(
    "--force", is_flag=True, help="Reinicializar mesmo se .specify/ já existe"
)
def cmd_init(force: bool) -> None:
    """Inicializa .specify/ no projeto atual."""
    root = find_project_root()
    if root is None:
        raise click.ClickException("Raiz do projeto não encontrada.")

    paths = get_project_paths(root)

    if paths.specify_dir.exists() and not force:
        raise click.ClickException(
            ".specify/ já existe. Use --force para reinicializar."
        )

    paths.specify_dir.mkdir(exist_ok=True)
    paths.tasks_dir.mkdir(exist_ok=True)

    init_db(paths.db_path)

    if not paths.index_md.exists():
        _write_index_md(paths.index_md, root)

    _ensure_gitignore(root)

    lang = detect(root)
    click.echo(f"specify inicializado em {paths.specify_dir}")
    if lang:
        click.echo(f"  linguagem: {lang.language}")
        click.echo(f"  teste:     {lang.test_cmd}")
        click.echo(f"  lint:      {lang.lint_cmd}")
    else:
        click.echo("  linguagem: não detectada — edite .specify/INDEX.md")
