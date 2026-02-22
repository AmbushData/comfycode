"""Backward compatibility shim. Import from comfycode.clients instead."""

# Re-export from new location for backward compatibility
from comfycode.clients.comfyui import ComfyUIClient, ComfyUIError, EventCallback

__all__ = ["ComfyUIClient", "ComfyUIError", "EventCallback"]
