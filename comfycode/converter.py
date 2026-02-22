"""Backward compatibility shim. Import from comfycode.interop instead."""

# Re-export from new location for backward compatibility
from comfycode.interop.converter import convert, ir_to_python, _to_var_name

__all__ = ["convert", "ir_to_python", "_to_var_name"]
