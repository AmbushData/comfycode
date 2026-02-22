"""Backward compatibility shim. Import from comfycode.interop instead."""

# Re-export from new location for backward compatibility
from comfycode.interop.export import export_prompt_json, export_from_module, ExportError, ENTRYPOINT_FUNCTION

__all__ = ["export_prompt_json", "export_from_module", "ExportError", "ENTRYPOINT_FUNCTION"]
