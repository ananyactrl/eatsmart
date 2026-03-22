"""
Test script to verify Google Cloud Vision API integration.
Creates a simple test image with text and verifies both endpoints work.
"""
import requests
import io
from PIL import Image, ImageDraw, ImageFont

def create_test_image():
    """Create a simple test image with nutrition label text."""
    # Create a white background
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add nutrition text
    text_lines = [
        "Nutrition Facts",
        "Serving Size: 100g",
        "Calories: 250",
        "Protein: 12g",
        "Carbohydrates: 30g",
        "Fat: 8g",
        "Sugar: 5g",
        "Fiber: 3g",
        "Sodium: 200mg"
    ]
    
    y = 20
    for line in text_lines:
        draw.text((20, y), line, fill='black')
        y += 25
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def test_extract_text():
    """Test the /extract-text endpoint."""
    print("\n" + "="*60)
    print("Testing /extract-text endpoint (Vision API Text Detection)")
    print("="*60)
    
    img_bytes = create_test_image()
    
    try:
        response = requests.post(
            'http://localhost:8000/extract-text',
            files={'file': ('test_label.png', img_bytes, 'image/png')},
            timeout=30
        )
        
        if response.ok:
            result = response.json()
            print(f"\n✅ Success! API used: {result.get('api_used', 'unknown')}")
            print(f"📝 Extracted {result.get('word_count', 0)} words")
            print(f"\nExtracted text preview:")
            text = result.get('extracted_text', '')
            print(text[:200] + ('...' if len(text) > 200 else ''))
            
            if 'vision_usage' in result:
                usage = result['vision_usage']
                print(f"\n📊 Vision API Usage:")
                print(f"   Units used: {usage['units_used']}/{usage.get('units_remaining', 0) + usage['units_used']}")
                print(f"   Percentage: {usage['percentage_used']}%")
            
            return True
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_detect_product():
    """Test the /detect-product endpoint."""
    print("\n" + "="*60)
    print("Testing /detect-product endpoint (Vision API Label Detection)")
    print("="*60)
    
    img_bytes = create_test_image()
    
    try:
        response = requests.post(
            'http://localhost:8000/detect-product',
            files={'file': ('test_product.png', img_bytes, 'image/png')},
            timeout=30
        )
        
        if response.ok:
            result = response.json()
            print(f"\n✅ Success! Detected {len(result.get('labels', []))} labels")
            
            labels = result.get('labels', [])
            if labels:
                print(f"\n🏷️  Top Labels:")
                for label in labels[:5]:
                    print(f"   - {label['description']}: {label['confidence']}")
            
            logos = result.get('logos', [])
            if logos:
                print(f"\n🔷 Detected Logos:")
                for logo in logos:
                    print(f"   - {logo['description']}: {logo['confidence']}")
            
            if 'vision_usage' in result:
                usage = result['vision_usage']
                print(f"\n📊 Vision API Usage:")
                print(f"   Units used: {usage['units_used']}/{usage.get('units_remaining', 0) + usage['units_used']}")
                print(f"   Percentage: {usage['percentage_used']}%")
            
            return True
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def test_usage_stats():
    """Test the /vision-usage endpoint."""
    print("\n" + "="*60)
    print("Testing /vision-usage endpoint")
    print("="*60)
    
    try:
        response = requests.get('http://localhost:8000/vision-usage', timeout=10)
        
        if response.ok:
            result = response.json()
            usage = result.get('usage', {})
            print(f"\n📊 Current Usage Statistics:")
            print(f"   Units used: {usage['units_used']}")
            print(f"   Units remaining: {usage['units_remaining']}")
            print(f"   Percentage used: {usage['percentage_used']}%")
            print(f"   Status: {usage['status']}")
            print(f"   Total requests: {usage['requests_count']}")
            return True
        else:
            print(f"\n❌ Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

if __name__ == '__main__':
    print("\n" + "🔬 Google Cloud Vision API Integration Tests" + "\n")
    print("Make sure the backend server is running on http://localhost:8000\n")
    
    # Test all endpoints
    results = []
    results.append(("Text Extraction", test_extract_text()))
    results.append(("Product Detection", test_detect_product()))
    results.append(("Usage Stats", test_usage_stats()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name:<30} {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n🎉 All tests passed! Vision API integration is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    print("\n" + "="*60 + "\n")
