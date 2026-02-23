import unittest
from comfycode.automation.documentation_generator import DocumentationGenerator
from comfycode.automation.lora_registry import LoRARegistry
from comfycode.automation.clothing_catalog import ClothingCatalog
from comfycode.automation.prompt_generator import PromptGenerator
import json
import os

class TestDocumentationGenerator(unittest.TestCase):
    def setUp(self):
        self.lora_registry_path = 'test_lora_registry.json'
        self.lora_catalog = {
            'influencer1': {
                'lora1': {'tags': ['lingerie', 'bedroom'], 'path': 'loras/influencer1/lora1.safetensors'},
            }
        }
        with open(self.lora_registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.lora_catalog, f, indent=2)
        self.lora_reg = LoRARegistry(self.lora_registry_path)

        self.clothing_catalog_path = 'test_clothing_catalog.json'
        self.clothing_catalog = {
            'influencer1': {
                'lingerie1': {'type': 'lingerie', 'color': 'red', 'path': 'clothing/influencer1/lingerie1.png'},
            }
        }
        with open(self.clothing_catalog_path, 'w', encoding='utf-8') as f:
            json.dump(self.clothing_catalog, f, indent=2)
        self.clothing_cat = ClothingCatalog(self.clothing_catalog_path)

        self.persona_library = {
            'influencer1': {'base_prompt': 'seductive influencer portrait', 'tags': ['lingerie', 'bedroom', 'smile']},
        }
        self.scenario_library = ['posing on a bed']
        self.explicitness_levels = ['suggestive']
        self.prompt_gen = PromptGenerator(self.persona_library, self.scenario_library, self.explicitness_levels)

        self.doc_gen = DocumentationGenerator(self.lora_reg, self.clothing_cat, self.prompt_gen)

    def tearDown(self):
        os.remove(self.lora_registry_path)
        os.remove(self.clothing_catalog_path)
        if os.path.exists('test_inventory_doc.json'):
            os.remove('test_inventory_doc.json')

    def test_generate_inventory_doc(self):
        self.doc_gen.generate_inventory_doc('test_inventory_doc.json')
        with open('test_inventory_doc.json', 'r', encoding='utf-8') as f:
            doc = json.load(f)
        self.assertIn('loras', doc)
        self.assertIn('clothing', doc)
        self.assertIn('personas', doc)
        self.assertIn('scenarios', doc)
        self.assertIn('explicitness_levels', doc)
        self.assertEqual(doc['loras'], self.lora_catalog)
        self.assertEqual(doc['clothing'], self.clothing_catalog)
        self.assertEqual(doc['personas'], self.persona_library)
        self.assertEqual(doc['scenarios'], self.scenario_library)
        self.assertEqual(doc['explicitness_levels'], self.explicitness_levels)

if __name__ == '__main__':
    unittest.main()
