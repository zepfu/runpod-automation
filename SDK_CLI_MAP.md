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
| `runpod.create_pod(...)` | See params below | `rpctl pod create` | **Partial** |
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
| `support_public_ip` | bool | True | — | `support_public_ip` | **GAP: field exists, no CLI flag** |
| `start_ssh` | bool | True | — | — | **GAP: not mapped** |
| `data_center_id` | str\|None | None | `--region` | `data_center_ids` | Yes (first only) |
| `country_code` | str\|None | None | — | — | **GAP: not mapped** |
| `gpu_count` | int | 1 | `--gpu-count` | `gpu_count` | Yes |
| `volume_in_gb` | int | 0 | `--volume-disk` | `volume_in_gb` | Yes |
| `container_disk_in_gb` | int\|None | None | `--container-disk` | `container_disk_in_gb` | Yes |
| `min_vcpu_count` | int | 1 | `--min-vcpu` | `min_vcpu_per_gpu` | Yes |
| `min_memory_in_gb` | int | 1 | `--min-ram` | `min_ram_per_gpu` | Yes |
| `docker_args` | str | `""` | — | `docker_entrypoint` | Yes (maps to `docker_args`) |
| — (not in SDK directly) | — | — | — | `docker_start_cmd` | **GAP: field exists, not passed to SDK** |
| `ports` | str\|None | None | `--ports` | `ports` | Yes |
| `volume_mount_path` | str | `"/runpod-volume"` | `--volume-mount` | `volume_mount_path` | Yes |
| `env` | dict\|None | None | `--env` | `env` | Yes |
| `template_id` | str\|None | None | `--template` | `template_id` | Yes |
| `network_volume_id` | str\|None | None | `--network-volume` | `network_volume_id` | Yes |
| `allowed_cuda_versions` | list\|None | None | — | `allowed_cuda_versions` | **GAP: field exists, no CLI flag, not passed to SDK** |
| `min_download` | — | None | — | — | **GAP: not mapped** |
| `min_upload` | — | None | — | — | **GAP: not mapped** |
| `instance_id` | str\|None | None | — | — | Not needed (internal) |
| — (custom) | — | — | `--spot` | `interruptible` | Yes (maps to `bid_per_gpu=0.0`) |
| — (custom) | — | — | `--cpu` | `cpu_flavor_ids` | Yes (custom) |

### Pod Gaps Summary

| Gap | Severity | Fix |
|-----|----------|-----|
| `--docker-start-cmd` not passed to SDK in `to_sdk_kwargs()` | **CRITICAL** | Add `docker_start_cmd` mapping |
| `--public-ip` CLI flag missing | HIGH | Add flag, wire to `support_public_ip` |
| `--cuda-versions` CLI flag missing | MEDIUM | Add flag, wire to `allowed_cuda_versions` |
| `--entrypoint` CLI flag missing | MEDIUM | Add flag, wire to `docker_entrypoint` → `docker_args` |
| `start_ssh` not exposed | LOW | Usually True, rarely needs override |
| `country_code` not exposed | LOW | `--region` covers datacenter ID |
| `min_download`/`min_upload` not exposed | LOW | Niche use cases |
| `rpctl pod wait POD_ID` missing | **CRITICAL** | Add polling command |

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
| `runpod.create_endpoint(...)` | See params below | `rpctl endpoint create` | **Partial** |
| `runpod.get_endpoints()` | (none) | `rpctl endpoint list` | **CLI** |
| — | — | `rpctl endpoint get EP_ID` | **GQL** (custom query) |
| `runpod.update_endpoint_template(ep_id, tmpl_id)` | `endpoint_id, template_id` | `rpctl endpoint update EP_ID` | **CLI** (extended) |
| — | — | `rpctl endpoint delete EP_ID` | **GQL** (custom mutation) |
| `Endpoint(ep_id).health()` | `timeout=3` | — | **GAP** |
| `Endpoint(ep_id).run(input)` | `request_input` → Job | — | **GAP** |
| `Endpoint(ep_id).run_sync(input)` | `request_input, timeout=86400` | — | **GAP** |
| `Endpoint(ep_id).purge_queue()` | `timeout=3` | — | **GAP** |
| `Job.status()` | — | — | **GAP** |
| `Job.output(timeout)` | `timeout=0` | — | **GAP** |
| `Job.cancel(timeout)` | `timeout=3` | — | **GAP** |
| `Job.stream()` | — | — | **GAP** |

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
| `allowed_cuda_versions` | str\|None | None | — | **GAP: not exposed** |
| `gpu_count` | int | 1 | `--gpu-count` | Yes |

### Endpoint Gaps Summary

| Gap | Severity | Fix |
|-----|----------|-----|
| `rpctl endpoint health EP_ID` | **CRITICAL** | Add command using `Endpoint.health()` |
| `rpctl endpoint wait EP_ID` | **CRITICAL** | Add polling wait using health check |
| `rpctl endpoint run EP_ID --input '{}'` | HIGH | Add sync/async job submission |
| `rpctl endpoint purge-queue EP_ID` | MEDIUM | Add command using `Endpoint.purge_queue()` |
| `rpctl endpoint job-status EP_ID JOB_ID` | MEDIUM | Add command using `Job.status()`/`output()` |
| `rpctl endpoint job-cancel EP_ID JOB_ID` | LOW | Add command using `Job.cancel()` |
| `--cuda-versions` on create | LOW | Wire to `allowed_cuda_versions` |

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

| Gap | Severity | Fix |
|-----|----------|-----|
| CPU capacity listing | MEDIUM | Query is defined (`CPU_TYPES_LIST`) but not exposed as CLI flag |

---

## 6. User/Account Management

### SDK Functions

| SDK Function | Signature | rpctl Command | Status |
|---|---|---|---|
| `runpod.get_user()` | `api_key=None` | — | **GAP** |
| `runpod.update_user_settings(pubkey)` | `pubkey, api_key=None` | — | **GAP** |

### User Gaps Summary

| Gap | Severity | Fix |
|-----|----------|-----|
| `rpctl user info` (show account, balance, SSH key) | HIGH | Add command using `get_user()` |
| `rpctl user set-ssh-key` (upload public key) | MEDIUM | Add command using `update_user_settings()` |

---

## 7. Container Registry Auth

### SDK Functions

| SDK Function | Signature | rpctl Command | Status |
|---|---|---|---|
| `runpod.create_container_registry_auth(name, user, pass)` | name, username, password | — | **GAP** |
| `runpod.update_container_registry_auth(id, user, pass)` | registry_auth_id, username, password | — | **GAP** |
| `runpod.delete_container_registry_auth(id)` | registry_auth_id | — | **GAP** |

### Registry Gaps Summary

| Gap | Severity | Fix |
|-----|----------|-----|
| `rpctl registry create --name N --user U --pass P` | HIGH | Add subcommand group |
| `rpctl registry update ID --user U --pass P` | MEDIUM | |
| `rpctl registry delete ID` | MEDIUM | |
| `rpctl registry list` | MEDIUM | No SDK function (need GQL) |

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

## Gap Priority Matrix

### CRITICAL (blocks agent automation)

| # | Gap | CLI Command | Fix Effort |
|---|-----|-------------|------------|
| 1 | Pod `docker_start_cmd` not passed to SDK | `rpctl pod create --docker-start-cmd` | Small — add to `to_sdk_kwargs()` |
| 2 | Pod wait/poll command missing | `rpctl pod wait POD_ID` | Medium — use `poll_until()` |
| 3 | Endpoint health check missing | `rpctl endpoint health EP_ID` | Small — use `Endpoint.health()` |
| 4 | Endpoint wait/poll command missing | `rpctl endpoint wait EP_ID` | Medium — poll health |

### HIGH (needed for full workflows)

| # | Gap | CLI Command | Fix Effort |
|---|-----|-------------|------------|
| 5 | Pod `--public-ip` flag missing | `rpctl pod create --public-ip` | Tiny |
| 6 | Pod `--entrypoint` flag missing | `rpctl pod create --entrypoint` | Tiny |
| 7 | Endpoint run/invoke missing | `rpctl endpoint run EP_ID` | Medium |
| 8 | User info missing | `rpctl user info` | Small |
| 9 | Container registry CRUD | `rpctl registry create/update/delete` | Medium |

### MEDIUM (nice to have)

| # | Gap | CLI Command | Fix Effort |
|---|-----|-------------|------------|
| 10 | Pod `--cuda-versions` flag missing | `rpctl pod create --cuda-versions` | Tiny |
| 11 | Endpoint purge-queue | `rpctl endpoint purge-queue EP_ID` | Small |
| 12 | Endpoint job status/cancel | `rpctl endpoint job-status` | Medium |
| 13 | User SSH key upload | `rpctl user set-ssh-key` | Small |
| 14 | CPU capacity in list | `rpctl capacity list --cpu` | Small |

### LOW (edge cases)

| # | Gap | CLI Command | Fix Effort |
|---|-----|-------------|------------|
| 15 | `start_ssh` on pod create | `rpctl pod create --no-ssh` | Tiny |
| 16 | `country_code` on pod create | `rpctl pod create --country` | Tiny |
| 17 | `min_download`/`min_upload` on pod create | `rpctl pod create --min-download` | Tiny |
| 18 | Endpoint `--cuda-versions` on create | `rpctl endpoint create --cuda-versions` | Tiny |

---

## Currently In Progress

Tasks being implemented now (from approved plan):

- [x] Template create — `--docker-start-cmd`, `--volume-mount-path`, `--registry-auth` (done)
- [ ] Pod create — `--docker-start-cmd` SDK mapping, `--entrypoint`, `--public-ip`, `--cuda-versions`
- [ ] `rpctl endpoint health EP_ID`
- [ ] `rpctl endpoint wait EP_ID`
- [ ] `rpctl pod wait POD_ID`
- [ ] Shared polling utility (`poll.py` created, needs tests)

## Future Backlog (from initial suggestions)

- `rpctl endpoint run EP_ID --input '{}' [--sync|--async]`
- `rpctl endpoint purge-queue EP_ID`
- `rpctl endpoint job-status EP_ID JOB_ID`
- `rpctl user info`
- `rpctl user set-ssh-key`
- `rpctl registry create/update/delete`
- CPU capacity display
- `--country`, `--min-download`, `--min-upload` on pod create
