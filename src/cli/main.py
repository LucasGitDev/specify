import sys

import click

from src.cli.cmd_artifact import cmd_artifact
from src.cli.cmd_gate import cmd_gate
from src.cli.cmd_init import cmd_init
from src.cli.cmd_log import cmd_log
from src.cli.cmd_memory import cmd_memory
from src.cli.cmd_task import cmd_task
from src.core.logger import get_logger


@click.group()
@click.pass_context
def cli(ctx: click.Context) -> None:
    """specify — SDD + TDD + Agentic SDLC framework."""
    ctx.ensure_object(dict)
    get_logger().debug("command: %s", " ".join(sys.argv[1:]))


cli.add_command(cmd_init)
cli.add_command(cmd_memory)
cli.add_command(cmd_task)
cli.add_command(cmd_gate)
cli.add_command(cmd_artifact)
cli.add_command(cmd_log)
