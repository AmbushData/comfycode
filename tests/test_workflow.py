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
import os
import pytest

from comfycode.workflow import Workflow, WorkflowError

WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), "..", "workflows")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def txt2img_workflow() -> Workflow:
    return Workflow.from_file(os.path.join(WORKFLOWS_DIR, "txt2img.json"))


@pytest.fixture()
def minimal_graph() -> dict:
    """Tiny graph with one CLIPTextEncode, one KSampler, one EmptyLatentImage."""
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "model.safetensors"},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "original positive", "clip": ["1", 1]},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "original negative", "clip": ["1", 1]},
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 512, "height": 512, "batch_size": 1},
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0],
                "seed": 0,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
            },
        },
    }


# ---------------------------------------------------------------------------
# from_file / from_dict
# ---------------------------------------------------------------------------

def test_from_file_loads_nodes(txt2img_workflow):
    assert len(txt2img_workflow.build()) == 7


def test_from_file_not_found():
    with pytest.raises(FileNotFoundError):
        Workflow.from_file("/nonexistent/path/workflow.json")


def test_from_dict_deep_copies(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_seed(999)
    # Original dict must not be mutated.
    assert minimal_graph["5"]["inputs"]["seed"] == 0


def test_from_file_via_tempfile(minimal_graph, tmp_path):
    path = tmp_path / "workflow.json"
    path.write_text(json.dumps(minimal_graph), encoding="utf-8")
    wf = Workflow.from_file(path)
    assert "5" in wf.build()


# ---------------------------------------------------------------------------
# Prompt setters
# ---------------------------------------------------------------------------

def test_set_positive_prompt(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_positive_prompt("a red fox")
    built = wf.build()
    assert built["2"]["inputs"]["text"] == "a red fox"


def test_set_negative_prompt(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_negative_prompt("blurry")
    built = wf.build()
    assert built["3"]["inputs"]["text"] == "blurry"


def test_set_checkpoint(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_checkpoint("dreamshaper.safetensors")
    assert wf.build()["1"]["inputs"]["ckpt_name"] == "dreamshaper.safetensors"


def test_set_seed(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_seed(12345)
    assert wf.build()["5"]["inputs"]["seed"] == 12345


def test_set_dimensions(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_dimensions(768, 1024)
    built = wf.build()
    assert built["4"]["inputs"]["width"] == 768
    assert built["4"]["inputs"]["height"] == 1024


def test_set_steps(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_steps(30)
    assert wf.build()["5"]["inputs"]["steps"] == 30


def test_set_cfg(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_cfg(8.5)
    assert wf.build()["5"]["inputs"]["cfg"] == 8.5


def test_set_sampler(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_sampler("dpm_2")
    assert wf.build()["5"]["inputs"]["sampler_name"] == "dpm_2"


def test_set_scheduler(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_scheduler("karras")
    assert wf.build()["5"]["inputs"]["scheduler"] == "karras"


# ---------------------------------------------------------------------------
# Low-level access
# ---------------------------------------------------------------------------

def test_set_node_input_direct(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    wf.set_node_input("4", "batch_size", 4)
    assert wf.build()["4"]["inputs"]["batch_size"] == 4


def test_set_node_input_missing_node(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    with pytest.raises(WorkflowError):
        wf.set_node_input("999", "text", "x")


def test_get_node(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    node = wf.get_node("1")
    assert node["class_type"] == "CheckpointLoaderSimple"
    # Must be a copy – mutations must not affect the internal graph.
    node["inputs"]["ckpt_name"] = "tampered"
    assert wf.get_node("1")["inputs"]["ckpt_name"] == "model.safetensors"


def test_get_node_missing(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    with pytest.raises(WorkflowError):
        wf.get_node("999")


def test_node_ids_by_class(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    ids = wf.node_ids_by_class("CLIPTextEncode")
    assert set(ids) == {"2", "3"}


def test_build_returns_deep_copy(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    b1 = wf.build()
    b1["5"]["inputs"]["seed"] = 9999
    b2 = wf.build()
    assert b2["5"]["inputs"]["seed"] == 0  # original untouched


def test_to_json(minimal_graph):
    wf = Workflow.from_dict(minimal_graph)
    data = json.loads(wf.to_json())
    assert "5" in data


# ---------------------------------------------------------------------------
# Chaining
# ---------------------------------------------------------------------------

def test_method_chaining(minimal_graph):
    wf = (
        Workflow.from_dict(minimal_graph)
        .set_positive_prompt("sunset")
        .set_seed(1)
        .set_steps(10)
        .set_cfg(6.0)
    )
    built = wf.build()
    assert built["2"]["inputs"]["text"] == "sunset"
    assert built["5"]["inputs"]["seed"] == 1
    assert built["5"]["inputs"]["steps"] == 10
    assert built["5"]["inputs"]["cfg"] == 6.0
