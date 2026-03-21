"""
Ingredient Analysis Agent for EatSmartly.
Uses ML/NLP to analyze food ingredients for hidden sugars and misleading claims.
"""
import re
import json
from typing import Dict, Any, Optional, List
import os

from config import settings
from agents.utils import setup_logger
from knowledge.ingredient_translator import translate_ingredient


logger = setup_logger(__name__, settings.LOG_LEVEL)


class IngredientAnalysisAgent:
    """Agent responsible for analyzing food ingredients for hidden sugars and claims."""

    def __init__(self):
        """Initialize the ingredient analysis agent."""
        self.model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'ingredient_classifier.pkl')
        self.vectorizer_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'tfidf_vectorizer.pkl')

        self.classifier = None
        self.vectorizer = None
        self.ml_model_available = False

        # Known sugar terms and alternatives
        self.sugar_terms = {
            'direct': ['sugar', 'sucrose', 'fructose', 'glucose', 'maltose', 'lactose', 'galactose'],
            'alternatives': ['acesulfame potassium', 'aspartame', 'sucralose', 'saccharin',
                           'stevia', 'purified stevia leaf extracts', 'erythritol', 'xylitol',
                           'sorbitol', 'mannitol', 'isomalt', 'maltitol', 'lactitol'],
            'hidden': ['high fructose corn syrup', 'corn syrup', 'agave nectar', 'honey',
                     'maple syrup', 'molasses', 'fruit juice concentrate', 'dextrose',
                     'maltodextrin', 'barley malt', 'rice syrup']
        }

        # Unhealthy ingredients categorized by health concern
        self.unhealthy_ingredients = {
            'refined_flours': ['maida', 'refined wheat flour', 'all-purpose flour', 'enriched flour',
                             'bleached flour', 'white flour', 'refined flour'],
            'trans_fats': ['partially hydrogenated', 'hydrogenated oil', 'trans fat', 'trans fatty acids'],
            'artificial_colors': ['red 40', 'yellow 5', 'yellow 6', 'blue 1', 'artificial color',
                                'fd&c', 'artificial coloring', 'red 3', 'erythrosine'],
            'preservatives': ['bha', 'bht', 'tbhq', 'sodium benzoate', 'potassium sorbate',
                            'sodium nitrite', 'nitrite', 'benzoic acid', 'benzene'],
            'artificial_flavors': ['artificial flavor', 'natural and artificial flavors',
                                 'chocolate flavoring', 'strawberry flavoring'],
            'metabolic_disruptors': ['high fructose corn syrup', 'hfcs'],
            'neurological_concerns': ['msg', 'monosodium glutamate', 'carrageenan'],
            'digestive_concerns': ['xanthan gum', 'guar gum'],
            'artificial_sweeteners_list': ['aspartame', 'sucralose', 'acesulfame potassium',
                                         'saccharin', 'acesulfame k'],
            'yeast_extracts': ['yeast extract', 'autolyzed yeast extract', 'hydrolyzed yeast extract'],
            'carcinogenic_risks': ['sodium nitrite', 'nitrite'],  # Already in preservatives, but emphasizing cancer risk
            'gums_thickeners': ['xanthan gum', 'guar gum']  # Already in digestive_concerns, but for completeness
        }

        # Claims to check
        self.claims = ['sugar-free', 'no sugar', 'sugarless', 'low sugar', 'reduced sugar',
                      'organic', 'natural', 'whole grain', 'whole wheat', 'no artificial']

        self._load_ml_model()
        logger.info("IngredientAnalysisAgent initialized")

    def _load_ml_model(self):
        """Load the trained ML model and vectorizer."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                import joblib
                self.classifier = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                self.ml_model_available = True
                logger.info("ML model loaded successfully")
            else:
                logger.warning("Trained ML model not found. Using rule-based analysis only.")
                self.ml_model_available = False
        except Exception as e:
            logger.warning(f"Could not load ML model: {e}. Using rule-based analysis only.")
            self.ml_model_available = False

    def analyze_ingredients(self, ingredients: str, product_name: str = "", labels: List[str] = None) -> Dict[str, Any]:
        """
        Analyze ingredients for hidden sugars and misleading claims.

        Args:
            ingredients: Ingredient list text
            product_name: Product name for context
            labels: Product labels/claims

        Returns:
            Analysis results dictionary
        """
        if not ingredients:
            return {"analysis": "No ingredients provided", "warnings": [], "score": 0}

        # Translate ingredients to English first (handles multi-language ingredients)
        try:
            ingredient_list = [ing.strip() for ing in ingredients.split(',')]
            translated_list = [translate_ingredient(ing) for ing in ingredient_list if ing.strip()]
            ingredients = ', '.join(translated_list)
            logger.debug(f"Translated ingredients for analysis: {ingredients[:100]}")
        except Exception as e:
            logger.warning(f"Error translating ingredients for analysis: {e}, proceeding with original")

        ingredients_lower = ingredients.lower()
        product_name_lower = product_name.lower()
        labels = labels or []

        warnings = []
        sugar_score = 0
        unhealthy_score = 0
        found_unhealthy = []

        # Check for misleading claims
        has_sugar_free_claim = any(claim in product_name_lower or claim in ' '.join(labels).lower()
                                 for claim in self.claims)

        if has_sugar_free_claim:
            # Check if ingredients contain sugars despite claim
            found_sugars = []
            for category, terms in self.sugar_terms.items():
                for term in terms:
                    if term in ingredients_lower:
                        found_sugars.append(f"{category}: {term}")
                        sugar_score += 1 if category == 'direct' else 0.5

            if found_sugars:
                warnings.append({
                    "type": "misleading_claim",
                    "message": f"Product claims to be sugar-free but contains: {', '.join(found_sugars)}",
                    "severity": "high"
                })

        # Check for unhealthy ingredients
        for category, terms in self.unhealthy_ingredients.items():
            for term in terms:
                if term in ingredients_lower:
                    found_unhealthy.append(f"{category}: {term}")
                    # Assign severity scores based on health risks
                    if category in ['refined_flours', 'trans_fats', 'artificial_colors', 'carcinogenic_risks']:
                        unhealthy_score += 2.5  # High severity - cancer, heart disease, diabetes risk
                    elif category in ['neurological_concerns', 'metabolic_disruptors', 'artificial_sweeteners_list']:
                        unhealthy_score += 2.0  # Medium-high severity - neurological, digestive, hyperactivity
                    elif category in ['preservatives', 'artificial_flavors', 'yeast_extracts']:
                        unhealthy_score += 1.5  # Medium severity - potential cancer links, sensitivities
                    else:  # gums_thickeners, digestive_concerns
                        unhealthy_score += 0.5  # Low severity - digestive issues only in large amounts

        # Generate warnings for unhealthy ingredients
        if unhealthy_score > 0:
            if unhealthy_score >= 3:
                warnings.append({
                    "type": "highly_processed",
                    "message": f"Contains multiple unhealthy ingredients: {', '.join(found_unhealthy[:3])}{'...' if len(found_unhealthy) > 3 else ''}",
                    "severity": "high"
                })
            elif unhealthy_score >= 2:
                warnings.append({
                    "type": "processed_ingredients",
                    "message": f"Contains processed/unhealthy ingredients: {', '.join(found_unhealthy)}",
                    "severity": "medium"
                })
            else:
                warnings.append({
                    "type": "questionable_ingredients",
                    "message": f"Contains potentially unhealthy ingredients: {', '.join(found_unhealthy)}",
                    "severity": "low"
                })

        # Analyze overall sugar content
        total_sugar_terms = sum(len(terms) for terms in self.sugar_terms.values())
        found_terms = sum(1 for category in self.sugar_terms.values()
                         for term in category if term in ingredients_lower)

        sugar_density = found_terms / len(ingredients.split()) if ingredients.split() else 0

        # Use ML model if available
        ml_analysis = {}
        misleading_probability = 0.0

        if self.ml_model_available and self.classifier and self.vectorizer:
            try:
                # Prepare text for ML model
                combined_text = ingredients + ' ' + product_name + ' ' + ' '.join(labels)
                X_vec = self.vectorizer.transform([combined_text])

                # Get prediction probability
                proba = self.classifier.predict_proba(X_vec)[0]
                misleading_probability = proba[1]  # Probability of being misleading (class 1)

                ml_analysis = {
                    "misleading_probability": float(misleading_probability),
                    "prediction": "misleading" if misleading_probability > 0.5 else "legitimate"
                }
            except Exception as e:
                logger.warning(f"ML analysis failed: {e}")

        # Enhanced warnings based on ML prediction
        if misleading_probability > 0.7:
            warnings.append({
                "type": "high_confidence_misleading",
                "message": f"High confidence ({misleading_probability:.2%}) that this product makes misleading sugar claims",
                "severity": "high"
            })
        elif misleading_probability > 0.5:
            warnings.append({
                "type": "potential_misleading",
                "message": f"Potential misleading sugar claims detected (confidence: {misleading_probability:.2%})",
                "severity": "medium"
            })
        health_warnings = self._generate_health_warnings(ingredients_lower, sugar_score)

        return {
            "analysis": "completed",
            "sugar_score": sugar_score,
            "unhealthy_score": unhealthy_score,
            "total_concern_score": sugar_score + unhealthy_score,
            "sugar_density": sugar_density,
            "warnings": warnings,
            "health_warnings": health_warnings,
            "ml_analysis": ml_analysis,
            "found_sugars": found_sugars if 'found_sugars' in locals() else [],
            "found_unhealthy": found_unhealthy
        }

    def _generate_health_warnings(self, ingredients_lower: str, sugar_score: float) -> List[Dict]:
        """Generate health-specific warnings based on ingredients."""
        warnings = []

        # Check for artificial sweeteners and health conditions
        artificial_sweeteners = [term for term in self.sugar_terms['alternatives']
                               if term in ingredients_lower]

        if artificial_sweeteners:
            warnings.append({
                "type": "artificial_sweeteners",
                "message": f"Contains artificial sweeteners: {', '.join(artificial_sweeteners)}. Consult healthcare provider if you have phenylketonuria or other conditions.",
                "severity": "medium"
            })

        # High sugar content warning
        if sugar_score > 2:
            warnings.append({
                "type": "high_sugar",
                "message": "High sugar content detected. May not be suitable for diabetics or weight management.",
                "severity": "high"
            })

        # Generate warnings for unhealthy ingredients based on categories
        for category, ingredients_list in self.unhealthy_ingredients.items():
            found_items = [item for item in ingredients_list if item in ingredients_lower]
            if found_items:
                if category == "neurological_concerns":
                    warnings.append({
                        "type": "neurological_risk",
                        "message": f"Contains ingredients linked to neurological concerns: {', '.join(found_items)}. May cause headaches, dizziness, or other neurological symptoms in sensitive individuals.",
                        "severity": "high"
                    })
                elif category == "artificial_colors":
                    warnings.append({
                        "type": "artificial_colors",
                        "message": f"Contains artificial colors: {', '.join(found_items)}. Linked to hyperactivity in children and potential carcinogenic effects.",
                        "severity": "high"
                    })
                elif category == "preservatives":
                    warnings.append({
                        "type": "preservative_concerns",
                        "message": f"Contains preservatives: {', '.join(found_items)}. May cause allergic reactions or digestive issues in sensitive individuals.",
                        "severity": "medium"
                    })
                elif category == "carcinogenic_risks":
                    warnings.append({
                        "type": "cancer_risk",
                        "message": f"Contains ingredients with potential carcinogenic risks: {', '.join(found_items)}. Linked to increased cancer risk with long-term consumption.",
                        "severity": "high"
                    })
                elif category == "digestive_concerns":
                    warnings.append({
                        "type": "digestive_issues",
                        "message": f"Contains ingredients that may cause digestive issues: {', '.join(found_items)}. May cause bloating, diarrhea, or gastrointestinal discomfort.",
                        "severity": "medium"
                    })
                elif category == "metabolic_disruptors":
                    warnings.append({
                        "type": "metabolic_risk",
                        "message": f"Contains metabolic disruptors: {', '.join(found_items)}. May interfere with blood sugar regulation and metabolism.",
                        "severity": "high"
                    })
                elif category == "gums_thickeners":
                    warnings.append({
                        "type": "gums_thickeners",
                        "message": f"Contains gums/thickeners: {', '.join(found_items)}. May cause digestive issues or allergic reactions in sensitive individuals.",
                        "severity": "low"
                    })
                elif category == "artificial_flavors":
                    warnings.append({
                        "type": "artificial_flavors",
                        "message": f"Contains artificial flavorings: {', '.join(found_items)}. May contain undisclosed allergens or cause sensitivities.",
                        "severity": "medium"
                    })
                elif category == "yeast_extracts":
                    warnings.append({
                        "type": "yeast_extract",
                        "message": f"Contains yeast extract: {', '.join(found_items)}. High in glutamate - may trigger MSG-like symptoms in sensitive individuals.",
                        "severity": "medium"
                    })

        return warnings

    def get_nutrition_insights(self, nutrition_data: Dict[str, Any], ingredients: str) -> Dict[str, Any]:
        """
        Provide insights combining nutrition data and ingredient analysis.

        Args:
            nutrition_data: Nutritional information
            ingredients: Ingredient list

        Returns:
            Combined insights
        """
        sugar_g = nutrition_data.get('sugar_g', 0)
        analysis = self.analyze_ingredients(ingredients)

        insights = {
            "sugar_content": sugar_g,
            "ingredient_analysis": analysis,
            "recommendations": []
        }

        # Generate recommendations
        if sugar_g > 10:
            insights["recommendations"].append("High sugar content - consider alternatives")
        elif analysis["sugar_score"] > 1:
            insights["recommendations"].append("Hidden sugars detected in ingredients")

        if analysis["warnings"]:
            insights["recommendations"].extend([w["message"] for w in analysis["warnings"]])

        return insights