"""
AI Meal Planner Agent
Uses Gemini 2.5 to create personalized meal plans based on:
- Available ingredients at home
- Nutritional goals (high protein, specific nutrients)
- Health preferences
- Researched-backed recipes with internet data
"""
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import requests

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)


class MealPlannerAgent:
    """AI-powered meal planner using Gemini 2.5 Flash"""
    
    def __init__(self):
        """Initialize the meal planner with Gemini API"""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name='gemini-2.5-flash')
        
        # Initialize API Ninjas Recipe API
        self.api_ninjas_key = os.getenv('API_NINJAS_KEY')
        self.api_ninjas_recipe_base = "https://api.api-ninjas.com/v3/recipe"
        
        logger.info("✅ Meal Planner initialized with Gemini 2.5")
        if self.api_ninjas_key:
            logger.info("✅ API Ninjas Recipe API enabled")
        else:
            logger.warning("⚠️  API Ninjas key not found - recipes will be from Gemini only")
    
    def get_recipe_suggestions(self, query: str, max_results: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Get recipe suggestions from API Ninjas Recipe API
        
        Args:
            query: Recipe query (e.g., "lentil soup", "chicken curry", "vegan pasta")
            max_results: Maximum number of recipes to return
        
        Returns:
            List of recipes or None if API call fails
        """
        if not self.api_ninjas_key:
            logger.debug(f"API Ninjas not configured, skipping recipe lookup for {query}")
            return None
        
        try:
            params = {
                'query': query
            }
            headers = {
                'X-Api-Key': self.api_ninjas_key
            }
            
            response = requests.get(
                self.api_ninjas_recipe_base,
                params=params,
                headers=headers,
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    # Return top recipes
                    recipes = data[:max_results]
                    logger.info(f"✅ Found {len(recipes)} recipes for '{query}'")
                    return recipes
                else:
                    logger.debug(f"No recipes found for '{query}'")
                    return None
            else:
                logger.debug(f"API Ninjas returned {response.status_code} for query '{query}'")
                return None
                
        except Exception as e:
            logger.warning(f"Error fetching recipes from API Ninjas: {e}")
            return None
    
    def search_recipes_by_ingredients(self, ingredients: List[str], max_results: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search for recipes that can be made with available ingredients
        
        Args:
            ingredients: List of available ingredients
            max_results: Maximum recipes to fetch per ingredient
        
        Returns:
            Dict mapping search queries to their recipe results
        """
        recipes_by_ingredient = {}
        
        for ingredient in ingredients[:5]:  # Limit to first 5 ingredients to avoid too many API calls
            recipes = self.get_recipe_suggestions(ingredient, max_results=max_results)
            if recipes:
                recipes_by_ingredient[ingredient] = recipes
        
        return recipes_by_ingredient
    
    def generate_meal_plan(
        self,
        available_ingredients: List[str],
        nutritional_goals: Dict[str, Any],
        dietary_restrictions: Optional[List[str]] = None,
        cuisine_preferences: Optional[List[str]] = None,
        meal_type: str = "balanced",  # balanced, high_protein, weight_loss, muscle_gain
        num_meals: int = 5,
        cooking_time_limit: int = 30,  # minutes
    ) -> Dict[str, Any]:
        """
        Generate personalized meal plan with recipes
        
        Args:
            available_ingredients: List of ingredients user has at home
            nutritional_goals: Dict with keys like 'protein_g', 'calories', 'carbs_g', 'fat_g'
            dietary_restrictions: List of restrictions (vegan, gluten_free, etc.)
            cuisine_preferences: Preferred cuisines
            meal_type: Type of meal plan
            num_meals: Number of meal suggestions to generate
            cooking_time_limit: Maximum cooking time in minutes
        
        Returns:
            Dict with meal suggestions, recipes, and nutritional info
        """
        try:
            logger.info(f"🍽️  Generating meal plan: {meal_type} with {num_meals} meals")
            logger.info(f"   Ingredients: {', '.join(available_ingredients[:5])}...")
            
            # Build the prompt
            prompt = self._build_meal_plan_prompt(
                available_ingredients,
                nutritional_goals,
                dietary_restrictions,
                cuisine_preferences,
                meal_type,
                num_meals,
                cooking_time_limit
            )
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                stream=False
            )
            
            # Parse and structure the response
            meal_plan = self._parse_meal_plan_response(response.text)
            
            logger.info(f"✅ Generated {len(meal_plan.get('meals', []))} meal suggestions")
            
            # Enrich meals with real recipes from API Ninjas
            enriched_meals = []
            for meal in meal_plan.get("meals", []):
                meal_name = meal.get("name", "")
                # Try to find a matching recipe
                recipes = self.get_recipe_suggestions(meal_name, max_results=1)
                if recipes:
                    meal["api_recipe"] = recipes[0]
                    logger.debug(f"✅ Enriched '{meal_name}' with API Ninjas recipe")
                enriched_meals.append(meal)
            
            return {
                "success": True,
                "meal_type": meal_type,
                "available_ingredients": available_ingredients,
                "nutritional_goals": nutritional_goals,
                "meals": enriched_meals,
                "daily_nutrition": meal_plan.get("daily_nutrition"),
                "shopping_list": self._generate_shopping_list(meal_plan.get("meals", [])),
                "generated_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating meal plan: {e}")
            return {
                "success": False,
                "error": str(e),
                "meal_type": meal_type
            }
    
    def get_recipes_from_gemini(
        self,
        ingredients: List[str],
        cuisine: Optional[str] = None,
        skill_level: str = "intermediate",  # beginner, intermediate, advanced
        dietary_needs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get recipe suggestions for given ingredients using Gemini
        
        Args:
            ingredients: Available ingredients
            cuisine: Preferred cuisine
            skill_level: Cooking skill level
            dietary_needs: Special dietary requirements
        
        Returns:
            List of recipe suggestions with details
        """
        try:
            logger.info(f"👨‍🍳 Getting recipe suggestions for {len(ingredients)} ingredients")
            
            prompt = self._build_recipe_prompt(
                ingredients,
                cuisine,
                skill_level,
                dietary_needs
            )
            
            response = self.model.generate_content(
                prompt,
                stream=False
            )
            
            recipes = self._parse_recipes_response(response.text)
            
            logger.info(f"✅ Found {len(recipes)} recipe suggestions")
            
            return {
                "success": True,
                "ingredients": ingredients,
                "recipes": recipes,
                "generated_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting recipes: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_nutrition_analysis(
        self,
        meal_description: str,
        serving_size: str = "1 serving",
    ) -> Dict[str, Any]:
        """
        Analyze nutrition of a meal using Gemini with internet data
        
        Args:
            meal_description: Description of the meal
            serving_size: Size of serving
        
        Returns:
            Nutritional breakdown
        """
        try:
            logger.info(f"🔬 Analyzing nutrition for: {meal_description}")
            
            prompt = f"""
            Analyze the complete nutritional content of this meal:
            
            MEAL: {meal_description}
            SERVING size: {serving_size}
            
            Please provide:
            1. Estimated calories
            2. Macronutrients (protein, carbs, fat) in grams
            3. Key micronutrients (fiber, sodium, vitamins)
            4. Health benefits
            5. Comparison to recommended daily values
            
            Base your analysis on verified nutritional databases and research.
            Format as JSON with these exact keys:
            {{
                "calories": <number>,
                "protein_g": <number>,
                "carbs_g": <number>,
                "fat_g": <number>,
                "fiber_g": <number>,
                "sodium_mg": <number>,
                "key_vitamins": [<list>],
                "health_benefits": [<list>],
                "notes": "<any important notes>"
            }}
            """
            
            response = self.model.generate_content(
                prompt,
                stream=False
            )
            
            nutrition_data = self._parse_nutrition_response(response.text)
            
            logger.info(f"✅ Nutrition analysis complete: {nutrition_data.get('calories')} cal")
            
            return {
                "success": True,
                "meal": meal_description,
                "nutrition": nutrition_data,
                "generated_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing nutrition: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_weekly_meal_plan(
        self,
        available_ingredients: List[str],
        nutritional_goals: Dict[str, Any],
        dietary_restrictions: Optional[List[str]] = None,
        cuisine_preferences: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete weekly meal plan
        
        Args:
            available_ingredients: List of ingredients
            nutritional_goals: Nutritional targets
            dietary_restrictions: Dietary restrictions
            cuisine_preferences: Cuisine preferences
        
        Returns:
            7-day meal plan with shopping list
        """
        try:
            logger.info("📅 Generating weekly meal plan...")
            
            prompt = f"""
            Create a complete, healthy 7-day meal plan with the following requirements:
            
            **AVAILABLE INGREDIENTS AT HOME:**
            {json.dumps(available_ingredients, indent=2)}
            
            **NUTRITIONAL GOALS:**
            {json.dumps(nutritional_goals, indent=2)}
            
            **DIETARY RESTRICTIONS:**
            {dietary_restrictions or "None"}
            
            **CUISINE PREFERENCES:**
            {cuisine_preferences or "Varied, international"}
            
            **REQUIREMENTS:**
            1. Each meal should use at least 50% of available ingredients
            2. High protein content (minimum 25g per meal)
            3. Balanced macronutrients
            4. Researched-backed healthy recipes
            5. Mix of cuisines and flavors
            6. Easy to prepare (30-45 min cooking time)
            7. Shopping list optimization (reuse ingredients across days)
            
            **FORMAT:**
            For each day (Monday-Sunday):
            - Breakfast: [Recipe name] - [Brief description, 2-3 lines]
              Nutrition: [Calories] cal, [Protein]g protein, [Carbs]g carbs, [Fat]g fat
              Ingredients needed: [List]
              Estimated prep time: [minutes]
              
            - Lunch: [Similar format]
            - Dinner: [Similar format]
            - Snack: [If applicable]
            
            At the end, provide:
            - COMBINED SHOPPING LIST: [Items to buy, organized by category]
            - WEEKLY NUTRITION SUMMARY: [Total calories, average macros, key nutrients]
            - MOTIVATIONAL NOTES: [Why these meals are healthy, tips for success]
            
            Make sure all suggestions are based on verified nutritional research
            and include citations to credible sources where applicable.
            """
            
            response = self.model.generate_content(
                prompt,
                stream=False
            )
            
            weekly_plan = self._parse_weekly_plan_response(response.text)
            
            logger.info("✅ Weekly meal plan generated successfully")
            
            return {
                "success": True,
                "weekly_plan": weekly_plan,
                "generated_at": datetime.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"❌ Error generating weekly plan: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== Helper Methods ====================
    
    def _build_meal_plan_prompt(
        self,
        available_ingredients: List[str],
        nutritional_goals: Dict[str, Any],
        dietary_restrictions: Optional[List[str]],
        cuisine_preferences: Optional[List[str]],
        meal_type: str,
        num_meals: int,
        cooking_time_limit: int,
    ) -> str:
        """Build the prompt for meal plan generation"""
        
        meal_type_descriptions = {
            "balanced": "Well-balanced macronutrients (40% carbs, 30% protein, 30% fat)",
            "high_protein": "High protein content (40%+ of calories from protein)",
            "weight_loss": "Low calorie, high protein, filling meals for weight loss",
            "muscle_gain": "High calories and protein for muscle building",
        }
        
        prompt = f"""
        You are an expert nutritionist and chef. Generate {num_meals} meal suggestions
        using ONLY the available ingredients at home. Use internet data to research
        healthiest preparation methods and sourced recipes.
        
        **AVAILABLE INGREDIENTS:**
        {', '.join(available_ingredients)}
        
        **MEAL TYPE:** {meal_type}
        ({meal_type_descriptions.get(meal_type, "Balanced nutrition")})
        
        **NUTRITIONAL GOALS PER MEAL:**
        {json.dumps(nutritional_goals, indent=2)}
        
        **DIETARY RESTRICTIONS:**
        {', '.join(dietary_restrictions) if dietary_restrictions else "None"}
        
        **CUISINE PREFERENCES:**
        {', '.join(cuisine_preferences) if cuisine_preferences else "Varied"}
        
        **MAXIMUM COOKING TIME:** {cooking_time_limit} minutes
        
        **FOR EACH MEAL SUGGESTION, PROVIDE:**
        1. Meal name and cuisine type
        2. Detailed recipe with step-by-step instructions
        3. Complete ingredient list with quantities
        4. Estimated nutritional content (calories, protein, carbs, fat, fiber)
        5. Cooking time and difficulty level
        6. Why this meal is healthy (backed by nutrition science)
        7. Health benefits of key ingredients
        8. Tips for preparation and variations
        
        **CRITICAL REQUIREMENTS:**
        - Use ONLY available ingredients (can add basic staples like oil, salt, spices)
        - High protein focus
        - Backed by nutritional research
        - Include internet-researched healthy recipes
        - Make it practical and doable at home
        
        Format each meal clearly with ### MEAL [Number] [Name] as header.
        """
        
        return prompt
    
    def _build_recipe_prompt(
        self,
        ingredients: List[str],
        cuisine: Optional[str],
        skill_level: str,
        dietary_needs: Optional[List[str]],
    ) -> str:
        """Build the prompt for recipe suggestions"""
        
        prompt = f"""
        You are a professional chef with expertise in researched-backed healthy cooking.
        
        Find creative, researched-backed recipes using only these ingredients:
        {', '.join(ingredients)}
        
        **CRITERIA:**
        - Cuisine: {cuisine or "Any"}
        - Cooking skill level: {skill_level}
        - Dietary requirements: {', '.join(dietary_needs) if dietary_needs else "None"}
        - Focus on healthy, nutritious options
        - Include internet-researched authentic recipes
        
        **FOR EACH RECIPE, PROVIDE:**
        1. Recipe name and origin
        2. Ingredients with quantities
        3. Step-by-step instructions
        4. Estimated nutrition facts
        5. Cooking time
        6. Health benefits
        7. Sourced from credible recipe/nutrition databases
        
        Focus on quality over quantity.
        """
        
        return prompt
    
    def _build_nutrition_prompt(self) -> str:
        """Build prompt for nutrition-focused meals"""
        pass
    
    def _parse_meal_plan_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response into structured meal plan"""
        try:
            # Try to extract JSON if present
            if "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start < json_end:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
            
            # Otherwise return structured data from text
            return {
                "meals": [
                    {
                        "name": "Parsed from Gemini response",
                        "description": response_text[:500],
                    }
                ],
                "daily_nutrition": {
                    "calories": "To be calculated",
                    "protein_g": "From Gemini response",
                }
            }
        except Exception as e:
            logger.warning(f"Could not parse full response: {e}")
            return {
                "meals": [],
                "raw_response": response_text
            }
    
    def _parse_recipes_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse recipe response"""
        try:
            # Extract structured recipe data
            recipes = []
            lines = response_text.split('\n')
            
            current_recipe = None
            for line in lines:
                if line.startswith('###') or line.startswith('**Recipe'):
                    if current_recipe:
                        recipes.append(current_recipe)
                    current_recipe = {"name": line.replace('#', '').strip()}
                elif current_recipe and line.strip():
                    current_recipe["description"] = line
            
            if current_recipe:
                recipes.append(current_recipe)
            
            return recipes if recipes else [{"raw": response_text}]
        except Exception as e:
            logger.warning(f"Could not parse recipes: {e}")
            return []
    
    def _parse_nutrition_response(self, response_text: str) -> Dict[str, Any]:
        """Parse nutrition analysis response"""
        try:
            # Try to extract JSON
            if "{" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            
            return {"raw_analysis": response_text}
        except Exception as e:
            logger.warning(f"Could not parse nutrition: {e}")
            return {"raw_analysis": response_text}
    
    def _parse_weekly_plan_response(self, response_text: str) -> str:
        """Parse weekly plan response"""
        return response_text
    
    def _generate_shopping_list(self, meals: List[Dict]) -> List[str]:
        """Generate consolidated shopping list from meals"""
        shopping_list = set()
        
        for meal in meals:
            if isinstance(meal, dict):
                ingredients = meal.get("ingredients", [])
                if isinstance(ingredients, list):
                    shopping_list.update(ingredients)
        
        return sorted(list(shopping_list))
    
    def format_recipe_data(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format API Ninjas recipe data for app display
        
        Args:
            recipe: Raw recipe data from API Ninjas
        
        Returns:
            Formatted recipe data with essential fields
        """
        return {
            'title': recipe.get('title', 'Recipe'),
            'ingredients': recipe.get('ingredients', []),
            'instructions': recipe.get('instructions', ''),
            'servings': recipe.get('servings', 2),
            'cook_time_minutes': recipe.get('cook_time_minutes'),
            'prep_time_minutes': recipe.get('prep_time_minutes'),
            'tags': recipe.get('tags', []),
            'source': 'API Ninjas Recipe Database',
        }


# Global instance
_meal_planner = None


def get_meal_planner() -> MealPlannerAgent:
    """Get or create meal planner instance"""
    global _meal_planner
    if _meal_planner is None:
        _meal_planner = MealPlannerAgent()
    return _meal_planner
