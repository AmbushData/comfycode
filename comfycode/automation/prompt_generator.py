"""
Prompt Generator for AI Influencer Automation

Generates persona-aware, scenario-driven, explicit prompts for influencer workflows.
"""
from typing import List, Dict, Optional
import random

class PromptGenerator:
    def __init__(self, persona_library: Dict[str, Dict], scenario_library: List[str], explicitness_levels: List[str]):
        self.persona_library = persona_library
        self.scenario_library = scenario_library
        self.explicitness_levels = explicitness_levels

    def generate_prompt(self, influencer_id: str, scenario: Optional[str] = None, explicitness: Optional[str] = None) -> str:
        persona = self.persona_library.get(influencer_id, {})
        scenario = scenario or random.choice(self.scenario_library)
        explicitness = explicitness or random.choice(self.explicitness_levels)
        base_prompt = persona.get('base_prompt', 'influencer portrait')
        persona_tags = persona.get('tags', [])
        explicit_tag = f"{explicitness}"
        prompt = f"{base_prompt}, {scenario}, {' '.join(persona_tags)}, {explicit_tag}"
        return prompt

    def batch_generate(self, influencer_ids: List[str], n_per_influencer: int = 10) -> Dict[str, List[str]]:
        prompts = {}
        for influencer_id in influencer_ids:
            prompts[influencer_id] = [self.generate_prompt(influencer_id) for _ in range(n_per_influencer)]
        return prompts

    def store_prompts(self, prompts: Dict[str, List[str]], storage_path: str):
        import json
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2)

# Example persona and scenario libraries (to be replaced with real metadata)
persona_library = {
    'influencer1': {'base_prompt': 'seductive influencer portrait', 'tags': ['lingerie', 'bedroom', 'smile']},
    'influencer2': {'base_prompt': 'playful influencer photo', 'tags': ['outdoor', 'sunlight', 'laughter']},
}
scenario_library = ['posing on a bed', 'mirror selfie', 'lingerie shoot', 'poolside glamour', 'couch relaxation']
explicitness_levels = ['suggestive', 'explicit', 'very explicit']

# Usage example
if __name__ == '__main__':
    generator = PromptGenerator(persona_library, scenario_library, explicitness_levels)
    prompts = generator.batch_generate(['influencer1', 'influencer2'], n_per_influencer=20)
    generator.store_prompts(prompts, 'prompts.json')
