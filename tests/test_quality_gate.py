import unittest
from comfycode.automation.quality_gate import QualityGate

class TestQualityGate(unittest.TestCase):
    def setUp(self):
        self.gate = QualityGate()
        self.batch_results = {
            'influencer1': [
                {'prompt': 'seductive influencer portrait', 'loras': ['lora1'], 'clothing': 'lingerie1', 'provenance': {}},
                {'prompt': 'mirror selfie', 'loras': ['lora2'], 'clothing': 'lingerie2', 'provenance': {}},
            ],
            'influencer2': [
                {'prompt': 'playful influencer photo', 'loras': ['lora3'], 'clothing': 'swimsuit1', 'provenance': {}},
            ]
        }

    def test_score_output(self):
        entry = self.batch_results['influencer1'][0]
        scored = self.gate.score_output(entry.copy())
        self.assertIn('quality_score', scored)
        self.assertIn('nsfw_score', scored)
        self.assertIn('nsfw_class', scored)
        self.assertTrue(scored['nsfw_class'] in ['sfw', 'nsfw-mild', 'nsfw-explicit'])

    def test_filter_and_route(self):
        routed = self.gate.filter_and_route(self.batch_results, nsfw_policy='mixed', min_quality=0.0)
        self.assertIn('influencer1', routed)
        self.assertIn('influencer2', routed)
        self.assertTrue(len(routed['influencer1']) > 0)
        self.assertTrue(len(routed['influencer2']) > 0)
        # Test SFW-only policy
        routed_sfw = self.gate.filter_and_route(self.batch_results, nsfw_policy='sfw', min_quality=0.0)
        for entries in routed_sfw.values():
            for entry in entries:
                self.assertEqual(entry['nsfw_class'], 'sfw')

if __name__ == '__main__':
    unittest.main()
