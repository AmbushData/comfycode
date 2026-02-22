"""Tests for comfycode.ui_export — IR to UI workflow JSON export."""

import json
import pytest

from comfycode.ui_export import (
    ir_to_ui_json,
    prompt_to_ui_json,
)
from comfycode.ir import (
    WorkflowIR,
    IRNode,
    IREdge,
    prompt_json_to_ir,
)
from comfycode.formats import validate_ui_json


class TestIRToUIJSON:
    """Tests for converting IR to UI workflow JSON."""

    def test_produces_valid_ui_json(self):
        """Output conforms to UI JSON format."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="Test", inputs={"value": 42}))
        
        result = ir_to_ui_json(ir)
        
        errors = validate_ui_json(result)
        assert errors == [], f"Validation errors: {errors}"

    def test_nodes_have_positions(self):
        """All nodes have position data."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="Test", inputs={}))
        ir.add_node(IRNode(node_id="2", class_type="Test2", inputs={}))
        
        result = ir_to_ui_json(ir)
        
        for node in result["nodes"]:
            assert "pos" in node
            assert isinstance(node["pos"], list)
            assert len(node["pos"]) == 2

    def test_nodes_have_type(self):
        """Nodes have correct type field (class_type)."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="KSampler", inputs={}))
        
        result = ir_to_ui_json(ir)
        
        node = result["nodes"][0]
        assert node["type"] == "KSampler"

    def test_nodes_have_integer_ids(self):
        """UI nodes have integer IDs."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="42", class_type="Test", inputs={}))
        
        result = ir_to_ui_json(ir)
        
        node = result["nodes"][0]
        assert node["id"] == 42

    def test_widget_values_populated(self):
        """Non-link inputs become widget values."""
        ir = WorkflowIR()
        ir.add_node(IRNode(
            node_id="1",
            class_type="KSampler",
            inputs={"seed": 42, "steps": 20},
        ))
        
        result = ir_to_ui_json(ir)
        
        node = result["nodes"][0]
        assert "widgets_values" in node
        # Values should be in the widgets_values list
        assert 42 in node["widgets_values"]
        assert 20 in node["widgets_values"]

    def test_links_generated(self):
        """Edges become links in the correct format."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="Source", inputs={}))
        ir.add_node(IRNode(node_id="2", class_type="Sink", inputs={}))
        ir.add_edge(IREdge(from_node="1", from_slot=0, to_node="2", to_input="x"))
        
        result = ir_to_ui_json(ir)
        
        assert "links" in result
        assert len(result["links"]) == 1
        link = result["links"][0]
        # Link format: [link_id, from_node, from_slot, to_node, to_slot, type]
        assert isinstance(link, list)
        assert len(link) >= 6

    def test_last_node_id_correct(self):
        """last_node_id is set to the highest node ID."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="A", inputs={}))
        ir.add_node(IRNode(node_id="5", class_type="B", inputs={}))
        ir.add_node(IRNode(node_id="3", class_type="C", inputs={}))
        
        result = ir_to_ui_json(ir)
        
        assert result["last_node_id"] == 5

    def test_last_link_id_correct(self):
        """last_link_id matches the number of links."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="Source", inputs={}))
        ir.add_node(IRNode(node_id="2", class_type="Sink", inputs={}))
        ir.add_edge(IREdge(from_node="1", from_slot=0, to_node="2", to_input="a"))
        ir.add_edge(IREdge(from_node="1", from_slot=1, to_node="2", to_input="b"))
        
        result = ir_to_ui_json(ir)
        
        assert result["last_link_id"] == 2

    def test_has_version(self):
        """Output includes version number."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="Test", inputs={}))
        
        result = ir_to_ui_json(ir)
        
        assert "version" in result
        assert isinstance(result["version"], (int, float))

    def test_empty_ir_produces_empty_workflow(self):
        """Empty IR produces valid but empty UI JSON."""
        ir = WorkflowIR()
        
        result = ir_to_ui_json(ir)
        
        errors = validate_ui_json(result)
        assert errors == []
        assert result["nodes"] == []
        assert result["links"] == []


class TestPromptToUIJSON:
    """Tests for the convenience function prompt_to_ui_json."""

    SIMPLE_PROMPT = {
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

    def test_converts_prompt_to_ui_json(self):
        """Can convert prompt JSON directly to UI JSON."""
        result = prompt_to_ui_json(self.SIMPLE_PROMPT)
        
        errors = validate_ui_json(result)
        assert errors == []
        assert len(result["nodes"]) == 2
        assert len(result["links"]) == 1

    def test_nodes_have_layout(self):
        """Converted nodes have deterministic positions."""
        result = prompt_to_ui_json(self.SIMPLE_PROMPT)
        
        # Find checkpoint and sampler nodes
        nodes_by_type = {n["type"]: n for n in result["nodes"]}
        
        checkpoint = nodes_by_type["CheckpointLoaderSimple"]
        sampler = nodes_by_type["KSampler"]
        
        # Checkpoint should be to the left of sampler
        assert checkpoint["pos"][0] < sampler["pos"][0]

    def test_output_is_serializable(self):
        """Output can be serialized to JSON string."""
        result = prompt_to_ui_json(self.SIMPLE_PROMPT)
        
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        
        # And can be parsed back
        parsed = json.loads(json_str)
        assert parsed == result

    def test_deterministic_output(self):
        """Same input produces same output."""
        result1 = prompt_to_ui_json(self.SIMPLE_PROMPT)
        result2 = prompt_to_ui_json(self.SIMPLE_PROMPT)
        
        # Positions should be identical
        for n1, n2 in zip(result1["nodes"], result2["nodes"]):
            assert n1["pos"] == n2["pos"]
