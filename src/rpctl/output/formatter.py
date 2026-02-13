"""Output routing — table, JSON, CSV, or YAML based on --output flag."""

from __future__ import annotations

from typing import Any

from rpctl.output.csv_output import print_csv
from rpctl.output.json_output import print_json
from rpctl.output.tables import (
    print_dry_run,
    print_endpoint_detail,
    print_endpoint_health,
    print_endpoint_list,
    print_endpoint_purge_result,
    print_endpoint_run_result,
    print_gpu_check,
    print_gpu_compare,
    print_gpu_list,
    print_pod_detail,
    print_pod_list,
    print_preset_detail,
    print_preset_list,
    print_regions,
    print_registry_detail,
    print_template_detail,
    print_template_list,
    print_user_info,
    print_volume_detail,
    print_volume_list,
)
from rpctl.output.yaml_output import print_yaml

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
    "endpoint_health": print_endpoint_health,
    "endpoint_run_result": print_endpoint_run_result,
    "endpoint_purge_result": print_endpoint_purge_result,
    "endpoint_create_dry_run": print_dry_run,
    "volume_list": print_volume_list,
    "volume_detail": print_volume_detail,
    "template_list": print_template_list,
    "template_detail": print_template_detail,
    "preset_list": print_preset_list,
    "preset_detail": print_preset_detail,
    "user_info": print_user_info,
    "registry_detail": print_registry_detail,
}


def output(
    data: Any,
    *,
    json_mode: bool = False,
    output_format: str = "table",
    table_type: str,
) -> None:
    """Route output to the appropriate renderer.

    Precedence: explicit output_format > json_mode shorthand > table default.
    """
    fmt = output_format
    if fmt == "table" and json_mode:
        fmt = "json"

    if fmt == "json":
        print_json(data)
    elif fmt == "csv":
        print_csv(data, table_type=table_type)
    elif fmt == "yaml":
        print_yaml(data)
    else:
        renderer = TABLE_RENDERERS.get(table_type)
        if renderer:
            renderer(data)
        else:
            print_json(data)
