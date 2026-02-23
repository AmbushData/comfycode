"""
Batch Workflow Orchestrator for AI Influencer Automation

Executes influencer × clothing × prompt grid, tracks provenance, and routes outputs.
"""
from typing import List, Dict
from comfycode.automation.prompt_generator import PromptGenerator
from comfycode.automation.lora_registry import LoRARegistry
from comfycode.automation.clothing_catalog import ClothingCatalog
import json

class BatchWorkflowOrchestrator:
    def __init__(self, prompt_generator: PromptGenerator, lora_registry: LoRARegistry, clothing_catalog: ClothingCatalog):
        self.prompt_generator = prompt_generator
        self.lora_registry = lora_registry
        self.clothing_catalog = clothing_catalog

    def run_grid(self, influencer_ids: List[str], n_prompts: int = 5, n_clothing: int = 3) -> Dict[str, List[Dict]]:
        results = {}
        for influencer_id in influencer_ids:
            prompts = self.prompt_generator.batch_generate([influencer_id], n_per_influencer=n_prompts)[influencer_id]
            clothing_items = self.clothing_catalog.batch_select(influencer_id, n_items=n_clothing)
            influencer_results = []
            for prompt in prompts:
                loras = self.lora_registry.multi_lora_stack(influencer_id, prompt)
                for clothing in clothing_items:
                    influencer_results.append({
                        'influencer_id': influencer_id,
                        'prompt': prompt,
                        'loras': loras,
                        'clothing': clothing,
                        'provenance': {
                            'prompt_source': 'PromptGenerator',
                            'lora_source': 'LoRARegistry',
                            'clothing_source': 'ClothingCatalog'
                        }
                    })
            results[influencer_id] = influencer_results
        return results

    def store_results(self, results: Dict[str, List[Dict]], storage_path: str):
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

# Example usage
if __name__ == '__main__':
    from comfycode.automation.prompt_generator import persona_library, scenario_library, explicitness_levels
    prompt_gen = PromptGenerator(persona_library, scenario_library, explicitness_levels)
    lora_reg = LoRARegistry('lora_registry.json')
    clothing_cat = ClothingCatalog('clothing_catalog.json')
    orchestrator = BatchWorkflowOrchestrator(prompt_gen, lora_reg, clothing_cat)
    results = orchestrator.run_grid(['influencer1', 'influencer2'], n_prompts=2, n_clothing=2)
    orchestrator.store_results(results, 'batch_results.json')
