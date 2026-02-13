"""rpctl — RunPod CLI entry point."""

from __future__ import annotations

import logging
import sys

import typer

from rpctl import __version__
from rpctl.cli import capacity, config, endpoint, pod, preset, ssh, template, volume

app = typer.Typer(
    name="rpctl",
    help="RunPod CLI — manage pods, endpoints, volumes, and capacity.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"rpctl {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    profile: str | None = typer.Option(None, help="Config profile to use"),
    json_output: bool = typer.Option(
        False, "--json", help="Output as JSON (shorthand for --output json)"
    ),
    output_format: str | None = typer.Option(
        None, "--output", "-o", help="Output format: table, json, csv, yaml"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj["profile"] = profile
    # Resolve output format: --output takes precedence over --json
    if output_format:
        ctx.obj["output_format"] = output_format
    elif json_output:
        ctx.obj["output_format"] = "json"
    else:
        ctx.obj["output_format"] = "table"
    ctx.obj["json"] = ctx.obj["output_format"] == "json"
    ctx.obj["verbose"] = verbose

    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit()


app.add_typer(config.app, name="config", help="Manage configuration and profiles.")
app.add_typer(pod.app, name="pod", help="Manage GPU/CPU pods.")
app.add_typer(endpoint.app, name="endpoint", help="Manage serverless endpoints.")
app.add_typer(volume.app, name="volume", help="Manage network volumes.")
app.add_typer(template.app, name="template", help="Manage templates.")
app.add_typer(preset.app, name="preset", help="Manage saved presets.")
app.add_typer(capacity.app, name="capacity", help="Query GPU/CPU availability and pricing.")
app.add_typer(ssh.app, name="ssh", help="SSH into a running pod.")

if __name__ == "__main__":
    app()
