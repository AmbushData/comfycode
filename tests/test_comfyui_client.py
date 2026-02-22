"""Tests for comfycode.comfyui_client."""

import json
import threading
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from comfycode.config import Config
from comfycode.comfyui_client import ComfyUIClient, ComfyUIError


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def config():
    return Config(comfyui_host="127.0.0.1", comfyui_port=8188)


@pytest.fixture()
def client(config):
    return ComfyUIClient(config)


@pytest.fixture()
def simple_workflow():
    return {
        "1": {
            "class_type": "KSampler",
            "inputs": {"seed": 0, "steps": 20},
        }
    }


# ---------------------------------------------------------------------------
# _queue_prompt
# ---------------------------------------------------------------------------

def test_queue_prompt_returns_id(client, simple_workflow):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"prompt_id": "abc-123"}
    mock_resp.raise_for_status = MagicMock()
    with patch.object(client._session, "post", return_value=mock_resp) as mock_post:
        prompt_id = client._queue_prompt(simple_workflow)
    assert prompt_id == "abc-123"
    args, kwargs = mock_post.call_args
    assert "/prompt" in args[0]
    assert kwargs["json"]["prompt"] == simple_workflow
    assert kwargs["json"]["client_id"] == client._client_id


# ---------------------------------------------------------------------------
# get_queue / get_history / interrupt
# ---------------------------------------------------------------------------

def test_get_queue(client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"queue_running": [], "queue_pending": []}
    mock_resp.raise_for_status = MagicMock()
    with patch.object(client._session, "get", return_value=mock_resp):
        result = client.get_queue()
    assert "queue_running" in result


def test_get_history(client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"abc": {"status": {"completed": True}, "outputs": {}}}
    mock_resp.raise_for_status = MagicMock()
    with patch.object(client._session, "get", return_value=mock_resp):
        result = client.get_history("abc")
    assert "abc" in result


def test_interrupt(client):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()
    with patch.object(client._session, "post", return_value=mock_resp):
        client.interrupt()  # should not raise


# ---------------------------------------------------------------------------
# _run_with_polling
# ---------------------------------------------------------------------------

def test_run_with_polling_success(client, simple_workflow):
    history = {
        "pid-1": {
            "status": {"completed": True, "status_str": "success"},
            "outputs": {
                "7": {"images": [{"filename": "out.png", "subfolder": "", "type": "output"}]}
            },
        }
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = history
    mock_resp.raise_for_status = MagicMock()
    with patch.object(client._session, "get", return_value=mock_resp):
        outputs = client._run_with_polling("pid-1")
    assert len(outputs) == 1
    assert outputs[0]["node_id"] == "7"
    assert outputs[0]["type"] == "images"


def test_run_with_polling_error(client):
    history = {
        "pid-err": {
            "status": {"completed": False, "status_str": "error", "messages": ["oh no"]},
            "outputs": {},
        }
    }
    mock_resp = MagicMock()
    mock_resp.json.return_value = history
    mock_resp.raise_for_status = MagicMock()
    with patch.object(client._session, "get", return_value=mock_resp):
        with pytest.raises(ComfyUIError, match="failed"):
            client._run_with_polling("pid-err")


# ---------------------------------------------------------------------------
# run_workflow delegates correctly
# ---------------------------------------------------------------------------

def test_run_workflow_uses_polling_when_flag_false(client, simple_workflow):
    with patch.object(client, "_queue_prompt", return_value="pid-x") as mock_q, \
         patch.object(client, "_run_with_polling", return_value=[]) as mock_poll:
        outputs = client.run_workflow(simple_workflow, use_websocket=False)
    mock_q.assert_called_once_with(simple_workflow)
    mock_poll.assert_called_once_with("pid-x")
    assert outputs == []


def test_run_workflow_uses_websocket_by_default(client, simple_workflow):
    with patch.object(client, "_queue_prompt", return_value="pid-y"), \
         patch.object(client, "_run_with_websocket", return_value=[{"node_id": "7"}]) as mock_ws:
        outputs = client.run_workflow(simple_workflow)
    mock_ws.assert_called_once_with("pid-y")
    assert outputs[0]["node_id"] == "7"


# ---------------------------------------------------------------------------
# Event callback
# ---------------------------------------------------------------------------

def test_on_event_callback_invoked(config, simple_workflow):
    events = []

    def capture(event_type, data):
        events.append((event_type, data))

    c = ComfyUIClient(config, on_event=capture)

    # Simulate the WebSocket path by directly calling _log_event + callback.
    c._on_event("progress", {"value": 5, "max": 20})
    assert ("progress", {"value": 5, "max": 20}) in events
