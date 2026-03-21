"""
Ingredient Translation Module
Handles translation of ingredient names from multiple languages to English
"""
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class IngredientTranslator:
    """Translate ingredient names to English"""
    
    # Common ingredient translations (French, Spanish, German, Italian, Hindi)
    TRANSLATION_MAP = {
        # French
        'vinaigre': 'vinegar',
        'sucre': 'sugar',
        'sel': 'salt',
        'eau': 'water',
        'farine': 'flour',
        'huile': 'oil',
        'beurre': 'butter',
        'lait': 'milk',
        'oeufs': 'eggs',
        'oeuf': 'egg',
        'tomates': 'tomatoes',
        'tomate': 'tomato',
        'fromage': 'cheese',
        'poivre': 'pepper',
        'herbes': 'herbs',
        'épices': 'spices',
        'épice': 'spice',
        'levure': 'yeast',
        'miel': 'honey',
        'citron': 'lemon',
        'ail': 'garlic',
        'oignon': 'onion',
        'oignons': 'onions',
        'porc': 'pork',
        'boeuf': 'beef',
        'poulet': 'chicken',
        'poisson': 'fish',
        'riz': 'rice',
        'pâtes': 'pasta',
        'pain': 'bread',
        'biscuits': 'crackers',
        'chocolat': 'chocolate',
        'cacao': 'cocoa',
        'vanille': 'vanilla',
        'cannelle': 'cinnamon',
        'sucre blanc': 'white sugar',
        'sucre roux': 'brown sugar',
        'moutarde': 'mustard',
        'ketchup': 'ketchup',
        'mayonnaise': 'mayonnaise',
        'vin': 'wine',
        'bière': 'beer',
        'café': 'coffee',
        'thé': 'tea',
        'jus': 'juice',
        'lait écrémé': 'skimmed milk',
        'lait entier': 'whole milk',
        'crème': 'cream',
        'yaourt': 'yogurt',
        'glace': 'ice cream',
        
        # Spanish
        'agua': 'water',
        'azúcar': 'sugar',
        'sal': 'salt',
        'harina': 'flour',
        'aceite': 'oil',
        'mantequilla': 'butter',
        'leche': 'milk',
        'huevos': 'eggs',
        'tomates': 'tomatoes',
        'queso': 'cheese',
        'pimienta': 'pepper',
        'ajo': 'garlic',
        'cebolla': 'onion',
        'pan': 'bread',
        'chocolate': 'chocolate',
        'vino': 'wine',
        'cerveza': 'beer',
        'café': 'coffee',
        'té': 'tea',
        'jugo': 'juice',
        'yogur': 'yogurt',
        
        # German
        'wasser': 'water',
        'zucker': 'sugar',
        'salz': 'salt',
        'mehl': 'flour',
        'öl': 'oil',
        'butter': 'butter',
        'milch': 'milk',
        'eier': 'eggs',
        'käse': 'cheese',
        'pfeffer': 'pepper',
        'knoblauch': 'garlic',
        'zwiebel': 'onion',
        'brot': 'bread',
        'schokolade': 'chocolate',
        'wein': 'wine',
        'bier': 'beer',
        'kaffee': 'coffee',
        'tee': 'tea',
        'saft': 'juice',
        'jogurt': 'yogurt',
        
        # Italian
        'acqua': 'water',
        'zucchero': 'sugar',
        'sale': 'salt',
        'farina': 'flour',
        'olio': 'oil',
        'burro': 'butter',
        'latte': 'milk',
        'uova': 'eggs',
        'formaggio': 'cheese',
        'pepe': 'pepper',
        'aglio': 'garlic',
        'cipolla': 'onion',
        'pane': 'bread',
        'cioccolato': 'chocolate',
        'vino': 'wine',
        'birra': 'beer',
        'caffè': 'coffee',
        'tè': 'tea',
        'succo': 'juice',
        'yogurt': 'yogurt',
        
        # Hindi/Common Indian ingredients
        'नमक': 'salt',
        'चीनी': 'sugar',
        'मैदा': 'flour',
        'दाल': 'lentils',
        'चावल': 'rice',
        'तेल': 'oil',
        'दही': 'yogurt',
        'प्याज': 'onion',
        'लहसुन': 'garlic',
        'अदरक': 'ginger',
        'मिर्च': 'chili',
        'हल्दी': 'turmeric',
        'मसाले': 'spices',
    }
    
    def __init__(self):
        """Initialize translator with common mappings"""
        self.translations = self.TRANSLATION_MAP.copy()
    
    def translate_ingredient(self, ingredient: str) -> str:
        """
        Translate a single ingredient name to English
        
        Args:
            ingredient: Ingredient name (possibly in another language)
            
        Returns:
            English ingredient name (or original if no translation found)
        """
        if not ingredient:
            return ingredient
        
        ingredient_lower = ingredient.lower().strip()
        
        # Direct lookup
        if ingredient_lower in self.translations:
            return self.translations[ingredient_lower]
        
        # Check if it's already in English or contains English patterns
        if self._is_likely_english(ingredient_lower):
            return ingredient
        
        # Try partial matching for compound words
        for foreign_word, english_word in self.translations.items():
            if foreign_word in ingredient_lower:
                # Replace and return
                result = ingredient_lower.replace(foreign_word, english_word)
                return result.capitalize()
        
        # Return original if no translation found
        return ingredient
    
    def translate_ingredients_list(self, ingredients: List[str]) -> List[str]:
        """
        Translate a list of ingredient names to English
        
        Args:
            ingredients: List of ingredient names
            
        Returns:
            List of translated ingredient names
        """
        return [self.translate_ingredient(ing) for ing in ingredients]
    
    def clean_ingredient_name(self, ingredient: str) -> str:
        """
        Clean and standardize ingredient name after translation
        
        Args:
            ingredient: Ingredient name
            
        Returns:
            Cleaned ingredient name
        """
        if not ingredient:
            return ingredient
        
        # Remove extra whitespace
        ingredient = ' '.join(ingredient.split())
        
        # Capitalize properly
        ingredient = ingredient.strip()
        if ingredient:
            ingredient = ingredient[0].upper() + ingredient[1:].lower()
        
        return ingredient
    
    def _is_likely_english(self, text: str) -> bool:
        """Check if text is likely already in English"""
        # Common English patterns
        english_keywords = {
            'water', 'salt', 'sugar', 'flour', 'oil', 'butter', 'milk',
            'eggs', 'cheese', 'pepper', 'garlic', 'onion', 'bread',
            'chocolate', 'wine', 'beer', 'coffee', 'tea', 'juice',
            'yogurt', 'cream', 'vinegar', 'honey', 'yeast', 'spice',
            'herb', 'chicken', 'beef', 'pork', 'fish', 'rice', 'pasta'
        }
        
        # Check if any English keyword is in the text
        for keyword in english_keywords:
            if keyword in text:
                return True
        
        # Check if contains mostly ASCII letters (English likely)
        ascii_count = sum(1 for c in text if ord(c) < 128)
        if ascii_count >= len(text) * 0.8:
            return True
        
        return False
    
    def add_translation(self, foreign_word: str, english_word: str):
        """Add a custom translation mapping"""
        self.translations[foreign_word.lower()] = english_word.lower()
        logger.info(f"Added translation: {foreign_word} -> {english_word}")


# Global instance
_translator = None

def get_translator() -> IngredientTranslator:
    """Get or create the global translator instance"""
    global _translator
    if _translator is None:
        _translator = IngredientTranslator()
    return _translator

def translate_ingredient(ingredient: str) -> str:
    """Convenience function to translate an ingredient"""
    translator = get_translator()
    return translator.clean_ingredient_name(translator.translate_ingredient(ingredient))

def translate_ingredients(ingredients: List[str]) -> List[str]:
    """Convenience function to translate a list of ingredients"""
    translator = get_translator()
    return [
        translator.clean_ingredient_name(translated)
        for translated in translator.translate_ingredients_list(ingredients)
    ]
