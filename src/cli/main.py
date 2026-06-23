import click

from src.cli.cmd_init import cmd_init


@click.group()
def cli() -> None:
    """specify — SDD + TDD + Agentic SDLC framework."""


cli.add_command(cmd_init)
