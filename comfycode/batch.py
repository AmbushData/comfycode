"""Backward compatibility shim. Import from comfycode.pipeline instead."""

# Re-export from new location for backward compatibility
from comfycode.pipeline.batch import BatchResult, BatchProcessor

__all__ = ["BatchResult", "BatchProcessor"]
