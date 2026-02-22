"""Workflow templating and programmatic building for ComfyUI.

This module provides two complementary approaches to creating ComfyUI workflows:

1. **Programmatic building** — Use :meth:`Workflow.add_node` to construct
   workflows node-by-node in Python (used by the JSON-to-Python converter).

2. **Template loading** — Use :meth:`Workflow.from_file` to load existing JSON
   workflows and inject parameters (used by Pipeline/BatchProcessor).

Both approaches produce the same prompt dict format that ComfyUI expects.
"""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class WorkflowError(Exception):
    """Raised when a workflow is malformed or a requested node is not found."""


class NodeOutput:
    """Represents a single output slot of a workflow node.

    Used when programmatically building workflows to wire node outputs
    to other node inputs.
    """

    def __init__(self, node: "Node", index: int) -> None:
        self.node = node
        self.index = index

    def to_link(self) -> list:
        """Serialize as a ComfyUI node-link pair [node_id, output_index]."""
        return [self.node.node_id, self.index]


class Node:
    """Represents a single node in a ComfyUI workflow.

    Used when programmatically building workflows via :meth:`Workflow.add_node`.
    """

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
    """A ComfyUI prompt graph with building and parameter-injection helpers.

    Supports two construction modes:

    1. **From scratch** — Call ``Workflow()`` with no arguments, then use
       :meth:`add_node` to build programmatically.

    2. **From template** — Call :meth:`from_file` or :meth:`from_dict` to
       load an existing workflow, then use setters like :meth:`set_seed`.

    Parameters
    ----------
    graph:
        Optional raw ComfyUI prompt dict.  If provided, the workflow
        operates in template mode.  If omitted, starts with an empty
        graph for programmatic building.

    Examples
    --------
    Build from scratch:

    >>> wf = Workflow()
    >>> ckpt = wf.add_node("CheckpointLoaderSimple", ckpt_name="model.ckpt")
    >>> prompt_dict = wf.build()

    Load from a JSON file and set parameters:

    >>> wf = Workflow.from_file("workflows/txt2img.json")
    >>> wf.set_positive_prompt("a red fox in a snowy forest")
    >>> wf.set_seed(42)
    >>> prompt_dict = wf.build()
    """

    def __init__(self, graph: dict[str, Any] | None = None) -> None:
        if graph is not None:
            # Template mode: work on a deep copy.
            self._graph: dict[str, Any] = copy.deepcopy(graph)
            self._nodes: dict[str, Node] = {}
            # Start counter past the highest existing numeric node ID.
            numeric_ids = [int(nid) for nid in graph if nid.isdigit()]
            self._counter: int = max(numeric_ids) + 1 if numeric_ids else 1
        else:
            # Programmatic building mode: start empty.
            self._graph = {}
            self._nodes = {}
            self._counter = 1

    # ------------------------------------------------------------------
    # Constructors (template mode)
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: str | Path) -> "Workflow":
        """Load a workflow from a JSON file.

        Parameters
        ----------
        path:
            Path to a ``.json`` file containing a ComfyUI prompt graph.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Workflow file not found: {p}")
        with p.open("r", encoding="utf-8") as fh:
            graph = json.load(fh)
        logger.debug("Loaded workflow from %s (%d nodes)", p, len(graph))
        return cls(graph)

    @classmethod
    def from_dict(cls, graph: dict[str, Any]) -> "Workflow":
        """Create a :class:`Workflow` from an existing prompt dict."""
        return cls(graph)

    @classmethod
    def from_json(cls, data: str | dict) -> "Workflow":
        """Load a workflow from a JSON string or dict (ComfyUI API prompt format)."""
        if isinstance(data, str):
            data = json.loads(data)
        return cls(data)

    # ------------------------------------------------------------------
    # Programmatic building (add_node mode)
    # ------------------------------------------------------------------

    def add_node(self, class_type: str, **inputs: Any) -> Node:
        """Add a new node and return it so its outputs can be wired to other nodes.

        This method is used for programmatic workflow construction.

        Parameters
        ----------
        class_type:
            The ComfyUI node class type (e.g., ``"KSampler"``).
        **inputs:
            Keyword arguments for the node inputs.  Values can be
            :class:`NodeOutput` instances to wire connections.

        Returns
        -------
        Node
            The created node, whose :meth:`Node.output` method can be
            used to connect to other nodes.
        """
        node_id = str(self._counter)
        self._counter += 1
        node = Node(node_id, class_type, **inputs)
        self._nodes[node_id] = node
        return node

    # ------------------------------------------------------------------
    # High-level parameter setters (template mode)
    # ------------------------------------------------------------------

    def set_positive_prompt(self, text: str) -> "Workflow":
        """Inject *text* into the positive conditioning ``CLIPTextEncode`` nodes."""
        positive_ids = self._find_ksampler_conditioning_ids("positive")
        if positive_ids:
            for node_id in positive_ids:
                self.set_node_input(node_id, "text", text)
        else:
            # Fallback: set the first CLIPTextEncode node found.
            for node_id in self._find_nodes_by_class("CLIPTextEncode"):
                self.set_node_input(node_id, "text", text)
                break
        return self

    def set_negative_prompt(self, text: str) -> "Workflow":
        """Inject *text* into the negative conditioning ``CLIPTextEncode``."""
        negative_ids = self._find_ksampler_conditioning_ids("negative")
        if negative_ids:
            for node_id in negative_ids:
                self.set_node_input(node_id, "text", text)
        else:
            nodes = self._find_nodes_by_class("CLIPTextEncode")
            if len(nodes) > 1:
                self.set_node_input(nodes[1], "text", text)
        return self

    def set_checkpoint(self, model_name: str) -> "Workflow":
        """Set the model checkpoint in any ``CheckpointLoaderSimple`` node."""
        for node_id in self._find_nodes_by_class("CheckpointLoaderSimple"):
            self.set_node_input(node_id, "ckpt_name", model_name)
        return self

    def set_seed(self, seed: int) -> "Workflow":
        """Set *seed* on all ``KSampler`` nodes."""
        for node_id in self._find_nodes_by_class("KSampler"):
            self.set_node_input(node_id, "seed", seed)
        return self

    def set_dimensions(self, width: int, height: int) -> "Workflow":
        """Set *width* and *height* on all ``EmptyLatentImage`` nodes."""
        for node_id in self._find_nodes_by_class("EmptyLatentImage"):
            self.set_node_input(node_id, "width", width)
            self.set_node_input(node_id, "height", height)
        return self

    def set_steps(self, steps: int) -> "Workflow":
        """Set the number of sampling *steps* on all ``KSampler`` nodes."""
        for node_id in self._find_nodes_by_class("KSampler"):
            self.set_node_input(node_id, "steps", steps)
        return self

    def set_cfg(self, cfg_scale: float) -> "Workflow":
        """Set the CFG scale on all ``KSampler`` nodes."""
        for node_id in self._find_nodes_by_class("KSampler"):
            self.set_node_input(node_id, "cfg", cfg_scale)
        return self

    def set_sampler(self, sampler_name: str) -> "Workflow":
        """Set the sampler name on all ``KSampler`` nodes."""
        for node_id in self._find_nodes_by_class("KSampler"):
            self.set_node_input(node_id, "sampler_name", sampler_name)
        return self

    def set_scheduler(self, scheduler: str) -> "Workflow":
        """Set the scheduler on all ``KSampler`` nodes."""
        for node_id in self._find_nodes_by_class("KSampler"):
            self.set_node_input(node_id, "scheduler", scheduler)
        return self

    # ------------------------------------------------------------------
    # Low-level node access
    # ------------------------------------------------------------------

    def set_node_input(self, node_id: str, key: str, value: Any) -> "Workflow":
        """Directly set an input *key* on node *node_id*.

        Parameters
        ----------
        node_id:
            The string key identifying the node in the graph (e.g. ``"4"``).
        key:
            The input field name (e.g. ``"text"``, ``"seed"``).
        value:
            The new value to assign.

        Raises
        ------
        WorkflowError
            If *node_id* is not present in the graph.
        """
        if node_id not in self._graph:
            raise WorkflowError(f"Node {node_id!r} not found in workflow graph")
        self._graph[node_id]["inputs"][key] = value
        logger.debug("Set node %s.%s = %r", node_id, key, value)
        return self

    def get_node(self, node_id: str) -> dict[str, Any]:
        """Return a copy of the node dict for *node_id*."""
        if node_id not in self._graph:
            raise WorkflowError(f"Node {node_id!r} not found in workflow graph")
        return copy.deepcopy(self._graph[node_id])

    def node_ids_by_class(self, class_type: str) -> list[str]:
        """Return all node IDs whose ``class_type`` matches *class_type*."""
        return self._find_nodes_by_class(class_type)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def build(self) -> dict[str, Any]:
        """Return the final prompt dict ready to be submitted to ComfyUI.

        Merges the template graph with any programmatically added nodes.
        """
        result: dict[str, Any] = copy.deepcopy(self._graph)
        # Add any programmatically-added nodes.
        for node_id, node in self._nodes.items():
            result[node_id] = node.to_dict()
        return result

    def to_json(self, indent: int = 2, **kwargs: Any) -> str:
        """Serialize the workflow to a JSON string."""
        return json.dumps(self.build(), indent=indent, **kwargs)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_nodes_by_class(self, class_type: str) -> list[str]:
        return [
            nid
            for nid, node in self._graph.items()
            if node.get("class_type") == class_type
        ]

    def _find_ksampler_conditioning_ids(self, conditioning: str) -> list[str]:
        """Return CLIPTextEncode node IDs wired to KSampler *conditioning*."""
        result: list[str] = []
        for node in self._graph.values():
            if node.get("class_type") != "KSampler":
                continue
            inputs = node.get("inputs", {})
            ref = inputs.get(conditioning)
            # ComfyUI link format: [source_node_id, output_slot]
            if isinstance(ref, list) and ref:
                source_id = str(ref[0])
                source_node = self._graph.get(source_id, {})
                if source_node.get("class_type") == "CLIPTextEncode":
                    result.append(source_id)
        return result
