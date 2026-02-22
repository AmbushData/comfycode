"""Convert a ComfyUI workflow (API prompt JSON) into equivalent Python code.

This module provides two conversion paths:

1. ``convert(workflow)`` — Direct prompt JSON to Python (original, lean path).
2. ``ir_to_python(ir)`` — IR to Python (for use with other IR-based conversions).

Design Note: The direct ``convert()`` function does not use the IR because:
- JSON → Python doesn't benefit from layout metadata
- The direct path is simpler and well-tested
- Keeping it separate avoids unnecessary abstraction for a simple use case

The IR-based path exists for consistency with other conversions (e.g., future
UI JSON → IR → Python flows).
"""

import json
import re
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from comfycode.ir import WorkflowIR


def _to_var_name(class_type: str) -> str:
    """Convert a CamelCase class type to a snake_case variable name.

    Examples:
        "KSampler"                -> "k_sampler"
        "CheckpointLoaderSimple"  -> "checkpoint_loader_simple"
        "VAEDecode"               -> "vae_decode"
    """
    # Insert underscore before a capital letter that follows a lowercase letter
    # or before a capital letter that is followed by a lowercase letter (handles
    # sequences like "VAE" → "VAE" stays together until next word begins).
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", class_type)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    return s.lower()


_MAX_LINE_LENGTH = 88  # PEP 8 extended limit; keeps generated code readable


def _is_link(value: Any) -> bool:
    """Return True when *value* looks like a ComfyUI node-link [node_id, slot]."""
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and isinstance(value[1], int)
    )


def convert(workflow: "dict | str") -> str:
    """Convert a ComfyUI workflow dict or JSON string to Python source code.

    The generated code uses the :class:`comfycode.Workflow` API so it can be
    run directly or edited further.

    Args:
        workflow: A dict in the ComfyUI API prompt format, or a JSON string
                  representing such a dict.

    Returns:
        A string containing the equivalent Python source code.
    """
    if isinstance(workflow, str):
        workflow = json.loads(workflow)

    lines: list[str] = [
        "from comfycode import Workflow",
        "",
        "workflow = Workflow()",
        "",
    ]

    # Sort by numeric node ID for a deterministic, readable output order.
    def _sort_key(item: tuple) -> tuple:
        node_id = item[0]
        return (int(node_id),) if node_id.isdigit() else (float("inf"), node_id)

    sorted_nodes = sorted(workflow.items(), key=_sort_key)

    # First pass: assign unique variable names to every node.
    var_names: dict[str, str] = {}
    name_counts: dict[str, int] = {}
    for node_id, node_data in sorted_nodes:
        base = _to_var_name(node_data["class_type"])
        count = name_counts.get(base, 0) + 1
        name_counts[base] = count
        var_names[node_id] = f"{base}_{count}" if count > 1 else base

    # Second pass: emit one add_node() call per node.
    for node_id, node_data in sorted_nodes:
        var = var_names[node_id]
        class_type = node_data["class_type"]
        inputs = node_data.get("inputs", {})

        arg_parts: list[str] = []
        for key, value in inputs.items():
            if _is_link(value):
                ref_id, slot = value
                ref_var = var_names.get(ref_id, f"node_{ref_id}")
                ref_call = f"{ref_var}.output()" if slot == 0 else f"{ref_var}.output({slot})"
                arg_parts.append(f"{key}={ref_call}")
            else:
                arg_parts.append(f"{key}={repr(value)}")

        call_prefix = f'{var} = workflow.add_node("{class_type}"'
        if arg_parts:
            inline = ", ".join(arg_parts)
            if len(call_prefix) + 2 + len(inline) + 1 <= _MAX_LINE_LENGTH:
                lines.append(f"{call_prefix}, {inline})")
            else:
                indent = "    "
                joined = f",\n{indent}".join(arg_parts)
                lines.append(f"{call_prefix},\n{indent}{joined})")
        else:
            lines.append(f"{call_prefix})")

    lines += ["", "prompt = workflow.build()"]
    return "\n".join(lines) + "\n"


def ir_to_python(ir: "WorkflowIR") -> str:
    """Convert a WorkflowIR to Python source code.

    This function provides an IR-based path to Python code generation,
    for consistency with other IR-based conversions.

    Args:
        ir: A WorkflowIR instance.

    Returns:
        A string containing the equivalent Python source code.
    """
    from comfycode.ir import ir_to_prompt_json

    # Convert IR back to prompt JSON, then use the existing convert function.
    # This ensures consistent output formatting and behavior.
    prompt = ir_to_prompt_json(ir)
    return convert(prompt)
