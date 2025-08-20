# RunPod Manager

A Python package for managing RunPod instances across multiple projects. This package provides a reusable, configurable interface for deploying, starting, stopping, and managing RunPod GPU instances.

## Features

- **Project-agnostic**: Configure pod naming patterns and settings per project
- **Flexible configuration**: Support for environment variables, config files, and programmatic configuration
- **GPU cost optimization**: Automatically selects the cheapest available GPU within your budget
- **Full pod lifecycle management**: Start, stop, restart, deploy, terminate, and status operations
- **CLI and programmatic interfaces**: Use as a command-line tool or import as a Python library
- **Robust error handling**: Graceful fallbacks and detailed error reporting

## Installation

```bash
pip install runpod_manager
```

## Quick Start

### Environment Setup

Set your RunPod API key:

```bash
export RUNPOD_API_KEY="your-runpod-api-key"
```

### CLI Usage

```bash
# Deploy a new pod
runpod-manager myproject main deploy

# Start an existing pod
runpod-manager myproject main start

# Check pod status
runpod-manager myproject main status

# Stop a pod
runpod-manager myproject main stop

# Restart a pod
runpod-manager myproject main restart

# Terminate (delete) a pod
runpod-manager myproject main terminate
```

### Programmatic Usage

```python
from runpod_manager import PodManager, PodConfig

# Basic usage with defaults
manager = PodManager("myproject")

# Deploy a new pod
success = manager.deploy_pod("main")

# Start the pod
success = manager.start_pod("main")

# Check status
success = manager.status_pod("main")
```

### Advanced Configuration

```python
from runpod_manager import PodManager, PodConfig

# Create custom configuration
config = PodConfig(
    project_name="myproject",
    MAX_GPU_PRICE="0.50",  # Higher budget
    CONTAINER_DISK="50",   # Larger disk
    IMAGE_NAME_BASE="docker.io/myorg/myimage",
    TEMPLATE_ID="my-template-id",
    NETWORK_VOLUME_ID="my-volume-id"
)

# Create manager with custom config
manager = PodManager("myproject", config=config, verbose=True)

# Deploy with custom settings
success = manager.deploy_pod("production")
```

## Configuration Options

### Core Settings

- `project_name`: Project identifier used in pod naming (required)
- `MAX_GPU_PRICE`: Maximum price per hour for GPU selection (default: "0.30")
- `CONTAINER_DISK`: Container disk size in GB (default: "20")
- `GPU_COUNT`: Number of GPUs per pod (default: "1")

### Deployment Settings

- `IMAGE_NAME_BASE`: Base Docker image name (optional)
- `TEMPLATE_ID`: RunPod template ID (optional)
- `NETWORK_VOLUME_ID`: Network volume ID for persistent storage (optional)
- `VOLUME_MOUNT_PATH`: Mount path for network volume (default: "/workspace")

### Pod Settings

- `SUPPORT_PUBLIC_IP`: Enable public IP (default: "true")
- `START_SSH`: Enable SSH access (default: "true")
- `INACTIVITY_TIMEOUT_SECONDS`: Auto-shutdown timeout (default: "3600")

### Configuration Methods

1. **Constructor parameters** (highest priority):
   ```python
   manager = PodManager("myproject", MAX_GPU_PRICE="0.50")
   ```

2. **Environment variables**:
   ```bash
   export RUNPOD_API_KEY="your-key"
   export MAX_GPU_PRICE="0.50"
   ```

3. **Configuration file**:
   ```python
   config = PodConfig("myproject", config_file="config.env")
   ```

   Config file format:
   ```
   MAX_GPU_PRICE=0.50
   CONTAINER_DISK=30
   IMAGE_NAME_BASE=docker.io/myorg/myimage
   ```

## Pod Naming Convention

Pods are automatically named using the pattern: `{project_name}-{pod_type}-{timestamp}`

Examples:
- `myproject-main-1692123456`
- `myproject-branch-1692123789`

## CLI Reference

```bash
runpod-manager PROJECT_NAME POD_TYPE ACTION [OPTIONS]

Arguments:
  PROJECT_NAME          Project name for pod naming
  POD_TYPE             Pod type identifier (e.g., main, branch, dev)
  ACTION               Action to perform: start, stop, restart, status, deploy, terminate

Options:
  --verbose, -v        Enable verbose output
  --deploy-new-if-needed  Deploy new pod if current one cannot be started
  --config-file FILE   Path to configuration file
```

## Error Handling

The package includes robust error handling:

- **GPU availability**: Automatically tries multiple GPUs if the first choice is unavailable
- **Pod failures**: Option to deploy new pods if existing ones fail to start
- **Network issues**: Graceful handling of API timeouts and connection errors
- **Configuration errors**: Clear error messages for missing or invalid settings

## Examples

### Multi-environment Setup

```python
# Development environment
dev_config = PodConfig(
    project_name="myapp",
    MAX_GPU_PRICE="0.20",
    CONTAINER_DISK="20"
)
dev_manager = PodManager("myapp", config=dev_config)

# Production environment  
prod_config = PodConfig(
    project_name="myapp",
    MAX_GPU_PRICE="1.00",
    CONTAINER_DISK="100",
    GPU_COUNT="2"
)
prod_manager = PodManager("myapp", config=prod_config)

# Deploy to different environments
dev_manager.deploy_pod("dev")
prod_manager.deploy_pod("prod")
```

### Custom Pod Types

```python
from runpod_manager.cli import main

# Define custom pod types for your project
custom_pod_types = ["frontend", "backend", "worker", "gpu-training"]

# Use custom CLI with your pod types
if __name__ == "__main__":
    main(pod_types=custom_pod_types)
```

## Requirements

- Python 3.8+
- RunPod account and API key
- `runpod` Python SDK

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
