"""Unit tests for service layer (pod, endpoint, template, volume)."""

from __future__ import annotations

from unittest.mock import MagicMock

from rpctl.services.endpoint_service import EndpointService
from rpctl.services.pod_service import PodService
from rpctl.services.template_service import TemplateService
from rpctl.services.volume_service import VolumeService

# --- PodService ---


def _pod_api_data(**overrides):
    base = {
        "id": "pod-001",
        "name": "test-pod",
        "desiredStatus": "RUNNING",
        "imageName": "nvidia/cuda",
        "machine": {"gpuDisplayName": "A100"},
        "gpuCount": 1,
    }
    base.update(overrides)
    return base


def test_pod_service_list():
    client = MagicMock()
    client.get_pods.return_value = [_pod_api_data()]
    svc = PodService(client)
    pods = svc.list_pods()
    assert len(pods) == 1
    assert pods[0].id == "pod-001"


def test_pod_service_list_filter():
    client = MagicMock()
    client.get_pods.return_value = [
        _pod_api_data(id="p1", desiredStatus="RUNNING"),
        _pod_api_data(id="p2", desiredStatus="EXITED"),
    ]
    svc = PodService(client)
    pods = svc.list_pods(status_filter="running")
    assert len(pods) == 1
    assert pods[0].id == "p1"


def test_pod_service_list_filter_all():
    client = MagicMock()
    client.get_pods.return_value = [_pod_api_data(), _pod_api_data(id="p2")]
    svc = PodService(client)
    pods = svc.list_pods(status_filter="all")
    assert len(pods) == 2


def test_pod_service_get():
    client = MagicMock()
    client.get_pod.return_value = _pod_api_data()
    svc = PodService(client)
    pod = svc.get_pod("pod-001")
    assert pod.id == "pod-001"


def test_pod_service_create():
    from rpctl.models.pod import PodCreateParams

    client = MagicMock()
    client.create_pod.return_value = _pod_api_data()
    svc = PodService(client)
    params = PodCreateParams(image_name="nvidia/cuda")
    pod = svc.create_pod(params)
    assert pod.id == "pod-001"
    client.create_pod.assert_called_once()


def test_pod_service_stop():
    client = MagicMock()
    client.stop_pod.return_value = {}
    svc = PodService(client)
    svc.stop_pod("pod-001")
    client.stop_pod.assert_called_once_with("pod-001")


def test_pod_service_start():
    client = MagicMock()
    client.resume_pod.return_value = {}
    svc = PodService(client)
    svc.start_pod("pod-001")
    client.resume_pod.assert_called_once_with("pod-001")


def test_pod_service_restart():
    client = MagicMock()
    client.stop_pod.return_value = {}
    client.resume_pod.return_value = {}
    svc = PodService(client)
    svc.restart_pod("pod-001")
    client.stop_pod.assert_called_once_with("pod-001")
    client.resume_pod.assert_called_once_with("pod-001")


def test_pod_service_delete():
    client = MagicMock()
    client.terminate_pod.return_value = {}
    svc = PodService(client)
    svc.delete_pod("pod-001")
    client.terminate_pod.assert_called_once_with("pod-001")


# --- EndpointService ---


def _ep_api_data(**overrides):
    base = {
        "id": "ep-001",
        "name": "test-ep",
        "templateId": "tmpl-001",
        "gpuIds": "AMPERE_24",
        "workersMin": 0,
        "workersMax": 5,
        "idleTimeout": 10,
    }
    base.update(overrides)
    return base


def test_endpoint_service_list():
    client = MagicMock()
    client.get_endpoints.return_value = [_ep_api_data()]
    svc = EndpointService(client)
    endpoints = svc.list_endpoints()
    assert len(endpoints) == 1
    assert endpoints[0].id == "ep-001"


def test_endpoint_service_get():
    client = MagicMock()
    client.get_endpoint.return_value = _ep_api_data()
    svc = EndpointService(client)
    ep = svc.get_endpoint("ep-001")
    assert ep.id == "ep-001"


def test_endpoint_service_create():
    from rpctl.models.endpoint import EndpointCreateParams

    client = MagicMock()
    client.create_endpoint.return_value = _ep_api_data()
    svc = EndpointService(client)
    params = EndpointCreateParams(name="test", template_id="tmpl-001")
    ep = svc.create_endpoint(params)
    assert ep.id == "ep-001"


def test_endpoint_service_update():
    client = MagicMock()
    client.update_endpoint.return_value = _ep_api_data(workersMax=10)
    svc = EndpointService(client)
    ep = svc.update_endpoint("ep-001", workers_max=10)
    assert ep.id == "ep-001"


def test_endpoint_service_delete():
    client = MagicMock()
    client.delete_endpoint.return_value = {}
    svc = EndpointService(client)
    svc.delete_endpoint("ep-001")
    client.delete_endpoint.assert_called_once_with("ep-001")


# --- TemplateService ---


def _tmpl_api_data(**overrides):
    base = {
        "id": "tmpl-001",
        "name": "test-tmpl",
        "imageName": "runpod/pytorch:2.1",
        "isServerless": True,
    }
    base.update(overrides)
    return base


def test_template_service_list():
    client = MagicMock()
    client.get_templates.return_value = [_tmpl_api_data()]
    svc = TemplateService(client)
    templates = svc.list_templates()
    assert len(templates) == 1
    assert templates[0].id == "tmpl-001"


def test_template_service_get():
    client = MagicMock()
    client.get_template.return_value = _tmpl_api_data()
    svc = TemplateService(client)
    tmpl = svc.get_template("tmpl-001")
    assert tmpl.id == "tmpl-001"


def test_template_service_create():
    client = MagicMock()
    client.create_template.return_value = _tmpl_api_data()
    svc = TemplateService(client)
    tmpl = svc.create_template(name="test", image_name="test")
    assert tmpl.id == "tmpl-001"


def test_template_service_update():
    client = MagicMock()
    client.update_template.return_value = _tmpl_api_data(name="updated")
    svc = TemplateService(client)
    tmpl = svc.update_template("tmpl-001", name="updated")
    assert tmpl.id == "tmpl-001"


def test_template_service_delete():
    client = MagicMock()
    client.delete_template.return_value = {}
    svc = TemplateService(client)
    svc.delete_template("tmpl-001")
    client.delete_template.assert_called_once_with("tmpl-001")


# --- VolumeService ---


def _vol_api_data(**overrides):
    base = {
        "id": "vol-001",
        "name": "test-vol",
        "size": 100,
        "dataCenterId": "US-TX-3",
    }
    base.update(overrides)
    return base


def test_volume_service_list():
    client = MagicMock()
    client.get_volumes.return_value = [_vol_api_data()]
    svc = VolumeService(client)
    volumes = svc.list_volumes()
    assert len(volumes) == 1
    assert volumes[0].id == "vol-001"


def test_volume_service_get():
    client = MagicMock()
    client.get_volume.return_value = _vol_api_data()
    svc = VolumeService(client)
    vol = svc.get_volume("vol-001")
    assert vol.id == "vol-001"


def test_volume_service_create():
    client = MagicMock()
    client.create_volume.return_value = _vol_api_data()
    svc = VolumeService(client)
    vol = svc.create_volume(name="test", size_gb=100, data_center_id="US-TX-3")
    assert vol.id == "vol-001"


def test_volume_service_update():
    client = MagicMock()
    client.update_volume.return_value = _vol_api_data(name="updated")
    svc = VolumeService(client)
    vol = svc.update_volume("vol-001", name="updated")
    assert vol.id == "vol-001"


def test_volume_service_delete():
    client = MagicMock()
    client.delete_volume.return_value = {}
    svc = VolumeService(client)
    svc.delete_volume("vol-001")
    client.delete_volume.assert_called_once_with("vol-001")
