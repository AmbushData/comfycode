"""Tests for comfycode.layout — deterministic DAG layout generation."""

import pytest

from comfycode.layout import (
    compute_layout,
    LayoutConfig,
    NodeLayout,
)
from comfycode.ir import (
    WorkflowIR,
    IRNode,
    IREdge,
    prompt_json_to_ir,
)


class TestLayoutConfig:
    """Tests for layout configuration."""

    def test_default_config_has_spacing(self):
        """Default config has reasonable X and Y spacing."""
        config = LayoutConfig()
        assert config.x_step > 0
        assert config.y_step > 0

    def test_config_has_sensible_defaults(self):
        """Default spacing is around 300x120 as per architecture doc."""
        config = LayoutConfig()
        # Allow some flexibility but should be in the ballpark
        assert 200 <= config.x_step <= 400
        assert 80 <= config.y_step <= 160


class TestNodeLayout:
    """Tests for the NodeLayout data class."""

    def test_create_node_layout(self):
        """Can create a NodeLayout with position."""
        layout = NodeLayout(node_id="1", x=100.0, y=200.0)
        assert layout.node_id == "1"
        assert layout.x == 100.0
        assert layout.y == 200.0


class TestComputeLayout:
    """Tests for the compute_layout function."""

    def test_single_node_at_origin(self):
        """A single node is placed near the origin."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="Test", inputs={}))
        
        layouts = compute_layout(ir)
        
        assert "1" in layouts
        assert layouts["1"].x >= 0
        assert layouts["1"].y >= 0

    def test_two_connected_nodes_horizontal(self):
        """Connected nodes are placed left-to-right."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="Source", inputs={}))
        ir.add_node(IRNode(node_id="2", class_type="Sink", inputs={}))
        ir.add_edge(IREdge(from_node="1", from_slot=0, to_node="2", to_input="x"))
        
        layouts = compute_layout(ir)
        
        # Source (1) should be to the left of sink (2)
        assert layouts["1"].x < layouts["2"].x

    def test_chain_of_three_nodes(self):
        """Chain: 1 → 2 → 3 should be laid out left-to-right."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="A", inputs={}))
        ir.add_node(IRNode(node_id="2", class_type="B", inputs={}))
        ir.add_node(IRNode(node_id="3", class_type="C", inputs={}))
        ir.add_edge(IREdge(from_node="1", from_slot=0, to_node="2", to_input="x"))
        ir.add_edge(IREdge(from_node="2", from_slot=0, to_node="3", to_input="x"))
        
        layouts = compute_layout(ir)
        
        assert layouts["1"].x < layouts["2"].x < layouts["3"].x

    def test_parallel_nodes_same_layer(self):
        """Two nodes with same source should be in same layer but different Y."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="Source", inputs={}))
        ir.add_node(IRNode(node_id="2", class_type="SinkA", inputs={}))
        ir.add_node(IRNode(node_id="3", class_type="SinkB", inputs={}))
        ir.add_edge(IREdge(from_node="1", from_slot=0, to_node="2", to_input="x"))
        ir.add_edge(IREdge(from_node="1", from_slot=0, to_node="3", to_input="x"))
        
        layouts = compute_layout(ir)
        
        # Nodes 2 and 3 should be in the same layer (same X, approximately)
        assert abs(layouts["2"].x - layouts["3"].x) < 10
        # But different Y positions
        assert layouts["2"].y != layouts["3"].y

    def test_no_overlap_guaranteed(self):
        """Nodes should not overlap (Y positions should be sufficiently separated)."""
        ir = WorkflowIR()
        # Add multiple nodes in the same layer
        ir.add_node(IRNode(node_id="1", class_type="Source", inputs={}))
        for i in range(2, 6):
            ir.add_node(IRNode(node_id=str(i), class_type=f"Sink{i}", inputs={}))
            ir.add_edge(IREdge(from_node="1", from_slot=0, to_node=str(i), to_input="x"))
        
        layouts = compute_layout(ir)
        config = LayoutConfig()
        
        # All sink nodes should have unique Y positions with at least y_step separation
        sink_ys = sorted([layouts[str(i)].y for i in range(2, 6)])
        for i in range(len(sink_ys) - 1):
            assert sink_ys[i + 1] - sink_ys[i] >= config.y_step * 0.9  # Allow 10% tolerance

    def test_deterministic_layout(self):
        """Same IR produces same layout every time."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="A", inputs={}))
        ir.add_node(IRNode(node_id="2", class_type="B", inputs={}))
        ir.add_edge(IREdge(from_node="1", from_slot=0, to_node="2", to_input="x"))
        
        layout1 = compute_layout(ir)
        layout2 = compute_layout(ir)
        
        assert layout1["1"].x == layout2["1"].x
        assert layout1["1"].y == layout2["1"].y
        assert layout1["2"].x == layout2["2"].x
        assert layout1["2"].y == layout2["2"].y

    def test_respects_custom_config(self):
        """Layout respects custom spacing configuration."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="A", inputs={}))
        ir.add_node(IRNode(node_id="2", class_type="B", inputs={}))
        ir.add_edge(IREdge(from_node="1", from_slot=0, to_node="2", to_input="x"))
        
        config = LayoutConfig(x_step=500, y_step=200)
        layouts = compute_layout(ir, config=config)
        
        # The horizontal gap should reflect the custom x_step
        x_gap = layouts["2"].x - layouts["1"].x
        assert x_gap >= config.x_step * 0.9

    def test_empty_ir_returns_empty_layout(self):
        """Empty IR produces empty layout."""
        ir = WorkflowIR()
        layouts = compute_layout(ir)
        assert layouts == {}

    def test_disconnected_nodes_handled(self):
        """Disconnected nodes are still laid out (treated as separate sources)."""
        ir = WorkflowIR()
        ir.add_node(IRNode(node_id="1", class_type="A", inputs={}))
        ir.add_node(IRNode(node_id="2", class_type="B", inputs={}))
        # No edges - disconnected
        
        layouts = compute_layout(ir)
        
        assert "1" in layouts
        assert "2" in layouts
        # Both should be in layer 0 but different Y
        assert layouts["1"].y != layouts["2"].y


class TestLayoutFromPromptJSON:
    """Integration tests: layout from prompt JSON."""

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
        "3": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["2", 0],
                "vae": ["1", 2],
            },
        },
    }

    def test_prompt_to_layout(self):
        """Can compute layout from prompt JSON via IR."""
        ir = prompt_json_to_ir(self.SIMPLE_PROMPT)
        layouts = compute_layout(ir)
        
        assert len(layouts) == 3
        # Checkpoint (source) should be leftmost
        assert layouts["1"].x < layouts["2"].x
        assert layouts["1"].x < layouts["3"].x
        # VAEDecode depends on KSampler, so should be to its right
        assert layouts["2"].x < layouts["3"].x
