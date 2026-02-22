"""Tests for comfycode.pipeline."""

import os
import pytest
from unittest.mock import MagicMock, patch, call

from comfycode.config import Config
from comfycode.pipeline import Pipeline
from comfycode.workflow import Workflow


WORKFLOWS_DIR = os.path.join(os.path.dirname(__file__), "..", "workflows")
TXT2IMG = os.path.join(WORKFLOWS_DIR, "txt2img.json")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def config(tmp_path):
    return Config(
        comfyui_host="127.0.0.1",
        comfyui_port=8188,
        output_dir=str(tmp_path / "output"),
    )


@pytest.fixture()
def mock_client_outputs():
    return [{"node_id": "7", "type": "images", "files": [{"filename": "out.png"}]}]


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def test_pipeline_loads_workflow(config):
    p = Pipeline(TXT2IMG, config=config, auto_provision=False)
    assert p.workflow is not None
    # The workflow should have the nodes from the JSON file.
    assert "5" in p.workflow.build()


def test_pipeline_bad_workflow_path(config):
    with pytest.raises(FileNotFoundError):
        Pipeline("/nonexistent/workflow.json", config=config, auto_provision=False)


def test_client_not_available_before_start(config):
    p = Pipeline(TXT2IMG, config=config, auto_provision=False)
    with pytest.raises(RuntimeError):
        _ = p.client


# ---------------------------------------------------------------------------
# start / teardown
# ---------------------------------------------------------------------------

def test_start_creates_client(config):
    p = Pipeline(TXT2IMG, config=config, auto_provision=False)
    p.start()
    assert p._client is not None


def test_start_idempotent(config):
    p = Pipeline(TXT2IMG, config=config, auto_provision=False)
    p.start()
    client_ref = p._client
    p.start()  # second call must be a no-op
    assert p._client is client_ref


def test_teardown_clears_client(config):
    p = Pipeline(TXT2IMG, config=config, auto_provision=False)
    p.start()
    p.teardown()
    assert p._client is None


# ---------------------------------------------------------------------------
# run (single)
# ---------------------------------------------------------------------------

def test_run_returns_outputs(config, mock_client_outputs, tmp_path):
    p = Pipeline(TXT2IMG, config=config, auto_provision=False)
    p.start()
    with patch.object(p._client, "run_workflow", return_value=mock_client_outputs):
        outputs = p.run(positive_prompt="a cat", seed=1)
    assert len(outputs) == 1
    assert outputs[0]["type"] == "images"


def test_run_creates_output_dir(config, mock_client_outputs, tmp_path):
    out_dir = str(tmp_path / "new_output_dir")
    cfg = Config(comfyui_host="127.0.0.1", comfyui_port=8188, output_dir=out_dir)
    p = Pipeline(TXT2IMG, config=cfg, auto_provision=False)
    p.start()
    with patch.object(p._client, "run_workflow", return_value=mock_client_outputs):
        p.run()
    assert os.path.isdir(out_dir)


# ---------------------------------------------------------------------------
# run_batch
# ---------------------------------------------------------------------------

def test_run_batch_returns_batch_results(config, mock_client_outputs):
    p = Pipeline(TXT2IMG, config=config, auto_provision=False)
    p.start()
    with patch.object(p._client, "run_workflow", return_value=mock_client_outputs):
        results = p.run_batch([
            {"positive_prompt": "fox", "seed": 1},
            {"positive_prompt": "wolf", "seed": 2},
        ])
    assert len(results) == 2
    assert all(r.success for r in results)


# ---------------------------------------------------------------------------
# auto_provision=False skips RunPod
# ---------------------------------------------------------------------------

def test_no_runpod_when_auto_provision_false(config):
    with patch("comfycode.pipeline.RunPodClient") as mock_rp:
        p = Pipeline(TXT2IMG, config=config, auto_provision=False)
        p.start()
    mock_rp.assert_not_called()


# ---------------------------------------------------------------------------
# on_event callback forwarded to client
# ---------------------------------------------------------------------------

def test_on_event_forwarded(config, mock_client_outputs):
    events = []

    def capture(event_type, data):
        events.append(event_type)

    p = Pipeline(TXT2IMG, config=config, auto_provision=False, on_event=capture)
    p.start()
    assert p._client._on_event is capture
