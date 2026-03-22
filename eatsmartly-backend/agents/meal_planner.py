"""
AI Meal Planner Agent — EatSmartly
Fixed version:
- Proper system prompt for conversational chat
- Clean plain-text responses (no markdown leaking)
- Robust parsing that doesn't silently fall back to garbage
- Chat history support for multi-turn conversations
- generate_meal_plan / weekly plan / nutrition analysis all working
"""

import logging
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import requests

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables at module level
load_dotenv()

# Import nutrition database for data-driven responses
from agents.nutrition_database import get_nutrition_database

logger = logging.getLogger(__name__)

# Global instance
_meal_planner = None

# ---------------------------------------------------------------------------
# System prompt — used for ALL chat interactions
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are EatSmartly's meal planning assistant for Indian users.

You have access to a comprehensive nutrition database with 652+ food items and their exact nutritional information.

MANDATORY FORMAT for recipe responses:

[Recipe Name] ([exact calories from database], [exact protein from database])

Ingredients:
1. [ingredient with quantity]
2. [ingredient with quantity]

Steps:
1. [cooking step]
2. [cooking step]

RULES:
- Use EXACT nutrition data from the database when available
- Always format responses as: Recipe name, Ingredients list, Steps list
- No conversational text, just recipe format
- Maximum 2 recipes per response
- Focus on Indian/healthy cooking methods
- Always use accurate calorie and protein values from dataset
"""

# ---------------------------------------------------------------------------
# MealPlannerAgent
# ---------------------------------------------------------------------------

class MealPlannerAgent:
    """AI-powered meal planner using Gemini 1.5 Flash"""

    def __init__(self):
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")

            genai.configure(api_key=api_key)

            # Chat model — used for conversational meal planning
            self.chat_model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=SYSTEM_PROMPT,
                generation_config={
                    "temperature": 0.7,
                    "max_output_tokens": 1024,
                    "top_p": 0.9,
                },
            )

            # Generation model — used for structured meal plans / nutrition analysis
            self.gen_model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                generation_config={
                    "temperature": 0.4,   # lower = more consistent structured output
                    "max_output_tokens": 4096,
                },
            )

            # API Ninjas for real recipe enrichment (optional)
            self.api_ninjas_key = os.getenv("API_NINJAS_KEY")
            self.api_ninjas_recipe_base = "https://api.api-ninjas.com/v1/recipe"

            # Initialize nutrition database for accurate responses
            self.nutrition_db = get_nutrition_database()
            logger.info(f"Nutrition database loaded with {len(self.nutrition_db.df) if self.nutrition_db.df is not None else 0} food items")

            # Initialize as working agent
            self.is_fallback = False
            logger.info("MealPlannerAgent initialized with Gemini 2.5 Flash and Nutrition Database")

        except Exception as e:
            logger.error(f"Failed to initialize Gemini models: {e}")
            # Initialize as fallback mode - no AI models but keep nutrition database
            self.chat_model = None
            self.gen_model = None
            self.api_ninjas_key = None
            self.api_ninjas_recipe_base = None

            # Always load nutrition database even in fallback mode
            self.nutrition_db = get_nutrition_database()

            self.is_fallback = True
            logger.info("MealPlannerAgent initialized in fallback mode (no AI model, using nutrition database only)")


    # ------------------------------------------------------------------
    # CHAT — main method called by your Flutter chat screen
    # ------------------------------------------------------------------

    def chat(self, user_message: str, history: Optional[List[Dict]] = None) -> str:
        """
        Handle a single conversational message with data-driven nutrition responses.

        Args:
            user_message: What the user typed
            history: List of {"role": "user"|"model", "parts": ["text"]}
                     Pass the last 6 messages max for context.

        Returns:
            Plain text response (no markdown) with accurate nutrition data
        """
        try:
            logger.info(f"Processing chat message: {user_message[:50]}...")

            # Extract ingredients from the user message
            ingredients = self._extract_ingredients(user_message)
            logger.info(f"Extracted ingredients: {ingredients}")

            # If we have ingredients, use nutrition database for accurate responses
            if ingredients and self.nutrition_db and self.nutrition_db.df is not None:
                logger.info("Using nutrition database for data-driven response")
                return self._get_data_driven_response(ingredients, user_message)

            # For general chat or if no nutrition data available, use AI
            if not self.is_fallback and self.chat_model is not None:
                logger.info("Using AI model for general response")
                return self._get_ai_response(user_message, history)

            # Fallback response
            logger.info("Using fallback response")
            return self._get_fallback_response(user_message)

        except Exception as e:
            logger.error(f"Chat error details: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Chat error traceback: {traceback.format_exc()}")

            # Return error for debugging
            return f"Error: {str(e)}. Please check server logs."

    def _extract_ingredients(self, message: str) -> List[str]:
        """Extract ingredient names from user message"""
        message_lower = message.lower()

        # Common ingredients to look for
        ingredients = [
            'chicken', 'rice', 'pasta', 'eggs', 'fish', 'beef', 'pork',
            'tofu', 'lentil', 'beans', 'vegetables', 'tomato', 'onion',
            'potato', 'cheese', 'milk', 'bread', 'quinoa', 'oats',
            'broccoli', 'spinach', 'carrot', 'bell pepper', 'mushroom'
        ]

        found_ingredients = []
        for ingredient in ingredients:
            if ingredient in message_lower:
                found_ingredients.append(ingredient)

        return found_ingredients

    def _get_data_driven_response(self, ingredients: List[str], user_message: str) -> str:
        """Get response using nutrition database with exact nutritional data"""
        try:
            # Get recipe suggestions from database
            recipes = self.nutrition_db.get_recipe_suggestions(ingredients)

            if not recipes:
                return "I couldn't find exact recipes for those ingredients in my database. Try asking about chicken, rice, pasta, or other common ingredients."

            # Format recipes using actual nutrition data
            response_parts = []
            for i, recipe in enumerate(recipes[:2]):  # Max 2 recipes
                formatted_recipe = self.nutrition_db.format_recipe_with_nutrition(recipe)
                if formatted_recipe:
                    response_parts.append(formatted_recipe)

            if response_parts:
                return "\n\n".join(response_parts)
            else:
                return "I found matching ingredients but couldn't format the recipes. Please try rephrasing your request."

        except Exception as e:
            logger.error(f"Data-driven response error: {e}")
            return self._get_fallback_response(user_message)

    def _get_ai_response(self, user_message: str, history: Optional[List[Dict]] = None) -> str:
        """Get response from AI model"""
        try:
            # Build Gemini-format history (last 6 turns = 3 exchanges)
            gemini_history = []
            if history:
                for msg in history[-6:]:
                    role = msg.get("role", "user")
                    content = msg.get("parts", msg.get("content", ""))
                    if isinstance(content, list):
                        content = content[0]
                    if role in ("user", "model") and content:
                        gemini_history.append({
                            "role": role,
                            "parts": [str(content)]
                        })

            chat_session = self.chat_model.start_chat(history=gemini_history)
            response = chat_session.send_message(user_message)

            return self._clean_text(response.text)

        except Exception as e:
            logger.error(f"AI response error: {e}")
            raise e

    def _get_fallback_response(self, user_message: str) -> str:
        """Simple fallback response for basic interactions"""
        message_lower = user_message.lower()

        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm your meal planning assistant. Tell me what ingredients you have and I'll suggest recipes with accurate nutrition information."

        elif any(word in message_lower for word in ['help', 'what', 'how']):
            return "I can help you with meal planning using my nutrition database! Just tell me what ingredients you have (like chicken, rice, pasta) and I'll suggest recipes with exact calories and protein information."

        else:
            return "I specialize in meal planning with accurate nutrition data. Tell me what ingredients you have available and I'll suggest specific recipes!"

    def _fallback_response(self, user_message: str) -> str:
        """Smart fallback responses without AI model"""
        message_lower = user_message.lower()

        # Check for ingredients mentioned
        common_ingredients = {
            'chicken': 'chicken',
            'rice': 'rice',
            'eggs': 'eggs',
            'potato': 'potatoes',
            'tomato': 'tomatoes',
            'onion': 'onions',
            'pasta': 'pasta',
            'bread': 'bread',
            'milk': 'milk',
            'cheese': 'cheese',
            'paneer': 'paneer',
            'dal': 'dal',
            'roti': 'roti',
            'chapati': 'chapati',
            'vegetables': 'vegetables',
            'mutton': 'mutton',
            'fish': 'fish'
        }

        found_ingredients = []
        for ingredient, display_name in common_ingredients.items():
            if ingredient in message_lower:
                found_ingredients.append(display_name)

        # Provide ingredient-specific suggestions
        if found_ingredients:
            if 'chicken' in found_ingredients and 'rice' in found_ingredients:
                return "With chicken and rice, you can make: 1. Chicken Biryani - fragrant basmati rice with spiced chicken (about 450 calories, 25g protein), 2. Chicken Fried Rice - quick stir-fry with vegetables (about 380 calories, 22g protein), 3. Chicken Pulao - one-pot rice dish with mild spices (about 400 calories, 24g protein). All are nutritious and filling!"

            elif 'chicken' in found_ingredients:
                return "Great choice with chicken! Here are some healthy options: 1. Chicken Curry - with onions and tomatoes (about 250 calories, 30g protein per serving), 2. Grilled Chicken - simple and healthy (about 200 calories, 25g protein), 3. Chicken Soup - nourishing and light (about 150 calories, 20g protein). Each provides excellent protein!"

            elif 'rice' in found_ingredients:
                return "Rice is so versatile! Try these: 1. Vegetable Fried Rice - with mixed vegetables and eggs (about 320 calories, 12g protein), 2. Dal Rice - classic comfort food with lentils (about 280 calories, 15g protein), 3. Jeera Rice - cumin-flavored rice as a side (about 200 calories, 4g protein). All are satisfying and nutritious!"

            elif 'eggs' in found_ingredients:
                return "Eggs are perfect for any meal! Consider: 1. Scrambled Eggs with vegetables (about 180 calories, 14g protein), 2. Egg Curry - spiced and flavorful (about 220 calories, 16g protein), 3. Boiled Eggs with toast (about 250 calories, 18g protein). High in protein and very filling!"

            elif any(ingredient in found_ingredients for ingredient in ['dal', 'lentils']):
                return "Dal is incredibly nutritious! Try: 1. Dal Tadka - tempered lentils with spices (about 200 calories, 12g protein), 2. Dal Makhani - creamy and rich (about 280 calories, 14g protein), 3. Sambhar - South Indian lentil curry with vegetables (about 180 calories, 10g protein). Great source of plant protein!"

            else:
                ingredients_text = ', '.join(found_ingredients)
                return f"With {ingredients_text}, you have good options! For a balanced meal, try combining them with spices like turmeric, cumin, and coriander. Consider making a curry, stir-fry, or simple grilled preparation. Each cooking method brings out different flavors while keeping nutrition high!"

        # General meal planning responses
        elif any(word in message_lower for word in ['meal', 'plan', 'diet', 'nutrition']):
            return "For a healthy meal plan, focus on: 1. Include protein in every meal (chicken, eggs, dal, paneer), 2. Add fiber-rich foods (vegetables, whole grains), 3. Keep portions balanced (1/4 plate protein, 1/2 plate vegetables, 1/4 plate carbs), 4. Stay hydrated and eat at regular intervals. This approach provides sustained energy and proper nutrition!"

        elif any(word in message_lower for word in ['protein', 'muscle', 'workout']):
            return "For high protein meals try: 1. Grilled chicken with vegetables (30g protein), 2. Paneer bhurji with roti (25g protein), 3. Boiled eggs with dal (20g protein), 4. Fish curry with rice (28g protein). Aim for 20-30g protein per meal for muscle maintenance and satiety!"

        elif any(word in message_lower for word in ['weight', 'lose', 'fat', 'slim']):
            return "For weight management focus on: 1. Vegetable-heavy meals with lean protein, 2. Grilled or steamed preparations over fried, 3. Portion control with fiber-rich foods, 4. Regular meal timing. Try dishes like grilled chicken salad, vegetable soup with protein, or dal with lots of vegetables!"

        elif any(word in message_lower for word in ['quick', 'fast', 'easy', 'simple']):
            return "For quick meals try: 1. Scrambled eggs with toast (5 minutes), 2. Vegetable upma or poha (10 minutes), 3. Chicken sandwich or roll (8 minutes), 4. Instant oats with fruits and nuts (3 minutes). All are nutritious and can be made rapidly!"

        # Greetings and general queries
        elif any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return "Hello! I'm here to help you plan nutritious and delicious meals. You can tell me what ingredients you have, your dietary goals, or ask about specific recipes. What would you like to cook today?"

        elif any(word in message_lower for word in ['help', 'what', 'how']):
            return "I can help you with meal planning, recipe suggestions, nutrition advice, and cooking tips! Just tell me what ingredients you have available, your dietary preferences, or what type of meal you're looking for. I'll suggest practical recipes with calorie and protein information."

        else:
            return "I'd love to help you with meal planning! You can ask me about recipes, nutrition, meal prep ideas, or tell me what ingredients you have available. For example, try asking 'I have chicken and vegetables, what can I make?' or 'I need a high protein breakfast idea.' What would you like to know?"

    # ------------------------------------------------------------------
    # STRUCTURED MEAL PLAN — used by the Form tab / meal plan endpoint
    # ------------------------------------------------------------------

    def generate_meal_plan(
        self,
        available_ingredients: List[str],
        nutritional_goals: Dict[str, Any],
        dietary_restrictions: Optional[List[str]] = None,
        cuisine_preferences: Optional[List[str]] = None,
        meal_type: str = "balanced",
        num_meals: int = 5,
        cooking_time_limit: int = 30,
    ) -> Dict[str, Any]:
        """Generate a structured meal plan. Returns dict with meals list."""
        try:
            logger.info(f"Generating {meal_type} meal plan with {num_meals} meals")

            prompt = self._build_meal_plan_prompt(
                available_ingredients,
                nutritional_goals,
                dietary_restrictions,
                cuisine_preferences,
                meal_type,
                num_meals,
                cooking_time_limit,
            )

            response = self.gen_model.generate_content(prompt)
            meals = self._parse_meals_from_text(response.text, num_meals)

            # Optionally enrich with API Ninjas recipes
            if self.api_ninjas_key:
                for meal in meals:
                    recipe = self.get_recipe_suggestions(meal.get("name", ""), max_results=1)
                    if recipe:
                        meal["api_recipe"] = self.format_recipe_data(recipe[0])

            return {
                "success": True,
                "meal_type": meal_type,
                "available_ingredients": available_ingredients,
                "nutritional_goals": nutritional_goals,
                "meals": meals,
                "shopping_list": self._generate_shopping_list(meals),
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"generate_meal_plan error: {e}")
            return {"success": False, "error": str(e), "meal_type": meal_type}

    # ------------------------------------------------------------------
    # WEEKLY PLAN
    # ------------------------------------------------------------------

    def generate_weekly_meal_plan(
        self,
        available_ingredients: List[str],
        nutritional_goals: Dict[str, Any],
        dietary_restrictions: Optional[List[str]] = None,
        cuisine_preferences: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate a 7-day meal plan."""
        try:
            logger.info("Generating weekly meal plan")

            prompt = f"""Create a practical 7-day Indian meal plan.

Available ingredients: {', '.join(available_ingredients)}
Nutritional goals: {json.dumps(nutritional_goals)}
Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
Cuisine preferences: {', '.join(cuisine_preferences) if cuisine_preferences else 'Indian, varied'}

Requirements:
- Use the available ingredients as the base for most meals
- Each meal must have at least 20g protein
- Include breakfast, lunch, dinner, and one snack per day
- Cooking time under 45 minutes per meal
- Mix of cuisines but primarily Indian-friendly

For each day write:
Day [number] - [Day name]
Breakfast: [Name] - [2 line description] - [calories] cal, [protein]g protein
Lunch: [Name] - [2 line description] - [calories] cal, [protein]g protein  
Dinner: [Name] - [2 line description] - [calories] cal, [protein]g protein
Snack: [Name] - [brief] - [calories] cal

After all 7 days:
Shopping List:
[item 1]
[item 2]
...

Weekly totals: average [X] calories/day, average [X]g protein/day

Write in plain text only. No markdown, no asterisks, no headers with hashes.
"""

            response = self.gen_model.generate_content(prompt)
            clean = self._clean_text(response.text)

            return {
                "success": True,
                "weekly_plan": clean,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"generate_weekly_meal_plan error: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # NUTRITION ANALYSIS
    # ------------------------------------------------------------------

    def get_nutrition_analysis(
        self,
        meal_description: str,
        serving_size: str = "1 serving",
    ) -> Dict[str, Any]:
        """Analyse nutrition of a described meal. Returns structured dict."""
        try:
            logger.info(f"Analysing nutrition: {meal_description}")

            prompt = f"""Analyse the nutritional content of this meal and return ONLY a JSON object.

Meal: {meal_description}
Serving size: {serving_size}

Return this exact JSON structure with no other text before or after it:
{{
    "calories": <integer>,
    "protein_g": <number>,
    "carbs_g": <number>,
    "fat_g": <number>,
    "fiber_g": <number>,
    "sodium_mg": <integer>,
    "key_vitamins": ["<vitamin1>", "<vitamin2>"],
    "health_benefits": ["<benefit1>", "<benefit2>", "<benefit3>"],
    "notes": "<any important dietary notes in one sentence>"
}}"""

            response = self.gen_model.generate_content(prompt)
            nutrition = self._extract_json(response.text)

            return {
                "success": True,
                "meal": meal_description,
                "nutrition": nutrition,
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"get_nutrition_analysis error: {e}")
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # RECIPE SUGGESTIONS — API Ninjas
    # ------------------------------------------------------------------

    def get_recipe_suggestions(self, query: str, max_results: int = 5) -> Optional[List[Dict]]:
        """Fetch real recipes from API Ninjas. Returns None if not configured."""
        if not self.api_ninjas_key:
            return None
        try:
            response = requests.get(
                self.api_ninjas_recipe_base,
                params={"query": query},
                headers={"X-Api-Key": self.api_ninjas_key},
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    return data[:max_results]
            return None
        except Exception as e:
            logger.warning(f"API Ninjas error for '{query}': {e}")
            return None

    def get_recipes_from_gemini(
        self,
        ingredients: List[str],
        cuisine: Optional[str] = None,
        skill_level: str = "intermediate",
        dietary_needs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get recipe suggestions from Gemini for given ingredients."""
        try:
            prompt = f"""Suggest 3 recipes using these ingredients: {', '.join(ingredients)}

Cuisine: {cuisine or 'Indian or any'}
Skill level: {skill_level}
Dietary needs: {', '.join(dietary_needs) if dietary_needs else 'None'}

For each recipe write:
Recipe [number]: [Name]
Ingredients needed: [list each on a new line]
How to make it: [step by step, numbered]
Time: [X] minutes
Nutrition: [calories] cal, [protein]g protein, [carbs]g carbs, [fat]g fat
Why it is healthy: [one sentence]

Write in plain text only. No markdown formatting.
"""
            response = self.gen_model.generate_content(prompt)

            return {
                "success": True,
                "ingredients": ingredients,
                "recipes_text": self._clean_text(response.text),
                "generated_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"get_recipes_from_gemini error: {e}")
            return {"success": False, "error": str(e)}

    def format_recipe_data(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Format API Ninjas recipe for app display."""
        return {
            "title": recipe.get("title", "Recipe"),
            "ingredients": recipe.get("ingredients", []),
            "instructions": recipe.get("instructions", ""),
            "servings": recipe.get("servings", 2),
            "cook_time_minutes": recipe.get("cook_time_minutes"),
            "prep_time_minutes": recipe.get("prep_time_minutes"),
            "tags": recipe.get("tags", []),
            "source": "API Ninjas Recipe Database",
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_meal_plan_prompt(
        self,
        available_ingredients,
        nutritional_goals,
        dietary_restrictions,
        cuisine_preferences,
        meal_type,
        num_meals,
        cooking_time_limit,
    ) -> str:
        meal_type_desc = {
            "balanced": "40% carbs, 30% protein, 30% fat",
            "high_protein": "40%+ calories from protein, lower carbs",
            "weight_loss": "low calorie, high protein, high fibre, filling",
            "muscle_gain": "high calories and protein for muscle building",
        }.get(meal_type, "balanced macros")

        return f"""You are an expert nutritionist. Generate exactly {num_meals} meal suggestions.

Available ingredients: {', '.join(available_ingredients)}
Meal type: {meal_type} ({meal_type_desc})
Nutritional goals per meal: {json.dumps(nutritional_goals)}
Dietary restrictions: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
Cuisine: {', '.join(cuisine_preferences) if cuisine_preferences else 'Indian preferred, varied'}
Max cooking time: {cooking_time_limit} minutes

For each meal write exactly this format:

MEAL [number]: [Meal name]
Cuisine: [type]
Cooking time: [X] minutes
Difficulty: [Easy/Medium/Hard]
Ingredients: [ingredient 1], [ingredient 2], [ingredient 3]
How to cook: [3 to 5 step instructions as numbered list]
Nutrition: [calories] cal, [protein]g protein, [carbs]g carbs, [fat]g fat
Why healthy: [one sentence backed by nutrition science]

Write in plain text only. No markdown, no asterisks, no bold text.
"""

    def _parse_meals_from_text(self, text: str, expected_count: int) -> List[Dict[str, Any]]:
        """
        Parse structured meal text into a list of dicts.
        Handles plain text format from _build_meal_plan_prompt.
        """
        meals = []
        # Split on MEAL [n]: pattern
        blocks = re.split(r"MEAL\s+\d+\s*:", text, flags=re.IGNORECASE)
        blocks = [b.strip() for b in blocks if b.strip()]

        for block in blocks:
            lines = block.split("\n")
            meal: Dict[str, Any] = {}

            # First non-empty line is the name
            for line in lines:
                if line.strip():
                    meal["name"] = line.strip()
                    break

            # Extract fields by label
            full_text = "\n".join(lines)
            meal["cuisine"] = self._extract_field(full_text, "Cuisine")
            meal["cooking_time"] = self._extract_field(full_text, "Cooking time")
            meal["difficulty"] = self._extract_field(full_text, "Difficulty")
            meal["ingredients"] = [
                i.strip()
                for i in self._extract_field(full_text, "Ingredients").split(",")
                if i.strip()
            ]
            meal["instructions"] = self._extract_field(full_text, "How to cook")
            meal["nutrition_text"] = self._extract_field(full_text, "Nutrition")
            meal["why_healthy"] = self._extract_field(full_text, "Why healthy")
            meal["description"] = block[:300]

            if meal.get("name"):
                meals.append(meal)

        # If parsing found nothing (Gemini ignored the format), return raw
        if not meals:
            logger.warning("Could not parse meals from text, returning raw response")
            return [{"name": "Meal suggestions", "description": self._clean_text(text)}]

        return meals[:expected_count]

    def _extract_field(self, text: str, label: str) -> str:
        """Extract value after a label like 'Cuisine: Indian'"""
        pattern = rf"(?i){re.escape(label)}\s*:\s*(.+?)(?=\n[A-Z][a-z]+\s*:|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Safely extract a JSON object from Gemini response text."""
        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?", "", text).strip()
        try:
            # Try direct parse first
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Find first { ... } block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning("Could not extract JSON from response")
        return {"raw_analysis": text}

    def _clean_text(self, text: str) -> str:
        """
        Strip markdown formatting so Flutter Text() displays cleanly.
        Call this on EVERY string returned to the app.
        """
        # Remove bold/italic markers
        text = re.sub(r"\*{1,3}(.+?)\*{1,3}", r"\1", text)
        # Remove markdown headers
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # Remove leading dashes/bullets
        text = re.sub(r"^[\-\•\*]\s+", "", text, flags=re.MULTILINE)
        # Remove trailing spaces
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        # Collapse more than 2 consecutive blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _generate_shopping_list(self, meals: List[Dict]) -> List[str]:
        """Consolidate all ingredients across meals into a sorted shopping list."""
        items: set = set()
        for meal in meals:
            ingredients = meal.get("ingredients", [])
            if isinstance(ingredients, list):
                items.update(i.strip() for i in ingredients if i.strip())
            elif isinstance(ingredients, str):
                items.update(i.strip() for i in ingredients.split(",") if i.strip())
        return sorted(items)


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_meal_planner: Optional[MealPlannerAgent] = None


def get_meal_planner() -> MealPlannerAgent:
    global _meal_planner
    # Force fresh instance every time to pick up prompt changes
    logger.info("Creating fresh MealPlannerAgent instance with updated prompt...")
    _meal_planner = MealPlannerAgent()
    logger.info(f"New agent initialized. System prompt length: {len(SYSTEM_PROMPT)} chars")
    return _meal_planner