"""Backward compatibility shim. Import from comfycode.interop instead."""

# Re-export from new location for backward compatibility
from comfycode.interop.ir import IRNode, IREdge, WorkflowIR, prompt_json_to_ir, ir_to_prompt_json

__all__ = ["IRNode", "IREdge", "WorkflowIR", "prompt_json_to_ir", "ir_to_prompt_json"]
