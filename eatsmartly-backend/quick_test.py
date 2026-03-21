from knowledge.local_product_db import local_db

# Add test products from Amazon
products = [
    {'name': 'Barilla Penne Pasta', 'brand': 'Barilla', 'calories': 131, 'source': 'amazon'},
    {'name': 'Maggi Noodles Masala', 'brand': 'Maggi', 'calories': 380, 'source': 'amazon'},
    {'name': 'Bournvita Chocolate', 'brand': 'Bournvita', 'calories': 400, 'source': 'amazon'},
    {'name': 'Fortune Pasta Fusilli', 'brand': 'Fortune', 'calories': 128, 'source': 'amazon'},
    {'name': 'Debonairs Pizza Masala', 'brand': 'Debonairs', 'calories': 120, 'source': 'amazon'},
]

print('Adding products to local database...')
for p in products:
    local_db.add_product(p)
    print(f'  Added: {p["name"]}')

print()
print(f'Total products in database: {local_db.count()}')
print()
print('SEARCH TEST - Query: "pasta"')
print('-' * 50)
results = local_db.search('pasta', limit=10)
for r in results:
    name = r.get('name', 'Unknown')
    brand = r.get('brand', 'No brand')
    source = r.get('source', 'unknown')
    print(f'  {name} ({brand}) - from {source}')
