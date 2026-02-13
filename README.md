# rpctl

CLI tool for managing RunPod GPU/CPU infrastructure. List available GPUs, create pods, manage serverless endpoints, and check capacity — all from the terminal.

## Installation

```bash
# From source (development)
git clone https://github.com/your-org/rpctl.git
cd rpctl
pip install -e ".[dev]"
```

## Quick Start

```bash
# Set up configuration and API key
rpctl config init

# List available GPU types with pricing
rpctl capacity list

# Create a pod
rpctl pod create --image runpod/pytorch:2.1 --gpu "NVIDIA RTX A6000"

# List your pods
rpctl pod list
```

## Commands

### Core Resources

| Command | Description |
|---------|-------------|
| `rpctl pod list` | List all pods |
| `rpctl pod create --image IMG` | Create a new pod |
| `rpctl pod get POD_ID` | Show pod details |
| `rpctl pod stop POD_ID` | Stop a running pod |
| `rpctl pod resume POD_ID` | Resume a stopped pod |
| `rpctl pod terminate POD_ID` | Permanently delete a pod |
| `rpctl endpoint list` | List serverless endpoints |
| `rpctl endpoint create --name N --template T` | Create an endpoint |
| `rpctl endpoint get EP_ID` | Show endpoint details |
| `rpctl endpoint update EP_ID` | Update endpoint settings |
| `rpctl endpoint delete EP_ID` | Delete an endpoint |
| `rpctl volume list` | List network volumes |
| `rpctl volume create --name N --size S --datacenter DC` | Create a volume |
| `rpctl template list` | List templates |
| `rpctl template create --name N --image IMG` | Create a template |

### Capacity & Pricing

| Command | Description |
|---------|-------------|
| `rpctl capacity list` | List GPU types with pricing and availability |
| `rpctl capacity list --gpu "A100"` | Filter by GPU type |
| `rpctl capacity list --datacenter US-TX-3` | Filter by datacenter |
| `rpctl capacity list --available` | Show only available GPUs |

### Presets

Save and reuse common configurations:

```bash
# Save a preset from CLI flags
rpctl preset save my-pod --image runpod/pytorch:2.1 --gpu "NVIDIA RTX A6000" --gpu-count 2

# Save a preset from an existing pod
rpctl preset save captured --from-pod POD_ID

# Create a pod from a preset (with overrides)
rpctl pod create --preset my-pod --gpu-count 4

# List, show, and delete presets
rpctl preset list
rpctl preset show my-pod
rpctl preset delete my-pod --confirm
```

### Configuration

```bash
rpctl config init              # Interactive setup wizard
rpctl config show              # Display active configuration
rpctl config set KEY VALUE     # Set a config value
rpctl config get KEY           # Read a config value
rpctl config set-key           # Store API key in OS keyring
rpctl config list-profiles     # List all profiles
rpctl config add-profile NAME  # Add a new profile
rpctl config use-profile NAME  # Switch active profile
```

## Global Flags

| Flag | Description |
|------|-------------|
| `--json` | Output as JSON (useful for scripting) |
| `--verbose` / `-v` | Enable debug logging to stderr |
| `--profile NAME` | Use a specific config profile |
| `--version` | Show version and exit |

## Configuration

rpctl uses a YAML config file at `~/.config/rpctl/config.yaml` with profile support. API keys are stored securely in the OS keyring.

```bash
# Set up with the wizard
rpctl config init

# Or set the API key directly
rpctl config set-key

# Override via environment variable
export RUNPOD_API_KEY=your-key-here
```

## Resilience

API calls automatically retry on transient failures (429 rate limits, 5xx server errors, timeouts, connection errors) with exponential backoff and jitter. Use `-v` to see retry attempts in stderr.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

## License

MIT
