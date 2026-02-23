import logging
def safe_get_prompts(prompt_generator, influencer_id, n_prompts):
    """
    Safely generate prompts for a given influencer, handling errors gracefully.
    """
    try:
        return prompt_generator.batch_generate([influencer_id], n_per_influencer=n_prompts)[influencer_id]
    except Exception as e:
        logging.error(f"Prompt generation failed for {influencer_id}: {e}")
        return []

def safe_get_clothing(clothing_catalog, influencer_id, n_clothing):
    """
    Safely select clothing items for a given influencer, handling errors gracefully.
    """
    try:
        return clothing_catalog.batch_select(influencer_id, n_items=n_clothing)
    except Exception as e:
        logging.error(f"Clothing selection failed for {influencer_id}: {e}")
        return []

def safe_get_loras(lora_registry, influencer_id, prompt):
    """
    Safely retrieve LoRA stack for a given influencer and prompt, handling errors gracefully.
    """
    try:
        return lora_registry.multi_lora_stack(influencer_id, prompt)
    except Exception as e:
        logging.error(f"LoRA stack failed for {influencer_id}: {e}")
        return []
"""
Batch Workflow Orchestrator for AI Influencer Automation

Executes influencer × clothing × prompt grid, tracks provenance, and routes outputs.
"""
from typing import List, Dict, Any
from pydantic import BaseModel, ValidationError
from comfycode.automation.prompt_generator import PromptGenerator
from comfycode.automation.lora_registry import LoRARegistry
from comfycode.automation.clothing_catalog import ClothingCatalog
import json

class BatchResultEntry(BaseModel):
    """
    Schema for a single batch result entry in influencer automation grid.
    Contains influencer ID, prompt, LoRA stack, clothing item, and provenance metadata.
    """
    influencer_id: str
    prompt: str
    loras: Any
    clothing: Any
    provenance: Dict[str, str]

class BatchWorkflowOrchestrator:
    """
    Orchestrates batch workflow for AI influencer automation.
    Executes influencer × clothing × prompt grid, validates results, and tracks provenance.
    """
    def __init__(self, prompt_generator: PromptGenerator, lora_registry: LoRARegistry, clothing_catalog: ClothingCatalog):
        """
        Initialize orchestrator with prompt generator, LoRA registry, and clothing catalog.
        """
        self.prompt_generator = prompt_generator
        self.lora_registry = lora_registry
        self.clothing_catalog = clothing_catalog

    def run_grid(self, influencer_ids: List[str], n_prompts: int = 5, n_clothing: int = 3) -> Dict[str, List[BatchResultEntry]]:
        """
        Executes influencer × clothing × prompt grid, validates results, and tracks provenance.
        Returns a dictionary mapping influencer IDs to lists of validated BatchResultEntry objects.
        """
        results = {}
        for influencer_id in influencer_ids:
            prompts = safe_get_prompts(self.prompt_generator, influencer_id, n_prompts)
            clothing_items = safe_get_clothing(self.clothing_catalog, influencer_id, n_clothing)
            influencer_results = []
            for prompt in prompts:
                loras = safe_get_loras(self.lora_registry, influencer_id, prompt)
                for clothing in clothing_items:
                    entry_data = {
                        'influencer_id': influencer_id,
                        'prompt': prompt,
                        'loras': loras,
                        'clothing': clothing,
                        'provenance': {
                            'prompt_source': 'PromptGenerator',
                            'lora_source': 'LoRARegistry',
                            'clothing_source': 'ClothingCatalog'
                        }
                    }
                    try:
                        entry = BatchResultEntry(**entry_data)
                        influencer_results.append(entry)
                    except ValidationError as ve:
                        logging.error(f"BatchResultEntry validation failed for {influencer_id}: {ve}")
                        continue
            results[influencer_id] = influencer_results
        return results

    def store_results(self, results: Dict[str, List[BatchResultEntry]], storage_path: str):
        """
        Serializes batch results to JSON and stores them at the specified path.
        """
        serializable = {k: [entry.model_dump() for entry in v] for k, v in results.items()}
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(serializable, f, indent=2)

# Example usage
if __name__ == '__main__':
    from comfycode.automation.prompt_generator import persona_library, scenario_library, explicitness_levels
    prompt_gen = PromptGenerator(persona_library, scenario_library, explicitness_levels)
    lora_reg = LoRARegistry('lora_registry.json')
    clothing_cat = ClothingCatalog('clothing_catalog.json')
    orchestrator = BatchWorkflowOrchestrator(prompt_gen, lora_reg, clothing_cat)
    results = orchestrator.run_grid(['influencer1', 'influencer2'], n_prompts=2, n_clothing=2)
    orchestrator.store_results(results, 'batch_results.json')
