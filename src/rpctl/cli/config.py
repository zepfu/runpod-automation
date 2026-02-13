"""rpctl config — manage configuration and profiles."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from rpctl.config.settings import Settings, get_config_dir
from rpctl.errors import ConfigError

app = typer.Typer(no_args_is_help=True)
console = Console()
err_console = Console(stderr=True)


@app.command()
def init() -> None:
    """Interactive setup wizard."""
    import keyring

    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    console.print("[bold]rpctl configuration wizard[/bold]\n")

    api_key = typer.prompt("RunPod API key", hide_input=True)
    if not api_key.strip():
        err_console.print("[red]API key cannot be empty.[/red]")
        raise typer.Exit(code=1)

    profile_name = typer.prompt("Profile name", default="default")
    cloud_type = typer.prompt(
        "Default cloud type (secure/community)",
        default="secure",
    )

    keyring.set_password("rpctl", profile_name, api_key.strip())

    settings = Settings.create_default(
        active_profile=profile_name,
        cloud_type=cloud_type,
    )
    settings.save()

    console.print(
        f"\n[green]Configuration saved.[/green] Active profile: [bold]{profile_name}[/bold]"
    )
    console.print("API key stored in OS keyring.")
    console.print("\nTry: [bold]rpctl capacity list[/bold]")


@app.command("set-key")
def set_key(
    profile: str | None = typer.Option(None, help="Profile to set key for"),
) -> None:
    """Store API key in OS keyring."""
    import keyring

    settings = Settings.load()
    profile_name = profile or settings.active_profile

    api_key = typer.prompt(f"API key for profile '{profile_name}'", hide_input=True)
    if not api_key.strip():
        err_console.print("[red]API key cannot be empty.[/red]")
        raise typer.Exit(code=1)

    keyring.set_password("rpctl", profile_name, api_key.strip())
    console.print(f"[green]API key stored for profile '{profile_name}'.[/green]")


@app.command()
def show(
    ctx: typer.Context,
) -> None:
    """Display active configuration (API key redacted)."""
    try:
        settings = Settings.load(profile=ctx.obj.get("profile") if ctx.obj else None)
    except ConfigError:
        err_console.print("[red]No configuration found. Run 'rpctl config init' first.[/red]")
        raise typer.Exit(code=3) from None

    has_key = settings.has_api_key()
    data = settings.to_display_dict()
    data["api_key"] = "[green]set[/green]" if has_key else "[red]not set[/red]"

    if ctx.obj and ctx.obj.get("json"):
        import json

        display = settings.to_display_dict()
        display["api_key"] = "***" if has_key else None
        typer.echo(json.dumps(display, indent=2))
        return

    table = Table(title="Active Configuration", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    for key, value in data.items():
        table.add_row(key, str(value))
    console.print(table)


@app.command("list-profiles")
def list_profiles(
    ctx: typer.Context,
) -> None:
    """List all configured profiles."""
    try:
        settings = Settings.load()
    except ConfigError:
        err_console.print("[red]No configuration found. Run 'rpctl config init' first.[/red]")
        raise typer.Exit(code=3) from None

    profiles = settings.list_profiles()
    active = settings.active_profile

    if ctx.obj and ctx.obj.get("json"):
        import json

        typer.echo(json.dumps({"active": active, "profiles": profiles}, indent=2))
        return

    table = Table(title="Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Active", justify="center")
    for name in profiles:
        marker = "[green]***[/green]" if name == active else ""
        table.add_row(name, marker)
    console.print(table)


@app.command("add-profile")
def add_profile_cmd(
    name: str = typer.Argument(help="Profile name"),
    cloud_type: str = typer.Option("secure", help="Default cloud type for this profile"),
) -> None:
    """Add a new configuration profile."""
    try:
        settings = Settings.load()
    except ConfigError:
        err_console.print("[red]No configuration found. Run 'rpctl config init' first.[/red]")
        raise typer.Exit(code=3) from None

    try:
        from rpctl.config.profiles import add_profile

        add_profile(settings, name, cloud_type=cloud_type)
        settings.save()
        console.print(f"[green]Profile '{name}' added.[/green]")
    except ConfigError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from None


@app.command("use-profile")
def use_profile_cmd(
    name: str = typer.Argument(help="Profile name to activate"),
) -> None:
    """Switch the active profile."""
    try:
        settings = Settings.load()
    except ConfigError:
        err_console.print("[red]No configuration found. Run 'rpctl config init' first.[/red]")
        raise typer.Exit(code=3) from None

    try:
        from rpctl.config.profiles import use_profile

        use_profile(settings, name)
        settings.save()
        console.print(f"[green]Active profile set to '{name}'.[/green]")
    except ConfigError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=1) from None


@app.command("set")
def set_config(
    key: str = typer.Argument(help="Config key (e.g., cloud_type, default_gpu)"),
    value: str = typer.Argument(help="Config value"),
) -> None:
    """Set a default configuration value."""
    try:
        settings = Settings.load()
    except ConfigError:
        err_console.print("[red]No configuration found. Run 'rpctl config init' first.[/red]")
        raise typer.Exit(code=3) from None

    settings.set_default(key, value)
    settings.save()
    console.print(f"[green]Set {key} = {value}[/green]")


@app.command("get")
def get_config(
    key: str = typer.Argument(help="Config key to read"),
) -> None:
    """Read a configuration value."""
    try:
        settings = Settings.load()
    except ConfigError:
        err_console.print("[red]No configuration found. Run 'rpctl config init' first.[/red]")
        raise typer.Exit(code=3) from None

    value = settings.get(key)
    if value is None:
        err_console.print(f"[yellow]Key '{key}' is not set.[/yellow]")
        raise typer.Exit(code=1)
    typer.echo(value)
