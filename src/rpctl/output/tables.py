"""Rich table renderers for each resource/view type."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

console = Console()


def _price_str(value: float | None) -> str:
    if value is None:
        return "-"
    return f"${value:.4f}/hr"


def _stock_style(status: str | None) -> str:
    if not status:
        return "[dim]-[/dim]"
    lower = status.lower()
    if lower == "high":
        return f"[green]{status}[/green]"
    if lower == "low":
        return f"[yellow]{status}[/yellow]"
    if lower in ("unavailable", "none"):
        return f"[red]{status}[/red]"
    return status


def _status_style(status: str) -> str:
    lower = status.lower()
    if lower in ("running", "ready"):
        return f"[green]{status}[/green]"
    if lower in ("exited", "stopped"):
        return f"[yellow]{status}[/yellow]"
    if lower in ("error", "failed"):
        return f"[red]{status}[/red]"
    return status


def _detail_table(title: str, data: BaseModel | dict[str, Any]) -> None:
    """Render any model/dict as a key-value detail table."""
    table = Table(title=title, show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    items: dict[str, Any]
    if isinstance(data, BaseModel):
        items = data.model_dump(exclude_none=True)
    elif isinstance(data, dict):
        items = data
    else:
        items = {"value": str(data)}

    for key, value in items.items():
        display_key = key.replace("_", " ").title()
        if isinstance(value, dict):
            for sub_key, sub_val in value.items():
                sub_display = f"  {sub_key.replace('_', ' ').title()}"
                table.add_row(sub_display, str(sub_val))
        elif isinstance(value, list):
            table.add_row(display_key, ", ".join(str(v) for v in value) if value else "-")
        else:
            table.add_row(display_key, str(value))

    console.print(table)


# --- GPU/Capacity tables ---


def print_gpu_list(gpu_types: list[Any]) -> None:
    """Render GPU types as a table."""
    if not gpu_types:
        console.print("[dim]No GPU types found matching filters.[/dim]")
        return

    table = Table(title="GPU Types — Pricing & Availability")
    table.add_column("GPU", style="cyan", no_wrap=True)
    table.add_column("VRAM", justify="right")
    table.add_column("Secure", justify="right")
    table.add_column("Community", justify="right")
    table.add_column("Spot (min bid)", justify="right")
    table.add_column("Stock", justify="center")
    table.add_column("Available", justify="right")

    for gpu in gpu_types:
        table.add_row(
            gpu.display_name,
            f"{gpu.memory_gb} GB" if gpu.memory_gb else "-",
            _price_str(gpu.pricing.secure_price),
            _price_str(gpu.pricing.community_price),
            _price_str(gpu.pricing.min_bid_price),
            _stock_style(gpu.stock.stock_status),
            str(gpu.stock.max_unreserved) if gpu.stock.max_unreserved is not None else "-",
        )

    console.print(table)
    console.print(f"\n[dim]{len(gpu_types)} GPU types listed.[/dim]")


def print_gpu_check(detail: Any) -> None:
    """Render detailed GPU availability."""
    table = Table(title=f"Availability — {detail.display_name}")
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("GPU", detail.display_name)
    table.add_row("VRAM", f"{detail.memory_gb} GB")
    table.add_row("Stock Status", _stock_style(detail.stock.stock_status))
    table.add_row("On-Demand Price", _price_str(detail.pricing.on_demand_price))
    table.add_row("Min Bid (Spot)", _price_str(detail.pricing.min_bid_price))
    table.add_row("Secure Price", _price_str(detail.pricing.secure_price))
    table.add_row("Community Price", _price_str(detail.pricing.community_price))

    if detail.stock.total_count is not None:
        table.add_row("Total GPUs", str(detail.stock.total_count))
    if detail.stock.rented_count is not None:
        table.add_row("Rented", str(detail.stock.rented_count))
    if detail.stock.max_unreserved is not None:
        table.add_row("Max Unreserved", str(detail.stock.max_unreserved))
    if detail.stock.rental_percentage is not None:
        table.add_row("Utilization", f"{detail.stock.rental_percentage:.1f}%")
    if detail.stock.available_counts:
        counts = ", ".join(str(c) for c in detail.stock.available_counts)
        table.add_row("Available Configs", counts)
    if detail.country_code:
        table.add_row("Country", detail.country_code)

    console.print(table)


def print_gpu_compare(gpu_types: list[Any]) -> None:
    """Render side-by-side GPU comparison."""
    if not gpu_types:
        console.print("[dim]No GPUs to compare.[/dim]")
        return

    table = Table(title="GPU Comparison")
    table.add_column("Metric", style="cyan")
    for gpu in gpu_types:
        table.add_column(gpu.display_name, justify="right")

    table.add_row("VRAM", *[f"{g.memory_gb} GB" for g in gpu_types])
    table.add_row("Secure Price", *[_price_str(g.pricing.secure_price) for g in gpu_types])
    table.add_row("Community Price", *[_price_str(g.pricing.community_price) for g in gpu_types])
    table.add_row("Spot (min bid)", *[_price_str(g.pricing.min_bid_price) for g in gpu_types])
    table.add_row("Stock", *[_stock_style(g.stock.stock_status) for g in gpu_types])
    avail = [
        str(g.stock.max_unreserved) if g.stock.max_unreserved is not None else "-"
        for g in gpu_types
    ]
    table.add_row("Available", *avail)
    table.add_row(
        "Max GPUs",
        *[str(g.max_gpu_count) if g.max_gpu_count else "-" for g in gpu_types],
    )

    console.print(table)


def print_regions(datacenters: list[Any]) -> None:
    """Render datacenter availability as a table."""
    if not datacenters:
        console.print("[dim]No datacenters found matching filters.[/dim]")
        return

    table = Table(title="Datacenters — GPU Availability")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Location")
    table.add_column("Region")
    table.add_column("Storage", justify="center")
    table.add_column("GPUs Available", justify="right")

    for dc in datacenters:
        available_count = sum(1 for g in dc.gpus if g.available)
        total_count = len(dc.gpus)
        storage = "[green]Yes[/green]" if dc.storage_support else "[dim]No[/dim]"

        table.add_row(
            dc.id,
            dc.name or "-",
            dc.location or "-",
            dc.region or "-",
            storage,
            f"{available_count}/{total_count}",
        )

    console.print(table)
    console.print(f"\n[dim]{len(datacenters)} datacenters listed.[/dim]")


# --- Pod tables ---


def print_pod_list(pods: list[Any]) -> None:
    """Render pods as a table."""
    if not pods:
        console.print("[dim]No pods found.[/dim]")
        return

    table = Table(title="Pods")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Status", justify="center")
    table.add_column("GPU")
    table.add_column("Image")
    table.add_column("Cost/hr", justify="right")

    for pod in pods:
        table.add_row(
            pod.id,
            pod.name or "-",
            _status_style(pod.status),
            f"{pod.gpu_count}x {pod.gpu_type}" if pod.gpu_type else "-",
            pod.image_name[:40] if pod.image_name else "-",
            _price_str(pod.cost_per_hr) if pod.cost_per_hr else "-",
        )

    console.print(table)
    console.print(f"\n[dim]{len(pods)} pods listed.[/dim]")


def print_pod_detail(pod: Any) -> None:
    """Render pod detail view."""
    _detail_table(f"Pod — {pod.name or pod.id}", pod)


# --- Endpoint tables ---


def print_endpoint_list(endpoints: list[Any]) -> None:
    """Render endpoints as a table."""
    if not endpoints:
        console.print("[dim]No endpoints found.[/dim]")
        return

    table = Table(title="Serverless Endpoints")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("GPU")
    table.add_column("Workers", justify="center")
    table.add_column("Idle Timeout", justify="right")
    table.add_column("Queue Delay", justify="right")

    for ep in endpoints:
        workers = f"{ep.workers_min}-{ep.workers_max} ({ep.workers_current} active)"
        table.add_row(
            ep.id,
            ep.name or "-",
            ep.gpu_ids or "-",
            workers,
            f"{ep.idle_timeout}s",
            str(ep.queue_delay) if ep.queue_delay else "-",
        )

    console.print(table)
    console.print(f"\n[dim]{len(endpoints)} endpoints listed.[/dim]")


def print_endpoint_detail(endpoint: Any) -> None:
    """Render endpoint detail view."""
    _detail_table(f"Endpoint — {endpoint.name or endpoint.id}", endpoint)


def print_endpoint_health(health: Any) -> None:
    """Render endpoint health status."""
    if isinstance(health, dict):
        table = Table(title="Endpoint Health")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right")

        workers = health.get("workers", {})
        jobs = health.get("jobs", {})

        if isinstance(workers, dict):
            for key, val in workers.items():
                table.add_row(f"workers.{key}", str(val))
        if isinstance(jobs, dict):
            for key, val in jobs.items():
                table.add_row(f"jobs.{key}", str(val))

        # Top-level fields
        for key in ("requestsPerMinute", "avgResponseTime", "queueLength"):
            if key in health:
                table.add_row(key, str(health[key]))

        console.print(table)
    else:
        _detail_table("Endpoint Health", health)


# --- Volume tables ---


def print_volume_list(volumes: list[Any]) -> None:
    """Render volumes as a table."""
    if not volumes:
        console.print("[dim]No network volumes found.[/dim]")
        return

    table = Table(title="Network Volumes")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Size", justify="right")
    table.add_column("Used", justify="right")
    table.add_column("Datacenter")

    for vol in volumes:
        used = f"{vol.used_size_gb:.1f} GB" if vol.used_size_gb else "-"
        table.add_row(
            vol.id,
            vol.name or "-",
            f"{vol.size_gb} GB",
            used,
            vol.data_center_id or "-",
        )

    console.print(table)
    console.print(f"\n[dim]{len(volumes)} volumes listed.[/dim]")


def print_volume_detail(volume: Any) -> None:
    """Render volume detail view."""
    _detail_table(f"Volume — {volume.name or volume.id}", volume)


# --- Template tables ---


def print_template_list(templates: list[Any]) -> None:
    """Render templates as a table."""
    if not templates:
        console.print("[dim]No templates found.[/dim]")
        return

    table = Table(title="Templates")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Image")
    table.add_column("Type", justify="center")

    for tmpl in templates:
        tmpl_type = "Serverless" if tmpl.is_serverless else "Pod"
        table.add_row(
            tmpl.id,
            tmpl.name or "-",
            tmpl.image_name[:40] if tmpl.image_name else "-",
            tmpl_type,
        )

    console.print(table)
    console.print(f"\n[dim]{len(templates)} templates listed.[/dim]")


def print_template_detail(template: Any) -> None:
    """Render template detail view."""
    _detail_table(f"Template — {template.name or template.id}", template)


# --- Preset tables ---


def print_preset_list(presets: list[Any]) -> None:
    """Render presets as a table."""
    if not presets:
        console.print("[dim]No presets found.[/dim]")
        return

    table = Table(title="Presets")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Type", justify="center")
    table.add_column("Description")
    table.add_column("Key Params")
    table.add_column("Created")

    for p in presets:
        params = p.params
        rtype = p.metadata.resource_type
        if rtype == "pod":
            key = params.get("image_name", "-")
            gpus = params.get("gpu_type_ids", [])
            if gpus:
                key += f" | {','.join(gpus)}"
        else:
            key = f"tmpl:{params.get('template_id', '-')}"

        created = p.metadata.created_at[:10] if p.metadata.created_at else "-"
        table.add_row(
            p.metadata.name,
            rtype,
            (p.metadata.description[:40] if p.metadata.description else "-"),
            key[:50],
            created,
        )

    console.print(table)
    console.print(f"\n[dim]{len(presets)} presets listed.[/dim]")


def print_preset_detail(preset: Any) -> None:
    """Render preset detail — metadata + params."""
    _detail_table(f"Preset — {preset.metadata.name}", preset.metadata)
    console.print()
    _detail_table("Parameters", preset.params)


# --- Dry run ---


def print_dry_run(params: Any) -> None:
    """Render create parameters as a preview table."""
    _detail_table("Dry Run — Parameters", params)
