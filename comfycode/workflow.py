"""Core workflow classes for building ComfyUI workflows programmatically."""

import json
from typing import Any


class NodeOutput:
    """Represents a single output slot of a workflow node."""

    def __init__(self, node: "Node", index: int) -> None:
        self.node = node
        self.index = index

    def to_link(self) -> list:
        """Serialize as a ComfyUI node-link pair [node_id, output_index]."""
        return [self.node.node_id, self.index]


class Node:
    """Represents a single node in a ComfyUI workflow."""

    def __init__(self, node_id: str, class_type: str, **inputs: Any) -> None:
        self.node_id = node_id
        self.class_type = class_type
        self.inputs = inputs

    def output(self, index: int = 0) -> NodeOutput:
        """Return a reference to one of this node's output slots."""
        return NodeOutput(self, index)

    def to_dict(self) -> dict:
        """Serialize to the ComfyUI API prompt format."""
        serialized_inputs: dict[str, Any] = {}
        for key, value in self.inputs.items():
            if isinstance(value, NodeOutput):
                serialized_inputs[key] = value.to_link()
            else:
                serialized_inputs[key] = value
        return {"class_type": self.class_type, "inputs": serialized_inputs}


class Workflow:
    """Builds and serializes a ComfyUI workflow (API prompt format)."""

    def __init__(self) -> None:
        self._nodes: dict[str, Node] = {}
        self._counter: int = 1

    def add_node(self, class_type: str, **inputs: Any) -> Node:
        """Add a new node and return it so its outputs can be wired to other nodes."""
        node_id = str(self._counter)
        self._counter += 1
        node = Node(node_id, class_type, **inputs)
        self._nodes[node_id] = node
        return node

    def build(self) -> dict:
        """Return the complete workflow as a dict in the ComfyUI API prompt format."""
        return {node_id: node.to_dict() for node_id, node in self._nodes.items()}

    def to_json(self, **kwargs: Any) -> str:
        """Serialize the workflow to a JSON string."""
        return json.dumps(self.build(), **kwargs)

    @classmethod
    def from_json(cls, data: "str | dict") -> "Workflow":
        """Load a workflow from a JSON string or dict (ComfyUI API prompt format)."""
        if isinstance(data, str):
            data = json.loads(data)
        workflow = cls()
        for node_id, node_data in data.items():
            node = Node(node_id, node_data["class_type"], **node_data.get("inputs", {}))
            workflow._nodes[node_id] = node
        numeric_ids = [int(nid) for nid in data if nid.isdigit()]
        if numeric_ids:
            workflow._counter = max(numeric_ids) + 1
        return workflow
