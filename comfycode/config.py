"""Configuration management for comfycode.

Values are read from environment variables with optional overrides supplied
at construction time.  All settings are exposed as plain attributes so that
any layer of the stack can depend only on a ``Config`` instance rather than
importing ``os`` directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Config:
    """Central configuration object.

    Parameters
    ----------
    runpod_api_key:
        RunPod API key used to provision GPU pods.  Defaults to the
        ``RUNPOD_API_KEY`` environment variable.
    runpod_template_id:
        RunPod template (Docker image) used when creating a new pod.
        Defaults to ``RUNPOD_TEMPLATE_ID``.
    runpod_gpu_type:
        GPU type string recognised by the RunPod API (e.g.
        ``"NVIDIA GeForce RTX 3090"``).  Defaults to ``RUNPOD_GPU_TYPE``.
    comfyui_host:
        Hostname or IP of the running ComfyUI server.  Defaults to the
        ``COMFYUI_HOST`` environment variable, falling back to
        ``"127.0.0.1"``.
    comfyui_port:
        TCP port the ComfyUI server listens on.  Defaults to
        ``COMFYUI_PORT``, falling back to ``8188``.
    comfyui_timeout:
        HTTP request timeout in seconds.  Defaults to ``COMFYUI_TIMEOUT``,
        falling back to ``30``.
    output_dir:
        Local directory where generated images are saved.  Defaults to
        ``OUTPUT_DIR``, falling back to ``"./output"``.
    """

    runpod_api_key: str = field(default_factory=lambda: os.environ.get("RUNPOD_API_KEY", ""))
    runpod_template_id: str = field(
        default_factory=lambda: os.environ.get("RUNPOD_TEMPLATE_ID", "")
    )
    runpod_gpu_type: str = field(
        default_factory=lambda: os.environ.get("RUNPOD_GPU_TYPE", "NVIDIA GeForce RTX 3090")
    )
    comfyui_host: str = field(
        default_factory=lambda: os.environ.get("COMFYUI_HOST", "127.0.0.1")
    )
    comfyui_port: int = field(
        default_factory=lambda: int(os.environ.get("COMFYUI_PORT", "8188"))
    )
    comfyui_timeout: int = field(
        default_factory=lambda: int(os.environ.get("COMFYUI_TIMEOUT", "30"))
    )
    output_dir: str = field(
        default_factory=lambda: os.environ.get("OUTPUT_DIR", "./output")
    )

    # ---------------------------------------------------------------------------
    # Derived helpers
    # ---------------------------------------------------------------------------

    @property
    def comfyui_base_url(self) -> str:
        """HTTP base URL for the ComfyUI REST API."""
        return f"http://{self.comfyui_host}:{self.comfyui_port}"

    @property
    def comfyui_ws_url(self) -> str:
        """WebSocket URL used for streaming intermediate execution events."""
        return f"ws://{self.comfyui_host}:{self.comfyui_port}/ws"
