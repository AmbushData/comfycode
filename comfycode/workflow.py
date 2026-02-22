"""Workflow templating and parameterization.

A :class:`Workflow` wraps a ComfyUI JSON prompt graph and provides helpers
for injecting parameters (positive/negative prompts, model checkpoint, seed,
dimensions, sampler settings) into specific nodes by their *class type* or
by an explicit *node ID*.

Workflows can be loaded from JSON files on disk so that the graph structure
is version-controlled separately from the Python code that runs it.
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


class Workflow:
    """A ComfyUI prompt graph with parameter-injection helpers.

    Parameters
    ----------
    graph:
        The raw ComfyUI prompt dict (maps node IDs → node dicts, each
        containing ``"class_type"`` and ``"inputs"`` keys).

    Examples
    --------
    Load from a JSON file and set a positive prompt:

    >>> wf = Workflow.from_file("workflows/txt2img.json")
    >>> wf.set_positive_prompt("a red fox in a snowy forest")
    >>> wf.set_seed(42)
    >>> prompt_dict = wf.build()
    """

    def __init__(self, graph: dict[str, Any]) -> None:
        # Keep the original untouched; work on a deep copy.
        self._graph: dict[str, Any] = copy.deepcopy(graph)

    # ------------------------------------------------------------------
    # Constructors
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

    # ------------------------------------------------------------------
    # High-level parameter setters
    # ------------------------------------------------------------------

    def set_positive_prompt(self, text: str) -> "Workflow":
        """Inject *text* into the ``text`` input of all ``CLIPTextEncode``
        nodes wired to a ``KSampler`` as the positive conditioning.

        Falls back to setting *all* ``CLIPTextEncode`` nodes whose first
        appearance in the graph has a ``text`` key.
        """
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

    def build(self) -> dict[str, Any]:
        """Return the final prompt dict ready to be submitted to ComfyUI."""
        return copy.deepcopy(self._graph)

    def to_json(self, indent: int = 2) -> str:
        """Serialise the current graph to a JSON string."""
        return json.dumps(self._graph, indent=indent)

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
