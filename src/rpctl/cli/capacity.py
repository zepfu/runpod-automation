"""rpctl capacity — query GPU/CPU availability and pricing."""

from __future__ import annotations

import typer

from rpctl.config.settings import Settings
from rpctl.errors import RpctlError
from rpctl.output.formatter import output

app = typer.Typer(no_args_is_help=True)


def _get_capacity_service(ctx: typer.Context):
    from rpctl.api.graphql_client import GraphQLClient
    from rpctl.services.capacity_service import CapacityService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = GraphQLClient(settings.api_key)
    return CapacityService(client)


@app.command("list")
def list_gpus(
    ctx: typer.Context,
    cloud_type: str = typer.Option("all", help="Filter: secure, community, or all"),
    min_vram: int | None = typer.Option(None, help="Minimum VRAM in GB"),
    available_only: bool = typer.Option(False, help="Only show GPUs with stock"),
    sort_by: str = typer.Option("price", help="Sort by: price, vram, name, availability"),
) -> None:
    """List all GPU types with pricing and availability."""
    try:
        svc = _get_capacity_service(ctx)
        gpu_types = svc.list_gpu_types(
            cloud_type=cloud_type,
            min_vram=min_vram,
            available_only=available_only,
            sort_by=sort_by,
        )
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(gpu_types, output_format=fmt, table_type="gpu_list")
    except RpctlError as e:
        from rich.console import Console

        Console(stderr=True).print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def check(
    ctx: typer.Context,
    gpu: str = typer.Option(..., help="GPU type ID (e.g., 'NVIDIA GeForce RTX 4090')"),
    gpu_count: int = typer.Option(1, help="Number of GPUs needed"),
    cloud_type: str = typer.Option("secure", help="secure or community"),
) -> None:
    """Check availability for a specific GPU across regions."""
    try:
        svc = _get_capacity_service(ctx)
        availability = svc.check_gpu(
            gpu_type=gpu,
            gpu_count=gpu_count,
            cloud_type=cloud_type,
        )
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(availability, output_format=fmt, table_type="gpu_check")
    except RpctlError as e:
        from rich.console import Console

        Console(stderr=True).print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def regions(
    ctx: typer.Context,
    gpu: str | None = typer.Option(None, help="Filter regions by GPU availability"),
) -> None:
    """List all datacenters with GPU availability."""
    try:
        svc = _get_capacity_service(ctx)
        datacenters = svc.list_regions(gpu_filter=gpu)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(datacenters, output_format=fmt, table_type="regions")
    except RpctlError as e:
        from rich.console import Console

        Console(stderr=True).print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def compare(
    ctx: typer.Context,
    gpus: list[str] = typer.Argument(help="GPU type IDs to compare (2 or more)"),
    cloud_type: str = typer.Option("all", help="Filter: secure, community, or all"),
) -> None:
    """Compare GPUs side-by-side on pricing and availability."""
    if len(gpus) < 2:
        from rich.console import Console

        Console(stderr=True).print("[red]Provide at least 2 GPU types to compare.[/red]")
        raise typer.Exit(code=1)

    try:
        svc = _get_capacity_service(ctx)
        all_types = svc.list_gpu_types(cloud_type=cloud_type)
        gpu_lower = [g.lower() for g in gpus]
        matched = [
            gt
            for gt in all_types
            if gt.id.lower() in gpu_lower or gt.display_name.lower() in gpu_lower
        ]

        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(matched, output_format=fmt, table_type="gpu_compare")
    except RpctlError as e:
        from rich.console import Console

        Console(stderr=True).print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None
