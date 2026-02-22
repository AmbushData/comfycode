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

from .config import Config
from .runpod_client import RunPodClient
from .comfyui_client import ComfyUIClient
from .workflow import Node, NodeOutput, Workflow, WorkflowError
from .batch import BatchProcessor
from .pipeline import Pipeline

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

