"""
Test the new web scraping product search
"""
import requests
import json

BASE_URL = "http://localhost:3000"

def test_product_search():
    """Test searching for a product by name"""
    print("\n" + "="*60)
    print("🧪 TESTING PRODUCT SEARCH BY NAME")
    print("="*60)
    
    # Test with a common Indian product
    product_name = "Maggi Noodles"
    
    print(f"\n🔍 Searching for: {product_name}")
    
    response = requests.post(
        f"{BASE_URL}/search-product-by-name",
        json={
            "product_name": product_name,
            "max_results": 3
        }
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Search completed successfully!")
        print(f"Found: {data['found']}")
        print(f"Total results: {data['total_found']}")
        print(f"Sources searched: {', '.join(data['sources_searched'])}")
        
        if data['results']:
            print(f"\n📦 TOP 3 RESULTS:")
            for i, product in enumerate(data['results'][:3], 1):
                print(f"\n{i}. {product.get('product_name', 'N/A')}")
                print(f"   Brand: {product.get('brand', 'N/A')}")
                print(f"   Price: ₹{product.get('price', 'N/A')}")
                print(f"   Rating: {product.get('rating', 'N/A')}")
                print(f"   Source: {product.get('source', 'N/A')}")
                print(f"   URL: {product.get('product_url', 'N/A')[:80]}...")
            
            # Test getting detailed info for top match
            if data['results'][0].get('product_url'):
                print(f"\n{'='*60}")
                print("🔬 TESTING DETAILED PRODUCT INFO")
                print("="*60)
                
                top_url = data['results'][0]['product_url']
                print(f"Getting details from: {top_url[:80]}...")
                
                details_response = requests.post(
                    f"{BASE_URL}/get-product-details",
                    params={"product_url": top_url}
                )
                
                if details_response.status_code == 200:
                    details = details_response.json()
                    product = details['product']
                    
                    print(f"\n✅ Got detailed product info!")
                    print(f"Product: {product.get('product_name', 'N/A')}")
                    print(f"Brand: {product.get('brand', 'N/A')}")
                    print(f"Description: {product.get('description', 'N/A')[:100]}...")
                    
                    if product.get('nutrition'):
                        print(f"\n🥗 NUTRITION INFO:")
                        for key, value in product['nutrition'].items():
                            print(f"   {key}: {value}")
                    else:
                        print(f"\n⚠️ No nutrition info found on product page")
                    
                    if product.get('features'):
                        print(f"\n📋 FEATURES ({len(product['features'])}):")
                        for feature in product['features'][:3]:
                            print(f"   • {feature[:80]}...")
                else:
                    print(f"❌ Details request failed: {details_response.status_code}")
                    print(details_response.text)
        else:
            print("\n⚠️ No results found")
            if data.get('error'):
                print(f"Error: {data['error']}")
    else:
        print(f"❌ Request failed: {response.status_code}")
        print(response.text)
    
    print("\n" + "="*60)

if __name__ == "__main__":
    test_product_search()
