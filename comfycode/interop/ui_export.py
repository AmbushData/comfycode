"""Export workflow IR to ComfyUI UI workflow JSON format.

This module converts a WorkflowIR (or prompt JSON) to the ComfyUI web UI
export format, including deterministic node layout positions.

The UI JSON format includes:
- nodes: Array of node objects with id, type, pos, widgets_values, etc.
- links: Array of link tuples [link_id, from_node, from_slot, to_node, to_slot, type]
- last_node_id, last_link_id: Counters for ID generation
- version: Schema version number

Note: This export is lossy — some UI-specific metadata cannot be reconstructed
from the prompt JSON or IR. See formats.py for lossiness documentation.
"""

from __future__ import annotations

from typing import Any

from .ir import WorkflowIR, prompt_json_to_ir
from .layout import compute_layout, LayoutConfig


# UI JSON schema version we produce (0.4 is common for recent ComfyUI)
UI_JSON_VERSION = 0.4


def ir_to_ui_json(
    ir: WorkflowIR,
    config: LayoutConfig | None = None,
) -> dict[str, Any]:
    """Convert a WorkflowIR to ComfyUI UI workflow JSON.

    Args:
        ir: The WorkflowIR to convert.
        config: Layout configuration. Uses defaults if not provided.

    Returns:
        A dict in the ComfyUI web UI workflow format.
    """
    if config is None:
        config = LayoutConfig()

    # Compute layout positions
    layouts = compute_layout(ir, config)

    # Build nodes list
    nodes: list[dict[str, Any]] = []
    node_id_to_int: dict[str, int] = {}

    for node_id in sorted(ir.nodes.keys(), key=lambda x: int(x) if x.isdigit() else float("inf")):
        node = ir.nodes[node_id]
        layout = layouts.get(node_id)

        # Convert node_id to integer
        int_id = int(node_id) if node_id.isdigit() else hash(node_id) % 1000000
        node_id_to_int[node_id] = int_id

        # Get position from layout or default
        if layout:
            pos = [layout.x, layout.y]
        else:
            pos = [0.0, 0.0]

        # Build widgets_values from non-link inputs
        widgets_values = list(node.inputs.values())

        ui_node: dict[str, Any] = {
            "id": int_id,
            "type": node.class_type,
            "pos": pos,
            "size": {"0": 315, "1": 98},  # Default size
            "flags": {},
            "order": len(nodes),
            "mode": 0,
            "inputs": [],
            "outputs": [],
            "widgets_values": widgets_values,
        }

        nodes.append(ui_node)

    # Build links list
    links: list[list[Any]] = []
    link_id = 1

    # Track input slots for each node
    node_input_slots: dict[str, dict[str, int]] = {}
    for edge in ir.edges:
        if edge.to_node not in node_input_slots:
            node_input_slots[edge.to_node] = {}
        if edge.to_input not in node_input_slots[edge.to_node]:
            slot_idx = len(node_input_slots[edge.to_node])
            node_input_slots[edge.to_node][edge.to_input] = slot_idx

    for edge in ir.edges:
        from_node_int = node_id_to_int.get(edge.from_node, 0)
        to_node_int = node_id_to_int.get(edge.to_node, 0)
        to_slot = node_input_slots.get(edge.to_node, {}).get(edge.to_input, 0)

        # Link format: [link_id, from_node, from_slot, to_node, to_slot, type_name]
        # We use "*" as a generic type since we don't track types in the IR
        link_entry = [link_id, from_node_int, edge.from_slot, to_node_int, to_slot, "*"]
        links.append(link_entry)
        link_id += 1

    # Build the complete UI workflow JSON
    max_node_id = max(node_id_to_int.values()) if node_id_to_int else 0

    result: dict[str, Any] = {
        "last_node_id": max_node_id,
        "last_link_id": len(links),
        "nodes": nodes,
        "links": links,
        "groups": [],
        "config": {},
        "extra": {},
        "version": UI_JSON_VERSION,
    }

    return result


def prompt_to_ui_json(
    prompt: dict[str, Any],
    config: LayoutConfig | None = None,
) -> dict[str, Any]:
    """Convert a ComfyUI prompt JSON to UI workflow JSON.

    This is a convenience function that:
    1. Converts prompt JSON to IR
    2. Computes deterministic layout
    3. Exports to UI JSON format

    Args:
        prompt: A dict in the ComfyUI API prompt format.
        config: Layout configuration. Uses defaults if not provided.

    Returns:
        A dict in the ComfyUI web UI workflow format.
    """
    ir = prompt_json_to_ir(prompt)
    return ir_to_ui_json(ir, config)
