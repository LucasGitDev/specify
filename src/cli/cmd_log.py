from __future__ import annotations

import click

from src.core.logger import get_log_path


@click.group("log")
def cmd_log() -> None:
    """Inspeciona o log de debug (specify.log)."""


@cmd_log.command("tail")
@click.option(
    "--lines", "-n", default=50, show_default=True, help="Número de linhas a exibir"
)
def cmd_tail(lines: int) -> None:
    """Exibe as últimas N linhas do log de debug."""
    log_path = get_log_path()
    if not log_path.exists():
        click.echo("(log vazio)")
        return
    all_lines = log_path.read_text(encoding="utf-8").splitlines()
    for line in all_lines[-lines:]:
        click.echo(line)


@cmd_log.command("clear")
def cmd_clear() -> None:
    """Apaga o arquivo de log de debug."""
    log_path = get_log_path()
    if log_path.exists():
        log_path.unlink()
        click.echo(f"✓ log apagado: {log_path}")
    else:
        click.echo("(nenhum log encontrado)")
