"""rpctl pod — manage GPU/CPU pods."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import typer
from rich.console import Console

from rpctl.errors import RpctlError
from rpctl.output.formatter import output

if TYPE_CHECKING:
    from rpctl.services.pod_service import PodService

app = typer.Typer(no_args_is_help=True)
err_console = Console(stderr=True)


def _get_pod_service(ctx: typer.Context) -> PodService:
    from rpctl.api.rest_client import RestClient
    from rpctl.config.settings import Settings
    from rpctl.services.pod_service import PodService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = RestClient(settings.api_key)
    return PodService(client)


def _parse_env(env_list: list[str] | None) -> dict[str, str]:
    """Parse KEY=VALUE pairs into a dict."""
    if not env_list:
        return {}
    result = {}
    for item in env_list:
        if "=" not in item:
            err_console.print(f"[red]Invalid env format: '{item}'. Use KEY=VALUE.[/red]")
            raise typer.Exit(code=1)
        key, _, value = item.partition("=")
        result[key] = value
    return result


@app.command()
def create(
    ctx: typer.Context,
    preset: str | None = typer.Option(None, "--preset", help="Load preset as base values"),
    save_preset: str | None = typer.Option(
        None,
        "--save-preset",
        help="Save params as a preset",
    ),
    name: str | None = typer.Option(None, help="Pod name (default: rpctl-pod)"),
    image: str | None = typer.Option(None, help="Container image"),
    gpu: list[str] = typer.Option([], help="GPU type ID(s) [repeatable]"),
    gpu_count: int | None = typer.Option(None, help="Number of GPUs (default: 1)"),
    cpu: list[str] = typer.Option(
        [],
        help="CPU flavor ID(s) for CPU pods [repeatable]",
    ),
    cloud_type: str | None = typer.Option(None, help="SECURE or COMMUNITY"),
    container_disk: int | None = typer.Option(None, help="Container disk in GB (default: 50)"),
    volume_disk: int | None = typer.Option(None, help="Persistent volume in GB (default: 20)"),
    volume_mount: str | None = typer.Option(None, help="Volume mount path"),
    network_volume: str | None = typer.Option(None, help="Network volume ID"),
    ports: str | None = typer.Option(None, help="Ports to expose"),
    env: list[str] = typer.Option(
        [],
        help="Environment variables (KEY=VALUE) [repeatable]",
    ),
    template: str | None = typer.Option(None, help="Template ID"),
    spot: bool = typer.Option(False, help="Use spot/interruptible pricing"),
    region: list[str] = typer.Option([], help="Datacenter IDs [repeatable]"),
    min_vcpu: int | None = typer.Option(None, help="Min vCPUs per GPU (default: 2)"),
    min_ram: int | None = typer.Option(None, help="Min RAM per GPU in GB (default: 8)"),
    docker_start_cmd: str | None = typer.Option(
        None, "--docker-start-cmd", help="Docker start command (e.g., 'python handler.py')"
    ),
    entrypoint: str | None = typer.Option(None, "--entrypoint", help="Docker entrypoint override"),
    public_ip: bool = typer.Option(False, "--public-ip", help="Request a public IP address"),
    cuda_versions: list[str] = typer.Option(
        [], "--cuda-version", help="Allowed CUDA versions [repeatable]"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show params without creating"),
) -> None:
    """Create a new GPU/CPU pod."""
    from rpctl.models.pod import PodCreateParams

    # Step 1: Load preset base values if provided
    base_params: dict[str, Any] = {}
    if preset:
        from rpctl.services.preset_service import PresetService

        preset_svc = PresetService()
        loaded = preset_svc.load(preset)
        if loaded.metadata.resource_type != "pod":
            err_console.print(
                f"[red]Preset '{preset}' is a {loaded.metadata.resource_type} "
                f"preset, not pod.[/red]",
            )
            raise typer.Exit(code=1)
        base_params = dict(loaded.params)

    # Step 2: Build CLI overrides (only non-None / non-empty values)
    cli_overrides: dict[str, Any] = {}
    if name is not None:
        cli_overrides["name"] = name
    if image is not None:
        cli_overrides["image_name"] = image
    if gpu:
        cli_overrides["gpu_type_ids"] = gpu
    if gpu_count is not None:
        cli_overrides["gpu_count"] = gpu_count
    if cpu:
        cli_overrides["cpu_flavor_ids"] = cpu
        cli_overrides["compute_type"] = "CPU"
    if cloud_type is not None:
        cli_overrides["cloud_type"] = cloud_type.upper()
    if container_disk is not None:
        cli_overrides["container_disk_in_gb"] = container_disk
    if volume_disk is not None:
        cli_overrides["volume_in_gb"] = volume_disk
    if volume_mount is not None:
        cli_overrides["volume_mount_path"] = volume_mount
    if network_volume is not None:
        cli_overrides["network_volume_id"] = network_volume
    if ports is not None:
        cli_overrides["ports"] = ports
    env_dict = _parse_env(env)
    if env_dict:
        cli_overrides["env"] = env_dict
    if template is not None:
        cli_overrides["template_id"] = template
    if spot:
        cli_overrides["interruptible"] = True
    if region:
        cli_overrides["data_center_ids"] = region
    if min_vcpu is not None:
        cli_overrides["min_vcpu_per_gpu"] = min_vcpu
    if min_ram is not None:
        cli_overrides["min_ram_per_gpu"] = min_ram
    if docker_start_cmd is not None:
        cli_overrides["docker_start_cmd"] = docker_start_cmd
    if entrypoint is not None:
        cli_overrides["docker_entrypoint"] = entrypoint
    if public_ip:
        cli_overrides["support_public_ip"] = True
    if cuda_versions:
        cli_overrides["allowed_cuda_versions"] = cuda_versions

    # Step 3: Merge preset + overrides, fill defaults
    from rpctl.services.preset_service import PresetService

    merged = PresetService.merge_preset_with_overrides(base_params, cli_overrides)

    # Validate required fields
    if not merged.get("image_name"):
        err_console.print(
            "[red]--image is required (or use a preset that includes it).[/red]",
        )
        raise typer.Exit(code=1)

    # Fill defaults for missing optional fields
    defaults = PodCreateParams(image_name=merged["image_name"]).model_dump()
    for key, value in defaults.items():
        if key not in merged:
            merged[key] = value

    params = PodCreateParams(**merged)
    fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"

    # Step 4: Save preset if requested
    if save_preset:
        from rpctl.models.preset import Preset, PresetMetadata

        preset_svc = PresetService()
        to_save = Preset(
            metadata=PresetMetadata(
                name=save_preset,
                resource_type="pod",
                source="cli",
            ),
            params=params.model_dump(exclude_none=True),
        )
        path = preset_svc.save(to_save, overwrite=True)
        Console().print(f"[green]Preset '{save_preset}' saved to {path}[/green]")

    # Step 5: Dry run or create
    if dry_run:
        output(params, output_format=fmt, table_type="pod_create_dry_run")
        return

    try:
        svc = _get_pod_service(ctx)
        pod = svc.create_pod(params)
        output(pod, output_format=fmt, table_type="pod_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command("list")
def list_pods(
    ctx: typer.Context,
    status: str = typer.Option("all", help="Filter: running, exited, or all"),
) -> None:
    """List all pods."""
    try:
        svc = _get_pod_service(ctx)
        pods = svc.list_pods(status_filter=status)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(pods, output_format=fmt, table_type="pod_list")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def get(
    ctx: typer.Context,
    pod_id: str = typer.Argument(help="Pod ID"),
) -> None:
    """Get pod details."""
    try:
        svc = _get_pod_service(ctx)
        pod = svc.get_pod(pod_id)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(pod, output_format=fmt, table_type="pod_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def start(
    ctx: typer.Context,
    pod_id: str = typer.Argument(help="Pod ID"),
) -> None:
    """Start/resume a stopped pod."""
    try:
        svc = _get_pod_service(ctx)
        svc.start_pod(pod_id)
        Console().print(f"[green]Pod {pod_id} started.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def stop(
    ctx: typer.Context,
    pod_id: str = typer.Argument(help="Pod ID"),
) -> None:
    """Stop a running pod."""
    try:
        svc = _get_pod_service(ctx)
        svc.stop_pod(pod_id)
        Console().print(f"[green]Pod {pod_id} stopped.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def restart(
    ctx: typer.Context,
    pod_id: str = typer.Argument(help="Pod ID"),
) -> None:
    """Restart a pod."""
    try:
        svc = _get_pod_service(ctx)
        svc.restart_pod(pod_id)
        Console().print(f"[green]Pod {pod_id} restarted.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def delete(
    ctx: typer.Context,
    pod_id: str = typer.Argument(help="Pod ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
) -> None:
    """Terminate and delete a pod."""
    if not confirm:
        typer.confirm(f"Delete pod {pod_id}? This cannot be undone", abort=True)

    try:
        svc = _get_pod_service(ctx)
        svc.delete_pod(pod_id)
        Console().print(f"[green]Pod {pod_id} deleted.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def wait(
    ctx: typer.Context,
    pod_id: str = typer.Argument(help="Pod ID"),
    timeout: int = typer.Option(300, help="Max seconds to wait"),
    interval: int = typer.Option(5, help="Seconds between polls"),
) -> None:
    """Wait for a pod to reach RUNNING status."""
    from rpctl.services.poll import PollTimeoutError

    try:
        svc = _get_pod_service(ctx)
        pod = svc.wait_until_running(pod_id, timeout=timeout, interval=interval)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(pod, output_format=fmt, table_type="pod_detail")
    except PollTimeoutError as e:
        err_console.print(f"[red]Timeout:[/red] {e}")
        raise typer.Exit(code=2) from None
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command("stop-all")
def stop_all(
    ctx: typer.Context,
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
    parallel: bool = typer.Option(False, "--parallel", help="Stop pods in parallel"),
    max_workers: int = typer.Option(5, "--workers", help="Max parallel workers"),
) -> None:
    """Stop all running pods."""
    try:
        svc = _get_pod_service(ctx)
        pods = svc.list_pods(status_filter="running")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None

    if not pods:
        Console().print("[yellow]No running pods to stop.[/yellow]")
        return

    if not confirm:
        typer.confirm(f"Stop {len(pods)} running pod(s)?", abort=True)

    if parallel:
        from rpctl.services.parallel import parallel_map

        result = parallel_map(lambda p: svc.stop_pod(p.id), pods, max_workers=max_workers)
        Console().print(f"[green]Stopped {len(result.succeeded)} pod(s).[/green]")
        for _item, exc in result.failed:
            err_console.print(f"[red]Failed to stop pod: {exc}[/red]")
        if result.failed:
            raise typer.Exit(code=1)
    else:
        for pod in pods:
            try:
                svc.stop_pod(pod.id)
                Console().print(f"[green]Stopped {pod.id} ({pod.name})[/green]")
            except RpctlError as e:
                err_console.print(f"[red]Failed to stop {pod.id}: {e}[/red]")


@app.command("delete-all")
def delete_all(
    ctx: typer.Context,
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
    parallel: bool = typer.Option(False, "--parallel", help="Delete pods in parallel"),
    max_workers: int = typer.Option(5, "--workers", help="Max parallel workers"),
) -> None:
    """Delete all pods. This cannot be undone."""
    try:
        svc = _get_pod_service(ctx)
        pods = svc.list_pods()
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None

    if not pods:
        Console().print("[yellow]No pods to delete.[/yellow]")
        return

    if not confirm:
        typer.confirm(
            f"Delete ALL {len(pods)} pod(s)? This cannot be undone",
            abort=True,
        )

    if parallel:
        from rpctl.services.parallel import parallel_map

        result = parallel_map(lambda p: svc.delete_pod(p.id), pods, max_workers=max_workers)
        Console().print(f"[green]Deleted {len(result.succeeded)} pod(s).[/green]")
        for _item, exc in result.failed:
            err_console.print(f"[red]Failed to delete pod: {exc}[/red]")
        if result.failed:
            raise typer.Exit(code=1)
    else:
        for pod in pods:
            try:
                svc.delete_pod(pod.id)
                Console().print(f"[green]Deleted {pod.id} ({pod.name})[/green]")
            except RpctlError as e:
                err_console.print(f"[red]Failed to delete {pod.id}: {e}[/red]")
