"""Tests for comfycode.formats — format contracts for Prompt JSON and UI JSON."""

import pytest

from comfycode.formats import (
    PromptNode,
    PromptJSON,
    UINode,
    UIWorkflow,
    PROMPT_JSON_VERSION,
    UI_JSON_VERSION,
    validate_prompt_json,
    validate_ui_json,
)


class TestPromptJSONContract:
    """Tests for the Prompt JSON format contract."""

    VALID_PROMPT = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "model.ckpt"},
        },
        "2": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 42,
                "model": ["1", 0],
            },
        },
    }

    def test_prompt_json_version_is_defined(self):
        """Version string documents the supported prompt JSON format."""
        assert isinstance(PROMPT_JSON_VERSION, str)
        assert len(PROMPT_JSON_VERSION) > 0

    def test_validate_prompt_json_accepts_valid(self):
        """Valid prompt JSON passes validation."""
        errors = validate_prompt_json(self.VALID_PROMPT)
        assert errors == []

    def test_validate_prompt_json_rejects_missing_class_type(self):
        """Prompt JSON without class_type is invalid."""
        invalid = {"1": {"inputs": {}}}
        errors = validate_prompt_json(invalid)
        assert len(errors) > 0
        assert any("class_type" in e.lower() for e in errors)

    def test_validate_prompt_json_rejects_non_dict_node(self):
        """Prompt JSON with non-dict node value is invalid."""
        invalid = {"1": "not a dict"}
        errors = validate_prompt_json(invalid)
        assert len(errors) > 0

    def test_prompt_node_structure(self):
        """PromptNode TypedDict defines expected fields."""
        # This tests the type definition exists and has the right keys
        node: PromptNode = {"class_type": "Test", "inputs": {}}
        assert "class_type" in node
        assert "inputs" in node


class TestUIJSONContract:
    """Tests for the UI workflow JSON format contract."""

    VALID_UI_WORKFLOW = {
        "last_node_id": 2,
        "last_link_id": 1,
        "nodes": [
            {
                "id": 1,
                "type": "CheckpointLoaderSimple",
                "pos": [100, 200],
                "size": {"0": 315, "1": 98},
                "inputs": [],
                "outputs": [{"name": "MODEL", "type": "MODEL", "links": [1]}],
                "widgets_values": ["model.ckpt"],
            },
        ],
        "links": [[1, 1, 0, 2, 0, "MODEL"]],
        "groups": [],
        "config": {},
        "extra": {},
        "version": 0.4,
    }

    def test_ui_json_version_is_defined(self):
        """Version string documents the supported UI JSON format."""
        assert isinstance(UI_JSON_VERSION, str)
        assert len(UI_JSON_VERSION) > 0

    def test_validate_ui_json_accepts_valid(self):
        """Valid UI workflow JSON passes validation."""
        errors = validate_ui_json(self.VALID_UI_WORKFLOW)
        assert errors == []

    def test_validate_ui_json_rejects_missing_nodes(self):
        """UI JSON without nodes array is invalid."""
        invalid = {"last_node_id": 1, "links": []}
        errors = validate_ui_json(invalid)
        assert len(errors) > 0
        assert any("nodes" in e.lower() for e in errors)

    def test_validate_ui_json_rejects_missing_links(self):
        """UI JSON without links array is invalid."""
        invalid = {"nodes": [], "last_node_id": 0}
        errors = validate_ui_json(invalid)
        assert len(errors) > 0
        assert any("links" in e.lower() for e in errors)

    def test_ui_node_requires_position(self):
        """UI nodes must have position data."""
        missing_pos = {
            "last_node_id": 1,
            "last_link_id": 0,
            "nodes": [{"id": 1, "type": "Test"}],  # missing pos
            "links": [],
        }
        errors = validate_ui_json(missing_pos)
        assert len(errors) > 0
        assert any("pos" in e.lower() for e in errors)


class TestLossinessDocumentation:
    """Tests that lossiness expectations are documented."""

    def test_prompt_to_ui_lossy_fields_documented(self):
        """Converting prompt→UI loses certain data; this is documented."""
        from comfycode.formats import PROMPT_TO_UI_LOSSY_FIELDS

        assert isinstance(PROMPT_TO_UI_LOSSY_FIELDS, (list, tuple, set))

    def test_ui_to_prompt_lossy_fields_documented(self):
        """Converting UI→prompt loses certain data; this is documented."""
        from comfycode.formats import UI_TO_PROMPT_LOSSY_FIELDS

        assert isinstance(UI_TO_PROMPT_LOSSY_FIELDS, (list, tuple, set))
