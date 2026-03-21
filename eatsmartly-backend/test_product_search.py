#!/usr/bin/env python3
"""
Test script to populate local database with products and test search
"""
import requests
import json

def test_product_search():
    """Test adding products and searching"""
    
    # Add some test products (like from Amazon)
    test_products = [
        {
            'name': 'Barilla Penne Pasta',
            'brand': 'Barilla',
            'barcode': '8076808000062',
            'source': 'amazon',
            'calories': 131,
            'protein_g': 5,
            'carbs_g': 25,
            'fat_g': 1.1,
            'sugar_g': 1.2
        },
        {
            'name': 'Maggi Noodles (Masala)',
            'brand': 'Maggi',
            'barcode': '8901234567890',
            'source': 'amazon',
            'calories': 380,
            'protein_g': 12,
            'carbs_g': 65,
            'fat_g': 9,
            'sugar_g': 2
        },
        {
            'name': 'Bournvita Chocolate Drink Powder',
            'brand': 'Bournvita',
            'source': 'amazon',
            'calories': 400,
            'protein_g': 8,
            'carbs_g': 70,
            'fat_g': 10,
            'sugar_g': 60
        },
        {
            'name': 'Fortune Pasta (Fusilli)',
            'brand': 'Fortune',
            'source': 'amazon',
            'calories': 128,
            'protein_g': 4.5,
            'carbs_g': 25,
            'fat_g': 1,
            'sugar_g': 1.5
        },
        {
            'name': 'Debonairs Pizza Masala',
            'brand': 'Debonairs',
            'source': 'amazon',
            'calories': 120,
            'protein_g': 5,
            'carbs_g': 20,
            'fat_g': 2
        }
    ]
    
    print("=" * 70)
    print("ADDING TEST PRODUCTS FROM AMAZON")
    print("=" * 70)
    
    for product in test_products:
        try:
            response = requests.post('http://localhost:8000/add-product', json=product)
            if response.status_code == 200:
                result = response.json()
                product_id = result.get('product_id')
                name = product['name']
                print(f"✅ Added: {name} (ID: {product_id})")
            else:
                name = product['name']
                print(f"❌ Failed: {name} - {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print("=" * 70)
    print("DATABASE STATUS")
    print("=" * 70)
    
    try:
        response = requests.get('http://localhost:8000/local-products/count')
        if response.status_code == 200:
            count_data = response.json()
            total = count_data.get('total_local_products', 0)
            print(f"✅ {count_data['message']}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    print("=" * 70)
    print("TESTING SEARCH - Query: 'pasta'")
    print("=" * 70)
    
    try:
        response = requests.post('http://localhost:8000/search-products', 
                               json={'query': 'pasta', 'limit': 10})
        if response.status_code == 200:
            result = response.json()
            query = result.get('query')
            total = result.get('total_results', 0)
            sources = result.get('sources', [])
            
            print(f"Query: '{query}'")
            print(f"Results: {total}")
            print(f"Sources: {', '.join(sources)}")
            print()
            
            if result.get('results'):
                print("Products found:")
                for i, product in enumerate(result['results'][:5], 1):
                    name = product.get('name', 'Unknown')
                    brand = product.get('brand', 'No brand')
                    source = product.get('source', 'unknown')
                    print(f"  {i}. {name} ({brand}) - from {source}")
            else:
                print("No products found")
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(response.text[:200])
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_product_search()
