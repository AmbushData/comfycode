import unittest
from comfycode.automation.batch_orchestrator import BatchWorkflowOrchestrator
from comfycode.automation.prompt_generator import PromptGenerator
from comfycode.automation.lora_registry import LoRARegistry
from comfycode.automation.clothing_catalog import ClothingCatalog
import json
import os

class TestBatchWorkflowOrchestrator(unittest.TestCase):
    def setUp(self):
        # Setup prompt generator
        self.persona_library = {
            'influencer1': {'base_prompt': 'seductive influencer portrait', 'tags': ['lingerie', 'bedroom', 'smile']},
            'influencer2': {'base_prompt': 'playful influencer photo', 'tags': ['outdoor', 'sunlight', 'laughter']},
        }
        self.scenario_library = ['posing on a bed', 'mirror selfie', 'lingerie shoot', 'poolside glamour', 'couch relaxation']
        self.explicitness_levels = ['suggestive', 'explicit', 'very explicit']
        self.prompt_gen = PromptGenerator(self.persona_library, self.scenario_library, self.explicitness_levels)

        # Setup LoRA registry
        self.lora_registry_path = 'test_lora_registry.json'
        self.lora_catalog = {
            'influencer1': {
                'lora1': {'tags': ['lingerie', 'bedroom'], 'path': 'loras/influencer1/lora1.safetensors'},
                'lora2': {'tags': ['smile', 'mirror'], 'path': 'loras/influencer1/lora2.safetensors'},
            },
            'influencer2': {
                'lora3': {'tags': ['outdoor', 'sunlight'], 'path': 'loras/influencer2/lora3.safetensors'},
            }
        }
        with open(self.lora_registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.lora_catalog, f, indent=2)
        self.lora_reg = LoRARegistry(self.lora_registry_path)

        # Setup clothing catalog
        self.clothing_catalog_path = 'test_clothing_catalog.json'
        self.clothing_catalog = {
            'influencer1': {
                'lingerie1': {'type': 'lingerie', 'color': 'red', 'path': 'clothing/influencer1/lingerie1.png'},
                'lingerie2': {'type': 'lingerie', 'color': 'black', 'path': 'clothing/influencer1/lingerie2.png'},
                'dress1': {'type': 'dress', 'color': 'blue', 'path': 'clothing/influencer1/dress1.png'},
            },
            'influencer2': {
                'swimsuit1': {'type': 'swimsuit', 'color': 'yellow', 'path': 'clothing/influencer2/swimsuit1.png'},
            }
        }
        with open(self.clothing_catalog_path, 'w', encoding='utf-8') as f:
            json.dump(self.clothing_catalog, f, indent=2)
        self.clothing_cat = ClothingCatalog(self.clothing_catalog_path)

        self.orchestrator = BatchWorkflowOrchestrator(self.prompt_gen, self.lora_reg, self.clothing_cat)

    def tearDown(self):
        os.remove(self.lora_registry_path)
        os.remove(self.clothing_catalog_path)

    def test_run_grid(self):
        results = self.orchestrator.run_grid(['influencer1', 'influencer2'], n_prompts=2, n_clothing=2)
        self.assertIn('influencer1', results)
        self.assertIn('influencer2', results)
        self.assertTrue(len(results['influencer1']) > 0)
        self.assertTrue(len(results['influencer2']) > 0)
        for entry in results['influencer1']:
            self.assertTrue(hasattr(entry, 'prompt'))
            self.assertTrue(hasattr(entry, 'loras'))
            self.assertTrue(hasattr(entry, 'clothing'))
            self.assertTrue(hasattr(entry, 'provenance'))

    def test_store_results(self):
        results = self.orchestrator.run_grid(['influencer1'], n_prompts=1, n_clothing=1)
        self.orchestrator.store_results(results, 'test_batch_results.json')
        with open('test_batch_results.json', 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        self.assertIn('influencer1', loaded)
        os.remove('test_batch_results.json')

if __name__ == '__main__':
    unittest.main()
