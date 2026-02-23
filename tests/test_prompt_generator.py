import unittest
from comfycode.automation.prompt_generator import PromptGenerator

class TestPromptGenerator(unittest.TestCase):
    def setUp(self):
        self.persona_library = {
            'influencer1': {'base_prompt': 'seductive influencer portrait', 'tags': ['lingerie', 'bedroom', 'smile']},
            'influencer2': {'base_prompt': 'playful influencer photo', 'tags': ['outdoor', 'sunlight', 'laughter']},
        }
        self.scenario_library = ['posing on a bed', 'mirror selfie', 'lingerie shoot', 'poolside glamour', 'couch relaxation']
        self.explicitness_levels = ['suggestive', 'explicit', 'very explicit']
        self.generator = PromptGenerator(self.persona_library, self.scenario_library, self.explicitness_levels)

    def test_generate_prompt(self):
        prompt = self.generator.generate_prompt('influencer1', 'mirror selfie', 'explicit')
        self.assertIn('seductive influencer portrait', prompt)
        self.assertIn('mirror selfie', prompt)
        self.assertIn('explicit', prompt)

    def test_batch_generate(self):
        prompts = self.generator.batch_generate(['influencer1', 'influencer2'], n_per_influencer=5)
        self.assertEqual(len(prompts['influencer1']), 5)
        self.assertEqual(len(prompts['influencer2']), 5)
        for p in prompts['influencer1']:
            self.assertIn('seductive influencer portrait', p)
        for p in prompts['influencer2']:
            self.assertIn('playful influencer photo', p)

    def test_store_prompts(self):
        prompts = self.generator.batch_generate(['influencer1'], n_per_influencer=2)
        self.generator.store_prompts(prompts, 'test_prompts.json')
        import json
        with open('test_prompts.json', 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        self.assertEqual(len(loaded['influencer1']), 2)

if __name__ == '__main__':
    unittest.main()
