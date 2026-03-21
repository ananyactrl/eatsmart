"""
Local Product Database - Fallback when Supabase is unavailable
Stores products as JSON for persistent local search capability
"""
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LocalProductDB:
    """Local JSON-based product database for persistence"""
    
    def __init__(self, db_file: str = "data/local_products.json"):
        self.db_file = Path(db_file)
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create database file if it doesn't exist"""
        if not self.db_file.exists():
            self._save({})
    
    def _load(self) -> Dict[str, List[Dict]]:
        """Load all products from JSON file"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load local products: {e}")
            return {}
    
    def _save(self, data: Dict):
        """Save products to JSON file"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save local products: {e}")
    
    def add_product(self, product: Dict[str, Any]) -> str:
        """
        Add or update a product
        Returns: product ID
        """
        data = self._load()
        products = data.get('products', [])
        
        # Generate ID if not present
        if 'id' not in product:
            product['id'] = f"local_{datetime.now().timestamp()}"
        
        # Check if product already exists
        existing_idx = next(
            (i for i, p in enumerate(products) if p.get('id') == product['id']),
            -1
        )
        
        # Add source and timestamp
        product['source'] = product.get('source', 'local_import')
        product['added_at'] = datetime.now().isoformat()
        
        if existing_idx >= 0:
            products[existing_idx] = product
        else:
            products.append(product)
        
        data['products'] = products
        data['updated_at'] = datetime.now().isoformat()
        self._save(data)
        
        logger.info(f"Saved product: {product.get('name')} (ID: {product['id']})")
        return product['id']
    
    def add_products_bulk(self, products: List[Dict[str, Any]]) -> int:
        """Add multiple products at once. Returns count added"""
        count = 0
        for product in products:
            try:
                self.add_product(product)
                count += 1
            except Exception as e:
                logger.warning(f"Could not add product {product.get('name')}: {e}")
        return count
    
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search products by name, brand, or ingredients
        Returns sorted list: exact matches first, then partial matches
        """
        data = self._load()
        products = data.get('products', [])
        query_lower = query.lower()
        
        results = []
        for product in products:
            name = (product.get('name') or '').lower()
            brand = (product.get('brand') or '').lower()
            ingredients = (product.get('ingredients') or '').lower()
            
            # Score based on match quality
            score = 0
            if name == query_lower:
                score = 100  # Exact match
            elif name.startswith(query_lower):
                score = 80   # Starts with
            elif query_lower in name:
                score = 60   # Contains in name
            elif query_lower in brand:
                score = 40   # Found in brand
            elif query_lower in ingredients:
                score = 20   # Found in ingredients
            
            if score > 0:
                product_copy = product.copy()
                product_copy['_search_score'] = score
                results.append(product_copy)
        
        # Sort by score (highest first)
        results.sort(key=lambda p: p.get('_search_score', 0), reverse=True)
        
        # Remove score from final results and limit
        for p in results:
            p.pop('_search_score', None)
        
        return results[:limit]
    
    def get_by_barcode(self, barcode: str) -> Optional[Dict[str, Any]]:
        """Find product by barcode"""
        data = self._load()
        products = data.get('products', [])
        
        for product in products:
            if product.get('barcode') == barcode:
                return product
        return None
    
    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all products, optionally limited"""
        data = self._load()
        products = data.get('products', [])
        
        if limit:
            return products[:limit]
        return products
    
    def count(self) -> int:
        """Get total number of products"""
        data = self._load()
        return len(data.get('products', []))
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a product by ID"""
        data = self._load()
        products = data.get('products', [])
        
        initial_count = len(products)
        products = [p for p in products if p.get('id') != product_id]
        
        if len(products) < initial_count:
            data['products'] = products
            data['updated_at'] = datetime.now().isoformat()
            self._save(data)
            return True
        
        return False


# Global instance
local_db = LocalProductDB()
