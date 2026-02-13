"""rpctl volume — manage network volumes."""

from __future__ import annotations

import typer
from rich.console import Console

from rpctl.errors import RpctlError
from rpctl.output.formatter import output

app = typer.Typer(no_args_is_help=True)
err_console = Console(stderr=True)


def _get_volume_service(ctx: typer.Context):
    from rpctl.api.rest_client import RestClient
    from rpctl.config.settings import Settings
    from rpctl.services.volume_service import VolumeService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = RestClient(settings.api_key)
    return VolumeService(client)


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Option(..., help="Volume name"),
    size: int = typer.Option(..., help="Size in GB (0-4000)"),
    region: str = typer.Option(..., help="Datacenter ID (e.g., US-TX-3)"),
) -> None:
    """Create a new network volume."""
    if size < 0 or size > 4000:
        err_console.print("[red]Size must be between 0 and 4000 GB.[/red]")
        raise typer.Exit(code=1)

    try:
        svc = _get_volume_service(ctx)
        volume = svc.create_volume(name=name, size_gb=size, data_center_id=region)
        json_mode = ctx.obj.get("json", False) if ctx.obj else False
        output(volume, json_mode=json_mode, table_type="volume_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command("list")
def list_volumes(ctx: typer.Context) -> None:
    """List all network volumes."""
    try:
        svc = _get_volume_service(ctx)
        volumes = svc.list_volumes()
        json_mode = ctx.obj.get("json", False) if ctx.obj else False
        output(volumes, json_mode=json_mode, table_type="volume_list")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def get(
    ctx: typer.Context,
    volume_id: str = typer.Argument(help="Volume ID"),
) -> None:
    """Get volume details."""
    try:
        svc = _get_volume_service(ctx)
        volume = svc.get_volume(volume_id)
        json_mode = ctx.obj.get("json", False) if ctx.obj else False
        output(volume, json_mode=json_mode, table_type="volume_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def update(
    ctx: typer.Context,
    volume_id: str = typer.Argument(help="Volume ID"),
    name: str | None = typer.Option(None, help="New name"),
    size: int | None = typer.Option(None, help="New size in GB"),
) -> None:
    """Update a network volume."""
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if size is not None:
        kwargs["size"] = size

    if not kwargs:
        err_console.print("[yellow]No update parameters provided.[/yellow]")
        raise typer.Exit(code=1)

    try:
        svc = _get_volume_service(ctx)
        volume = svc.update_volume(volume_id, **kwargs)
        json_mode = ctx.obj.get("json", False) if ctx.obj else False
        output(volume, json_mode=json_mode, table_type="volume_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def delete(
    ctx: typer.Context,
    volume_id: str = typer.Argument(help="Volume ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
) -> None:
    """Delete a network volume."""
    if not confirm:
        typer.confirm(f"Delete volume {volume_id}? All data will be lost", abort=True)

    try:
        svc = _get_volume_service(ctx)
        svc.delete_volume(volume_id)
        Console().print(f"[green]Volume {volume_id} deleted.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None
