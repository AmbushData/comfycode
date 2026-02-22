"""Format contracts for ComfyUI workflow JSON formats.

This module defines and documents the two JSON formats used by ComfyCode:

1. **Prompt JSON** — The ComfyUI API execution format (canonical for runtime).
2. **UI Workflow JSON** — The ComfyUI web UI export format (optional for viewing).

Schema Documentation
--------------------

**Prompt JSON** (API format):
    Structure: ``{ node_id: { class_type: str, inputs: dict } }``
    - node_id: String identifier (typically numeric like "1", "2", ...)
    - class_type: ComfyUI node class name (e.g., "KSampler")
    - inputs: Dict mapping input names to values or node links
    - Node links are [node_id, output_slot_index] pairs

**UI Workflow JSON** (web UI format):
    Structure: Top-level object with nodes array, links array, and metadata
    - nodes: Array of node objects with id, type, pos, size, widgets_values
    - links: Array of link tuples [link_id, from_node, from_slot, to_node, to_slot, type]
    - last_node_id, last_link_id: Counters for ID generation
    - groups, config, extra: UI-specific metadata
    - version: Schema version (e.g., 0.4)

Lossiness Notes
---------------
Converting between formats is inherently lossy:
- Prompt→UI loses: UI positions, node sizes, groups, UI config
- UI→Prompt loses: Link IDs, position data, widget layout, UI metadata
"""

from __future__ import annotations

from typing import Any, TypedDict


# =============================================================================
# Version Constants
# =============================================================================

PROMPT_JSON_VERSION = "comfyui-api-prompt-v1"
"""Version identifier for the prompt JSON format supported by ComfyCode.

This is the standard ComfyUI API prompt format used for workflow execution.
"""

UI_JSON_VERSION = "comfyui-web-ui-v0.4"
"""Version identifier for the UI workflow JSON format supported by ComfyCode.

This corresponds to the ComfyUI web UI export format (version 0.4).
Earlier or later versions may have schema differences.
"""


# =============================================================================
# Lossiness Documentation
# =============================================================================

PROMPT_TO_UI_LOSSY_FIELDS: tuple[str, ...] = (
    "node positions (generated deterministically)",
    "node sizes (uses defaults)",
    "link IDs (generated sequentially)",
    "groups (not present in prompt JSON)",
    "UI config/extra metadata (not present in prompt JSON)",
    "widget ordering (inferred from input order)",
)
"""Fields that cannot be preserved when converting prompt JSON → UI JSON.

These are generated or defaulted during conversion.
"""

UI_TO_PROMPT_LOSSY_FIELDS: tuple[str, ...] = (
    "node positions",
    "node sizes",
    "link IDs",
    "groups",
    "UI config",
    "extra metadata",
    "widget layout hints",
)
"""Fields that are discarded when converting UI JSON → prompt JSON.

These are UI-specific and not needed for workflow execution.
"""


# =============================================================================
# Type Definitions
# =============================================================================


class PromptNode(TypedDict, total=False):
    """A single node in a ComfyUI prompt JSON.

    Required fields:
        class_type: The ComfyUI node class name.
        inputs: Dict of input name to value or link reference.

    Links are represented as [node_id, output_slot_index] pairs.
    """

    class_type: str
    inputs: dict[str, Any]


# Prompt JSON is a dict mapping node_id strings to PromptNode dicts
PromptJSON = dict[str, PromptNode]


class UINodeOutput(TypedDict, total=False):
    """Output slot definition for a UI node."""

    name: str
    type: str
    links: list[int] | None


class UINodeInput(TypedDict, total=False):
    """Input slot definition for a UI node."""

    name: str
    type: str
    link: int | None


class UINode(TypedDict, total=False):
    """A single node in a ComfyUI UI workflow JSON.

    Required fields:
        id: Numeric node ID.
        type: The ComfyUI node class name.
        pos: [x, y] position in the UI canvas.

    Optional fields:
        size: Node dimensions.
        inputs: Array of input slot definitions.
        outputs: Array of output slot definitions.
        widgets_values: Array of widget values (non-link inputs).
    """

    id: int
    type: str
    pos: list[float]
    size: dict[str, float] | list[float]
    inputs: list[UINodeInput]
    outputs: list[UINodeOutput]
    widgets_values: list[Any]


class UIWorkflow(TypedDict, total=False):
    """Top-level structure of a ComfyUI UI workflow JSON.

    Required fields:
        nodes: Array of UINode objects.
        links: Array of link tuples.

    Optional fields:
        last_node_id: Counter for next node ID.
        last_link_id: Counter for next link ID.
        groups: Array of node group definitions.
        config: UI configuration object.
        extra: Additional metadata.
        version: Schema version number.
    """

    last_node_id: int
    last_link_id: int
    nodes: list[UINode]
    links: list[list[Any]]
    groups: list[Any]
    config: dict[str, Any]
    extra: dict[str, Any]
    version: float


# =============================================================================
# Validation Functions
# =============================================================================


def validate_prompt_json(data: Any) -> list[str]:
    """Validate that data conforms to the prompt JSON format.

    Args:
        data: The data to validate.

    Returns:
        A list of error messages. Empty list means valid.
    """
    errors: list[str] = []

    if not isinstance(data, dict):
        errors.append("Prompt JSON must be a dict")
        return errors

    for node_id, node_data in data.items():
        if not isinstance(node_id, str):
            errors.append(f"Node ID must be string, got {type(node_id).__name__}")

        if not isinstance(node_data, dict):
            errors.append(f"Node '{node_id}': value must be a dict, got {type(node_data).__name__}")
            continue

        if "class_type" not in node_data:
            errors.append(f"Node '{node_id}': missing required field 'class_type'")

        if "inputs" in node_data and not isinstance(node_data["inputs"], dict):
            errors.append(f"Node '{node_id}': 'inputs' must be a dict")

    return errors


def validate_ui_json(data: Any) -> list[str]:
    """Validate that data conforms to the UI workflow JSON format.

    Args:
        data: The data to validate.

    Returns:
        A list of error messages. Empty list means valid.
    """
    errors: list[str] = []

    if not isinstance(data, dict):
        errors.append("UI workflow JSON must be a dict")
        return errors

    if "nodes" not in data:
        errors.append("UI workflow JSON missing required field 'nodes'")
    elif not isinstance(data["nodes"], list):
        errors.append("UI workflow JSON 'nodes' must be an array")
    else:
        # Validate individual nodes
        for i, node in enumerate(data["nodes"]):
            if not isinstance(node, dict):
                errors.append(f"Node at index {i}: must be a dict")
                continue

            if "pos" not in node:
                errors.append(f"Node at index {i} (id={node.get('id', '?')}): missing required field 'pos'")

    if "links" not in data:
        errors.append("UI workflow JSON missing required field 'links'")
    elif not isinstance(data["links"], list):
        errors.append("UI workflow JSON 'links' must be an array")

    return errors
