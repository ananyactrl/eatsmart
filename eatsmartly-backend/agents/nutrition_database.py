"""
Nutrition Database Integration for EatSmartly
Uses the daily_food_nutrition_dataset.csv to provide accurate meal planning
"""

import pandas as pd
import logging
from typing import List, Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class NutritionDatabase:
    """Loads and queries the nutrition dataset for accurate meal planning"""

    def __init__(self):
        self.df = None
        self.load_dataset()

    def load_dataset(self):
        """Load the nutrition dataset"""
        try:
            dataset_path = "C:/Users/anany/projects/eatsmart/ml/archive/daily_food_nutrition_dataset.csv"

            # Read with error handling for malformed rows
            self.df = pd.read_csv(dataset_path, on_bad_lines='skip')
            logger.info(f"Loaded nutrition dataset with {len(self.df)} food items")

            # Clean column names
            self.df.columns = self.df.columns.str.strip()

        except Exception as e:
            logger.error(f"Failed to load nutrition dataset: {e}")
            self.df = None

    def find_ingredients(self, ingredients: List[str]) -> List[Dict]:
        """Find food items matching the given ingredients"""
        if self.df is None:
            return []

        matches = []
        for ingredient in ingredients:
            # Search for ingredient in food names (case insensitive)
            mask = self.df['Food_Item'].str.contains(ingredient, case=False, na=False)
            ingredient_matches = self.df[mask].to_dict('records')
            matches.extend(ingredient_matches)

        return matches[:10]  # Return top 10 matches

    def get_recipe_suggestions(self, ingredients: List[str]) -> List[Dict]:
        """Get recipe suggestions with accurate nutrition from dataset"""
        recipes = []

        # Find chicken recipes
        if any('chicken' in ing.lower() for ing in ingredients):
            chicken_items = self.df[
                self.df['Food_Item'].str.contains('chicken|grilled chicken', case=False, na=False)
            ]
            if not chicken_items.empty:
                recipes.extend(chicken_items.head(2).to_dict('records'))

        # Find rice recipes
        if any('rice' in ing.lower() for ing in ingredients):
            rice_items = self.df[
                self.df['Food_Item'].str.contains('rice|biryani|pulao', case=False, na=False)
            ]
            if not rice_items.empty:
                recipes.extend(rice_items.head(2).to_dict('records'))

        # Find pasta recipes
        if any('pasta' in ing.lower() for ing in ingredients):
            pasta_items = self.df[
                self.df['Food_Item'].str.contains('pasta|spaghetti', case=False, na=False)
            ]
            if not pasta_items.empty:
                recipes.extend(pasta_items.head(2).to_dict('records'))

        # Find vegetarian options
        if any(veg in ' '.join(ingredients).lower() for veg in ['tofu', 'vegetables', 'lentil']):
            veg_items = self.df[
                self.df['Food_Item'].str.contains('tofu|lentil|vegetarian', case=False, na=False)
            ]
            if not veg_items.empty:
                recipes.extend(veg_items.head(2).to_dict('records'))

        return recipes[:3]  # Return top 3 recipe suggestions

    def format_recipe_with_nutrition(self, food_item: Dict) -> str:
        """Format a food item as a recipe with accurate nutrition data"""
        try:
            name = food_item.get('Food_Item', 'Unknown Recipe')
            calories = food_item.get('Calories (kcal)', 0)
            protein = food_item.get('Protein (g)', 0)
            carbs = food_item.get('Carbohydrates (g)', 0)
            fat = food_item.get('Fat (g)', 0)
            fiber = food_item.get('Fiber (g)', 0)

            # Create recipe format
            recipe = f"{name} ({calories} calories, {protein}g protein)\n\n"

            # Generate ingredients based on the food item
            recipe += self._generate_ingredients(name, food_item)

            # Generate cooking steps
            recipe += self._generate_steps(name, food_item)

            return recipe

        except Exception as e:
            logger.error(f"Error formatting recipe: {e}")
            return ""

    def _generate_ingredients(self, name: str, nutrition: Dict) -> str:
        """Generate ingredient list for a recipe based on nutrition data"""
        name_lower = name.lower()

        ingredients = "Ingredients:\n"

        # Chicken recipes
        if 'chicken' in name_lower:
            ingredients += "1. 200g boneless chicken pieces\n"
            ingredients += "2. 2 tbsp cooking oil\n"
            ingredients += "3. 1 onion, sliced\n"
            ingredients += "4. 1 tsp ginger-garlic paste\n"
            ingredients += "5. 1 tsp turmeric powder\n"
            ingredients += "6. 1 tsp red chili powder\n"
            ingredients += "7. Salt to taste\n"

            if 'salad' in name_lower:
                ingredients += "8. Mixed greens\n9. Cherry tomatoes\n10. Cucumber\n"

        # Rice recipes
        elif 'rice' in name_lower:
            ingredients += "1. 1 cup basmati rice\n"
            ingredients += "2. 2 cups water or broth\n"
            ingredients += "3. 1 tbsp ghee or oil\n"
            ingredients += "4. Whole spices (cardamom, cinnamon)\n"
            ingredients += "5. Salt to taste\n"

        # Pasta recipes
        elif 'pasta' in name_lower or 'spaghetti' in name_lower:
            ingredients += "1. 200g pasta or spaghetti\n"
            ingredients += "2. 2 tbsp olive oil\n"
            ingredients += "3. 2 cloves garlic, minced\n"
            ingredients += "4. 1 can crushed tomatoes\n"
            ingredients += "5. Fresh basil leaves\n"
            ingredients += "6. Salt and pepper\n"

        # Vegetarian recipes
        elif any(word in name_lower for word in ['tofu', 'lentil', 'vegetarian']):
            ingredients += "1. 200g firm tofu or 1 cup lentils\n"
            ingredients += "2. Mixed vegetables\n"
            ingredients += "3. 2 tbsp oil\n"
            ingredients += "4. Spices and herbs\n"
            ingredients += "5. Salt to taste\n"

        else:
            # Generic ingredients
            ingredients += "1. Main ingredient as specified\n"
            ingredients += "2. Supporting ingredients\n"
            ingredients += "3. Seasonings and spices\n"

        return ingredients + "\n"

    def _generate_steps(self, name: str, nutrition: Dict) -> str:
        """Generate cooking steps for a recipe"""
        name_lower = name.lower()

        steps = "Steps:\n"

        if 'chicken' in name_lower:
            if 'salad' in name_lower:
                steps += "1. Season and grill chicken until fully cooked\n"
                steps += "2. Let chicken rest, then slice\n"
                steps += "3. Prepare fresh salad greens and vegetables\n"
                steps += "4. Arrange chicken over salad\n"
                steps += "5. Add dressing and serve immediately\n"
            else:
                steps += "1. Marinate chicken with spices for 15 minutes\n"
                steps += "2. Heat oil in a pan over medium heat\n"
                steps += "3. Add onions and cook until golden\n"
                steps += "4. Add chicken and cook for 15-20 minutes\n"
                steps += "5. Garnish and serve hot\n"

        elif 'rice' in name_lower:
            steps += "1. Wash and soak rice for 30 minutes\n"
            steps += "2. Heat ghee in a heavy-bottomed pot\n"
            steps += "3. Add whole spices and let them splutter\n"
            steps += "4. Add rice and water, bring to boil\n"
            steps += "5. Cover and cook on low heat for 20 minutes\n"
            steps += "6. Let it rest for 5 minutes before serving\n"

        elif 'pasta' in name_lower or 'spaghetti' in name_lower:
            steps += "1. Boil pasta according to package instructions\n"
            steps += "2. Heat olive oil in a large pan\n"
            steps += "3. Add garlic and cook until fragrant\n"
            steps += "4. Add tomatoes and simmer for 10 minutes\n"
            steps += "5. Toss with cooked pasta and fresh herbs\n"
            steps += "6. Serve immediately with garnish\n"

        else:
            steps += "1. Prepare all ingredients\n"
            steps += "2. Cook main ingredient properly\n"
            steps += "3. Combine with seasonings\n"
            steps += "4. Cook until done\n"
            steps += "5. Serve hot\n"

        return steps

# Global instance
_nutrition_db = None

def get_nutrition_database() -> NutritionDatabase:
    """Get the global nutrition database instance"""
    global _nutrition_db
    if _nutrition_db is None:
        _nutrition_db = NutritionDatabase()
    return _nutrition_db