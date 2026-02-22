"""Inventory documentation generator."""

from __future__ import annotations

from pathlib import Path
from typing import List, Union

from .loader import RegistryLoader


class InventoryGenerator:
    """Generates deterministic inventory documentation from registry entries."""
    
    def __init__(self, registry_path: Union[str, Path]):
        """Initialize the inventory generator.
        
        Args:
            registry_path: Path to the registry root directory.
        """
        self.registry_path = Path(registry_path)
        self.loader = RegistryLoader(registry_path)
    
    def generate(self) -> str:
        """Generate inventory markdown content.
        
        Returns:
            Markdown-formatted inventory documentation.
        """
        lines = []
        lines.append("# Asset Inventory")
        lines.append("")
        lines.append("*Auto-generated from registry entries. Do not edit manually.*")
        lines.append("")
        
        # Characters section
        lines.extend(self._generate_characters_section())
        lines.append("")
        
        # Models section
        lines.extend(self._generate_models_section())
        lines.append("")
        
        # LoRAs section
        lines.extend(self._generate_loras_section())
        lines.append("")
        
        # Clothing section
        lines.extend(self._generate_clothing_section())
        lines.append("")
        
        # Datasets section
        lines.extend(self._generate_datasets_section())
        
        return "\n".join(lines)
    
    def _generate_characters_section(self) -> List[str]:
        """Generate the characters section."""
        lines = ["## Characters", ""]
        
        characters = self.loader.load_all("characters")
        if not characters:
            lines.append("*No entries*")
            return lines
        
        lines.append("| ID | Name | Version | NSFW Rating |")
        lines.append("|-----|------|---------|-------------|")
        
        for char in characters:
            char_id = char.get("id", "")
            name = char.get("name", "")
            version = char.get("version", "")
            nsfw = char.get("nsfw", char.get("nsfw_rating", ""))
            lines.append(f"| {char_id} | {name} | {version} | {nsfw} |")
        
        return lines
    
    def _generate_models_section(self) -> List[str]:
        """Generate the models section."""
        lines = ["## Models", ""]
        
        models = self.loader.load_all("models")
        if not models:
            lines.append("*No entries*")
            return lines
        
        lines.append("| ID | Name | Type | Version |")
        lines.append("|-----|------|------|---------|")
        
        for model in models:
            model_id = model.get("id", "")
            name = model.get("name", "")
            model_type = model.get("model_type", "")
            version = model.get("version", "")
            lines.append(f"| {model_id} | {name} | {model_type} | {version} |")
        
        return lines
    
    def _generate_loras_section(self) -> List[str]:
        """Generate the LoRAs section."""
        lines = ["## LoRAs", ""]
        
        loras = self.loader.load_all("loras")
        if not loras:
            lines.append("*No entries*")
            return lines
        
        lines.append("| ID | Name | Type | Base Model | Version |")
        lines.append("|-----|------|------|------------|---------|")
        
        for lora in loras:
            lora_id = lora.get("id", "")
            name = lora.get("name", "")
            lora_type = lora.get("lora_type", "")
            base_model = lora.get("base_model", "")
            version = lora.get("version", "")
            lines.append(
                f"| {lora_id} | {name} | {lora_type} | {base_model} | {version} |"
            )
        
        return lines
    
    def _generate_clothing_section(self) -> List[str]:
        """Generate the clothing section."""
        lines = ["## Clothing", ""]
        
        clothing = self.loader.load_all("clothing")
        if not clothing:
            lines.append("*No entries*")
            return lines
        
        lines.append("| ID | Name | Category | Version |")
        lines.append("|-----|------|----------|---------|")
        
        for item in clothing:
            item_id = item.get("id", "")
            name = item.get("name", "")
            category = item.get("category", "")
            version = item.get("version", "")
            lines.append(f"| {item_id} | {name} | {category} | {version} |")
        
        return lines
    
    def _generate_datasets_section(self) -> List[str]:
        """Generate the datasets section."""
        lines = ["## Datasets", ""]
        
        datasets = self.loader.load_all("datasets")
        if not datasets:
            lines.append("*No entries*")
            return lines
        
        lines.append("| ID | Name | Purpose | Image Count | Version |")
        lines.append("|-----|------|---------|-------------|---------|")
        
        for ds in datasets:
            ds_id = ds.get("id", "")
            name = ds.get("name", "")
            purpose = ds.get("purpose", "")
            image_count = ds.get("image_count", "")
            version = ds.get("version", "")
            lines.append(
                f"| {ds_id} | {name} | {purpose} | {image_count} | {version} |"
            )
        
        return lines
    
    def write(self, output_path: Union[str, Path]) -> None:
        """Write inventory to a file.
        
        Args:
            output_path: Path to write the inventory markdown.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = self.generate()
        output_path.write_text(content, encoding="utf-8")
