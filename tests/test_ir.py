"""Tests for comfycode.ir — Workflow Intermediate Representation."""

import pytest

from comfycode.ir import (
    IRNode,
    IREdge,
    WorkflowIR,
    prompt_json_to_ir,
    ir_to_prompt_json,
)


class TestIRNode:
    """Tests for the IRNode data class."""

    def test_create_ir_node(self):
        """Can create an IR node with required fields."""
        node = IRNode(
            node_id="1",
            class_type="KSampler",
            inputs={"seed": 42},
        )
        assert node.node_id == "1"
        assert node.class_type == "KSampler"
        assert node.inputs == {"seed": 42}

    def test_ir_node_optional_layout(self):
        """IR nodes can have optional layout hints."""
        node = IRNode(
            node_id="1",
            class_type="Test",
            inputs={},
            pos=(100.0, 200.0),
        )
        assert node.pos == (100.0, 200.0)

    def test_ir_node_default_no_position(self):
        """IR nodes default to no position."""
        node = IRNode(node_id="1", class_type="Test", inputs={})
        assert node.pos is None


class TestIREdge:
    """Tests for the IREdge data class."""

    def test_create_ir_edge(self):
        """Can create an IR edge with required fields."""
        edge = IREdge(
            from_node="1",
            from_slot=0,
            to_node="2",
            to_input="model",
        )
        assert edge.from_node == "1"
        assert edge.from_slot == 0
        assert edge.to_node == "2"
        assert edge.to_input == "model"


class TestWorkflowIR:
    """Tests for the WorkflowIR container."""

    def test_create_empty_ir(self):
        """Can create an empty workflow IR."""
        ir = WorkflowIR()
        assert ir.nodes == {}
        assert ir.edges == []

    def test_add_node_to_ir(self):
        """Can add nodes to the IR."""
        ir = WorkflowIR()
        node = IRNode(node_id="1", class_type="Test", inputs={})
        ir.add_node(node)
        assert "1" in ir.nodes
        assert ir.nodes["1"] is node

    def test_add_edge_to_ir(self):
        """Can add edges to the IR."""
        ir = WorkflowIR()
        edge = IREdge(from_node="1", from_slot=0, to_node="2", to_input="x")
        ir.add_edge(edge)
        assert len(ir.edges) == 1
        assert ir.edges[0] is edge

    def test_get_node_by_id(self):
        """Can retrieve a node by ID."""
        ir = WorkflowIR()
        node = IRNode(node_id="1", class_type="Test", inputs={})
        ir.add_node(node)
        assert ir.get_node("1") is node
        assert ir.get_node("999") is None


class TestPromptJSONToIR:
    """Tests for converting prompt JSON to IR."""

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

    def test_creates_ir_nodes(self):
        """Prompt JSON nodes become IR nodes."""
        ir = prompt_json_to_ir(self.SIMPLE_PROMPT)
        assert "1" in ir.nodes
        assert "2" in ir.nodes
        assert ir.nodes["1"].class_type == "CheckpointLoaderSimple"
        assert ir.nodes["2"].class_type == "KSampler"

    def test_extracts_non_link_inputs(self):
        """Non-link inputs are preserved in IR nodes."""
        ir = prompt_json_to_ir(self.SIMPLE_PROMPT)
        assert ir.nodes["1"].inputs["ckpt_name"] == "model.ckpt"
        assert ir.nodes["2"].inputs["seed"] == 42

    def test_extracts_edges_from_links(self):
        """Link references become IR edges."""
        ir = prompt_json_to_ir(self.SIMPLE_PROMPT)
        assert len(ir.edges) == 1
        edge = ir.edges[0]
        assert edge.from_node == "1"
        assert edge.from_slot == 0
        assert edge.to_node == "2"
        assert edge.to_input == "model"

    def test_link_not_in_node_inputs(self):
        """Link inputs are moved to edges, not kept in node inputs."""
        ir = prompt_json_to_ir(self.SIMPLE_PROMPT)
        # The "model" input was a link, should not be in inputs dict
        assert "model" not in ir.nodes["2"].inputs


class TestIRToPromptJSON:
    """Tests for converting IR back to prompt JSON."""

    def test_round_trip_simple(self):
        """prompt JSON → IR → prompt JSON yields equivalent graph."""
        original = {
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
        ir = prompt_json_to_ir(original)
        result = ir_to_prompt_json(ir)

        # Should have same nodes
        assert set(result.keys()) == set(original.keys())

        # Node 1 should match
        assert result["1"]["class_type"] == "CheckpointLoaderSimple"
        assert result["1"]["inputs"]["ckpt_name"] == "model.ckpt"

        # Node 2 should match (including reconstructed link)
        assert result["2"]["class_type"] == "KSampler"
        assert result["2"]["inputs"]["seed"] == 42
        assert result["2"]["inputs"]["model"] == ["1", 0]

    def test_round_trip_multiple_links(self):
        """Round-trip preserves multiple links to the same node."""
        original = {
            "1": {"class_type": "Source", "inputs": {}},
            "2": {
                "class_type": "Sink",
                "inputs": {
                    "a": ["1", 0],
                    "b": ["1", 1],
                },
            },
        }
        ir = prompt_json_to_ir(original)
        result = ir_to_prompt_json(ir)

        assert result["2"]["inputs"]["a"] == ["1", 0]
        assert result["2"]["inputs"]["b"] == ["1", 1]

    def test_empty_ir_produces_empty_json(self):
        """Empty IR produces empty prompt JSON."""
        ir = WorkflowIR()
        result = ir_to_prompt_json(ir)
        assert result == {}
