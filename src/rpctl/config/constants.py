"""Constants for rpctl."""

from __future__ import annotations

GRAPHQL_URL = "https://api.runpod.io/graphql"
REST_BASE_URL = "https://rest.runpod.io/v1"

CONFIG_DIR_NAME = "rpctl"
CONFIG_FILE_NAME = "config.yaml"
PRESETS_DIR_NAME = "presets"

KEYRING_SERVICE = "rpctl"

DEFAULT_CLOUD_TYPE = "secure"
DEFAULT_CONTAINER_DISK_GB = 50
DEFAULT_VOLUME_DISK_GB = 20
DEFAULT_VOLUME_MOUNT_PATH = "/workspace"
DEFAULT_PORTS = "8888/http,22/tcp"
DEFAULT_MIN_VCPU_PER_GPU = 2
DEFAULT_MIN_RAM_PER_GPU = 8

DEFAULT_API_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BASE_DELAY = 1.0
DEFAULT_RETRY_MAX_DELAY = 30.0

GPU_TYPE_IDS = [
    "NVIDIA A100 80GB PCIe",
    "NVIDIA A100-SXM4-80GB",
    "NVIDIA A30",
    "NVIDIA A40",
    "NVIDIA B200",
    "NVIDIA GeForce RTX 3070",
    "NVIDIA GeForce RTX 3080",
    "NVIDIA GeForce RTX 3080 Ti",
    "NVIDIA GeForce RTX 3090",
    "NVIDIA GeForce RTX 3090 Ti",
    "NVIDIA GeForce RTX 4070 Ti",
    "NVIDIA GeForce RTX 4080",
    "NVIDIA GeForce RTX 4080 SUPER",
    "NVIDIA GeForce RTX 4090",
    "NVIDIA GeForce RTX 5080",
    "NVIDIA GeForce RTX 5090",
    "NVIDIA H100 80GB HBM3",
    "NVIDIA H100 NVL",
    "NVIDIA H100 PCIe",
    "NVIDIA H200",
    "NVIDIA H200 NVL",
    "NVIDIA L4",
    "NVIDIA L40",
    "NVIDIA L40S",
    "NVIDIA RTX 2000 Ada Generation",
    "NVIDIA RTX 4000 Ada Generation",
    "NVIDIA RTX 4000 SFF Ada Generation",
    "NVIDIA RTX 5000 Ada Generation",
    "NVIDIA RTX 6000 Ada Generation",
    "NVIDIA RTX A2000",
    "NVIDIA RTX A4000",
    "NVIDIA RTX A4500",
    "NVIDIA RTX A5000",
    "NVIDIA RTX A6000",
    "NVIDIA RTX PRO 6000 Blackwell Server Edition",
    "NVIDIA RTX PRO 6000 Blackwell Workstation Edition",
    "AMD Instinct MI300X OAM",
    "Tesla T4",
    "Tesla V100-PCIE-16GB",
    "Tesla V100-SXM2-16GB",
    "Tesla V100-SXM2-32GB",
]

CPU_FLAVOR_IDS = ["cpu3c", "cpu3g", "cpu3m", "cpu5c", "cpu5g", "cpu5m"]

DATACENTER_IDS = [
    "AP-JP-1",
    "CA-MTL-1",
    "CA-MTL-2",
    "CA-MTL-3",
    "EU-CZ-1",
    "EU-FR-1",
    "EU-NL-1",
    "EU-RO-1",
    "EU-SE-1",
    "EUR-IS-1",
    "EUR-IS-2",
    "EUR-IS-3",
    "EUR-NO-1",
    "OC-AU-1",
    "US-CA-2",
    "US-DE-1",
    "US-GA-1",
    "US-GA-2",
    "US-IL-1",
    "US-KS-2",
    "US-KS-3",
    "US-NC-1",
    "US-TX-1",
    "US-TX-3",
    "US-TX-4",
    "US-WA-1",
]
