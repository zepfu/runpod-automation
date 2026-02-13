"""Unit tests for output layer — tables, JSON, and formatter routing."""

from __future__ import annotations

from rpctl.models.capacity import (
    Datacenter,
    DatacenterGpu,
    GpuAvailabilityDetail,
    GpuPricing,
    GpuStock,
    GpuType,
)
from rpctl.models.endpoint import Endpoint
from rpctl.models.pod import Pod, PodCreateParams
from rpctl.models.preset import Preset, PresetMetadata
from rpctl.models.template import Template
from rpctl.models.volume import Volume
from rpctl.output.formatter import output
from rpctl.output.json_output import print_json
from rpctl.output.tables import (
    _detail_table,
    _price_str,
    _status_style,
    _stock_style,
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

# --- Helper function tests ---


def test_price_str_none():
    assert _price_str(None) == "-"


def test_price_str_value():
    assert _price_str(0.44) == "$0.4400/hr"


def test_stock_style_high():
    result = _stock_style("High")
    assert "green" in result


def test_stock_style_low():
    result = _stock_style("Low")
    assert "yellow" in result


def test_stock_style_unavailable():
    result = _stock_style("Unavailable")
    assert "red" in result


def test_stock_style_none_value():
    result = _stock_style("None")
    assert "red" in result


def test_stock_style_empty():
    result = _stock_style("")
    assert "dim" in result


def test_stock_style_other():
    result = _stock_style("Medium")
    assert result == "Medium"


def test_status_style_running():
    result = _status_style("RUNNING")
    assert "green" in result


def test_status_style_ready():
    result = _status_style("Ready")
    assert "green" in result


def test_status_style_exited():
    result = _status_style("Exited")
    assert "yellow" in result


def test_status_style_stopped():
    result = _status_style("Stopped")
    assert "yellow" in result


def test_status_style_error():
    result = _status_style("Error")
    assert "red" in result


def test_status_style_failed():
    result = _status_style("Failed")
    assert "red" in result


def test_status_style_other():
    result = _status_style("Pending")
    assert result == "Pending"


# --- GPU tables ---


def _gpu(gpu_id="A100", name="A100 80GB", vram=80):
    return GpuType(
        id=gpu_id,
        display_name=name,
        memory_gb=vram,
        max_gpu_count=8,
        pricing=GpuPricing(
            secure_price=2.0,
            community_price=1.5,
            min_bid_price=0.5,
        ),
        stock=GpuStock(
            stock_status="High",
            max_unreserved=10,
        ),
    )


def test_print_gpu_list():
    print_gpu_list([_gpu()])


def test_print_gpu_list_empty():
    print_gpu_list([])


def test_print_gpu_compare():
    print_gpu_compare([_gpu("A100", "A100", 80), _gpu("A6000", "A6000", 48)])


def test_print_gpu_compare_empty():
    print_gpu_compare([])


def test_print_gpu_check():
    detail = GpuAvailabilityDetail(
        id="A100",
        display_name="A100 80GB",
        memory_gb=80,
        country_code="US",
        pricing=GpuPricing(
            on_demand_price=2.0,
            secure_price=2.0,
            community_price=1.5,
            min_bid_price=0.5,
        ),
        stock=GpuStock(
            stock_status="High",
            max_unreserved=10,
            total_count=100,
            rented_count=90,
            rental_percentage=90.0,
            available_counts=[1, 2, 4],
        ),
    )
    print_gpu_check(detail)


def test_print_gpu_check_minimal():
    detail = GpuAvailabilityDetail(
        id="A100",
        display_name="A100 80GB",
        memory_gb=80,
    )
    print_gpu_check(detail)


# --- Region tables ---


def test_print_regions():
    dc = Datacenter(
        id="US-TX-3",
        name="Dallas",
        location="Texas, US",
        region="Americas",
        storage_support=True,
        gpus=[
            DatacenterGpu(gpu_type_id="A100", display_name="A100 80GB", available=True),
            DatacenterGpu(gpu_type_id="A6000", display_name="RTX A6000", available=False),
        ],
    )
    print_regions([dc])


def test_print_regions_empty():
    print_regions([])


# --- Pod tables ---


def _pod():
    return Pod(
        id="pod-001",
        name="test-pod",
        status="RUNNING",
        gpu_type="NVIDIA RTX A6000",
        gpu_count=1,
        image_name="runpod/pytorch:2.1",
        cost_per_hr=0.44,
    )


def test_print_pod_list():
    print_pod_list([_pod()])


def test_print_pod_list_empty():
    print_pod_list([])


def test_print_pod_detail():
    print_pod_detail(_pod())


# --- Endpoint tables ---


def _endpoint():
    return Endpoint(
        id="ep-001",
        name="test-ep",
        gpu_ids="AMPERE_24",
        workers_min=0,
        workers_max=5,
        idle_timeout=10,
        workers_current=2,
        queue_delay=3,
    )


def test_print_endpoint_list():
    print_endpoint_list([_endpoint()])


def test_print_endpoint_list_empty():
    print_endpoint_list([])


def test_print_endpoint_detail():
    print_endpoint_detail(_endpoint())


# --- Volume tables ---


def _volume():
    return Volume(
        id="vol-001",
        name="test-vol",
        size_gb=100,
        data_center_id="US-TX-3",
        used_size_gb=42.5,
    )


def test_print_volume_list():
    print_volume_list([_volume()])


def test_print_volume_list_empty():
    print_volume_list([])


def test_print_volume_detail():
    print_volume_detail(_volume())


def test_print_volume_no_used_size():
    vol = Volume(id="vol-002", name="empty-vol", size_gb=50)
    print_volume_list([vol])


# --- Template tables ---


def _template():
    return Template(
        id="tmpl-001",
        name="test-tmpl",
        image_name="runpod/pytorch:2.1",
        is_serverless=True,
    )


def test_print_template_list():
    print_template_list([_template()])


def test_print_template_list_empty():
    print_template_list([])


def test_print_template_list_pod_type():
    tmpl = Template(id="tmpl-002", name="pod-tmpl", image_name="test", is_serverless=False)
    print_template_list([tmpl])


def test_print_template_detail():
    print_template_detail(_template())


# --- Preset tables ---


def _preset_pod():
    return Preset(
        metadata=PresetMetadata(name="my-preset", resource_type="pod", description="Test"),
        params={"image_name": "nvidia/cuda", "gpu_type_ids": ["A100"]},
    )


def _preset_endpoint():
    return Preset(
        metadata=PresetMetadata(name="ep-preset", resource_type="endpoint"),
        params={"template_id": "tmpl-1"},
    )


def test_print_preset_list_pod():
    print_preset_list([_preset_pod()])


def test_print_preset_list_endpoint():
    print_preset_list([_preset_endpoint()])


def test_print_preset_list_empty():
    print_preset_list([])


def test_print_preset_detail():
    print_preset_detail(_preset_pod())


def test_print_preset_list_pod_no_gpus():
    p = Preset(
        metadata=PresetMetadata(name="no-gpu", resource_type="pod"),
        params={"image_name": "test"},
    )
    print_preset_list([p])


# --- Dry run ---


def test_print_dry_run():
    params = PodCreateParams(image_name="nvidia/cuda")
    print_dry_run(params)


# --- Detail table with dict and other types ---


def test_detail_table_with_dict():
    _detail_table("Test", {"key1": "value1", "nested": {"a": "b"}, "items": [1, 2, 3]})


def test_detail_table_with_empty_list():
    _detail_table("Test", {"items": []})


def test_detail_table_with_plain_value():
    _detail_table("Test", "just a string")


# --- JSON output ---


def test_print_json_list():
    pods = [_pod()]
    print_json(pods)


def test_print_json_single():
    print_json(_pod())


def test_print_json_dict():
    print_json({"key": "value"})


def test_print_json_string():
    print_json("hello")


# --- Formatter routing ---


def test_output_json_mode():
    pods = [_pod()]
    output(pods, json_mode=True, table_type="pod_list")


def test_output_table_mode():
    pods = [_pod()]
    output(pods, json_mode=False, table_type="pod_list")


def test_output_unknown_table_type():
    """Unknown table type falls back to JSON."""
    output({"key": "value"}, json_mode=False, table_type="nonexistent")
