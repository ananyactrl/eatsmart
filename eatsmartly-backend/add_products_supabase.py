"""
Add or update products in Supabase with nutrition data.
Supports both bulk product imports and individual products with detailed nutrition facts.

Usage:
  - Ensure SUPABASE_URL and SUPABASE_ANON_KEY are set in your environment or .env
  - python add_products_supabase.py
  
To add a product with nutrition:
  - Use add_product_with_nutrition(product_data, nutrition_data) function
"""
import os
import sys
import requests
import logging
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import brand scrapers
try:
    from scrapers.brand_scrapers import scrape_all_brands
except ImportError:
    # If import fails, we'll just use the hardcoded products list
    scrape_all_brands = None
    logging.warning("Could not import brand_scrapers. Will use hardcoded products only.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    logger.error("SUPABASE_URL and SUPABASE_ANON_KEY must be set in the environment.")
    raise SystemExit(1)

# Use the anon/public key for client-like requests as requested
HEADERS = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

# Try 'products' table first (as suggested by Supabase error), fallback to 'food_products'
API_BASE = SUPABASE_URL.rstrip('/') + '/rest/v1/products'
API_BASE_NUTRITION = SUPABASE_URL.rstrip('/') + '/rest/v1/nutrition_facts'

# Products to add/update (you can extend this list)
PRODUCTS = [
    {
        'name': 'Disano Whole Wheat Pasta',
        'brand': 'Disano',
        'category': 'Pasta',
        'source': 'manual',
        'official_website': 'https://disanofoods.com/',
        'product_page_url': 'https://disanofoods.com/',
        'is_indian_product': True
    },
    {
        'name': 'Barilla Whole Wheat Pasta',
        'brand': 'Barilla',
        'category': 'Pasta',
        'source': 'manual',
        'official_website': 'https://www.barilla.com/',
        'product_page_url': 'https://www.barilla.com/',
        'is_indian_product': False
    },
    {
        'name': 'Eco Life / Eco Valley Multigrain Pasta',
        'brand': 'Eco Life (Eco Valley)',
        'category': 'Pasta',
        'source': 'manual',
        'official_website': 'https://ecovalley.in/',
        'product_page_url': 'https://ecovalley.in/',
        'is_indian_product': True
    },
    {
        'name': 'BORGES Whole Wheat Pasta',
        'brand': 'BORGES',
        'category': 'Pasta',
        'source': 'manual',
        'official_website': 'https://www.borges-international.com/',
        'product_page_url': 'https://www.borges-international.com/',
        'is_indian_product': False
    },
    {
        'name': 'Organic Tattva Millet Pasta',
        'brand': 'Organic Tattva',
        'category': 'Pasta',
        'source': 'manual',
        'official_website': 'https://organictattva.com/',
        'product_page_url': 'https://organictattva.com/',
        'is_indian_product': True
    },
    {
        'name': '24 Mantra Organic Pasta',
        'brand': '24 Mantra Organic',
        'category': 'Pasta',
        'source': 'manual',
        'official_website': 'https://www.24mantra.com/',
        'product_page_url': 'https://www.24mantra.com/',
        'is_indian_product': True
    },
    {
        'name': 'Yogabar Multigrain Pasta',
        'brand': 'Yogabar',
        'category': 'Pasta',
        'source': 'manual',
        'official_website': 'https://yogabar.in/',
        'product_page_url': 'https://yogabar.in/',
        'is_indian_product': True
    },
    {
        'name': 'Slurrp Farm Millet Pasta',
        'brand': 'Slurrp Farm',
        'category': 'Pasta',
        'source': 'manual',
        'official_website': 'https://www.slurrpfarm.com/',
        'product_page_url': 'https://www.slurrpfarm.com/',
        'is_indian_product': True
    }
]


def add_product_with_nutrition(product_data, nutrition_data=None):
    """
    Add a single product with optional nutrition data to the database.
    
    Args:
        product_data (dict): Product info matching products table schema
            - product_name, brand, category, manufacturer, region, weight
            - fssai_license, image_url, barcode (optional)
        nutrition_data (dict, optional): Nutrition info for nutrition_facts table
            - serving_size, calories, protein, carbs, fat, fiber, etc.
    
    Returns:
        dict: Result with product and nutrition IDs
    """
    """
    Insert a product using the actual products table schema.
    Maps old field names to new schema: product_name, brand, category, etc.
    """
    # Map to actual products table schema
    product_record = {
        'product_name': product.get('name'),
        'brand': product.get('brand'),
        'category': product.get('category'),
        'manufacturer': product.get('manufacturer'),
        'region': product.get('region'),
        'weight': product.get('weight'),
        'fssai_license': product.get('fssai_license'),
        'image_url': product.get('image_url') or product.get('official_website'),
        'barcode': product.get('barcode')
    }
    
    # Remove None values
    product_record = {k: v for k, v in product_record.items() if v is not None}
    
    r = requests.post(API_BASE, headers=HEADERS, json=product_record
            'product_id': product_id,
            'serving_size': nutrition_data.get('serving_size', '100g'),
            'servings_per_container': nutrition_data.get('servings_per_container'),
            'calories': int(nutrition_data.get('calories', 0)),
            'total_fat': nutrition_data.get('total_fat'),
            'saturated_fat': nutrition_data.get('saturated_fat'),
            'trans_fat': nutrition_data.get('trans_fat'),
            'cholesterol': nutrition_data.get('cholesterol'),
            'sodium': nutrition_data.get('sodium'),
            'total_carbohydrates': nutrition_data.get('total_carbohydrates'),
            'dietary_fiber': nutrition_data.get('dietary_fiber'),
            'total_sugars': nutrition_data.get('total_sugars'),
            'added_sugars': nutrition_data.get('added_sugars'),
            'protein': nutrition_data.get('protein'),
            'confidence': nutrition_data.get('confidence', 'manual')
        }
        
        r_nutrition = requests.post(API_BASE_NUTRITION, headers=HEADERS, json=nutrition_record)
        
        if r_nutrition.status_code in (200, 201):
            nutrition_result = r_nutrition.json()
            logger.info(f"✅ Nutrition data added!")
            return {'product': result[0], 'nutrition': nutrition_result[0] if nutrition_result else None}
        else:
            logger.error(f"⚠️  Failed to add nutrition: {r_nutrition.status_code} - {r_nutrition.text}")
            return {'product': result[0], 'nutrition': None}
    
    return {'product': result[0], 'nutrition': None}


def supabase_get_by_url(url):
    # Try to filter by url field (not product_page_url)
    filter_url = quote_plus(f"url=eq.{url}")
    q = f"{API_BASE}?{filter_url}&select=id,url"
    r = requests.get(q, headers=HEADERS)
    if r.status_code != 200:
        # If url column doesn't exist, try name as secondary check
        logger.debug(f"GET query failed: {r.status_code} {r.text}")
        return None
    data = r.json()
    return data[0] if data else None


def supabase_insert(product):
    # Only send fields that definitely exist in the products table
    # Most Supabase product tables have: name, brand, category, source at minimum
    minimal_product = {
        'name': product['name'],
        'brand': product['brand'],
    }
    
    # Add optional fields if they exist in the schema
    if product.get('category'):
        minimal_product['category'] = product['category']
    if product.get('source'):
        minimal_product['source'] = product['source']
    if product.get('official_website'):
        minimal_product['url'] = product.get('official_website')  # Use 'url' not 'official_website'
    
    r = requests.post(API_BASE, headers=HEADERS, json=minimal_product)
    if r.status_code not in (200, 201):
        logger.error(f"Insert failed: {r.status_code} {r.text}")
        return None
    return r.json()[0] if r.json() else None


def supabase_update(product_id, product):
    url = f"{API_BASE}?id=eq.{product_id}"
    r = requests.patch(url, headers=HEADERS, json=product)
    if r.status_code not in (200, 204):
        logger.error(f"Update failed: {r.status_code} {r.text}")
        return None
    # fetch updated
    r2 = requests.get(f"{API_BASE}?id=eq.{product_id}&select=*")
    if r2.status_code == 200:
        return r2.json()[0]
    return None


def main():
    print("\n" + "="*60)
    print("BRAND PRODUCT SCRAPER & DATABASE IMPORTER")
    print("="*60)
    
    # Try to scrape products from brand websites
    scraped_products = []
    if scrape_all_brands:
        print("\n🔍 Scraping products from brand websites...")
        print("  - Disano Foods (https://disanofoods.com/)")
        print("  - Organic Tattva (https://organictattva.com/)")
        print("  - Barilla (https://www.barilla.com/)")
        print()
        
        try:
            products_by_brand = scrape_all_brands(max_per_brand=30)
            
            # Flatten the products list
            for brand, products in products_by_brand.items():
                for product in products:
                    # Convert scraped product to database format
                    scraped_products.append({
                        'name': product['name'],
                        'brand': product['brand'],
                        'category': product.get('category', 'Food'),
                        'source': product['source'],
                        'official_website': product.get('official_website'),
                        'product_page_url': product.get('product_url'),
                        'is_indian_product': product.get('is_indian_product', False)
                    })
            
            logger.info(f"\n✅ Scraped {len(scraped_products)} products from brand websites")
        except Exception as e:
            logger.error(f"❌ Error during scraping: {e}")
            logger.info("Falling back to hardcoded products list")
    else:
        logger.info("⚠️  Brand scrapers not available, using hardcoded products only")
    
    # Combine scraped products with hardcoded ones
    all_products = scraped_products + PRODUCTS if scraped_products else PRODUCTS
    
    print(f"\n📦 Processing {len(all_products)} total products...")
    print("="*60 + "\n")
    
    stats = {'added': 0, 'updated': 0, 'failed': 0}
    
    for i, p in enumerate(all_products, 1):
        logger.info(f"[{i}/{len(all_products)}] Processing: {p['brand']} - {p['name'][:50]}...")
        
        try:
            existing = supabase_get_by_url(p['product_page_url'])
            if existing:
                pid = existing['id']
                logger.info(f"  ↻ Found existing product id={pid}, updating...")
                updated = supabase_update(pid, p)
                if updated:
                    logger.info(f"  ✅ Updated successfully")
                    stats['updated'] += 1
                else:
                    logger.error(f"  ❌ Update failed")
                    stats['failed'] += 1
            else:
                inserted = supabase_insert(p)
                if inserted:
                    logger.info(f"  ✅ Inserted new product (ID: {inserted.get('id')})")
                    stats['added'] += 1
                else:
                    logger.error(f"  ❌ Insert failed")
                    stats['failed'] += 1
        except Exception as e:
            logger.error(f"  ❌ Error processing product: {e}")
            stats['failed'] += 1
    
    # Print summary
    print("\n" + "="*60)
    print("IMPORT SUMMARY")
    print("="*60)
    print(f"Total processed:      {len(all_products)}")
    print(f"New products added:   {stats['added']}")
    print(f"Existing updated:     {stats['updated']}")
    print(f"Failed:               {stats['failed']}")
    print(f"Success rate:         {((stats['added'] + stats['updated']) / len(all_products) * 100):.1f}%")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
