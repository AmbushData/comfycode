"""Tests for registry module and inventory generator."""

import json
import os
import tempfile
from pathlib import Path
from unittest import TestCase

from pydantic import ValidationError as PydanticValidationError


class TestInventoryGenerator(TestCase):
    """Tests for deterministic inventory.md generation."""

    def setUp(self):
        """Create temporary registry structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = Path(self.temp_dir) / "registry"
        self.registry_path.mkdir()
        
        # Create subdirectories
        for subdir in ["characters", "clothing", "models", "loras", "datasets"]:
            (self.registry_path / subdir).mkdir()
        
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def _create_character(self, char_id: str, name: str, version: str = "1.0.0"):
        """Helper to create a test character entry."""
        char_data = {
            "id": char_id,
            "version": version,
            "name": name,
            "identity": {
                "full_name": name,
                "age": 25,
                "nationality": "American"
            },
            "appearance": {
                "hair_color": "brown",
                "eye_color": "blue",
                "body_type": "athletic"
            },
            "nsfw_rating": "sfw"
        }
        char_file = self.registry_path / "characters" / f"{char_id}.json"
        char_file.write_text(json.dumps(char_data, indent=2))
        return char_file
    
    def _create_model(self, model_id: str, name: str, model_type: str = "sdxl"):
        """Helper to create a test model entry."""
        model_data = {
            "id": model_id,
            "version": "1.0.0",
            "name": name,
            "model_type": model_type,
            "blob_ref": {
                "container": "assets",
                "path": f"models/{model_id}/{model_id}-1.0.0.safetensors"
            }
        }
        model_file = self.registry_path / "models" / f"{model_id}.json"
        model_file.write_text(json.dumps(model_data, indent=2))
        return model_file
    
    def _create_lora(self, lora_id: str, name: str, lora_type: str = "character"):
        """Helper to create a test lora entry."""
        lora_data = {
            "id": lora_id,
            "version": "1.0.0",
            "name": name,
            "base_model": "sdxl",
            "lora_type": lora_type,
            "trigger_words": ["trigger1"],
            "blob_ref": {
                "container": "assets",
                "path": f"loras/{lora_id}/{lora_id}-1.0.0.safetensors"
            }
        }
        lora_file = self.registry_path / "loras" / f"{lora_id}.json"
        lora_file.write_text(json.dumps(lora_data, indent=2))
        return lora_file
    
    def test_generate_inventory_empty_registry(self):
        """Test inventory generation with empty registry."""
        from comfycode.registry import InventoryGenerator
        
        generator = InventoryGenerator(self.registry_path)
        output = generator.generate()
        
        # Should produce valid markdown with headers but no entries
        self.assertIn("# Asset Inventory", output)
        self.assertIn("## Characters", output)
        self.assertIn("## Models", output)
        self.assertIn("## LoRAs", output)
        self.assertIn("*No entries*", output)
    
    def test_generate_inventory_with_characters(self):
        """Test inventory includes character entries."""
        from comfycode.registry import InventoryGenerator
        
        self._create_character("aria-v1", "Aria Test")
        self._create_character("bella-v1", "Bella Test")
        
        generator = InventoryGenerator(self.registry_path)
        output = generator.generate()
        
        self.assertIn("aria-v1", output)
        self.assertIn("Aria Test", output)
        self.assertIn("bella-v1", output)
        self.assertIn("Bella Test", output)
    
    def test_generate_inventory_deterministic_order(self):
        """Test inventory generation is deterministic (sorted)."""
        from comfycode.registry import InventoryGenerator
        
        # Create in reverse alphabetical order
        self._create_character("zara-v1", "Zara Test")
        self._create_character("aria-v1", "Aria Test")
        self._create_character("maya-v1", "Maya Test")
        
        generator = InventoryGenerator(self.registry_path)
        output1 = generator.generate()
        output2 = generator.generate()
        
        # Must be identical
        self.assertEqual(output1, output2)
        
        # Must be in alphabetical order
        aria_pos = output1.find("aria-v1")
        maya_pos = output1.find("maya-v1")
        zara_pos = output1.find("zara-v1")
        
        self.assertLess(aria_pos, maya_pos)
        self.assertLess(maya_pos, zara_pos)
    
    def test_generate_inventory_with_models(self):
        """Test inventory includes model entries."""
        from comfycode.registry import InventoryGenerator
        
        self._create_model("sd-xl-base", "Stable Diffusion XL Base", "sdxl")
        self._create_model("realistic-vision", "Realistic Vision", "sd15")
        
        generator = InventoryGenerator(self.registry_path)
        output = generator.generate()
        
        self.assertIn("sd-xl-base", output)
        self.assertIn("sdxl", output)
        self.assertIn("realistic-vision", output)
        self.assertIn("sd15", output)
    
    def test_generate_inventory_with_loras(self):
        """Test inventory includes lora entries."""
        from comfycode.registry import InventoryGenerator
        
        self._create_lora("aria-face-v1", "Aria Face LoRA", "character")
        
        generator = InventoryGenerator(self.registry_path)
        output = generator.generate()
        
        self.assertIn("aria-face-v1", output)
        self.assertIn("character", output)
    
    def test_generate_inventory_writes_to_file(self):
        """Test inventory can be written to file."""
        from comfycode.registry import InventoryGenerator
        
        self._create_character("test-char", "Test Character")
        
        generator = InventoryGenerator(self.registry_path)
        output_path = Path(self.temp_dir) / "inventory.md"
        
        generator.write(output_path)
        
        self.assertTrue(output_path.exists())
        content = output_path.read_text()
        self.assertIn("test-char", content)


class TestRegistryLoader(TestCase):
    """Tests for registry entry loading and validation."""

    def setUp(self):
        """Create temporary registry structure for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry_path = Path(self.temp_dir) / "registry"
        self.registry_path.mkdir()
        
        for subdir in ["characters", "clothing", "models", "loras", "datasets"]:
            (self.registry_path / subdir).mkdir()
    
    def tearDown(self):
        """Clean up temporary directory."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_character(self):
        """Test loading a character entry."""
        from comfycode.registry import RegistryLoader
        
        char_data = {
            "id": "test-char",
            "version": "1.0.0",
            "name": "Test Character",
            "identity": {"full_name": "Test Character"},
            "appearance": {"hair_color": "brown"},
            "created_at": "2025-01-01T00:00:00Z"
        }
        char_file = self.registry_path / "characters" / "test-char.json"
        char_file.write_text(json.dumps(char_data))
        
        loader = RegistryLoader(self.registry_path)
        character = loader.load_character("test-char")
        
        self.assertEqual(character.id, "test-char")
        self.assertEqual(character.name, "Test Character")
    
    def test_load_all_characters(self):
        """Test loading all character entries."""
        from comfycode.registry import RegistryLoader
        
        for i in range(3):
            char_data = {
                "id": f"char-{i}",
                "version": "1.0.0",
                "name": f"Character {i}",
                "identity": {"full_name": f"Character {i}"},
                "appearance": {"hair_color": "brown"},
                "nsfw_rating": "sfw"
            }
            char_file = self.registry_path / "characters" / f"char-{i}.json"
            char_file.write_text(json.dumps(char_data))
        
        loader = RegistryLoader(self.registry_path)
        characters = loader.load_all("characters")
        
        self.assertEqual(len(characters), 3)
    
    def test_load_model(self):
        """Test loading a model entry."""
        from comfycode.registry import RegistryLoader
        
        model_data = {
            "id": "test-model",
            "version": "1.0.0",
            "name": "Test Model",
            "model_type": "sdxl",
            "blob_ref": {
                "container": "assets",
                "path": "models/test-model/test-model-1.0.0.safetensors"
            },
            "created_at": "2025-01-01T00:00:00Z"
        }
        model_file = self.registry_path / "models" / "test-model.json"
        model_file.write_text(json.dumps(model_data))
        
        loader = RegistryLoader(self.registry_path)
        model = loader.load_model("test-model")
        
        self.assertEqual(model.id, "test-model")
        self.assertEqual(model.model_type.value, "sdxl")
    
    def test_load_nonexistent_raises(self):
        """Test loading nonexistent entry raises error."""
        from comfycode.registry import RegistryLoader, RegistryEntryNotFound
        
        loader = RegistryLoader(self.registry_path)
        
        with self.assertRaises(RegistryEntryNotFound):
            loader.load_character("nonexistent")


class TestSchemaValidation(TestCase):
    """Tests for JSON schema validation of registry entries."""

    def test_validate_character_valid(self):
        """Test validation passes for valid character."""
        from comfycode.registry import validate_entry
        
        char_data = {
            "id": "test-char",
            "version": "1.0.0",
            "name": "Test Character",
            "description": "A test character for validation",
            "identity": {
                "persona": "Friendly test persona"
            },
            "appearance": {
                "hair_color": "brown",
                "eye_color": "blue"
            },
            "created_at": "2025-01-01T00:00:00Z"
        }
        
        # Should not raise
        is_valid = validate_entry(char_data, "character")
        self.assertTrue(is_valid)
    
    def test_validate_character_missing_required(self):
        """Test validation fails for missing required fields."""
        from comfycode.registry import validate_entry, ValidationError
        
        char_data = {
            "id": "test-char",
            # Missing required fields: version, name, identity, appearance, nsfw_rating
        }
        
        with self.assertRaises(ValidationError):
            validate_entry(char_data, "character")
    
    def test_validate_model_valid(self):
        """Test validation passes for valid model."""
        from comfycode.registry import validate_entry
        
        model_data = {
            "id": "test-model",
            "version": "1.0.0",
            "name": "Test Model",
            "model_type": "sdxl",
            "blob_ref": {
                "container": "assets",
                "path": "models/test-model/test-model-1.0.0.safetensors"
            },
            "created_at": "2025-01-01T00:00:00Z"
        }
        
        is_valid = validate_entry(model_data, "model")
        self.assertTrue(is_valid)
    
    def test_validate_model_invalid_type(self):
        """Test validation fails for invalid model type."""
        from comfycode.registry import validate_entry, ValidationError
        
        model_data = {
            "id": "test-model",
            "version": "1.0.0",
            "name": "Test Model",
            "model_type": "invalid_type",  # Not in enum
            "blob_ref": {
                "container": "assets",
                "path": "models/test-model/test-model-1.0.0.safetensors"
            },
            "created_at": "2025-01-01T00:00:00Z"
        }
        
        with self.assertRaises(ValidationError):
            validate_entry(model_data, "model")
