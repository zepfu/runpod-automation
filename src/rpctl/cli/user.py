"""rpctl user — manage account settings."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from rpctl.errors import RpctlError
from rpctl.output.formatter import output

if TYPE_CHECKING:
    from rpctl.services.user_service import UserService

app = typer.Typer(no_args_is_help=True)
err_console = Console(stderr=True)


def _get_user_service(ctx: typer.Context) -> UserService:
    from rpctl.api.rest_client import RestClient
    from rpctl.config.settings import Settings
    from rpctl.services.user_service import UserService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = RestClient(settings.api_key)
    return UserService(client)


@app.command()
def info(ctx: typer.Context) -> None:
    """Show account info (ID, SSH key, network volumes)."""
    try:
        svc = _get_user_service(ctx)
        data = svc.get_info()
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(data, output_format=fmt, table_type="user_info")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command("set-ssh-key")
def set_ssh_key(
    ctx: typer.Context,
    key_file: str = typer.Option(
        None, "--key", "-k", help="Path to public key file (default: ~/.ssh/id_ed25519.pub)"
    ),
    key_text: str = typer.Option(None, "--text", "-t", help="SSH public key as text"),
) -> None:
    """Upload or update your SSH public key on RunPod."""
    if key_text:
        pubkey = key_text
    elif key_file:
        path = Path(key_file).expanduser()
        if not path.exists():
            err_console.print(f"[red]Key file not found: {path}[/red]")
            raise typer.Exit(code=1)
        pubkey = path.read_text().strip()
    else:
        # Default: try common key paths
        for default_key in ["~/.ssh/id_ed25519.pub", "~/.ssh/id_rsa.pub"]:
            path = Path(default_key).expanduser()
            if path.exists():
                pubkey = path.read_text().strip()
                Console().print(f"[dim]Using key: {path}[/dim]")
                break
        else:
            err_console.print("[red]No SSH key found. Use --key or --text to specify one.[/red]")
            raise typer.Exit(code=1)

    try:
        svc = _get_user_service(ctx)
        svc.set_ssh_key(pubkey)
        Console().print("[green]SSH public key updated.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None
