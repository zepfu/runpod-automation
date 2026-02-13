"""Output routing — table vs JSON based on --json flag."""

from __future__ import annotations

from typing import Any

from rpctl.output.json_output import print_json
from rpctl.output.tables import (
    print_dry_run,
    print_endpoint_detail,
    print_endpoint_list,
    print_gpu_check,
    print_gpu_compare,
    print_gpu_list,
    print_pod_detail,
    print_pod_list,
    print_preset_detail,
    print_preset_list,
    print_regions,
    print_template_detail,
    print_template_list,
    print_volume_detail,
    print_volume_list,
)

TABLE_RENDERERS = {
    "gpu_list": print_gpu_list,
    "gpu_check": print_gpu_check,
    "gpu_compare": print_gpu_compare,
    "regions": print_regions,
    "pod_list": print_pod_list,
    "pod_detail": print_pod_detail,
    "pod_create_dry_run": print_dry_run,
    "endpoint_list": print_endpoint_list,
    "endpoint_detail": print_endpoint_detail,
    "endpoint_create_dry_run": print_dry_run,
    "volume_list": print_volume_list,
    "volume_detail": print_volume_detail,
    "template_list": print_template_list,
    "template_detail": print_template_detail,
    "preset_list": print_preset_list,
    "preset_detail": print_preset_detail,
}


def output(data: Any, *, json_mode: bool = False, table_type: str) -> None:
    """Route output to JSON or table renderer."""
    if json_mode:
        print_json(data)
        return

    renderer = TABLE_RENDERERS.get(table_type)
    if renderer:
        renderer(data)
    else:
        print_json(data)
