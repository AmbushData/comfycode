# comfycode
A developer-focused framework for AI image generation using a ComfyUI server deployed on RunPod GPUs.  Instead of relying on the ComfyUI interface, workflows are executed programmatically through Python, enabling version control, reproducibility, automation, and seamless integration into larger systems. Designed for scalable, AI pipelines.

## Getting Started

This project uses [uv](https://docs.astral.sh/uv/) as its project manager.

### Install uv

```bash
pip install uv
```

Or follow the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### Setup

```bash
# Install dependencies and create a virtual environment
uv sync

# Run the project
uv run main.py
```

### Adding dependencies

```bash
uv add <package>
```
