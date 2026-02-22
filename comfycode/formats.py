"""Backward compatibility shim. Import from comfycode.interop instead."""

# Re-export from new location for backward compatibility
from comfycode.interop.formats import (
    validate_prompt_json,
    validate_ui_json,
    PROMPT_JSON_VERSION,
    UI_JSON_VERSION,
    PROMPT_TO_UI_LOSSY_FIELDS,
    UI_TO_PROMPT_LOSSY_FIELDS,
    PromptNode,
    PromptJSON,
    UINode,
    UIWorkflow,
)

__all__ = [
    "validate_prompt_json",
    "validate_ui_json",
    "PROMPT_JSON_VERSION",
    "UI_JSON_VERSION",
    "PROMPT_TO_UI_LOSSY_FIELDS",
    "UI_TO_PROMPT_LOSSY_FIELDS",
    "PromptNode",
    "PromptJSON",
    "UINode",
    "UIWorkflow",
]
