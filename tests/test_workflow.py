"""Tests for comfycode.workflow."""

import json
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
