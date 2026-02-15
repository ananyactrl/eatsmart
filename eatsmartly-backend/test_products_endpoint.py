import requests

response = requests.get('http://localhost:8000/products?limit=10')
print('Status:', response.status_code)

if response.status_code == 200:
    data = response.json()
    print('Total products:', data.get('total', 0))
    print('Products found:', len(data.get('products', [])))
    print('Regions:', data.get('regions', []))
    print('Brands:', data.get('brands', []))

    if data.get('products'):
        print('\nFirst 3 products:')
        for i, product in enumerate(data['products'][:3], 1):
            name = product.get('product_name', 'N/A')
            print(f'{i}. {name[:50]}...')
            print(f'   Brand: {product.get("brand", "N/A")}')
            print(f'   Region: {product.get("region", "N/A")}')
            print(f'   Weight: {product.get("weight", "N/A")}')
            print(f'   Verified: {product.get("is_verified", "N/A")}')
            print()