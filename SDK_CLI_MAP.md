# RunPod SDK → rpctl CLI Mapping

> Generated 2026-02-13. SDK version: runpod 1.8.1

## Legend

| Symbol | Meaning |
|--------|---------|
| **CLI** | Fully exposed as a CLI command with all relevant SDK params |
| **Partial** | CLI command exists but missing SDK parameters |
| **GQL** | rpctl uses its own GraphQL client (bypasses SDK) |
| **None** | No CLI command — gap |
| **N/A** | SDK function not relevant to CLI (worker-side, internal) |

---

## 1. Pod Management

### SDK Functions

| SDK Function | Signature | rpctl Command | Status |
|---|---|---|---|
| `runpod.create_pod(...)` | See params below | `rpctl pod create` | **CLI** |
| `runpod.get_pods()` | `api_key=None` | `rpctl pod list` | **CLI** |
| `runpod.get_pod(pod_id)` | `pod_id, api_key=None` | `rpctl pod get POD_ID` | **CLI** |
| `runpod.stop_pod(pod_id)` | `pod_id` | `rpctl pod stop POD_ID` | **CLI** |
| `runpod.resume_pod(pod_id, gpu_count)` | `pod_id, gpu_count` | `rpctl pod start POD_ID` | **CLI** |
| `runpod.terminate_pod(pod_id)` | `pod_id` | `rpctl pod delete POD_ID` | **CLI** |

### `runpod.create_pod()` Parameter Mapping

| SDK Parameter | Type | Default | CLI Flag | PodCreateParams Field | Passed to SDK? |
|---|---|---|---|---|---|
| `name` | str | (required) | `--name` | `name` | Yes |
| `image_name` | str | `""` | `--image` | `image_name` | Yes |
| `gpu_type_id` | str\|None | None | `--gpu` (single) | `gpu_type_id` | Yes |
| — (not in SDK) | — | — | `--gpu` (multi) | `gpu_type_ids` | Yes (custom) |
| `cloud_type` | str | `"ALL"` | `--cloud-type` | `cloud_type` | Yes |
| `support_public_ip` | bool | True | `--public-ip` | `support_public_ip` | **CLI** |
| `start_ssh` | bool | True | `--no-ssh` | `start_ssh` | **CLI** |
| `data_center_id` | str\|None | None | `--region` | `data_center_ids` | Yes (first only) |
| `country_code` | str\|None | None | `--country` | `country_code` | **CLI** |
| `gpu_count` | int | 1 | `--gpu-count` | `gpu_count` | Yes |
| `volume_in_gb` | int | 0 | `--volume-disk` | `volume_in_gb` | Yes |
| `container_disk_in_gb` | int\|None | None | `--container-disk` | `container_disk_in_gb` | Yes |
| `min_vcpu_count` | int | 1 | `--min-vcpu` | `min_vcpu_per_gpu` | Yes |
| `min_memory_in_gb` | int | 1 | `--min-ram` | `min_ram_per_gpu` | Yes |
| `docker_args` | str | `""` | `--entrypoint` | `docker_entrypoint` | **CLI** |
| `docker_start_cmd` | str\|None | None | `--docker-start-cmd` | `docker_start_cmd` | **CLI** |
| `ports` | str\|None | None | `--ports` | `ports` | Yes |
| `volume_mount_path` | str | `"/runpod-volume"` | `--volume-mount` | `volume_mount_path` | Yes |
| `env` | dict\|None | None | `--env` | `env` | Yes |
| `template_id` | str\|None | None | `--template` | `template_id` | Yes |
| `network_volume_id` | str\|None | None | `--network-volume` | `network_volume_id` | Yes |
| `allowed_cuda_versions` | list\|None | None | `--cuda-version` | `allowed_cuda_versions` | **CLI** |
| `min_download` | — | None | `--min-download` | — | **CLI** |
| `min_upload` | — | None | `--min-upload` | — | **CLI** |
| `instance_id` | str\|None | None | — | — | Not needed (internal) |
| — (custom) | — | — | `--spot` | `interruptible` | Yes (maps to `bid_per_gpu=0.0`) |
| — (custom) | — | — | `--cpu` | `cpu_flavor_ids` | Yes (custom) |

### Pod Gaps Summary

All gaps closed. All pod parameters are now exposed via CLI flags:
- `--docker-start-cmd` ✓
- `--public-ip` ✓
- `--cuda-version` ✓
- `--entrypoint` ✓
- `--no-ssh` ✓
- `--country` ✓
- `--min-download`/`--min-upload` ✓
- `rpctl pod wait POD_ID` ✓

---

## 2. Template Management

### SDK Functions

| SDK Function | Signature | rpctl Command | Status |
|---|---|---|---|
| `runpod.create_template(...)` | See params below | `rpctl template create` | **CLI** (just updated) |
| — | — | `rpctl template list` | **GQL** (custom query) |
| — | — | `rpctl template get TMPL_ID` | **GQL** (custom query) |
| — | — | `rpctl template update TMPL_ID` | **GQL** (custom mutation) |
| — | — | `rpctl template delete TMPL_ID` | **GQL** (custom mutation) |

> The RunPod SDK only has `create_template()`. Our CLI uses custom GraphQL for list/get/update/delete via `RestClient` wrappers.

### `runpod.create_template()` Parameter Mapping

| SDK Parameter | Type | Default | CLI Flag | Passed? |
|---|---|---|---|---|
| `name` | str | (required) | `--name` | Yes |
| `image_name` | str | (required) | `--image` | Yes |
| `docker_start_cmd` | str\|None | None | `--docker-start-cmd` | Yes |
| `container_disk_in_gb` | int | 10 | `--container-disk` | Yes |
| `volume_in_gb` | int\|None | None | `--volume-disk` | Yes |
| `volume_mount_path` | str\|None | None | `--volume-mount-path` | Yes |
| `ports` | str\|None | None | `--ports` | Yes |
| `env` | dict\|None | None | `--env` | Yes |
| `is_serverless` | bool | False | `--serverless` | Yes |
| `registry_auth_id` | str\|None | None | `--registry-auth` | Yes |

### Template Gaps Summary

| Gap | Severity | Fix |
|-----|----------|-----|
| All parameters now covered | — | **None — fully mapped** |

---

## 3. Endpoint Management

### SDK Functions

| SDK Function | Signature | rpctl Command | Status |
|---|---|---|---|
| `runpod.create_endpoint(...)` | See params below | `rpctl endpoint create` | **CLI** |
| `runpod.get_endpoints()` | (none) | `rpctl endpoint list` | **CLI** |
| — | — | `rpctl endpoint get EP_ID` | **GQL** (custom query) |
| `runpod.update_endpoint_template(ep_id, tmpl_id)` | `endpoint_id, template_id` | `rpctl endpoint update EP_ID` | **CLI** (extended) |
| — | — | `rpctl endpoint delete EP_ID` | **GQL** (custom mutation) |
| `Endpoint(ep_id).health()` | `timeout=3` | `rpctl endpoint health EP_ID` | **CLI** |
| `Endpoint(ep_id).run(input)` | `request_input` → Job | `rpctl endpoint run EP_ID --input '{...}'` | **CLI** |
| `Endpoint(ep_id).run_sync(input)` | `request_input, timeout=86400` | `rpctl endpoint run EP_ID --wait` | **CLI** |
| `Endpoint(ep_id).purge_queue()` | `timeout=3` | `rpctl endpoint purge-queue EP_ID` | **CLI** |
| `Job.status()` | — | `rpctl endpoint job-status EP_ID JOB_ID` | **CLI** |
| `Job.output(timeout)` | `timeout=0` | `rpctl endpoint job-status EP_ID JOB_ID --output` | **CLI** |
| `Job.cancel(timeout)` | `timeout=3` | `rpctl endpoint job-cancel EP_ID JOB_ID` | **CLI** |
| `Job.stream()` | — | — | **Stretch Goal** |

### `runpod.create_endpoint()` Parameter Mapping

| SDK Parameter | Type | Default | CLI Flag | Passed? |
|---|---|---|---|---|
| `name` | str | (required) | `--name` | Yes |
| `template_id` | str | (required) | `--template` | Yes |
| `gpu_ids` | str | `"AMPERE_16"` | `--gpu` | Yes |
| `network_volume_id` | str\|None | None | `--network-volume` | Yes |
| `locations` | str\|None | None | `--locations` | Yes |
| `idle_timeout` | int | 5 | `--idle-timeout` | Yes |
| `scaler_type` | str | `"QUEUE_DELAY"` | `--scaler-type` | Yes |
| `scaler_value` | int | 4 | `--scaler-value` | Yes |
| `workers_min` | int | 0 | `--workers-min` | Yes |
| `workers_max` | int | 3 | `--workers-max` | Yes |
| `flashboot` | bool | False | `--flashboot` | Yes |
| `allowed_cuda_versions` | str\|None | None | `--cuda-version` | **CLI** |
| `gpu_count` | int | 1 | `--gpu-count` | Yes |

### Endpoint Gaps Summary

All endpoint gaps closed:
- `rpctl endpoint health EP_ID` ✓
- `rpctl endpoint wait EP_ID` ✓
- `rpctl endpoint run EP_ID` ✓
- `rpctl endpoint purge-queue EP_ID` ✓
- `rpctl endpoint job-status EP_ID JOB_ID` ✓
- `rpctl endpoint job-cancel EP_ID JOB_ID` ✓
- `--cuda-version` on create ✓

---

## 4. Volume Management

### SDK Functions

> The RunPod Python SDK (v1.8.1) exposes **NO** volume management functions. Our CLI implements all volume operations via custom GraphQL queries through `RestClient` wrappers.

| SDK Function | rpctl Command | Status |
|---|---|---|
| — | `rpctl volume create --name --size --region` | **GQL** (custom) |
| — | `rpctl volume list` | **GQL** (custom) |
| — | `rpctl volume get VOL_ID` | **GQL** (custom) |
| — | `rpctl volume update VOL_ID` | **GQL** (custom) |
| — | `rpctl volume delete VOL_ID` | **GQL** (custom) |

### Volume Gaps Summary

| Gap | Severity | Fix |
|-----|----------|-----|
| No SDK functions to wrap — all custom GQL | INFO | Working as designed |

---

## 5. Capacity & GPU Info

### SDK Functions

| SDK Function | Signature | rpctl Command | Status |
|---|---|---|---|
| `runpod.get_gpus()` | `api_key=None` | `rpctl capacity list` | **GQL** (richer query) |
| `runpod.get_gpu(gpu_id)` | `gpu_id, gpu_quantity=1` | `rpctl capacity check --gpu ID` | **GQL** (richer query) |
| — | — | `rpctl capacity regions` | **GQL** (custom query) |
| — | — | `rpctl capacity compare GPU1 GPU2` | **GQL** (computed) |

> Our capacity commands use custom GraphQL for richer data (pricing tiers, per-datacenter availability) than the SDK provides.

### Capacity Gaps Summary

All capacity gaps closed:
- CPU capacity listing: `rpctl capacity cpus` ✓

---

## 6. User/Account Management

### SDK Functions

| SDK Function | Signature | rpctl Command | Status |
|---|---|---|---|
| `runpod.get_user()` | `api_key=None` | `rpctl user info` | **CLI** |
| `runpod.update_user_settings(pubkey)` | `pubkey, api_key=None` | `rpctl user set-ssh-key` | **CLI** |

### User Gaps Summary

All user gaps closed:
- `rpctl user info` ✓
- `rpctl user set-ssh-key` ✓

---

## 7. Container Registry Auth

### SDK Functions

| SDK Function | Signature | rpctl Command | Status |
|---|---|---|---|
| `runpod.create_container_registry_auth(name, user, pass)` | name, username, password | `rpctl registry create` | **CLI** |
| `runpod.update_container_registry_auth(id, user, pass)` | registry_auth_id, username, password | `rpctl registry update` | **CLI** |
| `runpod.delete_container_registry_auth(id)` | registry_auth_id | `rpctl registry delete` | **CLI** |

### Registry Gaps Summary

All registry gaps closed:
- `rpctl registry create` ✓
- `rpctl registry update` ✓
- `rpctl registry delete` ✓
- `rpctl registry list` ✓

---

## 8. SSH / Key Management

### SDK Constants

| SDK Item | rpctl Command | Status |
|---|---|---|
| `runpod.SSH_KEY_PATH` | — | Not used (rpctl uses system ssh) |

### SSH in rpctl

| rpctl Command | What it does | Status |
|---|---|---|
| `rpctl ssh connect POD_ID` | SSH into running pod | **CLI** |
| `rpctl ssh connect --dry-run` | Print SSH command | **CLI** |
| `rpctl ssh connect --user --key --command` | Custom SSH options | **CLI** |

---

## 9. Serverless Worker Functions (Not Applicable to CLI)

These SDK functions are for building serverless handlers, not for CLI management:

| SDK Function | Purpose | CLI Relevance |
|---|---|---|
| `runpod.serverless.start(config)` | Start serverless worker | N/A |
| `runpod.RunPodLogger` | Structured logging | N/A |
| `runpod.serverless.progress_update()` | Report job progress | N/A |

---

## 10. Low-Level GraphQL Access

### SDK Internal Functions Available

| Function | Purpose | Used by rpctl? |
|---|---|---|
| `runpod.api.graphql.run_graphql_query(query)` | Raw GraphQL execution | No (we use httpx directly) |
| `runpod.api.mutations.pods.*` | Pod mutation generators | No |
| `runpod.api.mutations.templates.*` | Template mutation generators | No |
| `runpod.api.mutations.endpoints.*` | Endpoint mutation generators | No |
| `runpod.api.queries.pods.*` | Pod query generators | No |
| `runpod.api.queries.gpus.*` | GPU query generators | No |

> rpctl maintains its own GraphQL client (`GraphQLClient`) using httpx for capacity queries and operations the SDK doesn't expose (templates list/get/update/delete, volumes, etc.).

---

## Gap Priority Matrix — ALL CLOSED

All 18 gaps from the original audit have been implemented with full test coverage.

| # | Gap | CLI Command | Status |
|---|-----|-------------|--------|
| 1 | Pod `docker_start_cmd` not passed to SDK | `rpctl pod create --docker-start-cmd` | **DONE** |
| 2 | Pod wait/poll command | `rpctl pod wait POD_ID` | **DONE** |
| 3 | Endpoint health check | `rpctl endpoint health EP_ID` | **DONE** |
| 4 | Endpoint wait/poll | `rpctl endpoint wait EP_ID` | **DONE** |
| 5 | Pod `--public-ip` flag | `rpctl pod create --public-ip` | **DONE** |
| 6 | Pod `--entrypoint` flag | `rpctl pod create --entrypoint` | **DONE** |
| 7 | Endpoint run/invoke | `rpctl endpoint run EP_ID` | **DONE** |
| 8 | User info | `rpctl user info` | **DONE** |
| 9 | Container registry CRUD | `rpctl registry create/update/delete/list` | **DONE** |
| 10 | Pod `--cuda-version` flag | `rpctl pod create --cuda-version` | **DONE** |
| 11 | Endpoint purge-queue | `rpctl endpoint purge-queue EP_ID` | **DONE** |
| 12 | Endpoint job status/cancel | `rpctl endpoint job-status/job-cancel` | **DONE** |
| 13 | User SSH key upload | `rpctl user set-ssh-key` | **DONE** |
| 14 | CPU capacity listing | `rpctl capacity cpus` | **DONE** |
| 15 | `start_ssh` on pod create | `rpctl pod create --no-ssh` | **DONE** |
| 16 | `country_code` on pod create | `rpctl pod create --country` | **DONE** |
| 17 | `min_download`/`min_upload` on pod create | `rpctl pod create --min-download/--min-upload` | **DONE** |
| 18 | Endpoint `--cuda-versions` on create | `rpctl endpoint create --cuda-version` | **DONE** |

---

## Remaining Stretch Goals (not in SDK)

These items require features not exposed by the RunPod SDK (v1.8.1):

- `Job.stream()` — live streaming output from serverless jobs
- Template list/get/update/delete — already implemented via custom GQL
- Volume CRUD — already implemented via custom GQL
