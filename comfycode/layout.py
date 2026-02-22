"""Deterministic DAG layout generation for workflow visualization.

This module computes node positions for displaying ComfyUI workflows in
the web UI. The layout algorithm uses a layered DAG approach:

1. Compute topological depth for each node (layer assignment)
2. Order nodes within each layer deterministically
3. Assign X position based on layer, Y position based on order within layer

The result is a deterministic, non-overlapping, left-to-right layout.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from comfycode.ir import WorkflowIR


@dataclass
class LayoutConfig:
    """Configuration for layout generation.

    Attributes:
        x_step: Horizontal spacing between layers (default: 300).
        y_step: Vertical spacing between nodes in the same layer (default: 120).
        x_offset: X offset for the first layer (default: 50).
        y_offset: Y offset for the first node (default: 50).
    """

    x_step: float = 300.0
    y_step: float = 120.0
    x_offset: float = 50.0
    y_offset: float = 50.0


@dataclass
class NodeLayout:
    """Position information for a single node.

    Attributes:
        node_id: The node's ID.
        x: X coordinate in the UI canvas.
        y: Y coordinate in the UI canvas.
    """

    node_id: str
    x: float
    y: float


def compute_layout(
    ir: "WorkflowIR",
    config: LayoutConfig | None = None,
) -> dict[str, NodeLayout]:
    """Compute deterministic node positions for a workflow.

    Uses a layered DAG layout algorithm:
    - Sources (nodes with no incoming edges) are in layer 0
    - Each node's layer is max(layer of predecessors) + 1
    - Nodes in the same layer are ordered by (class_type, node_id) for stability

    Args:
        ir: The WorkflowIR to layout.
        config: Layout configuration. Uses defaults if not provided.

    Returns:
        Dict mapping node_id to NodeLayout with computed positions.
    """
    if config is None:
        config = LayoutConfig()

    if not ir.nodes:
        return {}

    # Build adjacency information
    # incoming_edges[node_id] = list of source node_ids
    # outgoing_edges[node_id] = list of target node_ids
    incoming_edges: dict[str, list[str]] = defaultdict(list)
    outgoing_edges: dict[str, list[str]] = defaultdict(list)

    for edge in ir.edges:
        incoming_edges[edge.to_node].append(edge.from_node)
        outgoing_edges[edge.from_node].append(edge.to_node)

    # Compute layer (topological depth) for each node
    layers: dict[str, int] = {}

    def compute_layer(node_id: str, visited: set[str]) -> int:
        """Recursively compute the layer for a node."""
        if node_id in layers:
            return layers[node_id]

        if node_id in visited:
            # Cycle detected - treat as layer 0 to avoid infinite recursion
            return 0

        visited.add(node_id)

        predecessors = incoming_edges.get(node_id, [])
        if not predecessors:
            # Source node - layer 0
            layer = 0
        else:
            # Layer is max of predecessor layers + 1
            layer = max(compute_layer(pred, visited) for pred in predecessors) + 1

        layers[node_id] = layer
        return layer

    # Compute layers for all nodes
    for node_id in ir.nodes:
        compute_layer(node_id, set())

    # Group nodes by layer
    nodes_by_layer: dict[int, list[str]] = defaultdict(list)
    for node_id, layer in layers.items():
        nodes_by_layer[layer].append(node_id)

    # Sort nodes within each layer for deterministic ordering
    # Order by (class_type, node_id) for stability
    for layer_nodes in nodes_by_layer.values():
        layer_nodes.sort(key=lambda nid: (ir.nodes[nid].class_type, nid))

    # Compute positions
    result: dict[str, NodeLayout] = {}
    for layer, layer_nodes in nodes_by_layer.items():
        x = config.x_offset + layer * config.x_step
        for i, node_id in enumerate(layer_nodes):
            y = config.y_offset + i * config.y_step
            result[node_id] = NodeLayout(node_id=node_id, x=x, y=y)

    return result
