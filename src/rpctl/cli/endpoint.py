"""rpctl endpoint — manage serverless endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import typer
from rich.console import Console

from rpctl.errors import RpctlError
from rpctl.output.formatter import output

if TYPE_CHECKING:
    from rpctl.services.endpoint_service import EndpointService

app = typer.Typer(no_args_is_help=True)
err_console = Console(stderr=True)


def _get_endpoint_service(ctx: typer.Context) -> EndpointService:
    from rpctl.api.rest_client import RestClient
    from rpctl.config.settings import Settings
    from rpctl.services.endpoint_service import EndpointService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = RestClient(settings.api_key)
    return EndpointService(client)


@app.command()
def create(
    ctx: typer.Context,
    preset: str | None = typer.Option(None, "--preset", help="Load preset as base values"),
    save_preset: str | None = typer.Option(
        None,
        "--save-preset",
        help="Save params as a preset",
    ),
    name: str | None = typer.Option(None, help="Endpoint name"),
    template: str | None = typer.Option(None, help="Template ID"),
    gpu: str | None = typer.Option(None, help="GPU category ID (default: AMPERE_24)"),
    gpu_count: int | None = typer.Option(None, help="GPUs per worker (default: 1)"),
    workers_min: int | None = typer.Option(None, help="Minimum workers (default: 0)"),
    workers_max: int | None = typer.Option(None, help="Maximum workers (default: 3)"),
    idle_timeout: int | None = typer.Option(None, help="Idle timeout in seconds (default: 5)"),
    scaler_type: str | None = typer.Option(None, help="QUEUE_DELAY or REQUEST_COUNT"),
    scaler_value: int | None = typer.Option(None, help="Scaler parameter (default: 4)"),
    network_volume: str | None = typer.Option(None, help="Network volume ID"),
    flashboot: bool = typer.Option(False, help="Enable flashboot"),
    locations: str | None = typer.Option(None, help="Datacenter locations (comma-sep)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show params without creating"),
) -> None:
    """Create a new serverless endpoint."""
    from rpctl.models.endpoint import EndpointCreateParams

    # Step 1: Load preset base values if provided
    base_params: dict[str, Any] = {}
    if preset:
        from rpctl.services.preset_service import PresetService

        preset_svc = PresetService()
        loaded = preset_svc.load(preset)
        if loaded.metadata.resource_type != "endpoint":
            err_console.print(
                f"[red]Preset '{preset}' is a {loaded.metadata.resource_type} "
                f"preset, not endpoint.[/red]",
            )
            raise typer.Exit(code=1)
        base_params = dict(loaded.params)

    # Step 2: Build CLI overrides
    cli_overrides: dict[str, Any] = {}
    if name is not None:
        cli_overrides["name"] = name
    if template is not None:
        cli_overrides["template_id"] = template
    if gpu is not None:
        cli_overrides["gpu_ids"] = gpu
    if gpu_count is not None:
        cli_overrides["gpu_count"] = gpu_count
    if workers_min is not None:
        cli_overrides["workers_min"] = workers_min
    if workers_max is not None:
        cli_overrides["workers_max"] = workers_max
    if idle_timeout is not None:
        cli_overrides["idle_timeout"] = idle_timeout
    if scaler_type is not None:
        cli_overrides["scaler_type"] = scaler_type
    if scaler_value is not None:
        cli_overrides["scaler_value"] = scaler_value
    if network_volume is not None:
        cli_overrides["network_volume_id"] = network_volume
    if flashboot:
        cli_overrides["flashboot"] = True
    if locations is not None:
        cli_overrides["locations"] = locations

    # Step 3: Merge
    from rpctl.services.preset_service import PresetService

    merged = PresetService.merge_preset_with_overrides(base_params, cli_overrides)

    # Validate required fields
    if not merged.get("name"):
        err_console.print(
            "[red]--name is required (or use a preset that includes it).[/red]",
        )
        raise typer.Exit(code=1)
    if not merged.get("template_id"):
        err_console.print(
            "[red]--template is required (or use a preset that includes it).[/red]",
        )
        raise typer.Exit(code=1)

    # Fill defaults for missing optional fields
    defaults = EndpointCreateParams(
        name=merged["name"],
        template_id=merged["template_id"],
    ).model_dump()
    for key, value in defaults.items():
        if key not in merged:
            merged[key] = value

    params = EndpointCreateParams(**merged)
    fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"

    # Step 4: Save preset if requested
    if save_preset:
        from rpctl.models.preset import Preset, PresetMetadata

        preset_svc = PresetService()
        to_save = Preset(
            metadata=PresetMetadata(
                name=save_preset,
                resource_type="endpoint",
                source="cli",
            ),
            params=params.model_dump(exclude_none=True),
        )
        path = preset_svc.save(to_save, overwrite=True)
        Console().print(f"[green]Preset '{save_preset}' saved to {path}[/green]")

    # Step 5: Dry run or create
    if dry_run:
        output(params, output_format=fmt, table_type="endpoint_create_dry_run")
        return

    try:
        svc = _get_endpoint_service(ctx)
        endpoint = svc.create_endpoint(params)
        output(endpoint, output_format=fmt, table_type="endpoint_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command("list")
def list_endpoints(ctx: typer.Context) -> None:
    """List all serverless endpoints."""
    try:
        svc = _get_endpoint_service(ctx)
        endpoints = svc.list_endpoints()
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(endpoints, output_format=fmt, table_type="endpoint_list")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def get(
    ctx: typer.Context,
    endpoint_id: str = typer.Argument(help="Endpoint ID"),
) -> None:
    """Get endpoint details."""
    try:
        svc = _get_endpoint_service(ctx)
        endpoint = svc.get_endpoint(endpoint_id)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(endpoint, output_format=fmt, table_type="endpoint_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def update(
    ctx: typer.Context,
    endpoint_id: str = typer.Argument(help="Endpoint ID"),
    workers_min: int | None = typer.Option(None, help="Minimum workers"),
    workers_max: int | None = typer.Option(None, help="Maximum workers"),
    idle_timeout: int | None = typer.Option(None, help="Idle timeout in seconds"),
    scaler_type: str | None = typer.Option(None, help="QUEUE_DELAY or REQUEST_COUNT"),
    scaler_value: int | None = typer.Option(None, help="Scaler parameter"),
) -> None:
    """Update an existing endpoint."""
    kwargs: dict[str, Any] = {}
    if workers_min is not None:
        kwargs["workers_min"] = workers_min
    if workers_max is not None:
        kwargs["workers_max"] = workers_max
    if idle_timeout is not None:
        kwargs["idle_timeout"] = idle_timeout
    if scaler_type is not None:
        kwargs["scaler_type"] = scaler_type
    if scaler_value is not None:
        kwargs["scaler_value"] = scaler_value

    if not kwargs:
        err_console.print("[yellow]No update parameters provided.[/yellow]")
        raise typer.Exit(code=1)

    try:
        svc = _get_endpoint_service(ctx)
        endpoint = svc.update_endpoint(endpoint_id, **kwargs)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(endpoint, output_format=fmt, table_type="endpoint_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def delete(
    ctx: typer.Context,
    endpoint_id: str = typer.Argument(help="Endpoint ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
) -> None:
    """Delete a serverless endpoint."""
    if not confirm:
        typer.confirm(f"Delete endpoint {endpoint_id}?", abort=True)

    try:
        svc = _get_endpoint_service(ctx)
        svc.delete_endpoint(endpoint_id)
        Console().print(f"[green]Endpoint {endpoint_id} deleted.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None
