-- ====================================================================
-- MIGRATION: DROP EXISTING AND CREATE COMPREHENSIVE HEALTH PROFILE SYSTEM
-- FIXED VERSION - Proper array type casting for PostgreSQL
-- ====================================================================

-- Step 1: Drop existing tables and their dependencies
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS user_meal_history CASCADE;
DROP TABLE IF EXISTS user_nutrition_analysis CASCADE;
DROP TABLE IF EXISTS health_condition_guidelines CASCADE;
DROP TABLE IF EXISTS allergy_ingredients CASCADE;

-- Step 2: Drop existing enum types if they exist
DROP TYPE IF EXISTS activity_level CASCADE;
DROP TYPE IF EXISTS health_goal CASCADE;
DROP TYPE IF EXISTS dietary_type CASCADE;
DROP TYPE IF EXISTS cooking_skill CASCADE;
DROP TYPE IF EXISTS gender CASCADE;

-- Step 3: Drop existing functions and triggers
DROP FUNCTION IF EXISTS update_profile_calculations() CASCADE;

-- ====================================================================
-- NOW CREATE THE NEW COMPREHENSIVE SCHEMA
-- ====================================================================

-- Create enum types for structured data
CREATE TYPE activity_level AS ENUM (
  'sedentary',     -- Little/no exercise, desk job
  'light',         -- Light exercise 1-3 days/week
  'moderate',      -- Moderate exercise 3-5 days/week
  'active',        -- Heavy exercise 6-7 days/week
  'very_active'    -- Very heavy exercise, physical job + exercise
);

CREATE TYPE health_goal AS ENUM (
  'maintain',      -- Maintain current weight
  'lose_fat',      -- Lose body fat
  'gain_muscle',   -- Build muscle mass
  'bulk',          -- Gain weight (muscle + fat)
  'recomp',        -- Body recomposition (lose fat + gain muscle)
  'performance',   -- Athletic performance
  'health'         -- General health improvement
);

CREATE TYPE dietary_type AS ENUM (
  'omnivore',      -- Eats everything
  'vegetarian',    -- No meat, fish, poultry
  'vegan',         -- No animal products
  'eggetarian',    -- Vegetarian + eggs (common in India)
  'pescatarian',   -- Vegetarian + fish
  'flexitarian'    -- Mostly vegetarian, occasional meat
);

CREATE TYPE cooking_skill AS ENUM (
  'beginner',      -- Basic cooking skills
  'intermediate',  -- Can follow recipes well
  'advanced',      -- Confident with complex dishes
  'expert'         -- Professional level skills
);

CREATE TYPE gender AS ENUM (
  'male',
  'female',
  'other',
  'prefer_not_to_say'
);

-- Main user profiles table
CREATE TABLE user_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

  -- LAYER 1: Body Context (BMR/TDEE calculation)
  age INTEGER CHECK (age >= 13 AND age <= 120),
  gender gender NOT NULL,
  weight_kg DECIMAL(5,2) CHECK (weight_kg >= 30 AND weight_kg <= 300),
  height_cm DECIMAL(5,2) CHECK (height_cm >= 120 AND height_cm <= 250),
  activity_level activity_level NOT NULL DEFAULT 'moderate',
  health_goal health_goal NOT NULL DEFAULT 'maintain',

  -- Calculated fields (computed from body data)
  bmr_calories DECIMAL(7,2), -- Basal Metabolic Rate
  tdee_calories DECIMAL(7,2), -- Total Daily Energy Expenditure
  target_calories DECIMAL(7,2), -- Adjusted for goal (deficit/surplus)
  target_protein_g DECIMAL(6,2),
  target_carbs_g DECIMAL(6,2),
  target_fat_g DECIMAL(6,2),

  -- LAYER 2: Health Context (medical conditions & allergies)
  health_conditions TEXT[] DEFAULT ARRAY[]::TEXT[], -- ['diabetes', 'pcos', 'hypertension', etc.]
  allergies TEXT[] DEFAULT ARRAY[]::TEXT[], -- ['dairy', 'nuts', 'shellfish', etc.]
  dietary_restrictions TEXT[] DEFAULT ARRAY[]::TEXT[], -- ['low_sodium', 'gluten_free', etc.]
  medications TEXT[] DEFAULT ARRAY[]::TEXT[], -- Medications that affect nutrition

  -- LAYER 3: Life Context (practical constraints)
  dietary_type dietary_type NOT NULL DEFAULT 'omnivore',
  cuisine_preferences TEXT[] DEFAULT ARRAY[]::TEXT[], -- ['south_indian', 'north_indian', 'italian', etc.]
  cooking_skill cooking_skill NOT NULL DEFAULT 'intermediate',
  max_cooking_time_minutes INTEGER CHECK (max_cooking_time_minutes >= 5 AND max_cooking_time_minutes <= 180) DEFAULT 30,
  budget_per_meal_inr INTEGER CHECK (budget_per_meal_inr >= 20 AND budget_per_meal_inr <= 1000) DEFAULT 100,

  -- Household context
  household_size INTEGER CHECK (household_size >= 1 AND household_size <= 10) DEFAULT 1,
  cooking_for_kids BOOLEAN DEFAULT FALSE,

  -- Kitchen equipment available
  kitchen_equipment TEXT[] DEFAULT ARRAY[]::TEXT[], -- ['oven', 'pressure_cooker', 'air_fryer', etc.]

  -- Profile metadata
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  profile_completed BOOLEAN DEFAULT FALSE, -- Track if user finished onboarding

  -- Constraints
  UNIQUE(user_id)
);

-- Predefined health conditions with their dietary implications
CREATE TABLE health_condition_guidelines (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  condition_name TEXT UNIQUE NOT NULL,
  description TEXT NOT NULL,
  avoid_ingredients TEXT[] DEFAULT ARRAY[]::TEXT[], -- Ingredients to flag as concerning
  recommended_nutrients TEXT[] DEFAULT ARRAY[]::TEXT[], -- Nutrients to emphasize
  restrict_nutrients TEXT[] DEFAULT ARRAY[]::TEXT[], -- Nutrients to limit
  meal_timing_notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert common health conditions (with proper array casting)
INSERT INTO health_condition_guidelines (condition_name, description, avoid_ingredients, recommended_nutrients, restrict_nutrients, meal_timing_notes) VALUES
('diabetes', 'Blood sugar management',
 ARRAY['refined_sugar', 'high_gi_carbs', 'processed_foods']::TEXT[],
 ARRAY['fiber', 'protein', 'complex_carbs']::TEXT[],
 ARRAY['simple_sugars', 'saturated_fat']::TEXT[],
 'Eat smaller, frequent meals. Avoid large carb loads.'),

('pcos', 'Polycystic Ovary Syndrome',
 ARRAY['refined_sugar', 'processed_foods', 'trans_fats']::TEXT[],
 ARRAY['fiber', 'protein', 'omega_3', 'chromium']::TEXT[],
 ARRAY['simple_sugars', 'refined_carbs']::TEXT[],
 'Focus on low-GI foods. Consider intermittent fasting.'),

('hypertension', 'High blood pressure',
 ARRAY['high_sodium', 'processed_meats', 'canned_foods']::TEXT[],
 ARRAY['potassium', 'magnesium', 'fiber']::TEXT[],
 ARRAY['sodium', 'saturated_fat']::TEXT[],
 'Limit sodium to <2300mg daily. Emphasize DASH diet principles.'),

('hypothyroid', 'Underactive thyroid',
 ARRAY['soy', 'cruciferous_raw', 'excessive_fiber']::TEXT[],
 ARRAY['iodine', 'selenium', 'zinc']::TEXT[],
 ARRAY[]::TEXT[],
 'Take medications on empty stomach. Wait 4h after eating.'),

('ibs', 'Irritable Bowel Syndrome',
 ARRAY['high_fodmap', 'spicy_foods', 'caffeine']::TEXT[],
 ARRAY['soluble_fiber', 'probiotics']::TEXT[],
 ARRAY['insoluble_fiber', 'high_fat']::TEXT[],
 'Follow low-FODMAP diet. Keep food diary.'),

('ckd', 'Chronic Kidney Disease',
 ARRAY['high_phosphorus', 'high_potassium', 'processed_meats']::TEXT[],
 ARRAY[]::TEXT[],
 ARRAY['protein', 'sodium', 'phosphorus', 'potassium']::TEXT[],
 'Protein restriction based on stage. Monitor mineral intake.'),

('gerd', 'Gastroesophageal Reflux Disease',
 ARRAY['citrus', 'tomatoes', 'spicy_foods', 'caffeine', 'chocolate']::TEXT[],
 ARRAY[]::TEXT[],
 ARRAY['high_fat']::TEXT[],
 'Avoid eating 3h before bed. Smaller, frequent meals.'),

('celiac', 'Celiac Disease',
 ARRAY['gluten', 'wheat', 'barley', 'rye']::TEXT[],
 ARRAY['fiber', 'b_vitamins', 'iron']::TEXT[],
 ARRAY[]::TEXT[],
 'Strict gluten avoidance. Check for cross-contamination.');

-- Common allergies and their ingredient patterns
CREATE TABLE allergy_ingredients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  allergy_name TEXT NOT NULL,
  avoid_ingredients TEXT[] NOT NULL,
  hidden_sources TEXT[] DEFAULT ARRAY[]::TEXT[], -- Where allergen might be hidden
  severity_level INTEGER DEFAULT 1 CHECK (severity_level >= 1 AND severity_level <= 3), -- 1=mild, 2=moderate, 3=severe
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

INSERT INTO allergy_ingredients (allergy_name, avoid_ingredients, hidden_sources, severity_level) VALUES
('dairy',
 ARRAY['milk', 'cheese', 'butter', 'yogurt', 'cream', 'whey', 'casein', 'lactose']::TEXT[],
 ARRAY['baked_goods', 'processed_meats', 'chocolate', 'salad_dressing']::TEXT[], 3),

('nuts',
 ARRAY['almonds', 'walnuts', 'cashews', 'pistachios', 'hazelnuts', 'pecans', 'brazil_nuts']::TEXT[],
 ARRAY['baked_goods', 'cereals', 'energy_bars', 'sauces']::TEXT[], 3),

('peanuts',
 ARRAY['peanuts', 'peanut_butter', 'peanut_oil']::TEXT[],
 ARRAY['asian_cuisine', 'baked_goods', 'cereals', 'candy']::TEXT[], 3),

('shellfish',
 ARRAY['shrimp', 'crab', 'lobster', 'clams', 'mussels', 'oysters']::TEXT[],
 ARRAY['fish_sauce', 'worcestershire_sauce', 'caesar_dressing']::TEXT[], 3),

('fish',
 ARRAY['salmon', 'tuna', 'cod', 'fish_oil']::TEXT[],
 ARRAY['worcestershire_sauce', 'caesar_dressing', 'supplements']::TEXT[], 2),

('eggs',
 ARRAY['eggs', 'egg_whites', 'albumin', 'lecithin']::TEXT[],
 ARRAY['baked_goods', 'pasta', 'mayonnaise', 'ice_cream']::TEXT[], 2),

('soy',
 ARRAY['soybeans', 'soy_sauce', 'tofu', 'tempeh', 'miso']::TEXT[],
 ARRAY['processed_foods', 'vegetarian_meat', 'chocolate', 'bread']::TEXT[], 1),

('gluten',
 ARRAY['wheat', 'barley', 'rye', 'bulgur', 'semolina']::TEXT[],
 ARRAY['soy_sauce', 'beer', 'processed_foods', 'oats']::TEXT[], 2);

-- User meal history for pattern analysis
CREATE TABLE user_meal_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  meal_date DATE NOT NULL,
  meal_type TEXT NOT NULL CHECK (meal_type IN ('breakfast', 'lunch', 'snack', 'dinner')),

  -- Meal details
  meal_name TEXT,
  ingredients TEXT[],
  estimated_calories DECIMAL(7,2),
  estimated_protein_g DECIMAL(6,2),
  estimated_carbs_g DECIMAL(6,2),
  estimated_fat_g DECIMAL(6,2),

  -- User feedback
  satisfaction_rating INTEGER CHECK (satisfaction_rating >= 1 AND satisfaction_rating <= 5),
  notes TEXT,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Nutritional gaps analysis (weekly summary)
CREATE TABLE user_nutrition_analysis (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
  analysis_week DATE NOT NULL, -- Start of week

  -- Average daily intake vs targets
  avg_calories DECIMAL(7,2),
  avg_protein_g DECIMAL(6,2),
  avg_carbs_g DECIMAL(6,2),
  avg_fat_g DECIMAL(6,2),

  -- Micronutrient analysis
  deficient_nutrients TEXT[] DEFAULT ARRAY[]::TEXT[], -- Nutrients consistently below RDA
  excess_nutrients TEXT[] DEFAULT ARRAY[]::TEXT[], -- Nutrients consistently above UL

  -- Recommendations
  ai_recommendations TEXT[],
  flagged_ingredients TEXT[], -- Ingredients to avoid based on health profile

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, analysis_week)
);

-- Triggers for automatic profile updates
CREATE OR REPLACE FUNCTION update_profile_calculations()
RETURNS TRIGGER AS $$
DECLARE
  bmr DECIMAL(7,2);
  tdee DECIMAL(7,2);
  target_cal DECIMAL(7,2);
  protein_g DECIMAL(6,2);
  carb_g DECIMAL(6,2);
  fat_g DECIMAL(6,2);
  activity_multiplier DECIMAL(3,2);
BEGIN
  -- Calculate BMR using Mifflin-St Jeor equation
  IF NEW.gender = 'male' THEN
    bmr := (10 * NEW.weight_kg) + (6.25 * NEW.height_cm) - (5 * NEW.age) + 5;
  ELSE
    bmr := (10 * NEW.weight_kg) + (6.25 * NEW.height_cm) - (5 * NEW.age) - 161;
  END IF;

  -- Calculate TDEE based on activity level
  activity_multiplier := CASE NEW.activity_level
    WHEN 'sedentary' THEN 1.2
    WHEN 'light' THEN 1.375
    WHEN 'moderate' THEN 1.55
    WHEN 'active' THEN 1.725
    WHEN 'very_active' THEN 1.9
    ELSE 1.55
  END;

  tdee := bmr * activity_multiplier;

  -- Adjust calories based on goal
  target_cal := CASE NEW.health_goal
    WHEN 'lose_fat' THEN tdee - 300  -- 300 cal deficit
    WHEN 'gain_muscle' THEN tdee + 200  -- 200 cal surplus
    WHEN 'bulk' THEN tdee + 400  -- 400 cal surplus
    WHEN 'recomp' THEN tdee  -- At maintenance
    ELSE tdee  -- Maintain
  END;

  -- Calculate macros (protein priority approach)
  protein_g := CASE NEW.health_goal
    WHEN 'lose_fat' THEN NEW.weight_kg * 2.2  -- High protein for muscle retention
    WHEN 'gain_muscle' THEN NEW.weight_kg * 2.0
    WHEN 'bulk' THEN NEW.weight_kg * 1.8
    ELSE NEW.weight_kg * 1.6  -- General health
  END;

  fat_g := target_cal * 0.25 / 9;  -- 25% of calories from fat
  carb_g := (target_cal - (protein_g * 4) - (fat_g * 9)) / 4;  -- Remaining from carbs

  -- Update calculated fields
  NEW.bmr_calories := bmr;
  NEW.tdee_calories := tdee;
  NEW.target_calories := target_cal;
  NEW.target_protein_g := protein_g;
  NEW.target_carbs_g := carb_g;
  NEW.target_fat_g := fat_g;
  NEW.updated_at := NOW();

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for automatic calculations
CREATE TRIGGER calculate_nutrition_targets
  BEFORE INSERT OR UPDATE OF age, gender, weight_kg, height_cm, activity_level, health_goal
  ON user_profiles
  FOR EACH ROW
  EXECUTE FUNCTION update_profile_calculations();

-- Row Level Security (RLS) policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_meal_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_nutrition_analysis ENABLE ROW LEVEL SECURITY;

-- Users can only access their own profile data
CREATE POLICY "Users can view own profile" ON user_profiles
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON user_profiles
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON user_profiles
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Similar policies for meal history and nutrition analysis
CREATE POLICY "Users can manage own meal history" ON user_meal_history
  FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own nutrition analysis" ON user_nutrition_analysis
  FOR ALL USING (auth.uid() = user_id);

-- Create indexes for performance
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_meal_history_user_date ON user_meal_history(user_id, meal_date);
CREATE INDEX idx_nutrition_analysis_user_week ON user_nutrition_analysis(user_id, analysis_week);

-- Grant necessary permissions
GRANT SELECT ON health_condition_guidelines TO authenticated;
GRANT SELECT ON allergy_ingredients TO authenticated;

-- Success message
SELECT 'Comprehensive Health Profile System created successfully! 🎉' as result;