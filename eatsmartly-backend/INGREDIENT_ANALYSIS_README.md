# Ingredient Analysis ML System

This system implements machine learning to detect hidden sugars and misleading claims in food products.

## Overview

The EatSmartly app now includes an Ingredient Analysis Agent that:

1. **Analyzes ingredients** for hidden sugars and artificial sweeteners
2. **Detects misleading claims** like "sugar-free" products containing fructose, sucralose, etc.
3. **Provides health warnings** for artificial sweeteners and sugar alternatives
4. **Uses ML models** (when trained) to classify potentially misleading products

## How It Works

### Rule-Based Analysis (Always Available)
- Scans ingredients for known sugar terms
- Checks product names and labels for sugar-free claims
- Flags mismatches between claims and actual ingredients
- Identifies artificial sweeteners and provides health warnings

### ML Model (Optional Enhancement)
- Trains on OpenFoodFacts data to detect misleading claims
- Uses text classification to identify suspicious ingredient patterns
- Provides confidence scores for analysis results

## Implementation

### Files Added/Modified

1. **`agents/ingredient_analyzer.py`** - Main analysis agent
2. **`train_ingredient_model.py`** - ML model training script
3. **`test_ingredient_analyzer.py`** - Test script
4. **`main.py`** - Integrated into product analysis endpoints
5. **`requirements.txt`** - Added ML dependencies

### Integration Points

The ingredient analysis is automatically included in:
- `/analyze_product` endpoint (barcode, product ID, or name)
- Product analysis results include `ingredient_analysis` field

## Usage

### Basic Analysis (Rule-Based)
```python
from agents.ingredient_analyzer import IngredientAnalysisAgent

analyzer = IngredientAnalysisAgent()
result = analyzer.analyze_ingredients(
    ingredients="Carbonated water, sucralose, acesulfame potassium",
    product_name="Sugar-Free Cola",
    labels=[]
)

print(result['warnings'])  # Shows misleading claim warnings
```

### Training ML Model
```bash
cd eatsmartly-backend
python train_ingredient_model.py
```

This will:
- Fetch training data from OpenFoodFacts
- Train a classifier on misleading vs legitimate claims
- Save model to `models/ingredient_classifier.pkl`

### API Response
Product analysis now includes:
```json
{
  "ingredient_analysis": {
    "analysis": "completed",
    "sugar_score": 1.0,
    "warnings": [
      {
        "type": "misleading_claim",
        "message": "Product claims to be sugar-free but contains: alternatives: sucralose",
        "severity": "high"
      }
    ],
    "health_warnings": [
      {
        "type": "artificial_sweeteners",
        "message": "Contains artificial sweeteners: sucralose. Consult healthcare provider...",
        "severity": "medium"
      }
    ],
    "ml_analysis": {
      "misleading_probability": 0.85,
      "prediction": "misleading"
    }
  }
}
```

## Detected Sugar Types

### Direct Sugars
- sugar, sucrose, fructose, glucose, maltose, lactose, galactose

### Artificial Sweeteners
- acesulfame potassium, aspartame, sucralose, saccharin
- stevia, purified stevia leaf extracts
- erythritol, xylitol, sorbitol, mannitol, isomalt, maltitol, lactitol

### Hidden Sugars
- high fructose corn syrup, corn syrup, agave nectar, honey
- maple syrup, molasses, fruit juice concentrate, dextrose
- maltodextrin, barley malt, rice syrup

## Health Warnings

The system provides warnings for:
- **Misleading claims**: Sugar-free products with hidden sugars
- **Artificial sweeteners**: Health conditions requiring consultation
- **High sugar content**: General sugar warnings
- **Hidden sugars**: Ingredients that may not be obvious sugars

## Training Data

The ML model is trained on OpenFoodFacts data with labels:
- **Misleading (1)**: Products claiming sugar-free but containing hidden sugars
- **Legitimate (0)**: Products with accurate claims or no claims

## Future Enhancements

1. **Expanded training data** from more sources
2. **Fine-tuned transformer models** for better accuracy
3. **Multi-language support** for international products
4. **Real-time model updates** as new sweeteners emerge
5. **Personalized warnings** based on user health profiles

## Testing

Run the test script:
```bash
python test_ingredient_analyzer.py
```

This tests various product types and validates warning detection.</content>
<parameter name="filePath">c:\Users\anany\projects\eatsmart\eatsmartly-backend\INGREDIENT_ANALYSIS_README.md