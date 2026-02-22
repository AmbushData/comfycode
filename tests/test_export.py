"""Tests for comfycode.export — execution-based Python→JSON export."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

from comfycode.export import (
    export_prompt_json,
    export_from_module,
    ExportError,
    ENTRYPOINT_FUNCTION,
)


class TestExportConstants:
    """Tests for export module constants."""

    def test_entrypoint_function_defined(self):
        """The entrypoint function name is documented."""
        assert isinstance(ENTRYPOINT_FUNCTION, str)
        assert ENTRYPOINT_FUNCTION == "create_workflow"


class TestExportPromptJSON:
    """Tests for the export_prompt_json function."""

    def test_exports_workflow_to_dict(self):
        """Can export a Workflow instance to a prompt dict."""
        from comfycode import Workflow

        wf = Workflow()
        wf.add_node("CheckpointLoaderSimple", ckpt_name="model.ckpt")
        
        result = export_prompt_json(wf)
        
        assert isinstance(result, dict)
        assert len(result) == 1
        node = list(result.values())[0]
        assert node["class_type"] == "CheckpointLoaderSimple"

    def test_exports_dict_passthrough(self):
        """If given a prompt dict, returns it unchanged."""
        prompt = {"1": {"class_type": "Test", "inputs": {}}}
        
        result = export_prompt_json(prompt)
        
        assert result == prompt

    def test_rejects_invalid_input(self):
        """Raises ExportError for invalid input types."""
        with pytest.raises(ExportError) as exc_info:
            export_prompt_json("not a workflow or dict")
        
        assert "Workflow" in str(exc_info.value) or "dict" in str(exc_info.value)


class TestExportFromModule:
    """Tests for the export_from_module function."""

    def test_loads_and_exports_module_with_entrypoint(self):
        """Can load a Python module and export its workflow."""
        # Create a temporary module file
        module_code = '''
from comfycode import Workflow

def create_workflow():
    wf = Workflow()
    wf.add_node("CheckpointLoaderSimple", ckpt_name="test.ckpt")
    return wf
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(module_code)
            module_path = f.name

        try:
            result = export_from_module(module_path)
            
            assert isinstance(result, dict)
            assert len(result) == 1
            node = list(result.values())[0]
            assert node["class_type"] == "CheckpointLoaderSimple"
        finally:
            os.unlink(module_path)

    def test_fails_if_no_entrypoint(self):
        """Raises ExportError if module has no create_workflow function."""
        module_code = '''
# Module without create_workflow
x = 42
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(module_code)
            module_path = f.name

        try:
            with pytest.raises(ExportError) as exc_info:
                export_from_module(module_path)
            
            assert "create_workflow" in str(exc_info.value)
        finally:
            os.unlink(module_path)

    def test_fails_if_entrypoint_returns_wrong_type(self):
        """Raises ExportError if create_workflow returns unexpected type."""
        module_code = '''
def create_workflow():
    return "not a workflow"
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(module_code)
            module_path = f.name

        try:
            with pytest.raises(ExportError) as exc_info:
                export_from_module(module_path)
            
            assert "Workflow" in str(exc_info.value) or "dict" in str(exc_info.value)
        finally:
            os.unlink(module_path)

    def test_handles_module_import_error(self):
        """Raises ExportError with context if module fails to import."""
        module_code = '''
import nonexistent_module_xyz123
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(module_code)
            module_path = f.name

        try:
            with pytest.raises(ExportError) as exc_info:
                export_from_module(module_path)
            
            assert "import" in str(exc_info.value).lower() or "module" in str(exc_info.value).lower()
        finally:
            os.unlink(module_path)

    def test_handles_entrypoint_execution_error(self):
        """Raises ExportError with context if create_workflow raises."""
        module_code = '''
def create_workflow():
    raise ValueError("Something went wrong")
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(module_code)
            module_path = f.name

        try:
            with pytest.raises(ExportError) as exc_info:
                export_from_module(module_path)
            
            assert "Something went wrong" in str(exc_info.value)
        finally:
            os.unlink(module_path)

    def test_supports_entrypoint_returning_dict(self):
        """Entrypoint can return a prompt dict directly."""
        module_code = '''
def create_workflow():
    return {"1": {"class_type": "Test", "inputs": {"value": 42}}}
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(module_code)
            module_path = f.name

        try:
            result = export_from_module(module_path)
            
            assert result == {"1": {"class_type": "Test", "inputs": {"value": 42}}}
        finally:
            os.unlink(module_path)


class TestExportError:
    """Tests for the ExportError exception."""

    def test_export_error_is_exception(self):
        """ExportError is a proper exception class."""
        assert issubclass(ExportError, Exception)

    def test_export_error_message(self):
        """ExportError captures error message."""
        error = ExportError("test message")
        assert str(error) == "test message"


class TestExportCLI:
    """Tests for the CLI export command."""

    def test_cli_export_produces_json(self):
        """CLI export command produces valid JSON output."""
        import subprocess

        module_code = '''
from comfycode import Workflow

def create_workflow():
    wf = Workflow()
    wf.add_node("CheckpointLoaderSimple", ckpt_name="test.ckpt")
    return wf
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(module_code)
            module_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "comfycode", "export", module_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )
            
            assert result.returncode == 0, f"stderr: {result.stderr}"
            output = json.loads(result.stdout)
            assert isinstance(output, dict)
            assert len(output) == 1
        finally:
            os.unlink(module_path)

    def test_cli_export_to_file(self):
        """CLI export can write to output file."""
        import subprocess

        module_code = '''
from comfycode import Workflow

def create_workflow():
    wf = Workflow()
    wf.add_node("Test", value=42)
    return wf
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(module_code)
            module_path = f.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as out_f:
            output_path = out_f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "comfycode", "export", module_path, "-o", output_path],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )
            
            assert result.returncode == 0, f"stderr: {result.stderr}"
            
            with open(output_path) as f:
                output = json.load(f)
            
            assert isinstance(output, dict)
            assert len(output) == 1
        finally:
            os.unlink(module_path)
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_cli_export_ui_json(self):
        """CLI export with --ui flag produces UI JSON format."""
        import subprocess

        module_code = '''
from comfycode import Workflow

def create_workflow():
    wf = Workflow()
    checkpoint = wf.add_node("CheckpointLoaderSimple", ckpt_name="test.ckpt")
    wf.add_node("KSampler", model=checkpoint.output(0))
    return wf
'''
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as f:
            f.write(module_code)
            module_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, "-m", "comfycode", "export", module_path, "--ui"],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent,
            )
            
            assert result.returncode == 0, f"stderr: {result.stderr}"
            output = json.loads(result.stdout)
            
            # UI JSON structure checks
            assert "nodes" in output
            assert "links" in output
            assert "version" in output
            assert "last_node_id" in output
            assert "last_link_id" in output
            
            # Should have 2 nodes
            assert len(output["nodes"]) == 2
            
            # Nodes should have positions
            for node in output["nodes"]:
                assert "pos" in node
                assert "type" in node
        finally:
            os.unlink(module_path)
