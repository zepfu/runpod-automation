"""rpctl preset — manage saved presets."""

from __future__ import annotations

import typer
from rich.console import Console

from rpctl.errors import PresetError, RpctlError
from rpctl.output.formatter import output

app = typer.Typer(no_args_is_help=True)
err_console = Console(stderr=True)


def _get_preset_service(presets_dir=None):
    from rpctl.services.preset_service import PresetService

    return PresetService(presets_dir=presets_dir)


def _get_pod_service(ctx: typer.Context):
    from rpctl.api.rest_client import RestClient
    from rpctl.config.settings import Settings
    from rpctl.services.pod_service import PodService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = RestClient(settings.api_key)
    return PodService(client)


def _get_endpoint_service(ctx: typer.Context):
    from rpctl.api.rest_client import RestClient
    from rpctl.config.settings import Settings
    from rpctl.services.endpoint_service import EndpointService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = RestClient(settings.api_key)
    return EndpointService(client)


@app.command()
def save(
    ctx: typer.Context,
    name: str = typer.Argument(help="Preset name"),
    resource_type: str = typer.Option(
        "pod",
        "--type",
        "-t",
        help="Resource type: pod or endpoint",
    ),
    description: str = typer.Option("", "--description", "-d", help="Preset description"),
    from_pod: str | None = typer.Option(
        None,
        "--from-pod",
        help="Capture config from existing pod ID",
    ),
    from_endpoint: str | None = typer.Option(
        None,
        "--from-endpoint",
        help="Capture config from existing endpoint ID",
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing preset"),
    # Pod params (all optional for manual preset building)
    image: str | None = typer.Option(None, "--image", help="Container image"),
    gpu: list[str] = typer.Option([], "--gpu", help="GPU type ID(s) [repeatable]"),
    gpu_count: int | None = typer.Option(None, "--gpu-count", help="Number of GPUs"),
    cloud_type: str | None = typer.Option(None, "--cloud-type", help="SECURE or COMMUNITY"),
    workers_min: int | None = typer.Option(None, "--workers-min", help="Minimum workers"),
    workers_max: int | None = typer.Option(None, "--workers-max", help="Maximum workers"),
    template_id: str | None = typer.Option(None, "--template", help="Template ID"),
) -> None:
    """Save a new preset from CLI args or an existing resource."""
    from rpctl.models.preset import Preset, PresetMetadata
    from rpctl.services.preset_service import PresetService

    if from_pod and from_endpoint:
        err_console.print("[red]Cannot use both --from-pod and --from-endpoint.[/red]")
        raise typer.Exit(code=1)

    svc = _get_preset_service()
    params: dict = {}
    source = "cli"

    if from_pod:
        try:
            pod_svc = _get_pod_service(ctx)
            pod = pod_svc.get_pod(from_pod)
            params = PresetService.params_from_pod(pod)
            resource_type = "pod"
            source = f"from-pod:{from_pod}"
        except RpctlError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=e.exit_code) from None

    elif from_endpoint:
        try:
            ep_svc = _get_endpoint_service(ctx)
            endpoint = ep_svc.get_endpoint(from_endpoint)
            params = PresetService.params_from_endpoint(endpoint)
            resource_type = "endpoint"
            source = f"from-endpoint:{from_endpoint}"
        except RpctlError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=e.exit_code) from None

    # Apply CLI overrides on top of extracted params
    cli_overrides: dict = {}
    if image is not None:
        cli_overrides["image_name"] = image
    if gpu:
        cli_overrides["gpu_type_ids"] = gpu
    if gpu_count is not None:
        cli_overrides["gpu_count"] = gpu_count
    if cloud_type is not None:
        cli_overrides["cloud_type"] = cloud_type.upper()
    if workers_min is not None:
        cli_overrides["workers_min"] = workers_min
    if workers_max is not None:
        cli_overrides["workers_max"] = workers_max
    if template_id is not None:
        cli_overrides["template_id"] = template_id

    params = PresetService.merge_preset_with_overrides(params, cli_overrides)

    if not params:
        err_console.print(
            "[red]No parameters provided. "
            "Use --from-pod, --from-endpoint, or specify options.[/red]",
        )
        raise typer.Exit(code=1)

    if resource_type not in ("pod", "endpoint"):
        err_console.print(
            f"[red]Invalid resource type '{resource_type}'. Use 'pod' or 'endpoint'.[/red]",
        )
        raise typer.Exit(code=1)

    preset = Preset(
        metadata=PresetMetadata(
            name=name,
            resource_type=resource_type,
            description=description,
            source=source,
        ),
        params=params,
    )

    try:
        path = svc.save(preset, overwrite=overwrite)
        Console().print(f"[green]Preset '{name}' saved to {path}[/green]")
    except PresetError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command("list")
def list_presets(ctx: typer.Context) -> None:
    """List all saved presets."""
    svc = _get_preset_service()
    presets = svc.list_presets()
    fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
    output(presets, output_format=fmt, table_type="preset_list")


@app.command()
def show(
    ctx: typer.Context,
    name: str = typer.Argument(help="Preset name"),
) -> None:
    """Show full details of a preset."""
    try:
        svc = _get_preset_service()
        preset = svc.load(name)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(preset, output_format=fmt, table_type="preset_detail")
    except PresetError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def delete(
    ctx: typer.Context,
    name: str = typer.Argument(help="Preset name"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
) -> None:
    """Delete a saved preset."""
    if not confirm:
        typer.confirm(f"Delete preset '{name}'?", abort=True)

    try:
        svc = _get_preset_service()
        svc.delete(name)
        Console().print(f"[green]Preset '{name}' deleted.[/green]")
    except PresetError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def apply(
    ctx: typer.Context,
    name: str = typer.Argument(help="Preset name to apply"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show params without creating"),
    # Common overrides
    pod_name: str | None = typer.Option(None, "--name", help="Override resource name"),
    gpu_count: int | None = typer.Option(None, "--gpu-count", help="Override GPU count"),
    workers_max: int | None = typer.Option(None, "--workers-max", help="Override max workers"),
) -> None:
    """Create a resource from a saved preset."""
    try:
        svc = _get_preset_service()
        preset = svc.load(name)
    except PresetError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None

    # Build overrides
    from rpctl.services.preset_service import PresetService

    cli_overrides: dict = {}
    if pod_name is not None:
        cli_overrides["name"] = pod_name
    if gpu_count is not None:
        cli_overrides["gpu_count"] = gpu_count
    if workers_max is not None:
        cli_overrides["workers_max"] = workers_max

    merged = PresetService.merge_preset_with_overrides(preset.params, cli_overrides)
    rtype = preset.metadata.resource_type

    fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"

    if rtype == "pod":
        from rpctl.models.pod import PodCreateParams

        params = PodCreateParams(**merged)
        if dry_run:
            output(params, output_format=fmt, table_type="pod_create_dry_run")
            return
        try:
            pod_svc = _get_pod_service(ctx)
            pod = pod_svc.create_pod(params)
            output(pod, output_format=fmt, table_type="pod_detail")
        except RpctlError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=e.exit_code) from None

    elif rtype == "endpoint":
        from rpctl.models.endpoint import EndpointCreateParams

        params = EndpointCreateParams(**merged)
        if dry_run:
            output(params, output_format=fmt, table_type="endpoint_create_dry_run")
            return
        try:
            ep_svc = _get_endpoint_service(ctx)
            endpoint = ep_svc.create_endpoint(params)
            output(endpoint, output_format=fmt, table_type="endpoint_detail")
        except RpctlError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=e.exit_code) from None

    else:
        err_console.print(f"[red]Unknown resource type '{rtype}' in preset.[/red]")
        raise typer.Exit(code=1)
