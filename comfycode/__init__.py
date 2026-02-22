"""comfycode – Programmatic AI image generation framework built on ComfyUI and RunPod.

Layers
------
config          Configuration management (env vars, dataclasses).
runpod_client   Infrastructure layer – provision/deprovision RunPod GPU pods.
comfyui_client  Execution layer – submit workflows, stream intermediate outputs.
workflow        Orchestration layer – workflow templating and parameterization.
batch           Batch processing – structured multi-prompt execution.
pipeline        Top-level entry point tying all layers together.
"""

# Re-export from new package locations for backward compatibility
from .config import Config
from .clients import RunPodClient, ComfyUIClient
from .workflows import Node, NodeOutput, Workflow, WorkflowError
from .pipeline import BatchProcessor, Pipeline

__all__ = [
    "Config",
    "RunPodClient",
    "ComfyUIClient",
    "Node",
    "NodeOutput",
    "Workflow",
    "WorkflowError",
    "BatchProcessor",
    "Pipeline",
]

