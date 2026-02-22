"""Workflow Intermediate Representation (IR) for ComfyCode.

The IR is an internal representation used to mediate conversions between
different workflow formats (prompt JSON, UI JSON, Python code).

This module is NOT a public API — the IR structure may change between versions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IRNode:
    """A single node in the workflow IR.

    Attributes:
        node_id: Unique identifier for this node (string, typically numeric).
        class_type: The ComfyUI node class name (e.g., "KSampler").
        inputs: Dict of non-link input values (links are stored as edges).
        pos: Optional (x, y) position hint for UI layout.
        size: Optional (width, height) size hint for UI layout.
    """

    node_id: str
    class_type: str
    inputs: dict[str, Any]
    pos: tuple[float, float] | None = None
    size: tuple[float, float] | None = None


@dataclass
class IREdge:
    """A directed edge in the workflow IR representing a node connection.

    Attributes:
        from_node: Source node ID.
        from_slot: Output slot index on the source node.
        to_node: Destination node ID.
        to_input: Input name on the destination node.
    """

    from_node: str
    from_slot: int
    to_node: str
    to_input: str


@dataclass
class WorkflowIR:
    """Container for the complete workflow intermediate representation.

    Attributes:
        nodes: Dict mapping node_id to IRNode.
        edges: List of IREdge connections.
        metadata: Optional dict for additional workflow-level metadata.
    """

    nodes: dict[str, IRNode] = field(default_factory=dict)
    edges: list[IREdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_node(self, node: IRNode) -> None:
        """Add a node to the IR."""
        self.nodes[node.node_id] = node

    def add_edge(self, edge: IREdge) -> None:
        """Add an edge to the IR."""
        self.edges.append(edge)

    def get_node(self, node_id: str) -> IRNode | None:
        """Get a node by ID, or None if not found."""
        return self.nodes.get(node_id)


def _is_link(value: Any) -> bool:
    """Return True if value is a ComfyUI node-link [node_id, slot]."""
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], str)
        and isinstance(value[1], int)
    )


def prompt_json_to_ir(prompt: dict[str, Any]) -> WorkflowIR:
    """Convert a ComfyUI prompt JSON dict to a WorkflowIR.

    Args:
        prompt: A dict in the ComfyUI API prompt format
                (``{ node_id: { class_type, inputs } }``).

    Returns:
        A WorkflowIR containing nodes and edges derived from the prompt.
    """
    ir = WorkflowIR()

    # First pass: create all nodes with non-link inputs
    for node_id, node_data in prompt.items():
        class_type = node_data["class_type"]
        raw_inputs = node_data.get("inputs", {})

        # Separate link inputs from value inputs
        non_link_inputs: dict[str, Any] = {}
        for input_name, value in raw_inputs.items():
            if _is_link(value):
                # This is a link — will become an edge
                from_node, from_slot = value
                edge = IREdge(
                    from_node=from_node,
                    from_slot=from_slot,
                    to_node=node_id,
                    to_input=input_name,
                )
                ir.add_edge(edge)
            else:
                # Regular value input
                non_link_inputs[input_name] = value

        node = IRNode(
            node_id=node_id,
            class_type=class_type,
            inputs=non_link_inputs,
        )
        ir.add_node(node)

    return ir


def ir_to_prompt_json(ir: WorkflowIR) -> dict[str, Any]:
    """Convert a WorkflowIR back to a ComfyUI prompt JSON dict.

    Args:
        ir: The WorkflowIR to convert.

    Returns:
        A dict in the ComfyUI API prompt format.
    """
    prompt: dict[str, Any] = {}

    # Build a lookup for edges by (to_node, to_input) for fast reconstruction
    edges_by_dest: dict[tuple[str, str], IREdge] = {}
    for edge in ir.edges:
        key = (edge.to_node, edge.to_input)
        edges_by_dest[key] = edge

    for node_id, node in ir.nodes.items():
        # Start with the non-link inputs
        inputs: dict[str, Any] = dict(node.inputs)

        # Add back the link inputs from edges
        for (to_node, to_input), edge in edges_by_dest.items():
            if to_node == node_id:
                inputs[to_input] = [edge.from_node, edge.from_slot]

        prompt[node_id] = {
            "class_type": node.class_type,
            "inputs": inputs,
        }

    return prompt
