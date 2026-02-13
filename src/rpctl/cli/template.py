"""rpctl template — manage templates."""

from __future__ import annotations

import typer
from rich.console import Console

from rpctl.errors import RpctlError
from rpctl.output.formatter import output

app = typer.Typer(no_args_is_help=True)
err_console = Console(stderr=True)


def _get_template_service(ctx: typer.Context):
    from rpctl.api.rest_client import RestClient
    from rpctl.config.settings import Settings
    from rpctl.services.template_service import TemplateService

    profile = ctx.obj.get("profile") if ctx.obj else None
    settings = Settings.load(profile=profile)
    client = RestClient(settings.api_key)
    return TemplateService(client)


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Option(..., help="Template name"),
    image: str = typer.Option(..., help="Container image"),
    serverless: bool = typer.Option(False, help="Mark as serverless template"),
    container_disk: int = typer.Option(50, help="Container disk in GB"),
    volume_disk: int = typer.Option(0, help="Volume in GB"),
    ports: str | None = typer.Option(None, help="Ports to expose"),
    env: list[str] = typer.Option([], help="Environment variables (KEY=VALUE) [repeatable]"),
    readme: str | None = typer.Option(None, help="Template description"),
) -> None:
    """Create a new template."""
    env_dict = {}
    for item in env:
        if "=" not in item:
            err_console.print(f"[red]Invalid env format: '{item}'. Use KEY=VALUE.[/red]")
            raise typer.Exit(code=1)
        key, _, value = item.partition("=")
        env_dict[key] = value

    kwargs: dict = {
        "name": name,
        "image_name": image,
        "is_serverless": serverless,
        "container_disk_in_gb": container_disk,
        "volume_in_gb": volume_disk,
    }
    if ports:
        kwargs["ports"] = ports
    if env_dict:
        kwargs["env"] = env_dict
    if readme:
        kwargs["readme"] = readme

    try:
        svc = _get_template_service(ctx)
        template = svc.create_template(**kwargs)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(template, output_format=fmt, table_type="template_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command("list")
def list_templates(ctx: typer.Context) -> None:
    """List all templates."""
    try:
        svc = _get_template_service(ctx)
        templates = svc.list_templates()
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(templates, output_format=fmt, table_type="template_list")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def get(
    ctx: typer.Context,
    template_id: str = typer.Argument(help="Template ID"),
) -> None:
    """Get template details."""
    try:
        svc = _get_template_service(ctx)
        template = svc.get_template(template_id)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(template, output_format=fmt, table_type="template_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def update(
    ctx: typer.Context,
    template_id: str = typer.Argument(help="Template ID"),
    name: str | None = typer.Option(None, help="New name"),
    image: str | None = typer.Option(None, help="New container image"),
) -> None:
    """Update a template."""
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if image is not None:
        kwargs["image_name"] = image

    if not kwargs:
        err_console.print("[yellow]No update parameters provided.[/yellow]")
        raise typer.Exit(code=1)

    try:
        svc = _get_template_service(ctx)
        template = svc.update_template(template_id, **kwargs)
        fmt = ctx.obj.get("output_format", "table") if ctx.obj else "table"
        output(template, output_format=fmt, table_type="template_detail")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None


@app.command()
def delete(
    ctx: typer.Context,
    template_id: str = typer.Argument(help="Template ID"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
) -> None:
    """Delete a template."""
    if not confirm:
        typer.confirm(f"Delete template {template_id}?", abort=True)

    try:
        svc = _get_template_service(ctx)
        svc.delete_template(template_id)
        Console().print(f"[green]Template {template_id} deleted.[/green]")
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None
