import unittest
from comfycode.automation.lora_registry import LoRARegistry
import json
import os

class TestLoRARegistry(unittest.TestCase):
    def setUp(self):
        self.registry_path = 'test_lora_registry.json'
        self.example_catalog = {
            'influencer1': {
                'lora1': {'tags': ['lingerie', 'bedroom'], 'path': 'loras/influencer1/lora1.safetensors'},
                'lora2': {'tags': ['smile', 'mirror'], 'path': 'loras/influencer1/lora2.safetensors'},
            },
            'influencer2': {
                'lora3': {'tags': ['outdoor', 'sunlight'], 'path': 'loras/influencer2/lora3.safetensors'},
            }
        }
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.example_catalog, f, indent=2)
        self.registry = LoRARegistry(self.registry_path)

    def tearDown(self):
        os.remove(self.registry_path)

    def test_lookup_lora(self):
        result = self.registry.lookup_lora('influencer1', 'mirror selfie lingerie')
        self.assertIn('lora1', result)
        self.assertIn('lora2', result)

    def test_multi_lora_stack(self):
        result = self.registry.multi_lora_stack('influencer1', 'bedroom smile')
        self.assertIn('lora1', result)
        self.assertIn('lora2', result)

    def test_add_lora(self):
        self.registry.add_lora('influencer2', 'lora4', {'tags': ['pool'], 'path': 'loras/influencer2/lora4.safetensors'})
        result = self.registry.lookup_lora('influencer2', 'poolside glamour')
        self.assertIn('lora4', result)

if __name__ == '__main__':
    unittest.main()
