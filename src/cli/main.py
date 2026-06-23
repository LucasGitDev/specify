import click

from src.cli.cmd_init import cmd_init
from src.cli.cmd_memory import cmd_memory


@click.group()
def cli() -> None:
    """specify — SDD + TDD + Agentic SDLC framework."""


cli.add_command(cmd_init)
cli.add_command(cmd_memory)
