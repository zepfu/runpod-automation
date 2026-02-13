"""Unit tests for Phase 2 Pydantic models."""

from __future__ import annotations

from rpctl.models.endpoint import Endpoint, EndpointCreateParams
from rpctl.models.pod import Pod, PodCreateParams
from rpctl.models.template import Template
from rpctl.models.volume import Volume


class TestPod:
    def test_from_api(self):
        raw = {
            "id": "pod-abc123",
            "name": "my-pod",
            "imageName": "runpod/pytorch:2.1",
            "desiredStatus": "RUNNING",
            "gpuCount": 1,
            "containerDiskInGb": 50,
            "volumeInGb": 20,
            "volumeMountPath": "/workspace",
            "costPerHr": 0.44,
            "cloudType": "SECURE",
            "port": "8888/http,22/tcp",
            "runtime": {"status": "RUNNING"},
            "machine": {"gpuDisplayName": "NVIDIA GeForce RTX 4090"},
        }
        pod = Pod.from_api(raw)
        assert pod.id == "pod-abc123"
        assert pod.name == "my-pod"
        assert pod.status == "RUNNING"
        assert pod.gpu_type == "NVIDIA GeForce RTX 4090"
        assert pod.cost_per_hr == 0.44

    def test_from_api_minimal(self):
        raw = {"id": "pod-min"}
        pod = Pod.from_api(raw)
        assert pod.id == "pod-min"
        assert pod.status == ""

    def test_create_params_to_sdk(self):
        params = PodCreateParams(
            name="test",
            image_name="nvidia/cuda",
            gpu_type_ids=["NVIDIA RTX A6000"],
            gpu_count=2,
            env={"KEY": "VALUE"},
            data_center_ids=["US-TX-3"],
        )
        kwargs = params.to_sdk_kwargs()
        assert kwargs["name"] == "test"
        assert kwargs["image_name"] == "nvidia/cuda"
        assert kwargs["gpu_type_ids"] == ["NVIDIA RTX A6000"]
        assert kwargs["gpu_count"] == 2
        assert kwargs["env"] == {"KEY": "VALUE"}
        assert kwargs["data_center_id"] == "US-TX-3"

    def test_create_params_spot(self):
        params = PodCreateParams(
            image_name="test",
            interruptible=True,
        )
        kwargs = params.to_sdk_kwargs()
        assert "bid_per_gpu" in kwargs


class TestEndpoint:
    def test_from_api(self):
        raw = {
            "id": "ep-abc123",
            "name": "my-endpoint",
            "templateId": "tmpl-123",
            "gpuIds": "AMPERE_24",
            "gpuCount": 1,
            "workersMin": 0,
            "workersMax": 5,
            "idleTimeout": 10,
            "scalerType": "QUEUE_DELAY",
            "scalerValue": 4,
            "flashboot": True,
        }
        ep = Endpoint.from_api(raw)
        assert ep.id == "ep-abc123"
        assert ep.name == "my-endpoint"
        assert ep.workers_max == 5
        assert ep.flashboot is True

    def test_create_params_to_sdk(self):
        params = EndpointCreateParams(
            name="test-ep",
            template_id="tmpl-123",
            gpu_ids="AMPERE_24",
            workers_max=5,
            flashboot=True,
        )
        kwargs = params.to_sdk_kwargs()
        assert kwargs["name"] == "test-ep"
        assert kwargs["template_id"] == "tmpl-123"
        assert kwargs["flashboot"] is True


class TestVolume:
    def test_from_api(self):
        raw = {
            "id": "vol-abc123",
            "name": "my-volume",
            "size": 100,
            "dataCenterId": "US-TX-3",
            "usedSize": 42.5,
        }
        vol = Volume.from_api(raw)
        assert vol.id == "vol-abc123"
        assert vol.size_gb == 100
        assert vol.used_size_gb == 42.5
        assert vol.data_center_id == "US-TX-3"


class TestTemplate:
    def test_from_api(self):
        raw = {
            "id": "tmpl-abc123",
            "name": "my-template",
            "imageName": "runpod/pytorch:2.1",
            "containerDiskInGb": 50,
            "isServerless": True,
            "isPublic": False,
        }
        tmpl = Template.from_api(raw)
        assert tmpl.id == "tmpl-abc123"
        assert tmpl.is_serverless is True
        assert tmpl.image_name == "runpod/pytorch:2.1"
