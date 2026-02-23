"""
LoRA Registry and Selector for AI Influencer Automation

Supports metadata-driven LoRA catalog, prompt→LoRA mapping, and multi-LoRA stacking.
"""

from typing import List, Dict, Optional
import json
from pydantic import BaseModel, ValidationError, Field

class LoRAMetadata(BaseModel):
    tags: List[str] = Field(default_factory=list, description="Tags describing LoRA")
    path: str = Field(..., description="Path to LoRA weights file")

class LoRARegistry:
    def __init__(self, registry_path: str):
        self.registry_path = registry_path
        self.lora_catalog = self._load_registry()

    def _load_registry(self) -> Dict[str, Dict]:
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                raw_catalog = json.load(f)
        except FileNotFoundError:
            return {}
        validated_catalog = {}
        for influencer_id, loras in raw_catalog.items():
            validated_catalog[influencer_id] = {}
            for lora_id, meta in loras.items():
                try:
                    validated_catalog[influencer_id][lora_id] = LoRAMetadata(**meta)
                except ValidationError as e:
                    print(f"Invalid LoRA metadata for {influencer_id}/{lora_id}: {e}")
        return validated_catalog

    def lookup_lora(self, influencer_id: str, prompt: str) -> List[str]:
        influencer_loras = self.lora_catalog.get(influencer_id, {})
        selected = []
        for lora_id, meta in influencer_loras.items():
            if not isinstance(meta, LoRAMetadata):
                continue
            tags = meta.tags
            if any(tag in prompt for tag in tags):
                selected.append(lora_id)
        return selected

    def multi_lora_stack(self, influencer_id: str, prompt: str) -> List[str]:
        return self.lookup_lora(influencer_id, prompt)

    def add_lora(self, influencer_id: str, lora_id: str, meta: Dict):
        try:
            validated_meta = LoRAMetadata(**meta)
        except ValidationError as e:
            print(f"Invalid LoRA metadata for {influencer_id}/{lora_id}: {e}")
            return
        if influencer_id not in self.lora_catalog:
            self.lora_catalog[influencer_id] = {}
        self.lora_catalog[influencer_id][lora_id] = validated_meta
        self._save_registry()

    def _save_registry(self):
        # Convert Pydantic models to dict for JSON serialization
        serializable_catalog = {}
        for influencer_id, loras in self.lora_catalog.items():
            serializable_catalog[influencer_id] = {}
            for lora_id, meta in loras.items():
                if isinstance(meta, LoRAMetadata):
                    serializable_catalog[influencer_id][lora_id] = meta.dict()
                else:
                    serializable_catalog[influencer_id][lora_id] = meta
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_catalog, f, indent=2)

class LoRARegistry:
    def __init__(self, registry_path: str):
        self.registry_path = registry_path
        self.lora_catalog = self._load_registry()

    def _load_registry(self) -> Dict[str, Dict]:
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def lookup_lora(self, influencer_id: str, prompt: str) -> List[str]:
        influencer_loras = self.lora_catalog.get(influencer_id, {})
        # Simple mapping: select LoRAs whose tags match prompt keywords
        selected = []
        for lora_id, meta in influencer_loras.items():
            tags = meta.get('tags', [])
            if any(tag in prompt for tag in tags):
                selected.append(lora_id)
        return selected

    def multi_lora_stack(self, influencer_id: str, prompt: str) -> List[str]:
        # For now, same as lookup_lora; extend for more complex stacking
        return self.lookup_lora(influencer_id, prompt)

    def add_lora(self, influencer_id: str, lora_id: str, meta: Dict):
        if influencer_id not in self.lora_catalog:
            self.lora_catalog[influencer_id] = {}
        self.lora_catalog[influencer_id][lora_id] = meta
        self._save_registry()

    def _save_registry(self):
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.lora_catalog, f, indent=2)

# Example registry structure (to be replaced with real metadata)
example_catalog = {
    'influencer1': {
        'lora1': {'tags': ['lingerie', 'bedroom'], 'path': 'loras/influencer1/lora1.safetensors'},
        'lora2': {'tags': ['smile', 'mirror'], 'path': 'loras/influencer1/lora2.safetensors'},
    },
    'influencer2': {
        'lora3': {'tags': ['outdoor', 'sunlight'], 'path': 'loras/influencer2/lora3.safetensors'},
    }
}

if __name__ == '__main__':
    # Save example catalog for testing
    with open('lora_registry.json', 'w', encoding='utf-8') as f:
        json.dump(example_catalog, f, indent=2)
    registry = LoRARegistry('lora_registry.json')
    print(registry.lookup_lora('influencer1', 'mirror selfie lingerie'))
    print(registry.multi_lora_stack('influencer1', 'bedroom smile'))
