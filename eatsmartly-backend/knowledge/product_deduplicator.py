"""
Product Deduplication and Grouping Module
Groups similar products and removes redundant results
"""
import logging
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
import re

logger = logging.getLogger(__name__)


class ProductDeduplicator:
    """Groups and deduplicates similar products"""
    
    # Similarity threshold (0-1) for considering products as duplicates
    EXACT_MATCH_THRESHOLD = 0.95  # Exact match or very close
    SIMILAR_MATCH_THRESHOLD = 0.80  # Similar variant
    
    # Keywords that indicate variant types (not unique products)
    VARIANT_KEYWORDS = {
        'zero', 'diet', 'light', 'lite', 'extra', 'original', 'classic',
        'new', 'mini', 'large', 'xl', 'jumbo', 'pack', 'bottle', 'can',
        'jar', 'box', 'sachet', 'stick', 'bar', 'pouch', 'bulk', 'combo',
        'sugar free', 'no sugar', 'low fat', 'fat free', 'organic', 'natural',
        '100g', '200g', '500g', '1kg', '500ml', '1l', 'strawberry', 'vanilla',
        'chocolate', 'caramel', 'coffee', 'mango', 'apple', 'orange', 'cherry'
    }
    
    @staticmethod
    def normalize_product_name(name: str) -> str:
        """
        Normalize product name for comparison
        Removes brand, variant info for core matching
        """
        if not name:
            return ""
        
        name_lower = name.lower().strip()
        
        # Remove common quantity indicators
        name_lower = re.sub(r'\b(pack of|box of|set of|bottle|can|jar|sachet|pouch|box|kg|g|ml|l)\b', '', name_lower)
        
        # Remove parentheses and brackets content
        name_lower = re.sub(r'\([^)]*\)', '', name_lower)
        name_lower = re.sub(r'\[[^\]]*\]', '', name_lower)
        
        # Remove multiple spaces
        name_lower = re.sub(r'\s+', ' ', name_lower).strip()
        
        return name_lower
    
    @staticmethod
    def extract_core_product_name(name: str) -> str:
        """
        Extract core product name without variants
        Example: "Coca Cola Zero Sugar" -> "Coca Cola"
        """
        if not name:
            return ""
        
        name_lower = ProductDeduplicator.normalize_product_name(name)
        words = name_lower.split()
        
        # Remove variant keywords from the end
        core_words = []
        for word in words:
            if word not in ProductDeduplicator.VARIANT_KEYWORDS:
                core_words.append(word)
            # If we encounter a variant keyword, stop adding to core
            # (variants typically at the end)
            elif core_words:  # Only stop if we already have some core words
                break
        
        core_name = ' '.join(core_words) if core_words else name_lower
        return core_name.strip()
    
    @staticmethod
    def similarity_score(name1: str, name2: str) -> float:
        """
        Calculate similarity between two product names (0-1)
        """
        norm1 = ProductDeduplicator.normalize_product_name(name1)
        norm2 = ProductDeduplicator.normalize_product_name(name2)
        
        if norm1 == norm2:
            return 1.0
        
        matcher = SequenceMatcher(None, norm1, norm2)
        return matcher.ratio()
    
    @staticmethod
    def are_same_product(name1: str, name2: str, brand1: Optional[str] = None, 
                        brand2: Optional[str] = None, threshold: float = 0.85) -> bool:
        """
        Determine if two products are the same (possibly different variants)
        """
        # Extract core product names
        core1 = ProductDeduplicator.extract_core_product_name(name1)
        core2 = ProductDeduplicator.extract_core_product_name(name2)
        
        # Check name similarity
        score = ProductDeduplicator.similarity_score(core1, core2)
        
        if score >= threshold:
            # If names are similar, check if brands match (if provided)
            if brand1 and brand2:
                brand_match = ProductDeduplicator.similarity_score(brand1, brand2) > 0.8
                return brand_match if brand_match else True  # If only names match, still same product
            return True
        
        return False
    
    @staticmethod
    def group_products(products: List[Dict]) -> List[List[Dict]]:
        """
        Group similar products together
        Returns list of groups, where each group contains similar products
        """
        if not products:
            return []
        
        groups: List[List[Dict]] = []
        used_indices = set()
        
        for i, product in enumerate(products):
            if i in used_indices:
                continue
            
            # Start a new group with this product
            group = [product]
            used_indices.add(i)
            
            # Find all similar products
            for j in range(i + 1, len(products)):
                if j in used_indices:
                    continue
                
                if ProductDeduplicator.are_same_product(
                    product.get('name', ''),
                    products[j].get('name', ''),
                    product.get('brand'),
                    products[j].get('brand'),
                    threshold=0.80
                ):
                    group.append(products[j])
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
    
    @staticmethod
    def select_best_from_group(group: List[Dict]) -> Dict:
        """
        Select the best product from a group of similar/duplicate products
        Priority: Most complete data, highest calories, brand name present
        """
        if not group:
            return {}
        
        if len(group) == 1:
            return group[0]
        
        def score_product(product: Dict) -> Tuple[int, int, int]:
            """
            Score a product for selection
            Returns (completeness_score, has_brand, has_calories, has_ingredients)
            """
            completeness = sum(1 for v in product.values() if v is not None and v != '')
            has_brand = 1 if product.get('brand') else 0
            has_calories = 1 if product.get('calories') else 0
            has_ingredients = 1 if product.get('ingredients') else 0
            
            return (completeness, has_brand, has_calories, has_ingredients)
        
        # Sort by scoring function (higher score = better product)
        sorted_group = sorted(group, key=score_product, reverse=True)
        return sorted_group[0]
    
    @staticmethod
    def deduplicate_results(products: List[Dict], max_per_group: int = 2) -> List[Dict]:
        """
        Deduplicate search results
        
        Args:
            products: List of product dictionaries
            max_per_group: Maximum number of variants to keep per product (default: 2)
                          Set to 1 for strict deduplication
        
        Returns:
            Deduplicated product list
        """
        if not products:
            return []
        
        logger.info(f"🔍 Deduplicating {len(products)} products...")
        
        # Group similar products
        groups = ProductDeduplicator.group_products(products)
        logger.info(f"   📊 Found {len(groups)} unique product groups")
        
        # Select best from each group + optional variants
        deduplicated = []
        
        for group in groups:
            # Always add the best product from the group
            best = ProductDeduplicator.select_best_from_group(group)
            deduplicated.append(best)
            
            # Optionally add up to (max_per_group - 1) other variants
            if max_per_group > 1 and len(group) > 1:
                # Sort remaining products by source preference and completeness
                remaining = [p for p in group if p != best]
                
                # Prefer different sources for variants
                source_buckets = {}
                for product in remaining:
                    source = product.get('source', 'unknown')
                    if source not in source_buckets:
                        source_buckets[source] = []
                    source_buckets[source].append(product)
                
                # Add variants from different sources (up to max_per_group - 1)
                variants_added = 0
                for source in source_buckets:
                    if variants_added >= max_per_group - 1:
                        break
                    for variant in source_buckets[source]:
                        if variants_added >= max_per_group - 1:
                            break
                        deduplicated.append(variant)
                        variants_added += 1
        
        logger.info(f"   ✅ Deduplicated to {len(deduplicated)} results")
        return deduplicated


def deduplicate_search_results(products: List[Dict], 
                               strict_mode: bool = False,
                               max_variants: int = 2) -> List[Dict]:
    """
    Convenience function to deduplicate search results
    
    Args:
        products: List of product results from search
        strict_mode: If True, only return best match per product (max_variants=1)
        max_variants: Maximum number of variants per product to keep
    
    Returns:
        Deduplicated product list
    """
    if strict_mode:
        max_variants = 1
    
    return ProductDeduplicator.deduplicate_results(products, max_per_group=max_variants)
