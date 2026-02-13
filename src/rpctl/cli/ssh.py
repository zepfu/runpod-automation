"""rpctl ssh — SSH into a running pod."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import typer
from rich.console import Console

from rpctl.errors import RpctlError

if TYPE_CHECKING:
    from rpctl.models.pod import Pod
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


def _resolve_ssh_info(pod: Pod) -> tuple[str, int]:
    """Extract SSH host and port from pod runtime data.

    RunPod exposes SSH via the runtime.ports list. Each entry looks like:
        {"ip": "x.x.x.x", "isIpPublic": true, "privatePort": 22,
         "publicPort": 12345, "type": "tcp"}

    Falls back to the proxy hostname format: {pod_id}-ssh.proxy.runpod.net:22.
    """
    runtime = pod.runtime or {}
    ports = runtime.get("ports") or []

    for port_entry in ports:
        if port_entry.get("privatePort") == 22:
            ip = port_entry.get("ip", "")
            public_port = port_entry.get("publicPort", 22)
            if ip:
                return ip, int(public_port)

    # Fallback: RunPod proxy hostname
    return f"{pod.id}-ssh.proxy.runpod.net", 22


def _build_ssh_command(
    host: str,
    port: int,
    user: str = "root",
    key_file: str | None = None,
    remote_command: str | None = None,
) -> list[str]:
    """Build the ssh command argument list."""
    cmd = ["ssh"]
    cmd.extend(["-p", str(port)])
    if key_file:
        cmd.extend(["-i", key_file])
    # Disable host key checking for dynamic cloud IPs
    cmd.extend(["-o", "StrictHostKeyChecking=no"])
    cmd.extend(["-o", "UserKnownHostsFile=/dev/null"])
    cmd.append(f"{user}@{host}")
    if remote_command:
        cmd.append(remote_command)
    return cmd


@app.command("connect")
def ssh_connect(
    ctx: typer.Context,
    pod_id: str = typer.Argument(help="Pod ID to SSH into"),
    user: str = typer.Option("root", "--user", "-u", help="SSH user"),
    key: str | None = typer.Option(None, "--key", "-i", help="Path to SSH private key"),
    command: str | None = typer.Option(None, "--command", "-c", help="Remote command to execute"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print SSH command without executing"),
) -> None:
    """SSH into a running pod."""
    try:
        svc = _get_pod_service(ctx)
        pod = svc.get_pod(pod_id)
    except RpctlError as e:
        err_console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(code=e.exit_code) from None

    # Validate pod is running
    if pod.status.upper() != "RUNNING":
        err_console.print(
            f"[red]Pod {pod_id} is not running (status: {pod.status}). "
            f"Start it first with: rpctl pod start {pod_id}[/red]",
        )
        raise typer.Exit(code=1)

    host, port = _resolve_ssh_info(pod)
    cmd = _build_ssh_command(host, port, user=user, key_file=key, remote_command=command)

    if dry_run:
        Console().print(" ".join(cmd))
        return

    # Replace current process with ssh
    Console(stderr=True).print(f"[dim]Connecting to {pod.name or pod_id}...[/dim]")
    os.execvp("ssh", cmd)
