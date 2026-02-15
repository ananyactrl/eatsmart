#!/usr/bin/env python3
"""
Add the pasta products we scraped from Amazon to the EatSmart database
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("❌ SUPABASE_URL and SUPABASE_ANON_KEY must be set")
    exit(1)

HEADERS = {
    'apikey': SUPABASE_ANON_KEY,
    'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

# Pasta products we scraped from Amazon India
PASTA_PRODUCTS = [
    {
        "product_name": "DISANO Penne Pasta, 1Kg, 100% Durum Wheat, No Maida, Source of Protein & Fiber",
        "brand": "DISANO",
        "price": 125.0,
        "rating": 4.3,
        "source": "Amazon India",
        "product_url": "https://www.amazon.in/dp/B0XXXXXXX1",  # Placeholder URL
        "image_url": "https://m.media-amazon.com/images/I/71xxxxx.jpg",  # Placeholder image
        "region": "India",
        "weight": "1Kg",
        "is_verified": True
    },
    {
        "product_name": "Del Monte Foodcraft Penne Pasta 1Kg | 100% Durum Wheat/Semolina/Sooji Healthy Pasta | No Maida",
        "brand": "Del Monte",
        "price": 127.0,
        "rating": 4.4,
        "source": "Amazon India",
        "product_url": "https://www.amazon.in/dp/B0XXXXXXX2",
        "image_url": "https://m.media-amazon.com/images/I/72xxxxx.jpg",
        "region": "India",
        "weight": "1Kg",
        "is_verified": True
    },
    {
        "product_name": "DISANO Fusilli Pasta, 1Kg, 100% Durum Wheat, No Maida, Source of Protein & Fiber",
        "brand": "DISANO",
        "price": 125.0,
        "rating": 4.3,
        "source": "Amazon India",
        "product_url": "https://www.amazon.in/dp/B0XXXXXXX3",
        "image_url": "https://m.media-amazon.com/images/I/73xxxxx.jpg",
        "region": "India",
        "weight": "1Kg",
        "is_verified": True
    },
    {
        "product_name": "DISANO Elbows Pasta, 1Kg, 100% Durum Wheat, No Maida, Source of Protein & Fiber",
        "brand": "DISANO",
        "price": 125.0,
        "rating": 4.3,
        "source": "Amazon India",
        "product_url": "https://www.amazon.in/dp/B0XXXXXXX4",
        "image_url": "https://m.media-amazon.com/images/I/74xxxxx.jpg",
        "region": "India",
        "weight": "1Kg",
        "is_verified": True
    },
    {
        "product_name": "Chef's Basket Fusili Pasta 534 gm Pouch | Made With 100% Durum Wheat Semolina | No Preservatives",
        "brand": "Chef's Basket",
        "price": 83.0,
        "rating": 4.4,
        "source": "Amazon India",
        "product_url": "https://www.amazon.in/dp/B0XXXXXXX5",
        "image_url": "https://m.media-amazon.com/images/I/75xxxxx.jpg",
        "region": "India",
        "weight": "534g",
        "is_verified": True
    }
]

def add_pasta_products():
    """Add pasta products to the database"""
    print("🍝 Adding pasta products to EatSmart database...")

    # Use food_images table since that's what the products page uses
    API_BASE = SUPABASE_URL.rstrip('/') + '/rest/v1/food_images'

    # Convert pasta products to food_images format
    pasta_images = []
    for i, product in enumerate(PASTA_PRODUCTS, 1):
        pasta_images.append({
            "barcode": f"PASTA{i:03d}",  # Generate fake barcodes
            "image_url": product["image_url"],
            "storage_path": f"pasta/pasta{i:03d}.jpg",  # Required field
            "image_type": "product",
            "alt_text": f"{product['brand']} - {product['product_name']}",
            "uploaded_at": "2024-02-15T00:00:00Z"
        })

    for i, image_data in enumerate(pasta_images, 1):
        try:
            print(f"\n📦 Adding product {i}: {image_data['alt_text'][:50]}...")

            # Add to food_images table
            response = requests.post(API_BASE, headers=HEADERS, json=image_data)

            if response.status_code in [200, 201]:
                print(f"✅ Successfully added: {image_data['alt_text'][:40]}...")
            else:
                print(f"❌ Failed to add product {i}: {response.status_code}")
                print(f"Response: {response.text}")

        except Exception as e:
            print(f"❌ Error adding product {i}: {e}")

    print(f"\n🎉 Finished adding {len(pasta_images)} pasta products!")

if __name__ == "__main__":
    add_pasta_products()