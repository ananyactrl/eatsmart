"""
OpenFoodFacts Indian Data Fetcher and Normalizer
Downloads and normalizes Indian FMCG product data from OpenFoodFacts
"""
import requests
import json
import csv
import logging
from typing import Dict, List, Optional
from datetime import datetime
import re
from knowledge.ingredient_translator import translate_ingredient, translate_ingredients

logger = logging.getLogger(__name__)

class OpenFoodFactsIndiaFetcher:
    """
    Fetch and normalize Indian product data from OpenFoodFacts
    Uses the Open Food Facts API and MongoDB export
    """
    
    def __init__(self):
        self.api_base = "https://world.openfoodfacts.org"
        self.india_api = "https://in.openfoodfacts.org"
        self.headers = {
            'User-Agent': 'EatSmartly/1.0 (Food Analysis App)',
            'Accept': 'application/json'
        }
        
        # Category normalization mappings
        self.category_mappings = {
            'snacks': ['Snacks', 'Salty snacks', 'Sweet snacks', 'Chips', 'Biscuits'],
            'beverages': ['Beverages', 'Soft drinks', 'Juices', 'Tea', 'Coffee'],
            'dairy': ['Dairy', 'Milk', 'Yogurt', 'Cheese', 'Butter', 'Ghee'],
            'cereals': ['Cereals', 'Breakfast cereals', 'Flakes', 'Oats'],
            'confectionery': ['Chocolates', 'Candies', 'Sweets', 'Desserts'],
            'ready-to-eat': ['Ready meals', 'Instant noodles', 'Instant food'],
            'staples': ['Rice', 'Wheat', 'Flour', 'Atta', 'Dal', 'Pulses'],
            'cooking': ['Cooking oil', 'Spices', 'Masala', 'Condiments'],
        }
    
    def fetch_indian_products(self, limit: int = 1000) -> List[Dict]:
        """
        Fetch Indian products from Open Food Facts
        """
        logger.info(f"🇮🇳 Fetching up to {limit} Indian products from OpenFoodFacts...")
        
        products = []
        page = 1
        page_size = 100
        
        while len(products) < limit:
            try:
                url = f"{self.india_api}/cgi/search.pl"
                params = {
                    'action': 'process',
                    'json': 1,
                    'page_size': page_size,
                    'page': page,
                    'countries_tags': 'en:india',
                    'sort_by': 'unique_scans_n',  # Most scanned products first
                    'lc': 'en',  # Request English language content
                    'fields': 'product_name,code,brands,categories_tags,nutriments,ingredients_text_en,allergens_tags,nutriscore_grade,nova_group,ecoscore_grade'
                }
                
                response = requests.get(url, params=params, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                page_products = data.get('products', [])
                
                if not page_products:
                    break
                
                products.extend(page_products)
                logger.info(f"   ✅ Page {page}: Found {len(page_products)} products (Total: {len(products)})")
                
                page += 1
                
                if len(data.get('products', [])) < page_size:
                    break  # Last page
                    
            except Exception as e:
                logger.error(f"   ❌ Error fetching page {page}: {e}")
                break
        
        logger.info(f"✅ Fetched {len(products)} Indian products")
        return products[:limit]
    
    def normalize_product(self, raw_product: Dict) -> Optional[Dict]:
        """
        Normalize raw OpenFoodFacts product data to our schema
        """
        try:
            # Extract basic info
            product_name = raw_product.get('product_name', '').strip()
            if not product_name:
                return None
            
            # Get barcode
            barcode = raw_product.get('code', '')
            
            # Get brand (multiple possible fields)
            brand = (
                raw_product.get('brands', '') or
                raw_product.get('brand_owner', '') or
                raw_product.get('manufacturer', '')
            ).strip()
            
            # Normalize categories
            categories_raw = raw_product.get('categories_tags', [])
            category = self._normalize_category(categories_raw)
            
            # Extract nutrition (per 100g)
            nutriments = raw_product.get('nutriments', {})
            
            normalized = {
                'barcode': barcode,
                'name': product_name,
                'brand': brand if brand else None,
                'category': category,
                'source': 'open_food_facts_india',
                
                # Nutrition per 100g
                'calories': nutriments.get('energy-kcal_100g'),
                'protein_g': nutriments.get('proteins_100g'),
                'carbs_g': nutriments.get('carbohydrates_100g'),
                'fat_g': nutriments.get('fat_100g'),
                'saturated_fat_g': nutriments.get('saturated-fat_100g'),
                'trans_fat_g': nutriments.get('trans-fat_100g'),
                'fiber_g': nutriments.get('fiber_100g'),
                'sugar_g': nutriments.get('sugars_100g'),
                'sodium_mg': nutriments.get('sodium_100g', 0) * 1000 if nutriments.get('sodium_100g') else None,  # Convert g to mg
                
                # Additional nutrients
                'calcium_mg': nutriments.get('calcium_100g', 0) * 1000 if nutriments.get('calcium_100g') else None,
                'iron_mg': nutriments.get('iron_100g', 0) * 1000 if nutriments.get('iron_100g') else None,
                'vitamin_a_mcg': nutriments.get('vitamin-a_100g', 0) * 1000 if nutriments.get('vitamin-a_100g') else None,
                'vitamin_c_mg': nutriments.get('vitamin-c_100g'),
                
                # Ingredients and allergens
                'ingredients': self._translate_and_normalize_ingredients(
                    raw_product.get('ingredients_text_en', '')
                ),
                'allergens': self._extract_allergens(raw_product),
                
                # Serving info
                'serving_size': nutriments.get('serving_size'),
                'serving_unit': 'g',
                
                # Metadata
                'is_indian_product': True,
                'official_website': None,
                'product_page_url': f"https://in.openfoodfacts.org/product/{barcode}",
                
                # Quality indicators
                'nutriscore_grade': raw_product.get('nutriscore_grade'),
                'nova_group': raw_product.get('nova_group'),
                'ecoscore_grade': raw_product.get('ecoscore_grade'),
            }
            
            return normalized
            
        except Exception as e:
            logger.warning(f"   ⚠️  Error normalizing product: {e}")
            return None
    
    def _normalize_category(self, categories_tags: List[str]) -> str:
        """
        Normalize category tags to main categories
        """
        if not categories_tags:
            return 'uncategorized'
        
        # Convert tags to readable names
        readable_categories = []
        for tag in categories_tags:
            # Remove language prefix (en:, fr:, etc.)
            category = tag.split(':')[-1] if ':' in tag else tag
            # Convert hyphens to spaces and capitalize
            category = category.replace('-', ' ').title()
            readable_categories.append(category)
        
        # Try to match to main category
        for main_category, keywords in self.category_mappings.items():
            for keyword in keywords:
                for cat in readable_categories:
                    if keyword.lower() in cat.lower():
                        return main_category
        
        # Return first category if no match
        return readable_categories[0].lower() if readable_categories else 'uncategorized'
    
    def _translate_and_normalize_ingredients(self, ingredients_text: str) -> str:
        """
        Translate and normalize ingredient text to English
        Handles multi-language ingredients and ensures English output
        """
        if not ingredients_text:
            return ''
        
        try:
            # Split ingredients by comma
            ingredient_list = [ing.strip() for ing in ingredients_text.split(',')]
            
            # Translate each ingredient to English
            translated_list = []
            for ingredient in ingredient_list:
                if ingredient:
                    # Translate the ingredient
                    english_ingredient = translate_ingredient(ingredient)
                    translated_list.append(english_ingredient)
            
            # Join back together
            normalized_text = ', '.join(translated_list)
            logger.debug(f"Translated ingredients: {ingredients_text[:100]} -> {normalized_text[:100]}")
            
            return normalized_text
            
        except Exception as e:
            logger.warning(f"Error translating ingredients: {e}, returning original")
            return ingredients_text
    
    def _extract_allergens(self, product: Dict) -> List[str]:
        """
        Extract allergen information
        """
        allergens = []
        
        # Get allergen tags
        allergen_tags = product.get('allergens_tags', [])
        for tag in allergen_tags:
            allergen = tag.split(':')[-1].replace('-', ' ').title()
            allergens.append(allergen)
        
        # Also check ingredients text for common allergens
        ingredients_text = product.get('ingredients_text_en', '').lower()
        common_allergens = ['milk', 'nuts', 'peanuts', 'soy', 'wheat', 'gluten', 'eggs']
        
        for allergen in common_allergens:
            if allergen in ingredients_text and allergen.title() not in allergens:
                allergens.append(allergen.title())
        
        return allergens
    
    def fetch_and_normalize_indian_products(self, limit: int = 1000) -> List[Dict]:
        """
        Fetch and normalize Indian products in one go
        """
        logger.info("=" * 80)
        logger.info("🇮🇳 OpenFoodFacts Indian Products Fetch & Normalize")
        logger.info("=" * 80)
        
        # Fetch raw products
        raw_products = self.fetch_indian_products(limit)
        
        # Normalize products
        logger.info(f"📊 Normalizing {len(raw_products)} products...")
        normalized_products = []
        
        for i, raw_product in enumerate(raw_products, 1):
            normalized = self.normalize_product(raw_product)
            if normalized:
                normalized_products.append(normalized)
            
            if i % 100 == 0:
                logger.info(f"   ✅ Normalized {i}/{len(raw_products)} products")
        
        logger.info(f"✅ Successfully normalized {len(normalized_products)} products")
        logger.info("=" * 80)
        
        return normalized_products
    
    def save_to_csv(self, products: List[Dict], filename: str = 'indian_products.csv'):
        """
        Save normalized products to CSV
        """
        if not products:
            logger.warning("No products to save")
            return
        
        logger.info(f"💾 Saving {len(products)} products to {filename}...")
        
        # Get all unique keys
        all_keys = set()
        for product in products:
            all_keys.update(product.keys())
        
        fieldnames = sorted(all_keys)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(products)
        
        logger.info(f"✅ Saved to {filename}")
    
    def save_to_json(self, products: List[Dict], filename: str = 'indian_products.json'):
        """
        Save normalized products to JSON
        """
        logger.info(f"💾 Saving {len(products)} products to {filename}...")
        
        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(products, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Saved to {filename}")
    
    def get_product_statistics(self, products: List[Dict]) -> Dict:
        """
        Get statistics about the products
        """
        if not products:
            return {}
        
        # Category distribution
        categories = {}
        brands = {}
        
        for product in products:
            category = product.get('category', 'uncategorized')
            brand = product.get('brand', 'Unknown')
            
            categories[category] = categories.get(category, 0) + 1
            brands[brand] = brands.get(brand, 0) + 1
        
        # Top categories and brands
        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]
        top_brands = sorted(brands.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # Nutrition stats
        with_nutrition = sum(1 for p in products if p.get('calories'))
        
        return {
            'total_products': len(products),
            'with_nutrition': with_nutrition,
            'unique_categories': len(categories),
            'unique_brands': len(brands),
            'top_categories': top_categories,
            'top_brands': top_brands,
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    fetcher = OpenFoodFactsIndiaFetcher()
    
    # Fetch and normalize 1000 Indian products
    products = fetcher.fetch_and_normalize_indian_products(limit=1000)
    
    # Save to files
    fetcher.save_to_csv(products, 'indian_fmcg_products.csv')
    fetcher.save_to_json(products, 'indian_fmcg_products.json')
    
    # Print statistics
    stats = fetcher.get_product_statistics(products)
    print("\n" + "=" * 80)
    print("📊 STATISTICS")
    print("=" * 80)
    print(f"Total Products: {stats['total_products']}")
    print(f"With Nutrition Data: {stats['with_nutrition']}")
    print(f"Unique Categories: {stats['unique_categories']}")
    print(f"Unique Brands: {stats['unique_brands']}")
    print("\nTop 10 Categories:")
    for category, count in stats['top_categories']:
        print(f"  • {category}: {count}")
    print("\nTop 20 Brands:")
    for brand, count in stats['top_brands'][:20]:
        print(f"  • {brand}: {count}")
    print("=" * 80)
