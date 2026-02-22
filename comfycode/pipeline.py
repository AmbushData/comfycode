"""Backward compatibility shim. Import from comfycode.pipeline instead."""

# Re-export from new location for backward compatibility
from comfycode.pipeline.orchestrator import Pipeline

__all__ = ["Pipeline"]
