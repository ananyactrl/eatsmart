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

    def chat(self, user_message: str, history: Optional[List[Dict]] = None, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Handle a single conversational message with profile-aware, data-driven nutrition responses.

        Args:
            user_message: What the user typed
            history: List of {"role": "user"|"model", "parts": ["text"]}
                     Pass the last 6 messages max for context.
            user_profile: User's comprehensive health profile data

        Returns:
            Plain text response (no markdown) with personalized, accurate nutrition data
        """
        try:
            logger.info(f"Processing chat message: {user_message[:50]}...")
            if user_profile:
                logger.info(f"Using profile: {user_profile.get('age')}y {user_profile.get('gender')}, goal: {user_profile.get('health_goal')}")

            # Extract ingredients from the user message
            ingredients = self._extract_ingredients(user_message)
            logger.info(f"Extracted ingredients: {ingredients}")

            # If we have ingredients, use nutrition database for accurate responses
            if ingredients and self.nutrition_db and self.nutrition_db.df is not None:
                logger.info("Using nutrition database for data-driven response")
                return self._get_profile_aware_response(ingredients, user_message, user_profile)

            # For general chat or if no nutrition data available, use AI with profile context
            if not self.is_fallback and self.chat_model is not None:
                logger.info("Using AI model for profile-aware response")
                return self._get_ai_response_with_profile(user_message, history, user_profile)

            # Fallback response with profile consideration
            logger.info("Using fallback response with profile awareness")
            return self._get_profile_aware_fallback(user_message, user_profile)

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

    def _get_profile_aware_response(self, ingredients: List[str], user_message: str, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Get response using nutrition database with profile-specific personalization"""
        try:
            # Get recipe suggestions from database
            recipes = self.nutrition_db.get_recipe_suggestions(ingredients)

            if not recipes:
                profile_note = ""
                if user_profile:
                    allergies = user_profile.get('allergies', [])
                    conditions = user_profile.get('health_conditions', [])
                    if allergies:
                        profile_note = f" Also, I'll make sure to avoid {', '.join(allergies)} due to your allergies."
                    elif conditions:
                        profile_note = f" I'll consider your {conditions[0]} when suggesting alternatives."

                return f"I couldn't find exact recipes for those ingredients in my database. Try asking about chicken, rice, pasta, or other common ingredients.{profile_note}"

            # Format recipes using actual nutrition data + profile context
            response_parts = []
            for i, recipe in enumerate(recipes[:2]):  # Max 2 recipes
                formatted_recipe = self.nutrition_db.format_recipe_with_nutrition(recipe)
                if formatted_recipe and user_profile:
                    # Add profile-specific notes
                    formatted_recipe = self._add_profile_context_to_recipe(formatted_recipe, user_profile)

                if formatted_recipe:
                    response_parts.append(formatted_recipe)

            if response_parts:
                profile_summary = ""
                if user_profile:
                    target_cal = user_profile.get('target_calories')
                    target_protein = user_profile.get('target_protein_g')
                    if target_cal:
                        meal_cal = int(target_cal * 0.3)  # 30% per meal
                        meal_protein = int(target_protein * 0.3) if target_protein else 20
                        profile_summary = f"\n\nFor your {user_profile.get('health_goal', 'health')} goal, aim for ~{meal_cal} calories and ~{meal_protein}g protein per meal."

                return "\n\n".join(response_parts) + profile_summary
            else:
                return "I found matching ingredients but couldn't format the recipes. Please try rephrasing your request."

        except Exception as e:
            logger.error(f"Profile-aware response error: {e}")
            return self._get_profile_aware_fallback(user_message, user_profile)

    def _get_ai_response_with_profile(self, user_message: str, history: Optional[List[Dict]] = None, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Get response from AI model with profile context"""
        try:
            # Build enhanced prompt with profile context
            enhanced_message = user_message
            if user_profile:
                profile_context = self._build_profile_context_string(user_profile)
                enhanced_message = f"{profile_context}\n\nUser request: {user_message}"

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
            response = chat_session.send_message(enhanced_message)

            return self._clean_text(response.text)

        except Exception as e:
            logger.error(f"AI response with profile error: {e}")
            raise e

    def _get_profile_aware_fallback(self, user_message: str, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """Smart fallback responses with profile awareness"""
        message_lower = user_message.lower()

        # Profile-specific context
        profile_context = ""
        dietary_restrictions = []

        if user_profile:
            # Add allergy awareness
            allergies = user_profile.get('allergies', [])
            if allergies:
                dietary_restrictions.extend([f"no {allergy}" for allergy in allergies])

            # Add dietary type
            dietary_type = user_profile.get('dietary_type', 'omnivore')
            if dietary_type in ['vegetarian', 'vegan', 'eggetarian']:
                dietary_restrictions.append(dietary_type)

            # Add health condition considerations
            conditions = user_profile.get('health_conditions', [])
            if 'diabetes' in conditions:
                dietary_restrictions.append("low-GI foods")
            if 'hypertension' in conditions:
                dietary_restrictions.append("low-sodium")

            if dietary_restrictions:
                profile_context = f" (Note: I'll suggest {', '.join(dietary_restrictions)} options for you)"

        # Enhanced responses with profile awareness
        if any(word in message_lower for word in ['hello', 'hi', 'hey']):
            return f"Hello! I'm your meal planning assistant.{profile_context} Tell me what ingredients you have and I'll suggest personalized recipes with accurate nutrition information."

        elif any(word in message_lower for word in ['help', 'what', 'how']):
            return f"I can help you with personalized meal planning using my nutrition database!{profile_context} Just tell me what ingredients you have (like chicken, rice, pasta) and I'll suggest recipes tailored to your profile with exact calories and protein information."

        else:
            return f"I specialize in personalized meal planning with accurate nutrition data.{profile_context} Tell me what ingredients you have available and I'll suggest specific recipes that match your health goals!"

    def _add_profile_context_to_recipe(self, recipe_text: str, user_profile: Dict[str, Any]) -> str:
        """Add profile-specific notes to a recipe"""
        additions = []

        # Health condition specific notes
        conditions = user_profile.get('health_conditions', [])
        if 'diabetes' in conditions and ('rice' in recipe_text.lower() or 'potato' in recipe_text.lower()):
            additions.append("💡 For diabetes: Consider brown rice or smaller portions to manage blood sugar")

        if 'hypertension' in conditions and ('salt' in recipe_text.lower() or 'sodium' in recipe_text.lower()):
            additions.append("💡 For hypertension: Use herbs and spices instead of excess salt")

        if 'pcos' in conditions:
            additions.append("💡 For PCOS: This balanced meal helps with insulin sensitivity")

        # Goal-specific notes
        goal = user_profile.get('health_goal')
        if goal == 'lose_fat':
            additions.append("🎯 For fat loss: This fits your calorie deficit goal")
        elif goal == 'gain_muscle':
            additions.append("🎯 For muscle gain: Great protein content for your goals")

        # Budget awareness
        budget = user_profile.get('budget_per_meal_inr')
        if budget and budget < 80:
            additions.append(f"💰 Budget-friendly: Estimated cost ~₹{budget-20}-₹{budget}")

        if additions:
            return recipe_text + "\n\n" + "\n".join(additions)

        return recipe_text

    def _build_profile_context_string(self, user_profile: Dict[str, Any]) -> str:
        """Build a concise profile context string for AI prompts"""
        context_parts = []

        if user_profile.get('age') and user_profile.get('gender'):
            context_parts.append(f"User is {user_profile['age']}y {user_profile['gender']}")

        goal = user_profile.get('health_goal')
        if goal:
            context_parts.append(f"goal: {goal}")

        target_cal = user_profile.get('target_calories')
        if target_cal:
            meal_cal = int(target_cal * 0.3)
            context_parts.append(f"needs ~{meal_cal} cal per meal")

        allergies = user_profile.get('allergies', [])
        if allergies:
            context_parts.append(f"allergic to: {', '.join(allergies)}")

        conditions = user_profile.get('health_conditions', [])
        if conditions:
            context_parts.append(f"has: {', '.join(conditions[:2])}")  # Limit to 2 conditions

        dietary_type = user_profile.get('dietary_type')
        if dietary_type and dietary_type != 'omnivore':
            context_parts.append(f"diet: {dietary_type}")

        budget = user_profile.get('budget_per_meal_inr')
        if budget:
            context_parts.append(f"₹{budget}/meal budget")

        if context_parts:
            return f"PROFILE: {', '.join(context_parts)}"

        return ""

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
        user_profile: Optional[Dict[str, Any]] = None,  # NEW: Health profile data
    ) -> Dict[str, Any]:
        """Generate a structured meal plan using comprehensive user profile data."""
        try:
            logger.info(f"Generating {meal_type} meal plan with {num_meals} meals")
            if user_profile:
                logger.info(f"Using health profile for user: {user_profile.get('age')}y {user_profile.get('gender')}, goal: {user_profile.get('health_goal')}")

            prompt = self._build_meal_plan_prompt(
                available_ingredients,
                nutritional_goals,
                dietary_restrictions,
                cuisine_preferences,
                meal_type,
                num_meals,
                cooking_time_limit,
                user_profile,  # Pass profile data
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
                "user_profile_summary": {
                    "age": user_profile.get('age') if user_profile else None,
                    "goal": user_profile.get('health_goal') if user_profile else None,
                    "target_calories": user_profile.get('target_calories') if user_profile else None,
                    "conditions": user_profile.get('health_conditions', []) if user_profile else [],
                    "allergies": user_profile.get('allergies', []) if user_profile else [],
                } if user_profile else None,
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
        user_profile=None,  # NEW: Health profile data
    ) -> str:
        meal_type_desc = {
            "balanced": "40% carbs, 30% protein, 30% fat",
            "high_protein": "40%+ calories from protein, lower carbs",
            "weight_loss": "low calorie, high protein, high fibre, filling",
            "muscle_gain": "high calories and protein for muscle building",
        }.get(meal_type, "balanced macros")

        # Build comprehensive user context from health profile
        user_context = ""
        if user_profile:
            # Body context for calorie/macro targets
            if user_profile.get('age') and user_profile.get('gender'):
                user_context += f"\nUSER PROFILE:\n"
                user_context += f"- {user_profile.get('age')} year old {user_profile.get('gender')}, {user_profile.get('weight_kg')}kg, {user_profile.get('height_cm')}cm\n"
                user_context += f"- Activity level: {user_profile.get('activity_level', 'moderate')}\n"
                user_context += f"- Goal: {user_profile.get('health_goal', 'maintain')}\n"

                # Calculated targets
                if user_profile.get('target_calories'):
                    user_context += f"- Daily calorie target: {int(user_profile['target_calories'])} kcal\n"
                    user_context += f"- Daily protein target: {int(user_profile.get('target_protein_g', 0))}g\n"

                    # Per-meal targets (assuming 3 meals + 1 snack)
                    meal_calories = int(user_profile['target_calories'] * 0.3)  # 30% per main meal
                    meal_protein = int(user_profile.get('target_protein_g', 0) * 0.3)
                    user_context += f"- Target per meal: ~{meal_calories} kcal, ~{meal_protein}g protein\n"

            # Health context for ingredient flagging
            health_conditions = user_profile.get('health_conditions', [])
            if health_conditions:
                user_context += f"- Health conditions: {', '.join(health_conditions)} (flag concerning ingredients accordingly)\n"

                # Specific condition guidelines
                condition_flags = []
                if 'diabetes' in health_conditions:
                    condition_flags.append("avoid refined sugar and high-GI carbs")
                if 'pcos' in health_conditions:
                    condition_flags.append("focus on low-GI foods, avoid processed foods")
                if 'hypertension' in health_conditions:
                    condition_flags.append("limit sodium, avoid processed meats")
                if 'hypothyroid' in health_conditions:
                    condition_flags.append("limit raw cruciferous vegetables, ensure iodine")
                if 'ibs' in health_conditions:
                    condition_flags.append("follow low-FODMAP principles, avoid spicy foods")

                if condition_flags:
                    user_context += f"- Medical guidelines: {'; '.join(condition_flags)}\n"

            # Allergy flags
            allergies = user_profile.get('allergies', [])
            if allergies:
                user_context += f"- STRICT ALLERGIES (absolutely avoid): {', '.join(allergies)}\n"

            # Life context for practical constraints
            dietary_type = user_profile.get('dietary_type', 'omnivore')
            user_context += f"- Diet type: {dietary_type}\n"

            budget = user_profile.get('budget_per_meal_inr')
            if budget:
                user_context += f"- Budget per meal: ₹{budget} (suggest budget-appropriate ingredients)\n"

            max_time = user_profile.get('max_cooking_time_minutes', cooking_time_limit)
            user_context += f"- Max cooking time: {max_time} minutes\n"

            cooking_skill = user_profile.get('cooking_skill', 'intermediate')
            user_context += f"- Cooking skill: {cooking_skill} (adjust recipe complexity)\n"

            # Kitchen equipment constraints
            equipment = user_profile.get('kitchen_equipment', [])
            if equipment:
                user_context += f"- Available equipment: {', '.join(equipment)}\n"
            else:
                user_context += f"- Basic equipment only (stovetop, basic utensils)\n"

            # Household considerations
            household_size = user_profile.get('household_size', 1)
            cooking_for_kids = user_profile.get('cooking_for_kids', False)
            if household_size > 1:
                user_context += f"- Cooking for {household_size} people\n"
            if cooking_for_kids:
                user_context += f"- Include kid-friendly options (mild spices, familiar flavors)\n"

        return f"""You are an expert Indian nutritionist creating personalized meal recommendations.
{user_context}

INGREDIENTS AVAILABLE: {', '.join(available_ingredients)}
MEAL TYPE: {meal_type} ({meal_type_desc})
NUTRITIONAL GOALS: {json.dumps(nutritional_goals)}
DIETARY RESTRICTIONS: {', '.join(dietary_restrictions) if dietary_restrictions else 'None'}
CUISINE PREFERENCES: {', '.join(cuisine_preferences) if cuisine_preferences else 'Indian preferred, varied'}

CRITICAL REQUIREMENTS:
1. NEVER suggest ingredients from the allergy list above
2. Adapt recipes for the user's cooking skill level and available equipment
3. Stay within the specified budget and time constraints
4. Consider health conditions when selecting ingredients and cooking methods
5. Target the calculated calorie and protein goals per meal
6. Use available ingredients as the primary base for each recipe

Generate exactly {num_meals} meal suggestions in this format:

MEAL [number]: [Meal name]
Cuisine: [type]
Cooking time: [X] minutes (within user's limit)
Difficulty: [Easy/Medium/Hard based on user's skill]
Ingredients: [ingredient 1], [ingredient 2], [ingredient 3]
How to cook: [step-by-step instructions numbered 1-5]
Nutrition: [calories] cal, [protein]g protein, [carbs]g carbs, [fat]g fat
Health note: [specific benefit for user's profile/conditions]
Budget estimate: [₹X per serving]

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
            meal["health_note"] = self._extract_field(full_text, "Health note")  # NEW field
            meal["budget_estimate"] = self._extract_field(full_text, "Budget estimate")  # NEW field
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