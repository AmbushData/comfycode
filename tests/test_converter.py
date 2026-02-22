"""Tests for comfycode.converter."""

import json
import pathlib
import textwrap

import pytest

from comfycode.converter import convert, ir_to_python, _to_var_name
from comfycode.ir import prompt_json_to_ir

WORKFLOWS_DIR = pathlib.Path(__file__).parent.parent / "workflows"


class TestToVarName:
    def test_simple_camel(self):
        assert _to_var_name("KSampler") == "k_sampler"

    def test_multiword_camel(self):
        assert _to_var_name("CheckpointLoaderSimple") == "checkpoint_loader_simple"

    def test_all_caps_prefix(self):
        assert _to_var_name("VAEDecode") == "vae_decode"

    def test_all_caps_prefix_encode(self):
        assert _to_var_name("VAEEncode") == "vae_encode"

    def test_single_word(self):
        assert _to_var_name("SaveImage") == "save_image"

    def test_load_image(self):
        assert _to_var_name("LoadImage") == "load_image"


class TestConvert:
    SIMPLE_WORKFLOW = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "model.ckpt"},
        },
        "2": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 512, "height": 512, "batch_size": 1},
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "a cat", "clip": ["1", 1]},
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "ugly", "clip": ["1", 2]},
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 1,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler_ancestral",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["3", 0],
                "negative": ["4", 0],
                "latent_image": ["2", 0],
            },
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["5", 0], "vae": ["1", 2]},
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "out", "images": ["6", 0]},
        },
    }

    def test_output_is_string(self):
        assert isinstance(convert(self.SIMPLE_WORKFLOW), str)

    def test_imports_workflow(self):
        code = convert(self.SIMPLE_WORKFLOW)
        assert "from comfycode import Workflow" in code

    def test_workflow_instantiation(self):
        code = convert(self.SIMPLE_WORKFLOW)
        assert "workflow = Workflow()" in code

    def test_build_call_at_end(self):
        code = convert(self.SIMPLE_WORKFLOW)
        assert "prompt = workflow.build()" in code

    def test_add_node_calls_present(self):
        code = convert(self.SIMPLE_WORKFLOW)
        assert 'workflow.add_node("CheckpointLoaderSimple"' in code
        assert 'workflow.add_node("KSampler"' in code
        assert 'workflow.add_node("SaveImage"' in code

    def test_slot_zero_uses_no_arg_output(self):
        code = convert(self.SIMPLE_WORKFLOW)
        # model=["1", 0] should become model=checkpoint_loader_simple.output()
        assert "model=checkpoint_loader_simple.output()" in code

    def test_slot_nonzero_uses_index_output(self):
        code = convert(self.SIMPLE_WORKFLOW)
        # clip=["1", 1] should become clip=checkpoint_loader_simple.output(1)
        assert "checkpoint_loader_simple.output(1)" in code
        assert "checkpoint_loader_simple.output(2)" in code

    def test_duplicate_class_types_get_numbered_vars(self):
        code = convert(self.SIMPLE_WORKFLOW)
        # Two CLIPTextEncode nodes → clip_text_encode and clip_text_encode_2
        assert "clip_text_encode =" in code
        assert "clip_text_encode_2 =" in code

    def test_accepts_json_string(self):
        json_str = json.dumps(self.SIMPLE_WORKFLOW)
        code = convert(json_str)
        assert "workflow.add_node" in code

    def test_no_inputs_node(self):
        workflow = {"1": {"class_type": "EmptyNode", "inputs": {}}}
        code = convert(workflow)
        assert 'workflow.add_node("EmptyNode")' in code

    def test_nodes_in_sorted_id_order(self):
        code = convert(self.SIMPLE_WORKFLOW)
        idx_ckpt = code.index("CheckpointLoaderSimple")
        idx_save = code.index("SaveImage")
        assert idx_ckpt < idx_save

    def test_generated_code_is_executable(self):
        """The generated code should run without errors."""
        code = convert(self.SIMPLE_WORKFLOW)
        namespace: dict = {}
        exec(compile(code, "<string>", "exec"), namespace)  # noqa: S102
        prompt = namespace["prompt"]
        assert isinstance(prompt, dict)
        assert len(prompt) == len(self.SIMPLE_WORKFLOW)

    def test_generated_code_produces_equivalent_workflow(self):
        """Executing the generated code reproduces the original workflow structure."""
        code = convert(self.SIMPLE_WORKFLOW)
        namespace: dict = {}
        exec(compile(code, "<string>", "exec"), namespace)  # noqa: S102
        prompt = namespace["prompt"]

        # Check class types match
        original_class_types = {v["class_type"] for v in self.SIMPLE_WORKFLOW.values()}
        generated_class_types = {v["class_type"] for v in prompt.values()}
        assert original_class_types == generated_class_types

        # Node 5 in generated code should still reference the checkpoint for 'model'
        ksampler = next(v for v in prompt.values() if v["class_type"] == "KSampler")
        ckpt_id = next(
            nid for nid, v in prompt.items() if v["class_type"] == "CheckpointLoaderSimple"
        )
        assert ksampler["inputs"]["model"] == [ckpt_id, 0]


class TestConvertExampleWorkflows:
    """Smoke-test the bundled example workflow files."""

    @pytest.mark.parametrize("filename", ["txt2img.json", "img2img.json"])
    def test_workflow_file_is_valid_json(self, filename):
        path = WORKFLOWS_DIR / filename
        assert path.exists(), f"Missing workflow file: {path}"
        with open(path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    @pytest.mark.parametrize("filename", ["txt2img.json", "img2img.json"])
    def test_workflow_converts_without_error(self, filename):
        path = WORKFLOWS_DIR / filename
        with open(path) as f:
            data = json.load(f)
        code = convert(data)
        assert "workflow.build()" in code

    @pytest.mark.parametrize("filename", ["txt2img.json", "img2img.json"])
    def test_workflow_generated_code_is_executable(self, filename):
        path = WORKFLOWS_DIR / filename
        with open(path) as f:
            data = json.load(f)
        code = convert(data)
        namespace: dict = {}
        exec(compile(code, "<string>", "exec"), namespace)  # noqa: S102
        assert isinstance(namespace["prompt"], dict)


class TestIRToPython:
    """Tests for the IR-based Python code generation."""

    SIMPLE_WORKFLOW = {
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

    def test_ir_to_python_produces_valid_code(self):
        """IR-based conversion produces executable Python code."""
        ir = prompt_json_to_ir(self.SIMPLE_WORKFLOW)
        code = ir_to_python(ir)
        namespace: dict = {}
        exec(compile(code, "<string>", "exec"), namespace)  # noqa: S102
        assert isinstance(namespace["prompt"], dict)

    def test_ir_to_python_equivalent_to_convert(self):
        """IR-based conversion produces functionally equivalent output to direct convert."""
        # Direct conversion
        direct_code = convert(self.SIMPLE_WORKFLOW)
        direct_ns: dict = {}
        exec(compile(direct_code, "<string>", "exec"), direct_ns)  # noqa: S102
        direct_prompt = direct_ns["prompt"]

        # IR-based conversion
        ir = prompt_json_to_ir(self.SIMPLE_WORKFLOW)
        ir_code = ir_to_python(ir)
        ir_ns: dict = {}
        exec(compile(ir_code, "<string>", "exec"), ir_ns)  # noqa: S102
        ir_prompt = ir_ns["prompt"]

        # Should have same class types
        direct_types = {v["class_type"] for v in direct_prompt.values()}
        ir_types = {v["class_type"] for v in ir_prompt.values()}
        assert direct_types == ir_types

    def test_ir_to_python_includes_workflow_import(self):
        """Generated code imports Workflow class."""
        ir = prompt_json_to_ir(self.SIMPLE_WORKFLOW)
        code = ir_to_python(ir)
        assert "from comfycode import Workflow" in code

    def test_ir_to_python_calls_build(self):
        """Generated code calls workflow.build()."""
        ir = prompt_json_to_ir(self.SIMPLE_WORKFLOW)
        code = ir_to_python(ir)
        assert "workflow.build()" in code

