"""
Enhanced Training Data Collection for Ingredient Analysis.
Multiple data sources for better model training.
"""
import pandas as pd
import requests
import json
import time
from typing import List, Dict, Any
import os


class EnhancedDataCollector:
    """Collect training data from multiple sources."""

    def __init__(self):
        self.data_sources = {
            'openfoodfacts': self._collect_openfoodfacts,
            'usda': self._collect_usda,
            'manual_labeled': self._load_manual_labels,
            'crowdsourced': self._collect_crowdsourced
        }

    def collect_all_sources(self) -> pd.DataFrame:
        """Collect data from all available sources."""
        all_data = []

        for source_name, collector_func in self.data_sources.items():
            try:
                print(f"Collecting from {source_name}...")
                data = collector_func()
                all_data.extend(data)
                print(f"Collected {len(data)} samples from {source_name}")
            except Exception as e:
                print(f"Error collecting from {source_name}: {e}")

        df = pd.DataFrame(all_data)
        print(f"Total training samples: {len(df)}")
        return df

    def _collect_openfoodfacts(self) -> List[Dict]:
        """Collect from OpenFoodFacts with enhanced labeling."""
        data = []
        categories = [
            'en:sugary-snacks', 'en:beverages', 'en:dairies', 'en:desserts',
            'en:chocolates', 'en:candies', 'en:ice-creams', 'en:sodas'
        ]

        for category in categories:
            try:
                url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms=&tagtype_0=categories&tag_contains_0=contains&tag_0={category}&json=1&page_size=200"
                response = requests.get(url, timeout=30)
                products = response.json().get('products', [])

                for product in products:
                    sample = self._process_openfoodfacts_product(product)
                    if sample:
                        data.append(sample)

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"Error with {category}: {e}")

        return data

    def _collect_usda(self) -> List[Dict]:
        """Collect from USDA FoodData Central."""
        # This would require USDA API key
        # Implementation would fetch branded foods data
        return []

    def _load_manual_labels(self) -> List[Dict]:
        """Load manually labeled examples."""
        manual_examples = [
            {
                'ingredients': 'carbonated water, caramel color, phosphoric acid, natural flavors, caffeine, sucralose, acesulfame potassium',
                'product_name': 'diet cola',
                'labels': ['sugar-free', 'diet'],
                'misleading': 1,  # Claims sugar-free but has artificial sweeteners
                'source': 'manual'
            },
            {
                'ingredients': 'milk, sugar, cocoa, vanilla extract',
                'product_name': 'chocolate milk',
                'labels': [],
                'misleading': 0,  # No false claims
                'source': 'manual'
            },
            # Add more manual examples...
        ]
        return manual_examples

    def _collect_crowdsourced(self) -> List[Dict]:
        """Collect from crowdsourced food databases."""
        # Could integrate with sources like:
        # - Nutritionix API
        # - Spoonacular API
        # - Local regulatory databases
        return []

    def _process_openfoodfacts_product(self, product: Dict) -> Dict:
        """Process a single OpenFoodFacts product."""
        ingredients = product.get('ingredients_text', '').lower().strip()
        if not ingredients:
            return None

        product_name = product.get('product_name', '').lower()
        labels = [label.lower() for label in product.get('labels_tags', [])]

        # Enhanced labeling logic
        sugar_free_claims = any(claim in product_name or any(claim in label for label in labels)
                               for claim in ['sugar-free', 'no sugar', 'sugarless', 'zero sugar'])

        # Check for various sugar types
        has_hidden_sugars = self._contains_hidden_sugars(ingredients)
        has_artificial_sweeteners = self._contains_artificial_sweeteners(ingredients)

        # Determine if misleading
        if sugar_free_claims and (has_hidden_sugars or has_artificial_sweeteners):
            misleading = 1  # Potentially misleading
        elif sugar_free_claims and not (has_hidden_sugars or has_artificial_sweeteners):
            misleading = 0  # Legitimate sugar-free
        else:
            misleading = 0  # No claim to be misleading about

        return {
            'ingredients': ingredients,
            'product_name': product_name,
            'labels': labels,
            'misleading': misleading,
            'source': 'openfoodfacts',
            'has_hidden_sugars': has_hidden_sugars,
            'has_artificial_sweeteners': has_artificial_sweeteners,
            'sugar_free_claim': sugar_free_claims
        }

    def _contains_hidden_sugars(self, ingredients: str) -> bool:
        """Check if ingredients contain hidden sugars."""
        hidden_sugars = [
            'fructose', 'sucrose', 'glucose', 'maltose', 'lactose', 'galactose',
            'high fructose corn syrup', 'corn syrup', 'agave nectar', 'honey',
            'maple syrup', 'molasses', 'fruit juice concentrate', 'dextrose',
            'maltodextrin', 'barley malt', 'rice syrup'
        ]
        return any(sugar in ingredients for sugar in hidden_sugars)

    def _contains_artificial_sweeteners(self, ingredients: str) -> bool:
        """Check if ingredients contain artificial sweeteners."""
        sweeteners = [
            'acesulfame potassium', 'aspartame', 'sucralose', 'saccharin',
            'stevia', 'erythritol', 'xylitol', 'sorbitol', 'mannitol',
            'isomalt', 'maltitol', 'lactitol'
        ]
        return any(sweetener in ingredients for sweetener in sweeteners)


if __name__ == "__main__":
    collector = EnhancedDataCollector()
    df = collector.collect_all_sources()
    print(f"Collected {len(df)} training samples")
    df.to_csv('training_data_enhanced.csv', index=False)</content>
<parameter name="filePath">c:\Users\anany\projects\eatsmart\eatsmartly-backend\enhanced_data_collection.py