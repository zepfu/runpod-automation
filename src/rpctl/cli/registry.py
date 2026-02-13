"""rpctl registry — manage container registry authentication."""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer
from rich.console import Console

from rpctl.errors import RpctlError
from rpctl.output.formatter import output

if TYPE_CHECKING:
    from rpctl.services.registry_service import RegistryService

app = typer.Typer(no_args_is_help=True)
err_console = Console(stderr=True)


def _get_registry_service(ctx: typer.Context) -> RegistryService:
    from rpctl.api.rest_client import RestClient
    from rpctl.config.settings import Settings
    from rpctl.services.registry_service import RegistryService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = RestClient(settings.api_key)
    return RegistryService(client)


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Option(..., help="Registry auth name"),
    username: str = typer.Option(..., help="Registry username"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Registry password"),
) -> None:
    """Create container registry credentials."""
    try:
        svc = _get_registry_service(ctx)
        result = svc.create(name, username, password)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(result, output_format=fmt, table_type="registry_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def update(
    ctx: typer.Context,
    registry_auth_id: str = typer.Argument(help="Registry auth ID"),
    username: str = typer.Option(..., help="New username"),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="New password"),
) -> None:
    """Update container registry credentials."""
    try:
        svc = _get_registry_service(ctx)
        result = svc.update(registry_auth_id, username, password)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(result, output_format=fmt, table_type="registry_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def delete(
    ctx: typer.Context,
    registry_auth_id: str = typer.Argument(help="Registry auth ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
) -> None:
    """Delete container registry credentials."""
    if not confirm:
        typer.confirm(f"Delete registry auth {registry_auth_id}?", abort=True)

    try:
        svc = _get_registry_service(ctx)
        svc.delete(registry_auth_id)
        Console().print(f"[green]Registry auth {registry_auth_id} deleted.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None
