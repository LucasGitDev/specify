from __future__ import annotations

import threading
import time
import webbrowser

import click


@click.command("studio")
@click.option("--host", default="127.0.0.1", show_default=True)
@click.option("--port", default=7842, show_default=True)
@click.option("--no-browser", is_flag=True, default=False)
def cmd_studio(host: str, port: int, no_browser: bool) -> None:
    """Abre o specify studio — visualização interativa das memórias."""
    try:
        import uvicorn
    except ImportError:
        raise click.ClickException(
            "uvicorn não encontrado. Instale com: pip install uvicorn"
        )

    try:
        import fastapi  # noqa: F401
    except ImportError:
        raise click.ClickException(
            "fastapi não encontrado. Instale com: pip install fastapi"
        )

    url = f"http://{host}:{port}"
    click.echo(f"specify studio → {url}")

    if not no_browser:

        def _open():
            time.sleep(0.8)
            webbrowser.open(url)

        threading.Thread(target=_open, daemon=True).start()

    from src.studio.app import app

    uvicorn.run(app, host=host, port=port, log_level="warning")
