"""Backward compatibility shim. Import from comfycode.interop instead."""

# Re-export from new location for backward compatibility
from comfycode.interop.ui_export import UI_JSON_VERSION, ir_to_ui_json, prompt_to_ui_json

__all__ = ["UI_JSON_VERSION", "ir_to_ui_json", "prompt_to_ui_json"]
