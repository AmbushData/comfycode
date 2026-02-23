import unittest
from comfycode.automation.clothing_catalog import ClothingCatalog
import json
import os

class TestClothingCatalog(unittest.TestCase):
    def setUp(self):
        self.catalog_path = 'test_clothing_catalog.json'
        self.example_catalog = {
            'influencer1': {
                'lingerie1': {'type': 'lingerie', 'color': 'red', 'path': 'clothing/influencer1/lingerie1.png'},
                'lingerie2': {'type': 'lingerie', 'color': 'black', 'path': 'clothing/influencer1/lingerie2.png'},
                'dress1': {'type': 'dress', 'color': 'blue', 'path': 'clothing/influencer1/dress1.png'},
            },
            'influencer2': {
                'swimsuit1': {'type': 'swimsuit', 'color': 'yellow', 'path': 'clothing/influencer2/swimsuit1.png'},
            }
        }
        with open(self.catalog_path, 'w', encoding='utf-8') as f:
            json.dump(self.example_catalog, f, indent=2)
        self.catalog = ClothingCatalog(self.catalog_path)

    def tearDown(self):
        os.remove(self.catalog_path)

    def test_get_closet(self):
        closet = self.catalog.get_closet('influencer1')
        self.assertIn('lingerie1', closet)
        self.assertIn('lingerie2', closet)
        self.assertIn('dress1', closet)

    def test_batch_select(self):
        batch = self.catalog.batch_select('influencer1', n_items=2)
        self.assertEqual(len(batch), 2)
        for item in batch:
            self.assertIn(item, ['lingerie1', 'lingerie2', 'dress1'])

    def test_add_clothing(self):
        self.catalog.add_clothing('influencer2', 'swimsuit2', {'type': 'swimsuit', 'color': 'green', 'path': 'clothing/influencer2/swimsuit2.png'})
        closet = self.catalog.get_closet('influencer2')
        self.assertIn('swimsuit2', closet)

if __name__ == '__main__':
    unittest.main()
