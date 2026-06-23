import click

from src.cli.cmd_gate import cmd_gate
from src.cli.cmd_init import cmd_init
from src.cli.cmd_memory import cmd_memory
from src.cli.cmd_task import cmd_task


@click.group()
def cli() -> None:
    """specify — SDD + TDD + Agentic SDLC framework."""


cli.add_command(cmd_init)
cli.add_command(cmd_memory)
cli.add_command(cmd_task)
cli.add_command(cmd_gate)
