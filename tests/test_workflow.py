"""Tests for comfycode.workflow."""

import json
import pytest

from comfycode.workflow import Node, NodeOutput, Workflow


class TestNodeOutput:
    def test_to_link_slot_zero(self):
        node = Node("3", "KSampler")
        out = node.output(0)
        assert out.to_link() == ["3", 0]

    def test_to_link_slot_nonzero(self):
        node = Node("1", "CheckpointLoaderSimple")
        assert node.output(1).to_link() == ["1", 1]
        assert node.output(2).to_link() == ["1", 2]

    def test_output_default_slot_is_zero(self):
        node = Node("5", "VAEDecode")
        assert node.output().index == 0


class TestNode:
    def test_to_dict_no_links(self):
        node = Node("2", "EmptyLatentImage", width=512, height=512, batch_size=1)
        d = node.to_dict()
        assert d["class_type"] == "EmptyLatentImage"
        assert d["inputs"] == {"width": 512, "height": 512, "batch_size": 1}

    def test_to_dict_with_link(self):
        ckpt = Node("1", "CheckpointLoaderSimple", ckpt_name="model.ckpt")
        clip_node = Node("3", "CLIPTextEncode", text="hello", clip=ckpt.output(1))
        d = clip_node.to_dict()
        assert d["inputs"]["clip"] == ["1", 1]
        assert d["inputs"]["text"] == "hello"

    def test_to_dict_no_inputs(self):
        node = Node("1", "CheckpointLoaderSimple")
        assert node.to_dict()["inputs"] == {}


class TestWorkflow:
    def _build_simple_workflow(self) -> Workflow:
        wf = Workflow()
        ckpt = wf.add_node("CheckpointLoaderSimple", ckpt_name="model.ckpt")
        latent = wf.add_node("EmptyLatentImage", width=512, height=512, batch_size=1)
        pos = wf.add_node("CLIPTextEncode", text="a cat", clip=ckpt.output(1))
        neg = wf.add_node("CLIPTextEncode", text="ugly", clip=ckpt.output(2))
        sampler = wf.add_node(
            "KSampler",
            seed=1,
            steps=20,
            cfg=7.0,
            sampler_name="euler_ancestral",
            scheduler="normal",
            denoise=1.0,
            model=ckpt.output(0),
            positive=pos.output(),
            negative=neg.output(),
            latent_image=latent.output(),
        )
        decoded = wf.add_node("VAEDecode", samples=sampler.output(), vae=ckpt.output(2))
        wf.add_node("SaveImage", filename_prefix="out", images=decoded.output())
        return wf

    def test_node_ids_are_sequential(self):
        wf = self._build_simple_workflow()
        prompt = wf.build()
        assert set(prompt.keys()) == {"1", "2", "3", "4", "5", "6", "7"}

    def test_links_are_serialized(self):
        wf = self._build_simple_workflow()
        prompt = wf.build()
        # KSampler (node 5) should reference checkpoint (node 1) for model
        assert prompt["5"]["inputs"]["model"] == ["1", 0]
        assert prompt["5"]["inputs"]["positive"] == ["3", 0]
        assert prompt["5"]["inputs"]["negative"] == ["4", 0]

    def test_build_returns_valid_class_types(self):
        wf = self._build_simple_workflow()
        prompt = wf.build()
        assert prompt["1"]["class_type"] == "CheckpointLoaderSimple"
        assert prompt["5"]["class_type"] == "KSampler"
        assert prompt["7"]["class_type"] == "SaveImage"

    def test_to_json_roundtrip(self):
        wf = self._build_simple_workflow()
        json_str = wf.to_json()
        data = json.loads(json_str)
        assert "5" in data
        assert data["5"]["class_type"] == "KSampler"

    def test_from_json_string(self):
        original = self._build_simple_workflow()
        json_str = original.to_json()
        loaded = Workflow.from_json(json_str)
        assert loaded.build() == original.build()

    def test_from_json_dict(self):
        original = self._build_simple_workflow()
        prompt = original.build()
        loaded = Workflow.from_json(prompt)
        assert loaded.build() == prompt

    def test_from_json_counter_advances_past_existing_ids(self):
        wf = self._build_simple_workflow()
        loaded = Workflow.from_json(wf.to_json())
        new_node = loaded.add_node("PreviewImage", images=["dummy"])
        assert int(new_node.node_id) > 7

    def test_add_node_returns_node(self):
        wf = Workflow()
        node = wf.add_node("CheckpointLoaderSimple", ckpt_name="x.ckpt")
        assert isinstance(node, Node)
        assert node.class_type == "CheckpointLoaderSimple"

    def test_empty_workflow_builds_to_empty_dict(self):
        assert Workflow().build() == {}
