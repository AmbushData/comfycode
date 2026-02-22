"""Backward compatibility shim. Import from comfycode.config instead."""

# Re-export from new location for backward compatibility
from comfycode.config.settings import Config

__all__ = ["Config"]
