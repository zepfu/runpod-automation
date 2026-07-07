"""GraphQL query strings for RunPod API."""

from __future__ import annotations

from typing import Any

GPU_TYPES_LIST = """
query GpuTypes {
  gpuTypes {
    id
    displayName
    manufacturer
    memoryInGb
    cudaCores
    secureCloud
    communityCloud
    securePrice
    communityPrice
    secureSpotPrice
    communitySpotPrice
    maxGpuCount
    maxGpuCountSecureCloud
    maxGpuCountCommunityCloud
    lowestPrice(input: {gpuCount: 1}) {
      minimumBidPrice
      uninterruptablePrice
      stockStatus
      rentedCount
      totalCount
      rentalPercentage
      maxUnreservedGpuCount
      availableGpuCounts
    }
  }
}
"""

GPU_TYPE_AVAILABILITY = """
query GpuTypeAvailability($gpuTypeId: String!, $gpuCount: Int!, $secureCloud: Boolean) {
  gpuTypes(input: {id: $gpuTypeId}) {
    id
    displayName
    memoryInGb
    securePrice
    communityPrice
    secureSpotPrice
    communitySpotPrice
    lowestPrice(input: {gpuCount: $gpuCount, secureCloud: $secureCloud}) {
      minimumBidPrice
      uninterruptablePrice
      stockStatus
      rentedCount
      totalCount
      rentalPercentage
      maxUnreservedGpuCount
      availableGpuCounts
      countryCode
    }
  }
}
"""

DATACENTER_AVAILABILITY = """
query DatacenterAvailability {
  myself {
    datacenters {
      id
      name
      location
      region
      listed
      storageSupport
      gpuAvailability(input: {gpuCount: 1}) {
        gpuTypeId
        gpuTypeDisplayName
        available
        stockStatus
      }
    }
  }
}
"""

CPU_TYPES_LIST = """
query CpuTypes {
  cpuTypes {
    id
    displayName
    manufacturer
    cores
    threadsPerCore
    groupId
  }
}
"""

# --- Endpoints ---

ENDPOINT_LIST = """
query {
  myself {
    endpoints {
      aiKey
      gpuIds
      id
      idleTimeout
      name
      networkVolumeId
      locations
      scalerType
      scalerValue
      templateId
      type
      userId
      version
      workersMax
      workersMin
      workersStandby
      gpuCount
      env {
        key
        value
      }
      createdAt
      networkVolume {
        id
        dataCenterId
      }
    }
  }
}
"""

_SAVE_ENDPOINT_RETURN_FIELDS = """
    id
    name
    templateId
    gpuIds
    networkVolumeId
    locations
    idleTimeout
    scalerType
    scalerValue
    workersMin
    workersMax
    allowedCudaVersions
    gpuCount
"""


def build_save_endpoint_mutation(params: dict[str, Any]) -> str:
    """Build a saveEndpoint mutation string from a dict of parameters.

    Used for both create (omit 'id') and update (include 'id').
    """
    input_fields: list[str] = []
    str_fields = {
        "id", "name", "templateId", "gpuIds", "networkVolumeId",
        "locations", "scalerType", "allowedCudaVersions",
    }
    int_fields = {
        "idleTimeout", "scalerValue", "workersMin", "workersMax", "gpuCount",
    }
    bool_fields = {"flashboot"}

    for key, value in params.items():
        if value is None:
            continue
        if key in str_fields:
            input_fields.append(f'{key}: "{value}"')
        elif key in int_fields:
            input_fields.append(f"{key}: {value}")
        elif key in bool_fields:
            input_fields.append(f"{key}: {str(value).lower()}")

    fields_str = ", ".join(input_fields)
    return f"""
    mutation {{
        saveEndpoint(input: {{{fields_str}}}) {{{_SAVE_ENDPOINT_RETURN_FIELDS}}}
    }}
    """


def build_delete_endpoint_mutation(endpoint_id: str) -> str:
    """Build a deleteEndpoint mutation string."""
    return f"""
    mutation {{
        deleteEndpoint(id: "{endpoint_id}")
    }}
    """


# --- Templates ---

TEMPLATE_LIST = """
query {
  podTemplates {
    id
    name
    imageName
    dockerArgs
    containerDiskInGb
    volumeInGb
    volumeMountPath
    ports
    env {
      key
      value
    }
    isServerless
    startSsh
    isPublic
    readme
    containerRegistryAuthId
  }
}
"""

_TEMPLATE_RETURN_FIELDS = """
    id
    name
    imageName
    dockerArgs
    containerDiskInGb
    volumeInGb
    volumeMountPath
    ports
    env {
      key
      value
    }
    isServerless
"""


def build_template_get_query(template_id: str) -> str:
    """Build a query to get a single template by ID."""
    return f"""
    query {{
        podTemplate(id: "{template_id}") {{{_TEMPLATE_RETURN_FIELDS}}}
    }}
    """


def build_save_template_mutation(params: dict[str, Any]) -> str:
    """Build a saveTemplate mutation string from a dict of parameters.

    Used for both create (omit 'id') and update (include 'id').
    """
    input_fields: list[str] = []
    str_fields = {
        "id", "name", "imageName", "dockerArgs", "volumeMountPath",
        "ports", "readme", "containerRegistryAuthId",
    }
    int_fields = {"containerDiskInGb", "volumeInGb"}
    bool_fields = {"isServerless", "startSsh", "isPublic"}

    for key, value in params.items():
        if value is None:
            continue
        if key == "env" and isinstance(value, list):
            env_entries = ", ".join(
                f'{{key: "{e["key"]}", value: "{e["value"]}"}}'
                for e in value
            )
            input_fields.append(f"env: [{env_entries}]")
        elif key in str_fields:
            input_fields.append(f'{key}: "{value}"')
        elif key in int_fields:
            input_fields.append(f"{key}: {value}")
        elif key in bool_fields:
            input_fields.append(f"{key}: {str(value).lower()}")

    fields_str = ", ".join(input_fields)
    return f"""
    mutation {{
        saveTemplate(input: {{{fields_str}}}) {{{_TEMPLATE_RETURN_FIELDS}}}
    }}
    """


def build_delete_template_mutation(template_name: str) -> str:
    """Build a deleteTemplate mutation. NOTE: uses template name, not ID."""
    return f"""
    mutation {{
        deleteTemplate(templateName: "{template_name}")
    }}
    """


# --- Network Volumes ---

VOLUME_LIST = """
query {
  myself {
    networkVolumes {
      id
      name
      size
      dataCenterId
    }
  }
}
"""

_VOLUME_RETURN_FIELDS = "id name size dataCenterId"


def build_create_volume_mutation(
    name: str, size: int, data_center_id: str,
) -> str:
    """Build a createNetworkVolume mutation."""
    return f"""
    mutation {{
        createNetworkVolume(input: {{
            name: "{name}",
            size: {size},
            dataCenterId: "{data_center_id}"
        }}) {{ {_VOLUME_RETURN_FIELDS} }}
    }}
    """


def build_update_volume_mutation(volume_id: str, **kwargs: Any) -> str:
    """Build an updateNetworkVolume mutation."""
    input_fields = [f'id: "{volume_id}"']
    for key, value in kwargs.items():
        if isinstance(value, str):
            input_fields.append(f'{key}: "{value}"')
        elif isinstance(value, int):
            input_fields.append(f"{key}: {value}")
    fields_str = ", ".join(input_fields)
    return f"""
    mutation {{
        updateNetworkVolume(input: {{{fields_str}}}) {{ {_VOLUME_RETURN_FIELDS} }}
    }}
    """


def build_delete_volume_mutation(volume_id: str) -> str:
    """Build a deleteNetworkVolume mutation."""
    return f"""
    mutation {{
        deleteNetworkVolume(input: {{id: "{volume_id}"}})
    }}
    """


# --- Pod Mutations ---


def build_pod_edit_mutation(pod_id: str, **kwargs: Any) -> str:
    """Build a podEditJob mutation for editing a running/stopped pod."""
    input_fields = [f'podId: "{pod_id}"']
    str_fields = {"imageName", "dockerArgs", "volumeMountPath", "ports", "dockerStartCmd"}
    int_fields = {"containerDiskInGb", "volumeInGb"}

    for key, value in kwargs.items():
        if value is None:
            continue
        if key == "env" and isinstance(value, list):
            env_entries = ", ".join(
                f'{{key: "{e["key"]}", value: "{e["value"]}"}}'
                for e in value
            )
            input_fields.append(f"env: [{env_entries}]")
        elif key in str_fields:
            input_fields.append(f'{key}: "{value}"')
        elif key in int_fields:
            input_fields.append(f"{key}: {value}")

    fields_str = ", ".join(input_fields)
    return f"""
    mutation {{
        podEditJob(input: {{{fields_str}}}) {{
            id
            desiredStatus
            imageName
            containerDiskInGb
            volumeInGb
            volumeMountPath
            ports
        }}
    }}
    """


def build_pod_migrate_mutation(
    pod_id: str,
    gpu_type_id: str | None = None,
    bid_per_gpu: float | None = None,
) -> str:
    """Build a podBidResume mutation for migrating a stopped pod."""
    input_fields = [f'podId: "{pod_id}"']
    if gpu_type_id:
        input_fields.append(f'gpuTypeId: "{gpu_type_id}"')
    if bid_per_gpu is not None:
        input_fields.append(f"bidPerGpu: {bid_per_gpu}")
    fields_str = ", ".join(input_fields)
    return f"""
    mutation {{
        podBidResume(input: {{{fields_str}}}) {{
            id
            desiredStatus
            machineId
        }}
    }}
    """


def build_pod_reset_mutation(pod_id: str, hard_reset: bool = False) -> str:
    """Build a podReset mutation."""
    hard_str = "true" if hard_reset else "false"
    return f"""
    mutation {{
        podReset(input: {{podId: "{pod_id}", hardReset: {hard_str}}})
    }}
    """


# --- Account ---

ACCOUNT_INFO = """
query {
  myself {
    clientBalance
    currentSpendPerHr
    spendLimit
  }
}
"""

# --- Secrets ---

SECRETS_LIST = """
query {
  myself {
    secrets {
      name
      value
    }
  }
}
"""


def build_add_secret_mutation(name: str, value: str) -> str:
    """Build an addSecret mutation."""
    # Escape quotes in value
    escaped_value = value.replace('"', '\\"')
    escaped_name = name.replace('"', '\\"')
    return f"""
    mutation {{
        addSecret(input: {{name: "{escaped_name}", value: "{escaped_value}"}})
    }}
    """


def build_delete_secret_mutation(name: str) -> str:
    """Build a deleteSecret mutation."""
    escaped_name = name.replace('"', '\\"')
    return f"""
    mutation {{
        deleteSecret(input: {{name: "{escaped_name}"}})
    }}
    """


# --- User ---

USER_INFO = """
query myself {
    myself {
        id
        pubKey
        networkVolumes {
            id
            name
            size
            dataCenterId
        }
    }
}
"""


def build_update_user_settings_mutation(pubkey: str) -> str:
    """Build an updateUserSettings mutation."""
    escaped = pubkey.replace("\\n", "\\\\n").replace('"', '\\\\"')
    return f"""
    mutation {{
        updateUserSettings(input: {{pubKey: "{escaped}"}}) {{
            id
            pubKey
        }}
    }}
    """


# --- Container Registry Auth ---

REGISTRY_AUTH_LIST = """
query {
    myself {
        containerRegistryAuths {
            id
            name
        }
    }
}
"""


def build_create_registry_auth_mutation(name: str, username: str, password: str) -> str:
    """Build a saveRegistryAuth mutation."""
    escaped_password = password.replace('"', '\\\\"')
    return f"""
    mutation {{
        saveRegistryAuth(input: {{name: "{name}", username: "{username}", password: "{escaped_password}"}}) {{
            id
            name
        }}
    }}
    """


def build_update_registry_auth_mutation(registry_auth_id: str, username: str, password: str) -> str:
    """Build an updateRegistryAuth mutation."""
    escaped_password = password.replace('"', '\\\\"')
    return f"""
    mutation {{
        updateRegistryAuth(input: {{id: "{registry_auth_id}", username: "{username}", password: "{escaped_password}"}}) {{
            id
            name
        }}
    }}
    """


def build_delete_registry_auth_mutation(registry_auth_id: str) -> str:
    """Build a deleteRegistryAuth mutation."""
    return f"""
    mutation {{
        deleteRegistryAuth(registryAuthId: "{registry_auth_id}")
    }}
    """


# --- Pod Queries ---

POD_LIST = """
query myPods {
    myself {
        pods {
            id
            containerDiskInGb
            costPerHr
            desiredStatus
            dockerArgs
            dockerId
            env
            gpuCount
            imageName
            lastStatusChange
            machineId
            memoryInGb
            name
            podType
            port
            ports
            uptimeSeconds
            vcpuCount
            volumeInGb
            volumeMountPath
            runtime {
                ports {
                    ip
                    isIpPublic
                    privatePort
                    publicPort
                    type
                }
            }
            machine {
                gpuDisplayName
            }
        }
    }
}
"""


def build_pod_get_query(pod_id: str) -> str:
    """Build a query for a single pod by ID."""
    return f"""
    query pod {{
        pod(input: {{podId: "{pod_id}"}}) {{
            id
            containerDiskInGb
            costPerHr
            desiredStatus
            dockerArgs
            dockerId
            env
            gpuCount
            imageName
            lastStatusChange
            machineId
            memoryInGb
            name
            podType
            port
            ports
            uptimeSeconds
            vcpuCount
            volumeInGb
            volumeMountPath
            runtime {{
                ports {{
                    ip
                    isIpPublic
                    privatePort
                    publicPort
                    type
                }}
            }}
            machine {{
                gpuDisplayName
            }}
        }}
    }}
    """


def build_pod_create_mutation(**kwargs: Any) -> str:
    """Build a podFindAndDeployOnDemand or deployCpuPod mutation."""
    input_fields: list[str] = []

    # Required fields
    input_fields.append(f'name: "{kwargs.get("name", "rpctl-pod")}"')
    input_fields.append(f'imageName: "{kwargs.get("image_name", "")}"')
    input_fields.append(f'cloudType: {kwargs.get("cloud_type", "ALL")}')

    if kwargs.get("start_ssh", True):
        input_fields.append("startSsh: true")

    gpu_type_id = kwargs.get("gpu_type_id")
    gpu_type_ids = kwargs.get("gpu_type_ids")

    # GPU Pod fields
    if gpu_type_id is not None:
        input_fields.append(f'gpuTypeId: "{gpu_type_id}"')
        input_fields.append(f'supportPublicIp: {str(kwargs.get("support_public_ip", True)).lower()}')

        if kwargs.get("gpu_count") is not None:
            input_fields.append(f'gpuCount: {kwargs["gpu_count"]}')
        if kwargs.get("volume_in_gb") is not None:
            input_fields.append(f'volumeInGb: {kwargs["volume_in_gb"]}')
        if kwargs.get("min_vcpu_count") is not None:
            input_fields.append(f'minVcpuCount: {kwargs["min_vcpu_count"]}')
        if kwargs.get("min_memory_in_gb") is not None:
            input_fields.append(f'minMemoryInGb: {kwargs["min_memory_in_gb"]}')
        if kwargs.get("docker_args") is not None:
            input_fields.append(f'dockerArgs: "{kwargs["docker_args"]}"')
        if kwargs.get("allowed_cuda_versions"):
            cuda_versions = ", ".join(f'"{v}"' for v in kwargs["allowed_cuda_versions"])
            input_fields.append(f"allowedCudaVersions: [{cuda_versions}]")
    elif gpu_type_ids:
        # Multiple GPU type IDs
        ids_str = ", ".join(f'"{gid}"' for gid in gpu_type_ids)
        input_fields.append(f"gpuTypeIds: [{ids_str}]")
        input_fields.append(f'supportPublicIp: {str(kwargs.get("support_public_ip", True)).lower()}')

        if kwargs.get("gpu_count") is not None:
            input_fields.append(f'gpuCount: {kwargs["gpu_count"]}')
        if kwargs.get("volume_in_gb") is not None:
            input_fields.append(f'volumeInGb: {kwargs["volume_in_gb"]}')
        if kwargs.get("min_vcpu_count") is not None:
            input_fields.append(f'minVcpuCount: {kwargs["min_vcpu_count"]}')
        if kwargs.get("min_memory_in_gb") is not None:
            input_fields.append(f'minMemoryInGb: {kwargs["min_memory_in_gb"]}')
        if kwargs.get("docker_args") is not None:
            input_fields.append(f'dockerArgs: "{kwargs["docker_args"]}"')
        if kwargs.get("allowed_cuda_versions"):
            cuda_versions = ", ".join(f'"{v}"' for v in kwargs["allowed_cuda_versions"])
            input_fields.append(f"allowedCudaVersions: [{cuda_versions}]")

    # Optional fields
    if kwargs.get("data_center_id") is not None:
        input_fields.append(f'dataCenterId: "{kwargs["data_center_id"]}"')
    if kwargs.get("country_code") is not None:
        input_fields.append(f'countryCode: "{kwargs["country_code"]}"')
    if kwargs.get("container_disk_in_gb") is not None:
        input_fields.append(f'containerDiskInGb: {kwargs["container_disk_in_gb"]}')
    if kwargs.get("ports") is not None:
        input_fields.append(f'ports: "{kwargs["ports"]}"')
    if kwargs.get("volume_mount_path") is not None:
        input_fields.append(f'volumeMountPath: "{kwargs["volume_mount_path"]}"')
    if kwargs.get("env") is not None:
        env = kwargs["env"]
        if isinstance(env, dict):
            env_items = [f'{{ key: "{k}", value: "{v}" }}' for k, v in env.items()]
            input_fields.append(f"env: [{', '.join(env_items)}]")
    if kwargs.get("template_id") is not None:
        input_fields.append(f'templateId: "{kwargs["template_id"]}"')
    if kwargs.get("network_volume_id") is not None:
        input_fields.append(f'networkVolumeId: "{kwargs["network_volume_id"]}"')
    if kwargs.get("docker_start_cmd") is not None:
        input_fields.append(f'dockerStartCmd: "{kwargs["docker_start_cmd"]}"')
    if kwargs.get("min_download") is not None:
        input_fields.append(f'minDownload: {kwargs["min_download"]}')
    if kwargs.get("min_upload") is not None:
        input_fields.append(f'minUpload: {kwargs["min_upload"]}')
    if kwargs.get("bid_per_gpu") is not None:
        input_fields.append(f'bidPerGpu: {kwargs["bid_per_gpu"]}')

    mutation_type = "podFindAndDeployOnDemand" if gpu_type_id or gpu_type_ids else "deployCpuPod"
    input_string = ", ".join(input_fields)

    return f"""
    mutation {{
        {mutation_type}(input: {{{input_string}}}) {{
            id
            imageName
            env
            machineId
            machine {{
                podHostId
            }}
        }}
    }}
    """


def build_pod_stop_mutation(pod_id: str) -> str:
    """Build a podStop mutation."""
    return f"""
    mutation {{
        podStop(input: {{ podId: "{pod_id}" }}) {{
            id
            desiredStatus
        }}
    }}
    """


def build_pod_resume_mutation(pod_id: str, gpu_count: int = 1) -> str:
    """Build a podResume mutation."""
    return f"""
    mutation {{
        podResume(input: {{ podId: "{pod_id}", gpuCount: {gpu_count} }}) {{
            id
            desiredStatus
            imageName
            env
            machineId
            machine {{
                podHostId
            }}
        }}
    }}
    """


def build_pod_terminate_mutation(pod_id: str) -> str:
    """Build a podTerminate mutation."""
    return f"""
    mutation {{
        podTerminate(input: {{ podId: "{pod_id}" }})
    }}
    """
