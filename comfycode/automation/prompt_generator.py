"""
Prompt Generator for AI Influencer Automation

Generates persona-aware, scenario-driven, explicit prompts for influencer workflows.
"""

from typing import List, Dict, Optional
import random
from pydantic import BaseModel, ValidationError, Field

class PersonaModel(BaseModel):
    base_prompt: str = Field(..., description="Base prompt for influencer persona")
    tags: List[str] = Field(default_factory=list, description="Tags describing persona")

class ScenarioModel(BaseModel):
    scenario: str = Field(..., description="Scenario description")

class ExplicitnessModel(BaseModel):
    level: str = Field(..., description="Explicitness level")

class PromptGenerator:
    def __init__(self, persona_library: Dict[str, Dict], scenario_library: List[str], explicitness_levels: List[str]):
        # Validate persona library
        self.persona_library = {}
        for pid, pdata in persona_library.items():
            try:
                self.persona_library[pid] = PersonaModel(**pdata)
            except ValidationError as e:
                print(f"Invalid persona for {pid}: {e}")
        # Validate scenarios
        self.scenario_library = []
        for s in scenario_library:
            try:
                self.scenario_library.append(ScenarioModel(scenario=s))
            except ValidationError as e:
                print(f"Invalid scenario: {e}")
        # Validate explicitness
        self.explicitness_levels = []
        for e in explicitness_levels:
            try:
                self.explicitness_levels.append(ExplicitnessModel(level=e))
            except ValidationError as e:
                print(f"Invalid explicitness: {e}")

    def generate_prompt(self, influencer_id: str, scenario: Optional[str] = None, explicitness: Optional[str] = None) -> str:
        persona = self.persona_library.get(influencer_id)
        if not persona:
            return f"[ERROR: Unknown influencer {influencer_id}]"
        scenario_obj = ScenarioModel(scenario=scenario) if scenario else random.choice(self.scenario_library)
        explicit_obj = ExplicitnessModel(level=explicitness) if explicitness else random.choice(self.explicitness_levels)
        base_prompt = persona.base_prompt
        persona_tags = persona.tags
        explicit_tag = explicit_obj.level
        prompt = f"{base_prompt}, {scenario_obj.scenario}, {' '.join(persona_tags)}, {explicit_tag}"
        return prompt

    def batch_generate(self, influencer_ids: List[str], n_per_influencer: int = 10) -> Dict[str, List[str]]:
        prompts = {}
        for influencer_id in influencer_ids:
            prompts[influencer_id] = []
            for _ in range(n_per_influencer):
                prompt = self.generate_prompt(influencer_id)
                if not prompt.startswith("[ERROR"):
                    prompts[influencer_id].append(prompt)
        return prompts

    def store_prompts(self, prompts: Dict[str, List[str]], storage_path: str):
        import json
        with open(storage_path, 'w', encoding='utf-8') as f:
            json.dump(prompts, f, indent=2)

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
