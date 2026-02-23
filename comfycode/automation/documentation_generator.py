"""
Documentation Generator for AI Influencer Automation

Generates inventory docs from registry, workflow, and artifact manifests.
"""
from comfycode.automation.lora_registry import LoRARegistry
from comfycode.automation.clothing_catalog import ClothingCatalog
from comfycode.automation.prompt_generator import PromptGenerator
import json

class DocumentationGenerator:
    def __init__(self, lora_registry: LoRARegistry, clothing_catalog: ClothingCatalog, prompt_generator: PromptGenerator):
        self.lora_registry = lora_registry
        self.clothing_catalog = clothing_catalog
        self.prompt_generator = prompt_generator

    def generate_inventory_doc(self, output_path: str):
        doc = {}
        doc['loras'] = self.lora_registry.lora_catalog
        doc['clothing'] = self.clothing_catalog.clothing_catalog
        doc['personas'] = self.prompt_generator.persona_library
        doc['scenarios'] = self.prompt_generator.scenario_library
        doc['explicitness_levels'] = self.prompt_generator.explicitness_levels
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2)

# Example usage
if __name__ == '__main__':
    lora_reg = LoRARegistry('lora_registry.json')
    clothing_cat = ClothingCatalog('clothing_catalog.json')
    from comfycode.automation.prompt_generator import persona_library, scenario_library, explicitness_levels
    prompt_gen = PromptGenerator(persona_library, scenario_library, explicitness_levels)
    doc_gen = DocumentationGenerator(lora_reg, clothing_cat, prompt_gen)
    doc_gen.generate_inventory_doc('inventory_doc.json')
