"""rpctl secret — manage environment secrets."""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from rich.console import Console

from rpctl.errors import RpctlError
from rpctl.output.formatter import output

if TYPE_CHECKING:
    from rpctl.services.secret_service import SecretService

app = typer.Typer(no_args_is_help=True)
err_console = Console(stderr=True)


def _get_secret_service(ctx: typer.Context) -> SecretService:
    from rpctl.api.rest_client import RestClient
    from rpctl.config.settings import Settings
    from rpctl.services.secret_service import SecretService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = RestClient(settings.api_key)
    return SecretService(client)


@app.command("list")
def list_secrets(
    ctx: typer.Context,
    reveal: bool = typer.Option(False, "--reveal", help="Show secret values (default: masked)"),
) -> None:
    """List all environment secrets."""
    try:
        svc = _get_secret_service(ctx)
        secrets = svc.list_secrets()
        if not reveal:
            secrets = [{"name": s["name"], "value": "***"} for s in secrets]
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(secrets, output_format=fmt, table_type="secret_list")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command("set")
def set_secret(
    ctx: typer.Context,
    name: str = typer.Argument(help="Secret name"),
    value: str = typer.Argument(help="Secret value"),
) -> None:
    """Create or update an environment secret."""
    try:
        svc = _get_secret_service(ctx)
        svc.set_secret(name, value)
        Console().print(f"[green]Secret '{name}' saved.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def delete(
    ctx: typer.Context,
    name: str = typer.Argument(help="Secret name to delete"),
) -> None:
    """Delete an environment secret."""
    try:
        svc = _get_secret_service(ctx)
        svc.delete_secret(name)
        Console().print(f"[green]Secret '{name}' deleted.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None
