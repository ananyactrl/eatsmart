"""
Amazon India Product Scraper
Searches Amazon.in for products and extracts nutrition information
"""
import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Rotate user agents to avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def get_headers():
    """Get randomized headers for requests"""
    import random
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-IN,en;q=0.9,hi;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none'
    }

def search_amazon_india(product_name: str, max_results: int = 5) -> List[Dict]:
    """
    Search Amazon India for products matching the given name
    
    Args:
        product_name: Name of product to search for
        max_results: Maximum number of results to return (default 5)
        
    Returns:
        List of product dictionaries with basic info
    """
    try:
        logger.info(f"🔍 Searching Amazon India for: {product_name}")
        
        # Format search query
        search_query = product_name.replace(' ', '+')
        search_url = f"https://www.amazon.in/s?k={search_query}"
        
        # Make request
        response = requests.get(
            search_url,
            headers=get_headers(),
            timeout=10
        )
        
        if response.status_code != 200:
            logger.warning(f"Amazon returned status code: {response.status_code}")
            return []
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')
        products = []
        
        # Find all product cards
        product_cards = soup.find_all('div', {'data-component-type': 's-search-result'})
        logger.info(f"Found {len(product_cards)} product cards on Amazon")
        
        for card in product_cards[:max_results]:
            try:
                # Extract ASIN (Amazon product ID)
                asin = card.get('data-asin')
                if not asin:
                    continue
                
                # Extract title
                title_elem = card.find('h2', class_='a-size-base-plus')
                if not title_elem:
                    # Fallback to any h2
                    h2s = card.find_all('h2')
                    if h2s:
                        # Take the h2 with the longest text (usually the main title)
                        title_elem = max(h2s, key=lambda h: len(h.get_text(strip=True)))
                title = title_elem.get_text(strip=True) if title_elem else None
                
                if not title:
                    continue
                
                # Extract price
                price_elem = card.find('span', class_='a-price-whole')
                price = None
                if price_elem:
                    price_text = price_elem.get_text(strip=True).replace(',', '')
                    try:
                        price = float(price_text)
                    except ValueError:
                        pass
                
                # Extract rating
                rating_elem = card.find('span', class_='a-icon-alt')
                rating = None
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    match = re.search(r'(\d+\.?\d*)', rating_text)
                    if match:
                        try:
                            rating = float(match.group(1))
                        except ValueError:
                            pass
                
                # Extract image
                img_elem = card.find('img', class_='s-image')
                image_url = img_elem.get('src') if img_elem else None
                
                # Build product URL
                product_url = f"https://www.amazon.in/dp/{asin}"
                
                # Extract brand (sometimes in title)
                brand = None
                brand_elem = card.find('span', class_='a-size-base-plus')
                if brand_elem:
                    brand = brand_elem.get_text(strip=True)
                
                products.append({
                    'source': 'Amazon India',
                    'product_name': title,
                    'brand': brand,
                    'price': price,
                    'rating': rating,
                    'image_url': image_url,
                    'product_url': product_url,
                    'asin': asin,
                    'confidence': 0.8  # Base confidence for Amazon results
                })
                
                logger.info(f"✅ Found: {title[:50]}... (₹{price if price else 'N/A'})")
                
            except Exception as e:
                logger.error(f"Error parsing product card: {e}")
                continue
        
        logger.info(f"✅ Returning {len(products)} products from Amazon India")
        return products
        
    except requests.exceptions.Timeout:
        logger.error("Amazon request timed out")
        return []
    except Exception as e:
        logger.error(f"Error searching Amazon India: {e}")
        return []

def get_amazon_product_details(product_url: str) -> Optional[Dict]:
    """
    Get detailed product information from Amazon product page
    
    Args:
        product_url: Full URL to Amazon product page
        
    Returns:
        Dictionary with detailed product info including nutrition
    """
    try:
        logger.info(f"📦 Getting Amazon product details from: {product_url}")
        
        # Add rate limiting to be polite
        time.sleep(1)
        
        response = requests.get(
            product_url,
            headers=get_headers(),
            timeout=15
        )
        
        if response.status_code != 200:
            logger.warning(f"Amazon returned status code: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Extract product title
        title_elem = soup.find('span', id='productTitle')
        product_name = title_elem.get_text(strip=True) if title_elem else None
        
        # Extract brand
        brand_elem = soup.find('a', id='bylineInfo')
        if not brand_elem:
            brand_elem = soup.find('span', class_='a-size-base po-break-word')
        brand = None
        if brand_elem:
            brand_text = brand_elem.get_text(strip=True)
            brand = brand_text.replace('Visit the ', '').replace(' Store', '').strip()
        
        # Extract image
        image_elem = soup.find('img', id='landingImage')
        if not image_elem:
            image_elem = soup.find('img', class_='a-dynamic-image')
        image_url = image_elem.get('src') if image_elem else None
        
        # Extract price
        price_elem = soup.find('span', class_='a-price-whole')
        price = None
        if price_elem:
            try:
                price = float(price_elem.get_text(strip=True).replace(',', ''))
            except ValueError:
                pass
        
        # Extract rating
        rating_elem = soup.find('span', class_='a-icon-alt')
        rating = None
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            match = re.search(r'(\d+\.?\d*)', rating_text)
            if match:
                try:
                    rating = float(match.group(1))
                except ValueError:
                    pass
        
        # Extract description
        desc_elem = soup.find('div', id='productDescription')
        description = None
        if desc_elem:
            desc_p = desc_elem.find('p')
            if desc_p:
                description = desc_p.get_text(strip=True)
        
        # Extract features (bullet points)
        features = []
        feature_div = soup.find('div', id='feature-bullets')
        if feature_div:
            feature_items = feature_div.find_all('span', class_='a-list-item')
            for item in feature_items:
                feature_text = item.get_text(strip=True)
                if feature_text and len(feature_text) > 10:  # Skip empty/short items
                    features.append(feature_text)
        
        # Extract specifications
        specifications = {}
        spec_table = soup.find('table', id='productDetails_techSpec_section_1')
        if spec_table:
            rows = spec_table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    key = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    specifications[key] = value
        
        # Extract nutrition information (CRITICAL FOR YOUR APP!)
        nutrition = extract_nutrition_from_page(soup)
        
        product_details = {
            'source': 'Amazon India',
            'product_name': product_name,
            'brand': brand,
            'image_url': image_url,
            'price': price,
            'rating': rating,
            'description': description,
            'features': features,
            'specifications': specifications,
            'nutrition': nutrition,
            'product_url': product_url
        }
        
        logger.info(f"✅ Extracted details for: {product_name}")
        if nutrition:
            logger.info(f"✅ Found nutrition info: {list(nutrition.keys())}")
        
        return product_details
        
    except requests.exceptions.Timeout:
        logger.error("Amazon product page request timed out")
        return None
    except Exception as e:
        logger.error(f"Error getting Amazon product details: {e}")
        return None

def extract_nutrition_from_page(soup: BeautifulSoup) -> Optional[Dict]:
    """
    Extract nutrition information from Amazon product page
    
    Args:
        soup: BeautifulSoup object of product page
        
    Returns:
        Dictionary with nutrition values or None
    """
    nutrition = {}
    
    try:
        # Look for nutrition tables in various sections
        sections_to_check = [
            soup.find('div', id='important-information'),
            soup.find('div', id='productDescription'),
            soup.find('div', class_='a-section content')
        ]
        
        for section in sections_to_check:
            if not section:
                continue
            
            # Look for text containing nutrition keywords
            section_text = section.get_text().lower()
            
            # Check if this section contains nutrition info
            if not any(keyword in section_text for keyword in ['nutrition', 'energy', 'protein', 'carbohydrate']):
                continue
            
            # Try to extract from table
            tables = section.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True).lower()
                        value_text = cells[1].get_text(strip=True)
                        
                        # Extract numeric value
                        match = re.search(r'(\d+\.?\d*)', value_text)
                        if match:
                            try:
                                value = float(match.group(1))
                                
                                # Map to standard nutrition keys
                                if 'energy' in key or 'calor' in key:
                                    nutrition['calories'] = value
                                elif 'protein' in key:
                                    nutrition['protein'] = value
                                elif 'fat' in key and 'saturated' not in key:
                                    nutrition['totalFat'] = value
                                elif 'saturated' in key:
                                    nutrition['saturatedFat'] = value
                                elif 'carbohydrate' in key or 'carbs' in key:
                                    nutrition['carbs'] = value
                                elif 'sugar' in key:
                                    nutrition['sugars'] = value
                                elif 'fiber' in key or 'fibre' in key:
                                    nutrition['fiber'] = value
                                elif 'sodium' in key or 'salt' in key:
                                    nutrition['sodium'] = value
                                    
                            except ValueError:
                                continue
            
            # If found nutrition info in this section, break
            if nutrition:
                break
        
        return nutrition if nutrition else None
        
    except Exception as e:
        logger.error(f"Error extracting nutrition: {e}")
        return None
