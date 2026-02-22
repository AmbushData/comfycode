# ComfyCode

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A developer-focused framework for AI image generation using ComfyUI servers deployed on RunPod GPUs. Instead of relying on the ComfyUI web interface, workflows are executed programmatically through Python, enabling version control, reproducibility, automation, and seamless integration into larger systems.

## Key Features

- **Workflow Builder** — Build ComfyUI workflows programmatically with a Python API
- **JSON-to-Python Converter** — Convert existing ComfyUI workflow JSON files to Python code
- **ComfyUI Execution** — Submit workflows to any ComfyUI server with real-time WebSocket event streaming
- **RunPod Integration** — On-demand GPU pod provisioning and lifecycle management
- **Batch Processing** — Execute multiple workflow variants with parameter injection
- **Pipeline Orchestration** — End-to-end pipelines combining infrastructure, execution, and workflow management

## Installation

**Requirements:** Python 3.10 or higher

```bash
# Clone the repository
git clone https://github.com/your-org/comfycode.git
cd comfycode

# Install in development mode
pip install -e .

# Or install directly
pip install .
```

### Dependencies

- `requests>=2.31.0` — HTTP client for REST API calls
- `websocket-client>=1.7.0` — WebSocket support for real-time event streaming
- `Pillow>=10.0.0` — Image processing

## Quick Start

### CLI: Convert Workflow JSON to Python

The simplest way to get started is converting an existing ComfyUI workflow to Python code. This works without any external services.

```bash
# Convert a workflow JSON file to Python (outputs to stdout)
python -m comfycode workflows/txt2img.json

# Save output to a file
python -m comfycode workflows/txt2img.json -o my_workflow.py
```

**Example output:**

```python
from comfycode import Workflow

workflow = Workflow()

checkpoint_loader_simple = workflow.add_node("CheckpointLoaderSimple",
    ckpt_name='v1-5-pruned-emaonly.ckpt')
empty_latent_image = workflow.add_node("EmptyLatentImage",
    width=512, height=512, batch_size=1)
clip_text_encode = workflow.add_node("CLIPTextEncode",
    text='a photo of a cat sitting on a windowsill',
    clip=checkpoint_loader_simple.output(1))
# ... more nodes ...

prompt = workflow.build()
```

### Python: Build Workflows Programmatically

Create workflows entirely in Python:

```python
from comfycode import Workflow

# Build a text-to-image workflow
workflow = Workflow()

# Load a checkpoint model
checkpoint = workflow.add_node("CheckpointLoaderSimple",
    ckpt_name="v1-5-pruned-emaonly.ckpt")

# Create an empty latent image
latent = workflow.add_node("EmptyLatentImage",
    width=512, height=512, batch_size=1)

# Encode positive prompt
positive = workflow.add_node("CLIPTextEncode",
    text="a red fox in a snowy forest, detailed fur, golden hour",
    clip=checkpoint.output(1))

# Encode negative prompt
negative = workflow.add_node("CLIPTextEncode",
    text="ugly, blurry, low quality",
    clip=checkpoint.output(1))

# Sample
sampler = workflow.add_node("KSampler",
    seed=42,
    steps=20,
    cfg=7.0,
    sampler_name="euler_ancestral",
    scheduler="normal",
    denoise=1.0,
    model=checkpoint.output(0),
    positive=positive.output(),
    negative=negative.output(),
    latent_image=latent.output())

# Decode to pixels
decoded = workflow.add_node("VAEDecode",
    samples=sampler.output(),
    vae=checkpoint.output(2))

# Save the image
workflow.add_node("SaveImage",
    images=decoded.output(),
    filename_prefix="comfycode")

# Get the prompt dict for submission to ComfyUI
prompt_dict = workflow.build()
```

### Python: Execute Workflows

Run workflows against a ComfyUI server:

```python
from comfycode import Config, ComfyUIClient, Workflow

# Configure connection (uses environment variables by default)
config = Config()

# Create client
client = ComfyUIClient(config)

# Load and run a workflow
workflow = Workflow.from_file("workflows/txt2img.json")
workflow.set_positive_prompt("a majestic mountain landscape at sunset")
workflow.set_seed(123)

outputs = client.run_workflow(workflow.build())

for output in outputs:
    print(f"Node {output['node_id']}: {output['type']} -> {output['files']}")
```

### Python: Full Pipeline with RunPod

For cloud execution with automatic GPU provisioning:

```python
from comfycode import Pipeline

# Pipeline provisions a RunPod GPU pod on demand
pipeline = Pipeline("workflows/txt2img.json")

# Run with parameter overrides
outputs = pipeline.run(
    positive_prompt="a cyberpunk cityscape at night",
    negative_prompt="blurry, low quality",
    seed=42,
    steps=30,
    cfg=7.5
)

# Batch execution
results = pipeline.run_batch([
    {"positive_prompt": "a red fox", "seed": 1},
    {"positive_prompt": "a blue whale", "seed": 2},
    {"positive_prompt": "a green parrot", "seed": 3},
])

for r in results:
    print(f"Item {r.index}: {'OK' if r.success else r.error}")

# Clean up (terminates RunPod pod)
pipeline.teardown()
```

## Configuration

ComfyCode reads configuration from environment variables with sensible defaults:

| Variable | Description | Default |
|----------|-------------|---------|
| `RUNPOD_API_KEY` | RunPod API key for GPU provisioning | *(empty — disables RunPod)* |
| `RUNPOD_TEMPLATE_ID` | RunPod template/image ID | *(empty)* |
| `RUNPOD_GPU_TYPE` | GPU type (e.g., `"NVIDIA GeForce RTX 3090"`) | `"NVIDIA GeForce RTX 3090"` |
| `COMFYUI_HOST` | ComfyUI server hostname/IP | `"127.0.0.1"` |
| `COMFYUI_PORT` | ComfyUI server port | `8188` |
| `COMFYUI_TIMEOUT` | HTTP request timeout (seconds) | `30` |
| `OUTPUT_DIR` | Directory for saved images | `"./output"` |

**Example `.env` file:**

```bash
# For local ComfyUI server
COMFYUI_HOST=127.0.0.1
COMFYUI_PORT=8188

# For RunPod cloud execution
RUNPOD_API_KEY=your_api_key_here
RUNPOD_TEMPLATE_ID=your_template_id
RUNPOD_GPU_TYPE=NVIDIA GeForce RTX 3090

OUTPUT_DIR=./generated_images
```

You can also override configuration programmatically:

```python
from comfycode import Config

config = Config(
    comfyui_host="192.168.1.100",
    comfyui_port=8188,
    output_dir="./my_outputs"
)
```

## Architecture

ComfyCode is organized in layered modules that can be used independently or composed together:

```
┌─────────────────────────────────────────────────────────────┐
│                        Pipeline                             │
│          (End-to-end orchestration entry point)             │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│     Batch     │     │   Workflow    │     │    Config     │
│   Processor   │     │   (Builder)   │     │ (Settings)    │
└───────────────┘     └───────────────┘     └───────────────┘
        │                     │                     │
        ▼                     │                     │
┌───────────────┐             │                     │
│  ComfyUI      │◄────────────┘                     │
│  Client       │◄──────────────────────────────────┘
└───────────────┘
        │
        ▼
┌───────────────┐
│   RunPod      │
│   Client      │
└───────────────┘
```

### Module Overview

| Module | Purpose |
|--------|---------|
| **`config`** | Centralized configuration from environment variables and programmatic overrides |
| **`runpod_client`** | RunPod API integration — provision/terminate GPU pods, poll status |
| **`comfyui_client`** | ComfyUI REST/WebSocket API — submit prompts, stream events, retrieve outputs |
| **`workflow`** | Workflow building and JSON templating with parameter injection |
| **`batch`** | Execute multiple parameterized workflow variants sequentially |
| **`pipeline`** | Top-level orchestration tying all layers together |
| **`converter`** | CLI tool to convert ComfyUI JSON workflows to Python code |

## API Reference

### `Config`

Centralized configuration dataclass. Reads from environment variables with optional overrides.

```python
config = Config(comfyui_host="localhost", comfyui_port=8188)
print(config.comfyui_base_url)  # "http://localhost:8188"
```

### `RunPodClient`

Manages RunPod GPU pod lifecycle.

```python
client = RunPodClient(config)
pod_id, host, port = client.provision_pod()
# ... use the pod ...
client.terminate_pod(pod_id)
```

### `ComfyUIClient`

Submits workflows to ComfyUI and streams execution events.

```python
client = ComfyUIClient(config, on_event=my_callback)
outputs = client.run_workflow(prompt_dict)
```

### `Workflow`

Builds ComfyUI prompts programmatically or loads from JSON files.

```python
# Build from scratch
wf = Workflow()
node = wf.add_node("CheckpointLoaderSimple", ckpt_name="model.ckpt")

# Load from file
wf = Workflow.from_file("workflow.json")
wf.set_positive_prompt("a sunset")
prompt = wf.build()
```

### `BatchProcessor`

Runs multiple workflow variants with parameter injection.

```python
processor = BatchProcessor(base_workflow, client)
results = processor.run([
    {"positive_prompt": "a cat", "seed": 1},
    {"positive_prompt": "a dog", "seed": 2},
])
```

### `Pipeline`

End-to-end orchestration with optional RunPod provisioning.

```python
pipeline = Pipeline("workflow.json", auto_provision=True)
outputs = pipeline.run(positive_prompt="hello world")
pipeline.teardown()
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=comfycode --cov-report=term-missing

# Run a specific test file
pytest tests/test_workflow.py
```

### Project Structure

```
comfycode/
├── __init__.py          # Package exports
├── __main__.py          # CLI entry point
├── config.py            # Configuration management
├── runpod_client.py     # RunPod API client
├── comfyui_client.py    # ComfyUI API client
├── workflow.py          # Workflow builder
├── batch.py             # Batch processing
├── pipeline.py          # Pipeline orchestration
└── converter.py         # JSON-to-Python converter

tests/                   # Unit tests
workflows/               # Example workflow JSON files
```

### Code Style

- Follow PEP 8 conventions
- Type hints are encouraged
- Maximum line length: 88 characters (Black-compatible)

## License

MIT License — see [LICENSE](LICENSE) for details.
