"""Tests for comfycode.config."""

import os
import pytest
from comfycode.config import Config


def test_defaults():
    """Default values come from fallback strings when env vars are unset."""
    c = Config()
    assert c.comfyui_host == os.environ.get("COMFYUI_HOST", "127.0.0.1")
    assert c.comfyui_port == int(os.environ.get("COMFYUI_PORT", "8188"))
    assert c.comfyui_timeout == int(os.environ.get("COMFYUI_TIMEOUT", "30"))
    assert c.output_dir == os.environ.get("OUTPUT_DIR", "./output")


def test_env_override(monkeypatch):
    """Environment variables are picked up at construction time."""
    monkeypatch.setenv("COMFYUI_HOST", "10.0.0.5")
    monkeypatch.setenv("COMFYUI_PORT", "9000")
    monkeypatch.setenv("RUNPOD_API_KEY", "mykey")
    c = Config()
    assert c.comfyui_host == "10.0.0.5"
    assert c.comfyui_port == 9000
    assert c.runpod_api_key == "mykey"


def test_explicit_override():
    """Explicitly supplied values take precedence over env vars."""
    c = Config(comfyui_host="192.168.1.1", comfyui_port=1234)
    assert c.comfyui_host == "192.168.1.1"
    assert c.comfyui_port == 1234


def test_derived_urls():
    """comfyui_base_url and comfyui_ws_url are derived correctly."""
    c = Config(comfyui_host="1.2.3.4", comfyui_port=8188)
    assert c.comfyui_base_url == "http://1.2.3.4:8188"
    assert c.comfyui_ws_url == "ws://1.2.3.4:8188/ws"
