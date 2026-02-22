"""Tests for comfycode.batch."""

import pytest
from unittest.mock import MagicMock, patch

from comfycode.batch import BatchProcessor, BatchResult
from comfycode.workflow import Workflow


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def base_graph():
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "model.safetensors"},
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "positive", "clip": ["1", 1]},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "negative", "clip": ["1", 1]},
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


@pytest.fixture()
def base_workflow(base_graph):
    return Workflow.from_dict(base_graph)


@pytest.fixture()
def mock_client():
    client = MagicMock()
    client.run_workflow.return_value = [
        {"node_id": "7", "type": "images", "files": [{"filename": "out.png"}]}
    ]
    return client


# ---------------------------------------------------------------------------
# BatchResult
# ---------------------------------------------------------------------------

def test_batch_result_success():
    r = BatchResult(index=0, params={"seed": 1}, outputs=[{"node_id": "1"}])
    assert r.success is True
    assert r.error is None


def test_batch_result_failure():
    err = ValueError("boom")
    r = BatchResult(index=0, params={}, error=err)
    assert r.success is False
    assert r.error is err
    assert r.outputs == []


def test_batch_result_repr():
    r = BatchResult(index=2, params={})
    assert "index=2" in repr(r)


# ---------------------------------------------------------------------------
# BatchProcessor.run – happy path
# ---------------------------------------------------------------------------

def test_run_single_item(base_workflow, mock_client):
    processor = BatchProcessor(base_workflow, mock_client)
    results = processor.run([{"positive_prompt": "a cat", "seed": 42}])
    assert len(results) == 1
    assert results[0].success
    assert results[0].outputs[0]["type"] == "images"
    mock_client.run_workflow.assert_called_once()


def test_run_multiple_items(base_workflow, mock_client):
    items = [
        {"positive_prompt": "fox", "seed": 1},
        {"positive_prompt": "whale", "seed": 2},
    ]
    processor = BatchProcessor(base_workflow, mock_client)
    results = processor.run(items)
    assert len(results) == 2
    assert all(r.success for r in results)
    assert mock_client.run_workflow.call_count == 2


def test_run_empty_batch(base_workflow, mock_client):
    processor = BatchProcessor(base_workflow, mock_client)
    results = processor.run([])
    assert results == []
    mock_client.run_workflow.assert_not_called()


# ---------------------------------------------------------------------------
# Parameter injection
# ---------------------------------------------------------------------------

def test_params_injected_independently(base_graph, mock_client):
    """Each batch item gets an independent copy of the workflow."""
    base = Workflow.from_dict(base_graph)
    processor = BatchProcessor(base, mock_client)

    captured_prompts = []

    def capture(prompt):
        captured_prompts.append(prompt)
        return []

    mock_client.run_workflow.side_effect = capture

    processor.run([
        {"seed": 1},
        {"seed": 2},
    ])

    seed_0 = captured_prompts[0]["5"]["inputs"]["seed"]
    seed_1 = captured_prompts[1]["5"]["inputs"]["seed"]
    assert seed_0 == 1
    assert seed_1 == 2
    # Base workflow seed must be unchanged.
    assert base.build()["5"]["inputs"]["seed"] == 0


def test_dimension_param_applied(base_workflow, mock_client):
    captured = []
    mock_client.run_workflow.side_effect = lambda p: captured.append(p) or []
    processor = BatchProcessor(base_workflow, mock_client)
    processor.run([{"width": 768, "height": 1024}])
    assert captured[0]["4"]["inputs"]["width"] == 768
    assert captured[0]["4"]["inputs"]["height"] == 1024


def test_unknown_param_ignored(base_workflow, mock_client):
    """Unknown parameter keys are silently ignored and don't raise."""
    processor = BatchProcessor(base_workflow, mock_client)
    results = processor.run([{"totally_unknown_key": "value"}])
    assert results[0].success


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_skip_errors_continues(base_workflow, mock_client):
    mock_client.run_workflow.side_effect = [
        RuntimeError("first failed"),
        [{"node_id": "7", "type": "images", "files": []}],
    ]
    processor = BatchProcessor(base_workflow, mock_client, skip_errors=True)
    results = processor.run([{"seed": 1}, {"seed": 2}])
    assert results[0].success is False
    assert results[1].success is True


def test_no_skip_errors_raises(base_workflow, mock_client):
    mock_client.run_workflow.side_effect = RuntimeError("fail fast")
    processor = BatchProcessor(base_workflow, mock_client, skip_errors=False)
    with pytest.raises(RuntimeError):
        processor.run([{"seed": 1}])
