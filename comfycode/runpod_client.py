"""Backward compatibility shim. Import from comfycode.clients instead."""

# Re-export from new location for backward compatibility
from comfycode.clients.runpod import RunPodClient

__all__ = ["RunPodClient"]
