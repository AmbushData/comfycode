"""Backward compatibility shim. Import from comfycode.workflows instead."""

# Re-export from new location for backward compatibility
from comfycode.workflows.builder import Node, NodeOutput, Workflow, WorkflowError

__all__ = ["Node", "NodeOutput", "Workflow", "WorkflowError"]
