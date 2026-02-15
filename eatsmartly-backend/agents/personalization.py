"""
Personalization Agent for EatSmartly.
Filters food recommendations based on user health profiles.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, text, Table, Column, String, Float, Integer, DateTime, MetaData
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from config import settings
from agents.utils import setup_logger, calculate_health_score


logger = setup_logger(__name__, settings.LOG_LEVEL)


class PersonalizationAgent:
    """Agent responsible for personalizing food recommendations."""
    
    def __init__(self):
        """Initialize the personalization agent."""
        try:
            self.db_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
            self.Session = sessionmaker(bind=self.db_engine)
            self._init_database()
        except Exception as e:
            logger.warning(f"Database connection failed: {e}. Running without user profiles.")
            self.db_engine = None
            self.Session = None
        
        logger.info("PersonalizationAgent initialized")
    
    def _init_database(self):
        """Initialize user profiles table."""
        if not self.db_engine:
            return
            
        try:
            # Test connection
            with self.db_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
            metadata = MetaData()
            
            user_profiles_table = Table(
                'user_profiles', metadata,
                Column('user_id', String(255), primary_key=True),
                Column('age', Integer),
                Column('gender', String(20)),
                Column('height_cm', Float),
                Column('weight_kg', Float),
                Column('activity_level', String(50)),
                Column('health_goal', String(100)),
                Column('allergies', String(500)),  # Comma-separated
                Column('health_conditions', String(500)),  # Comma-separated
                Column('dietary_restrictions', String(500)),  # Comma-separated
                Column('daily_calorie_target', Integer),
                Column('daily_protein_target_g', Float),
                Column('daily_carbs_target_g', Float),
                Column('daily_fat_target_g', Float),
                Column('created_at', DateTime, default=datetime.utcnow),
                Column('updated_at', DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            )
            
            metadata.create_all(self.db_engine)
            logger.info("User profiles table ready")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve user health profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile dictionary or None
        """
        if not self.Session:
            logger.warning(f"No database connection, using default profile for: {user_id}")
            return self._get_default_profile(user_id)
            
        try:
            with self.Session() as session:
                result = session.execute(
                    text("SELECT * FROM user_profiles WHERE user_id = :user_id"),
                    {"user_id": user_id}
                ).fetchone()
                
                if result:
                    return {
                        "user_id": result.user_id,
                        "age": result.age,
                        "gender": result.gender,
                        "height_cm": result.height_cm,
                        "weight_kg": result.weight_kg,
                        "activity_level": result.activity_level,
                        "health_goal": result.health_goal,
                        "allergies": result.allergies.split(",") if result.allergies else [],
                        "health_conditions": result.health_conditions.split(",") if result.health_conditions else [],
                        "dietary_restrictions": result.dietary_restrictions.split(",") if result.dietary_restrictions else [],
                        "daily_calorie_target": result.daily_calorie_target,
                        "daily_protein_target_g": result.daily_protein_target_g,
                        "daily_carbs_target_g": result.daily_carbs_target_g,
                        "daily_fat_target_g": result.daily_fat_target_g
                    }
                
                # Return default profile if not found
                logger.warning(f"User profile not found: {user_id}, using defaults")
                return self._get_default_profile(user_id)
                
        except Exception as e:
            logger.error(f"Error retrieving user profile: {e}")
            return self._get_default_profile(user_id)
    
    def _get_default_profile(self, user_id: str) -> Dict[str, Any]:
        """Return default user profile."""
        return {
            "user_id": user_id,
            "age": 30,
            "gender": "unspecified",
            "height_cm": 170,
            "weight_kg": 70,
            "activity_level": "moderate",
            "health_goal": "maintain_health",
            "allergies": [],
            "health_conditions": [],
            "dietary_restrictions": [],
            "daily_calorie_target": 2000,
            "daily_protein_target_g": 50,
            "daily_carbs_target_g": 250,
            "daily_fat_target_g": 65
        }
    
    def save_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Save or update user profile.
        
        Args:
            user_id: User identifier
            profile_data: Profile information
            
        Returns:
            True if successful
        """
        if not self.Session:
            logger.warning(f"No database connection, cannot save profile for: {user_id}")
            return False
            
        try:
            with self.Session() as session:
                allergies_str = ",".join(profile_data.get("allergies", []))
                conditions_str = ",".join(profile_data.get("health_conditions", []))
                restrictions_str = ",".join(profile_data.get("dietary_restrictions", []))
                
                session.execute(
                    text("""
                        INSERT INTO user_profiles 
                        (user_id, age, gender, height_cm, weight_kg, activity_level, 
                         health_goal, allergies, health_conditions, dietary_restrictions,
                         daily_calorie_target, daily_protein_target_g, daily_carbs_target_g,
                         daily_fat_target_g, updated_at)
                        VALUES 
                        (:user_id, :age, :gender, :height_cm, :weight_kg, :activity_level,
                         :health_goal, :allergies, :health_conditions, :dietary_restrictions,
                         :daily_calorie_target, :daily_protein_target_g, :daily_carbs_target_g,
                         :daily_fat_target_g, :updated_at)
                        ON CONFLICT (user_id) DO UPDATE SET
                            age = EXCLUDED.age,
                            gender = EXCLUDED.gender,
                            height_cm = EXCLUDED.height_cm,
                            weight_kg = EXCLUDED.weight_kg,
                            activity_level = EXCLUDED.activity_level,
                            health_goal = EXCLUDED.health_goal,
                            allergies = EXCLUDED.allergies,
                            health_conditions = EXCLUDED.health_conditions,
                            dietary_restrictions = EXCLUDED.dietary_restrictions,
                            daily_calorie_target = EXCLUDED.daily_calorie_target,
                            daily_protein_target_g = EXCLUDED.daily_protein_target_g,
                            daily_carbs_target_g = EXCLUDED.daily_carbs_target_g,
                            daily_fat_target_g = EXCLUDED.daily_fat_target_g,
                            updated_at = EXCLUDED.updated_at
                    """),
                    {
                        "user_id": user_id,
                        "age": profile_data.get("age"),
                        "gender": profile_data.get("gender"),
                        "height_cm": profile_data.get("height_cm"),
                        "weight_kg": profile_data.get("weight_kg"),
                        "activity_level": profile_data.get("activity_level"),
                        "health_goal": profile_data.get("health_goal"),
                        "allergies": allergies_str,
                        "health_conditions": conditions_str,
                        "dietary_restrictions": restrictions_str,
                        "daily_calorie_target": profile_data.get("daily_calorie_target"),
                        "daily_protein_target_g": profile_data.get("daily_protein_target_g"),
                        "daily_carbs_target_g": profile_data.get("daily_carbs_target_g"),
                        "daily_fat_target_g": profile_data.get("daily_fat_target_g"),
                        "updated_at": datetime.utcnow()
                    }
                )
                session.commit()
                logger.info(f"User profile saved: {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving user profile: {e}")
            return False
    
    def evaluate_food_safety(
        self, 
        food_data: Dict[str, Any], 
        user_profile: Dict[str, Any],
        ingredient_analysis: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate if food is safe for user based on profile.
        
        Args:
            food_data: Standardized food data
            user_profile: User health profile
            
        Returns:
            Safety evaluation with verdict and alerts
        """
        alerts = []
        warnings = []
        is_safe = True
        risk_level = "low"
        
        # Detect ultra-processed instant noodles and similar products
        product_name = (food_data.get("product_name", "") or "").lower()
        brand = (food_data.get("brand", "") or "").lower()
        ingredients_raw = food_data.get("ingredients", [])
        if isinstance(ingredients_raw, list):
            ingredients = " ".join(ingredients_raw).lower() if ingredients_raw else ""
        else:
            ingredients = ingredients_raw.lower() if ingredients_raw else ""
        
        is_instant_noodles = False
        instant_noodle_indicators = [
            "maggi", "noodles", "instant noodles", "ramen", "2 minute", "top ramen",
            "yippee", "wai wai", "sunfeast yippee", "knorr", "nissin", "indomie"
        ]
        
        for indicator in instant_noodle_indicators:
            if indicator in product_name or indicator in brand:
                is_instant_noodles = True
                break
        
        # Check ingredients for MSG, maida, palm oil - common in instant noodles
        if not is_instant_noodles:
            unhealthy_markers = ["msg", "monosodium glutamate", "maida", "palm oil", "flavor enhancer"]
            marker_count = sum(1 for marker in unhealthy_markers if marker in ingredients)
            if marker_count >= 2 and "noodle" in ingredients:
                is_instant_noodles = True
        
        # Use ingredient analysis results if available
        unhealthy_score = 0
        ingredient_warnings = []
        if ingredient_analysis:
            unhealthy_score = ingredient_analysis.get("unhealthy_score", 0)
            ingredient_warnings = ingredient_analysis.get("warnings", [])
            
            # Add ingredient analysis warnings to our alerts
            for warning in ingredient_warnings:
                if warning["severity"] == "high":
                    alerts.append(f"🚨 {warning['message']}")
                    if risk_level == "low":
                        risk_level = "medium"
                elif warning["severity"] == "medium":
                    warnings.append(f"⚠️ {warning['message']}")
                else:
                    warnings.append(f"ℹ️ {warning['message']}")
            
            # Adjust risk level based on unhealthy score
            if unhealthy_score >= 3:
                risk_level = "high"
                if not is_instant_noodles:  # Don't duplicate for noodles
                    alerts.append("🚨 HIGHLY PROCESSED: Contains multiple unhealthy ingredients")
            elif unhealthy_score >= 2 and risk_level == "low":
                risk_level = "medium"
        
        # Check allergens
        food_allergens = food_data.get("allergens", [])
        user_allergies = user_profile.get("allergies", [])
        
        allergen_matches = [a for a in food_allergens if a in user_allergies]
        if allergen_matches:
            is_safe = False
            risk_level = "high"
            alerts.append(f"⛔ ALLERGEN ALERT: Contains {', '.join(allergen_matches)}")
        
        # Check dietary restrictions
        restrictions = user_profile.get("dietary_restrictions", [])
        ingredients_raw = food_data.get("ingredients", [])
        # Handle both list and string formats
        if isinstance(ingredients_raw, list):
            ingredients = " ".join(ingredients_raw).lower() if ingredients_raw else ""
        else:
            ingredients = ingredients_raw.lower() if ingredients_raw else ""
        
        if "vegetarian" in restrictions:
            if any(meat in ingredients for meat in ["beef", "chicken", "pork", "fish", "meat"]):
                is_safe = False
                risk_level = "medium"
                alerts.append("⚠️ Contains meat (vegetarian restriction)")
        
        if "vegan" in restrictions:
            if any(animal in ingredients for animal in ["milk", "egg", "honey", "dairy", "meat", "fish"]):
                is_safe = False
                risk_level = "medium"
                alerts.append("⚠️ Contains animal products (vegan restriction)")
        
        if "gluten_free" in restrictions:
            if any(gluten in ingredients for gluten in ["wheat", "barley", "rye", "gluten"]):
                is_safe = False
                risk_level = "medium"
                alerts.append("⚠️ Contains gluten (gluten-free restriction)")
        
        # Check diabetes condition for sugar
        conditions = user_profile.get("health_conditions", [])
        if "diabetes" in conditions:
            sugar = food_data.get("sugar_g", 0) or 0
            if sugar > 15:
                warnings.append(f"⚠️ High sugar ({sugar:.1f}g) - Monitor blood glucose")
                if risk_level == "low":
                    risk_level = "medium"
        
        # INSTANT NOODLES WARNING - Critical health risks
        if is_instant_noodles:
            risk_level = "high"
            alerts.append("🚨 ULTRA-PROCESSED: Instant noodles are highly processed and unhealthy")
            alerts.append("⚠️ Contains excessive sodium (often >1500mg per serving)")
            alerts.append("⚠️ Made with refined flour (maida) - high glycemic index")
            alerts.append("⚠️ Contains harmful additives like MSG and TBHQ")
            
            # Condition-specific warnings for instant noodles
            if "diabetes" in conditions or "prediabetes" in conditions:
                alerts.append("❌ AVOID: Refined carbs spike blood sugar - Very dangerous for diabetics")
            if "hypertension" in conditions or "high_blood_pressure" in conditions:
                alerts.append("❌ AVOID: Extremely high sodium can worsen blood pressure")
            if "heart_disease" in conditions or "cardiovascular" in conditions:
                alerts.append("❌ AVOID: High sodium and saturated fat harm heart health")
            if "kidney_disease" in conditions or "renal" in conditions:
                alerts.append("❌ AVOID: High sodium and phosphates stress kidneys")
            if "obesity" in conditions or user_profile.get("health_goal") == "weight_loss":
                alerts.append("❌ AVOID: High calories, low nutrition - Hinders weight loss")
            
            warnings.append("💡 Replace with: Homemade vegetable soup, whole wheat pasta, or brown rice")
            warnings.append("💡 If consumed: Add vegetables, eggs, and limit to once per month")
        
        if "hypertension" in conditions or "high_blood_pressure" in conditions:
            sodium = food_data.get("sodium_mg", 0) or 0
            if sodium > 500:
                warnings.append(f"⚠️ High sodium ({sodium:.0f}mg) - May raise blood pressure")
                if risk_level == "low":
                    risk_level = "medium"
        
        if "heart_disease" in conditions or "high_cholesterol" in conditions:
            sat_fat = food_data.get("saturated_fat_g", 0) or 0
            if sat_fat > 5:
                warnings.append(f"⚠️ High saturated fat ({sat_fat:.1f}g) - Limit intake")
                if risk_level == "low":
                    risk_level = "medium"
        
        # Check health goals
        health_goal = user_profile.get("health_goal", "")
        
        if health_goal == "weight_loss":
            calories = food_data.get("calories", 0) or 0
            if calories > 300:
                warnings.append(f"💡 High calorie ({calories:.0f}) - Consider portion control")
        
        if health_goal == "muscle_gain":
            protein = food_data.get("protein_g", 0) or 0
            if protein < 10:
                warnings.append(f"💡 Low protein ({protein:.1f}g) - Add protein source")
        
        # Calculate overall health score (pass product info for instant noodles detection)
        product_name = food_data.get("product_name", "") or ""
        brand = food_data.get("brand", "") or ""
        health_score = calculate_health_score(food_data, product_name, brand)
        
        # Additional penalty for instant noodles (in case the function didn't catch it)
        if is_instant_noodles and health_score > 35:
            # Force health score to be very low
            health_score = min(health_score, 30)
            risk_level = "high"
            logger.info(f"🚨 Instant noodles detected - Health score capped at {health_score}")
        
        # Determine verdict based on health score and risk level
        # Health Score Ranges:
        # 70-100: Safe (green) - Healthy choice
        # 43-69:  Caution (yellow) - Okay in moderation (includes butter, oils)
        # 0-42:   Avoid (red) - Unhealthy choice (sugary drinks, ultra-processed)
        
        if not is_safe or risk_level == "high":
            # Allergens or critical restrictions
            verdict = "avoid"
        elif health_score >= 70 and risk_level == "low":
            verdict = "safe"
        elif health_score >= 43:
            verdict = "caution"
        else:
            verdict = "avoid"
        
        return {
            "verdict": verdict,
            "is_safe": is_safe,
            "risk_level": risk_level,
            "health_score": round(health_score, 1),
            "alerts": alerts,
            "warnings": warnings,
            "allergen_matches": allergen_matches
        }
    
    def generate_suggestions(
        self, 
        food_data: Dict[str, Any], 
        user_profile: Dict[str, Any],
        evaluation: Dict[str, Any]
    ) -> List[str]:
        """
        Generate personalized suggestions based on food and user profile.
        
        Args:
            food_data: Standardized food data
            user_profile: User health profile
            evaluation: Safety evaluation result
            
        Returns:
            List of personalized suggestions
        """
        suggestions = []
        
        # If food is unsafe, suggest avoiding
        if evaluation["verdict"] == "avoid":
            suggestions.append("❌ Avoid this product due to allergens or restrictions")
            return suggestions
        
        # Health goal-specific suggestions
        health_goal = user_profile.get("health_goal", "")
        
        if health_goal == "weight_loss":
            suggestions.append("🎯 Weight Loss Tips:")
            suggestions.append("  • Stick to single serving size")
            suggestions.append("  • Pair with vegetables for volume")
            suggestions.append("  • Drink water before eating")
        
        elif health_goal == "muscle_gain":
            protein = food_data.get("protein_g", 0) or 0
            if protein >= 10:
                suggestions.append("💪 Good protein content - supports muscle growth")
            else:
                suggestions.append("💡 Add protein: eggs, chicken, or protein shake")
        
        elif health_goal == "heart_health":
            suggestions.append("❤️ Heart Health:")
            suggestions.append("  • Choose whole grain versions when possible")
            suggestions.append("  • Watch sodium intake throughout the day")
        
        # Nutrient-specific suggestions
        fiber = food_data.get("fiber_g", 0) or 0
        if fiber < 2:
            suggestions.append("🌾 Low fiber - add vegetables or whole grains")
        
        sugar = food_data.get("sugar_g", 0) or 0
        if sugar > 10:
            suggestions.append("🍬 High sugar - limit to occasional treat")
        
        # Portion control suggestion
        calories = food_data.get("calories", 0) or 0
        if calories > 250:
            suggestions.append(f"⚖️ Portion control: {calories:.0f} cal per serving")
        
        return suggestions
