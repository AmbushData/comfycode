"""Execution-based Python → prompt JSON export.

This module provides the export functionality for converting Python workflow
modules into prompt JSON that can be used with the ComfyUI API.

Entrypoint Contract
-------------------
To export a Python workflow module, the module must define a function called
``create_workflow()`` that returns either:

1. A ``Workflow`` instance (will be built to a prompt dict), or
2. A prompt dict directly (dict with ``{node_id: {class_type, inputs}}``)

Example workflow module::

    from comfycode import Workflow

    def create_workflow():
        wf = Workflow()
        wf.add_node("CheckpointLoaderSimple", ckpt_name="model.ckpt")
        # ... add more nodes ...
        return wf

Safety Notes
------------
- Only the ``create_workflow()`` function is called; other module code runs
  during import.
- Side effects from module imports are the user's responsibility.
- Network calls, file I/O, etc. are not blocked — use with trusted code only.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

from comfycode.workflow import Workflow


ENTRYPOINT_FUNCTION = "create_workflow"
"""The required function name that workflow modules must define for export."""


class ExportError(Exception):
    """Raised when workflow export fails."""
    pass


def export_prompt_json(workflow: Workflow | dict[str, Any]) -> dict[str, Any]:
    """Export a Workflow instance or prompt dict to a prompt JSON dict.

    Args:
        workflow: Either a ``Workflow`` instance or a prompt dict.

    Returns:
        A prompt dict suitable for the ComfyUI API.

    Raises:
        ExportError: If the input is not a Workflow or dict.
    """
    if isinstance(workflow, Workflow):
        return workflow.build()
    elif isinstance(workflow, dict):
        # Assume it's already a prompt dict
        return workflow
    else:
        raise ExportError(
            f"Expected a Workflow instance or prompt dict, "
            f"got {type(workflow).__name__}"
        )


def export_from_module(module_path: str | Path) -> dict[str, Any]:
    """Load a Python module and export its workflow to a prompt dict.

    The module must define a ``create_workflow()`` function that returns
    a ``Workflow`` instance or a prompt dict.

    Args:
        module_path: Path to the Python module file.

    Returns:
        A prompt dict suitable for the ComfyUI API.

    Raises:
        ExportError: If the module cannot be loaded, doesn't define
            ``create_workflow()``, or the function fails.
    """
    module_path = Path(module_path)
    
    if not module_path.exists():
        raise ExportError(f"Module file not found: {module_path}")
    
    if not module_path.suffix == ".py":
        raise ExportError(f"Module must be a .py file: {module_path}")
    
    # Generate a unique module name to avoid conflicts
    module_name = f"_comfycode_export_{module_path.stem}_{id(module_path)}"
    
    # Load the module
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ExportError(f"Failed to create module spec for: {module_path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        # Clean up on import failure
        sys.modules.pop(module_name, None)
        raise ExportError(
            f"Failed to import module {module_path}: {type(e).__name__}: {e}"
        ) from e
    
    # Check for the entrypoint function
    if not hasattr(module, ENTRYPOINT_FUNCTION):
        sys.modules.pop(module_name, None)
        raise ExportError(
            f"Module {module_path} does not define a '{ENTRYPOINT_FUNCTION}()' function. "
            f"The module must define a function called '{ENTRYPOINT_FUNCTION}' that returns "
            f"a Workflow instance or a prompt dict."
        )
    
    entrypoint = getattr(module, ENTRYPOINT_FUNCTION)
    
    if not callable(entrypoint):
        sys.modules.pop(module_name, None)
        raise ExportError(
            f"'{ENTRYPOINT_FUNCTION}' in {module_path} is not callable"
        )
    
    # Call the entrypoint
    try:
        result = entrypoint()
    except Exception as e:
        sys.modules.pop(module_name, None)
        raise ExportError(
            f"Error executing {ENTRYPOINT_FUNCTION}() in {module_path}: "
            f"{type(e).__name__}: {e}"
        ) from e
    finally:
        # Clean up the temporary module
        sys.modules.pop(module_name, None)
    
    # Convert result to prompt dict
    return export_prompt_json(result)
