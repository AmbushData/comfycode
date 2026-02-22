"""Interoperability layer for JSON formats and conversions.

This subpackage handles prompt JSON, UI JSON, intermediate representation (IR),
layout computation, and format conversions.
"""

from .ir import IRNode, IREdge, WorkflowIR, prompt_json_to_ir, ir_to_prompt_json
from .layout import LayoutConfig, compute_layout
from .export import export_prompt_json, export_from_module, ExportError
from .ui_export import prompt_to_ui_json
from .converter import convert, ir_to_python
from .formats import (
    validate_prompt_json,
    validate_ui_json,
    PROMPT_JSON_VERSION,
    UI_JSON_VERSION,
    PROMPT_TO_UI_LOSSY_FIELDS,
    UI_TO_PROMPT_LOSSY_FIELDS,
)

__all__ = [
    # IR
    "IRNode",
    "IREdge", 
    "WorkflowIR",
    "prompt_json_to_ir",
    "ir_to_prompt_json",
    # Layout
    "LayoutConfig",
    "compute_layout",
    # Export
    "export_prompt_json",
    "export_from_module",
    "ExportError",
    # UI Export
    "prompt_to_ui_json",
    # Converter
    "convert",
    "ir_to_python",
    # Formats
    "validate_prompt_json",
    "validate_ui_json",
    "PROMPT_JSON_VERSION",
    "UI_JSON_VERSION",
    "PROMPT_TO_UI_LOSSY_FIELDS",
    "UI_TO_PROMPT_LOSSY_FIELDS",
]
