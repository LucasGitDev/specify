from __future__ import annotations

import sys
from pathlib import Path

import click

from src.core.project import get_project_paths

_VALID_ARTIFACTS = ["spec", "plan", "sdd.log", "review", "result"]


def _artifact_path(tasks_dir: Path, slug: str, artifact: str) -> Path:
    ext = "" if "." in artifact else ".md"
    return tasks_dir / slug / f"{artifact}{ext}"


@click.group("artifact")
def cmd_artifact() -> None:
    """Gerencia artefatos de tasks (.specify/tasks/<slug>/)."""


@cmd_artifact.command("save")
@click.option("--task", "slug", required=True, help="Slug da task")
@click.option(
    "--type",
    "artifact",
    required=True,
    type=click.Choice(_VALID_ARTIFACTS),
    help="Tipo do artefato",
)
@click.option("--content", default=None, help="Conteúdo (se omitido, lê de stdin)")
def cmd_save(slug: str, artifact: str, content: str | None) -> None:
    """Salva um artefato de task em .specify/tasks/<slug>/."""
    paths = get_project_paths()
    if not paths.specify_dir.exists():
        raise click.ClickException(
            ".specify/ não inicializado. Execute `specify init` primeiro."
        )

    task_dir = paths.tasks_dir / slug
    task_dir.mkdir(parents=True, exist_ok=True)

    if content is None:
        if sys.stdin.isatty():
            raise click.ClickException(
                "Forneça --content ou passe o conteúdo via stdin."
            )
        content = sys.stdin.read()

    dest = _artifact_path(paths.tasks_dir, slug, artifact)
    dest.write_text(content)
    click.echo(f"✓ {dest.relative_to(paths.specify_dir.parent)} salvo")


@cmd_artifact.command("show")
@click.option("--task", "slug", required=True, help="Slug da task")
@click.option(
    "--type",
    "artifact",
    required=True,
    type=click.Choice(_VALID_ARTIFACTS),
)
def cmd_show(slug: str, artifact: str) -> None:
    """Exibe o conteúdo de um artefato."""
    paths = get_project_paths()
    dest = _artifact_path(paths.tasks_dir, slug, artifact)
    if not dest.exists():
        raise click.ClickException(f"{dest.name} não encontrado para task '{slug}'")
    click.echo(dest.read_text())


@cmd_artifact.command("list")
@click.option("--task", "slug", required=True, help="Slug da task")
def cmd_list(slug: str) -> None:
    """Lista artefatos existentes de uma task."""
    paths = get_project_paths()
    task_dir = paths.tasks_dir / slug
    if not task_dir.exists():
        raise click.ClickException(f"task '{slug}' não encontrada em .specify/tasks/")
    files = sorted(task_dir.iterdir())
    if not files:
        click.echo("nenhum artefato encontrado")
        return
    for f in files:
        size = f.stat().st_size
        click.echo(f"  {f.name}  ({size}B)")
