# Training Data Sources for Ingredient Analysis ML Model

## Data Requirements

For training a model to detect misleading sugar claims, you need:

### **Required Fields:**
- `ingredients`: Full ingredient list text
- `product_name`: Product name/brand
- `labels`: List of claims (sugar-free, low-sugar, etc.)
- `misleading`: Binary label (1=misleading claim, 0=legitimate/no claim)

### **Optional but Helpful:**
- `nutrition_facts`: Sugar content per serving
- `category`: Product category (beverages, snacks, etc.)
- `brand`: Manufacturer information

## Recommended Data Sources

### 1. **OpenFoodFacts** ⭐⭐⭐⭐⭐ (FREE)
**Best starting point - already implemented**

```python
# Access via API
url = "https://world.openfoodfacts.org/cgi/search.pl"
params = {
    'search_terms': '',
    'tagtype_0': 'categories',
    'tag_contains_0': 'contains',
    'tag_0': 'en:sugary-snacks',
    'json': 1,
    'page_size': 100
}
```

**Pros:**
- 2+ million products worldwide
- Ingredient lists in multiple languages
- Labels and claims data
- Free API access
- Community-maintained

**Cons:**
- Inconsistent data quality
- Some products missing ingredients
- Limited nutrition facts

**Data Volume:** 10,000+ sugar-related products

### 2. **USDA FoodData Central** ⭐⭐⭐⭐ (FREE with API key)
**High-quality nutrition data**

```python
# Requires API key from USDA
base_url = "https://api.nal.usda.gov/fdc/v1"
endpoint = "/foods/search"
params = {
    'api_key': your_key,
    'query': 'sugar free',
    'dataType': ['Branded']
}
```

**Pros:**
- Official US government data
- Complete nutrition facts
- Ingredient lists for branded foods
- High data quality

**Cons:**
- API key required
- Rate limits
- US-focused

**Data Volume:** 300,000+ branded foods

### 3. **Nutritionix API** ⭐⭐⭐ (Paid)
**Commercial nutrition database**

```python
# Paid API service
url = "https://trackapi.nutritionix.com/v2/search/instant"
headers = {'x-app-id': app_id, 'x-app-key': app_key}
```

**Pros:**
- High-quality branded food data
- Real-time updates
- Global coverage
- Complete nutrition profiles

**Cons:**
- Paid service ($$$
- Rate limits
- API-only access

### 4. **Manual/Crowdsourced Labeling** ⭐⭐⭐⭐⭐ (HIGH QUALITY)
**Create your own labeled dataset**

**Sources:**
- Product packaging photos
- Store receipts with ingredients
- Regulatory filings (FDA, EU food labels)
- Expert nutritionist reviews

**Pros:**
- Highest quality labels
- Domain expert validation
- Custom focus on misleading claims

**Cons:**
- Time-intensive to collect
- Limited scale

**Recommended Approach:**
```python
# Start with 1000+ manually labeled examples
manual_data = [
    {
        'ingredients': 'water, sucralose, acesulfame potassium',
        'product_name': 'diet soda',
        'labels': ['sugar-free', 'zero calories'],
        'misleading': 1  # Artificial sweeteners present
    }
]
```

### 5. **European Food Safety Authority (EFSA)** ⭐⭐⭐ (FREE)
**EU regulatory data**

**Access:** https://www.efsa.europa.eu/en/data/food-consumption

**Pros:**
- European market data
- Regulatory compliance info
- Ingredient declarations

**Cons:**
- EU-focused
- Complex data formats

### 6. **Kaggle Datasets** ⭐⭐⭐ (FREE)
**Pre-labeled food datasets**

Search for:
- "food ingredients dataset"
- "nutrition facts dataset"
- "food labels classification"

**Pros:**
- Ready-to-use datasets
- Often pre-labeled
- Community validation

**Cons:**
- May not focus on misleading claims
- Variable quality

## Data Collection Strategy

### **Phase 1: Proof of Concept (1-2 weeks)**
1. **OpenFoodFacts** - 5,000 samples
2. **Manual labeling** - 500 samples
3. **Total:** ~5,500 samples

### **Phase 2: Model Improvement (2-4 weeks)**
1. **USDA API** - 10,000 samples
2. **Nutritionix** - 5,000 samples
3. **Additional manual labeling** - 1,000 samples
4. **Total:** ~21,500 samples

### **Phase 3: Production Model (1-2 months)**
1. **All sources combined** - 50,000+ samples
2. **Expert validation** - 5,000 samples
3. **Cross-validation with real products**

## Data Quality Considerations

### **Labeling Guidelines:**
```python
def label_product(ingredients, product_name, labels):
    sugar_free_claim = any(claim in product_name.lower() or
                          any(claim in label.lower() for label in labels)
                          for claim in ['sugar-free', 'no sugar', 'zero sugar'])

    has_sugars = contains_any(ingredients, [
        'fructose', 'sucrose', 'glucose',  # natural sugars
        'sucralose', 'aspartame', 'acesulfame'  # artificial
    ])

    if sugar_free_claim and has_sugars:
        return 1  # Misleading
    elif sugar_free_claim and not has_sugars:
        return 0  # Legitimate
    else:
        return 0  # No claim
```

### **Data Cleaning:**
- Remove products without ingredients
- Standardize ingredient formats
- Handle missing labels gracefully
- Balance classes (misleading vs legitimate)

### **Augmentation:**
- Synonym replacement (sucralose → sucralose sweetener)
- Brand name removal
- Ingredient order randomization

## Implementation

```bash
# Run enhanced data collection
python enhanced_data_collection.py

# Train model with collected data
python train_ingredient_model.py
```

## Expected Performance

With good data:
- **Accuracy:** 85-95%
- **Precision for misleading claims:** 80-90%
- **Recall for misleading claims:** 75-85%

## Cost Estimate

- **OpenFoodFacts:** FREE
- **USDA API:** FREE (key required)
- **Manual labeling:** $500-2000 (crowdsourcing)
- **Nutritionix:** $50-200/month
- **Total for MVP:** $0-500

## Next Steps

1. Start with OpenFoodFacts data collection
2. Add manual labeling for quality
3. Train baseline model
4. Evaluate and iterate
5. Add additional sources as needed</content>
<parameter name="filePath">c:\Users\anany\projects\eatsmart\eatsmartly-backend\TRAINING_DATA_GUIDE.md