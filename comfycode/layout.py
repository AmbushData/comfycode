"""Backward compatibility shim. Import from comfycode.interop instead."""

# Re-export from new location for backward compatibility
from comfycode.interop.layout import LayoutConfig, NodeLayout, compute_layout

__all__ = ["LayoutConfig", "NodeLayout", "compute_layout"]
