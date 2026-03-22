-- EatSmartly Clean Database Schema
-- Single table approach using Firebase UID directly
-- Run this in your Supabase SQL Editor

-- Drop existing user tables (keep meal history and other data tables)
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Create single comprehensive user_profiles table using Firebase UID
CREATE TABLE user_profiles (
    firebase_uid TEXT PRIMARY KEY,  -- Use Firebase UID directly as primary key
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,

    -- Basic profile info
    age INTEGER,
    gender TEXT,
    weight_kg NUMERIC,
    height_cm NUMERIC,

    -- Health and fitness
    activity_level TEXT,
    health_goal TEXT,
    bmr_calories NUMERIC,
    tdee_calories NUMERIC,
    target_calories NUMERIC,
    target_protein_g NUMERIC,
    target_carbs_g NUMERIC,
    target_fat_g NUMERIC,

    -- Health conditions and restrictions
    health_conditions TEXT[],
    allergies TEXT[],
    dietary_restrictions TEXT[],
    medications TEXT[],
    dietary_type TEXT,

    -- Cooking preferences
    cuisine_preferences TEXT[],
    cooking_skill TEXT,
    max_cooking_time_minutes INTEGER,
    budget_per_meal_inr INTEGER,
    household_size INTEGER,
    cooking_for_kids BOOLEAN DEFAULT FALSE,
    kitchen_equipment TEXT[],

    -- System fields
    profile_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Update other tables to use firebase_uid instead of user_id
ALTER TABLE user_meal_history
DROP CONSTRAINT IF EXISTS fk_user_meal_history_user_id;

ALTER TABLE user_meal_history
DROP COLUMN IF EXISTS user_id;

ALTER TABLE user_meal_history
ADD COLUMN firebase_uid TEXT;

ALTER TABLE scan_history
DROP CONSTRAINT IF EXISTS fk_scan_history_user_id;

ALTER TABLE scan_history
DROP COLUMN IF EXISTS user_id;

ALTER TABLE scan_history
ADD COLUMN firebase_uid TEXT;

ALTER TABLE user_contributions
DROP CONSTRAINT IF EXISTS fk_user_contributions_user_id;

ALTER TABLE user_contributions
DROP COLUMN IF EXISTS user_id;

ALTER TABLE user_contributions
ADD COLUMN firebase_uid TEXT;

ALTER TABLE user_nutrition_analysis
DROP CONSTRAINT IF EXISTS fk_user_nutrition_analysis_user_id;

ALTER TABLE user_nutrition_analysis
DROP COLUMN IF EXISTS user_id;

ALTER TABLE user_nutrition_analysis
ADD COLUMN firebase_uid TEXT;

-- Add foreign key constraints to reference the new user_profiles table
ALTER TABLE user_meal_history
ADD CONSTRAINT fk_user_meal_history_firebase_uid
FOREIGN KEY (firebase_uid) REFERENCES user_profiles(firebase_uid) ON DELETE CASCADE;

ALTER TABLE scan_history
ADD CONSTRAINT fk_scan_history_firebase_uid
FOREIGN KEY (firebase_uid) REFERENCES user_profiles(firebase_uid) ON DELETE CASCADE;

ALTER TABLE user_contributions
ADD CONSTRAINT fk_user_contributions_firebase_uid
FOREIGN KEY (firebase_uid) REFERENCES user_profiles(firebase_uid) ON DELETE CASCADE;

ALTER TABLE user_nutrition_analysis
ADD CONSTRAINT fk_user_nutrition_analysis_firebase_uid
FOREIGN KEY (firebase_uid) REFERENCES user_profiles(firebase_uid) ON DELETE CASCADE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_profiles_email ON user_profiles(email);
CREATE INDEX IF NOT EXISTS idx_user_meal_history_firebase_uid ON user_meal_history(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_scan_history_firebase_uid ON scan_history(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_user_contributions_firebase_uid ON user_contributions(firebase_uid);
CREATE INDEX IF NOT EXISTS idx_user_nutrition_analysis_firebase_uid ON user_nutrition_analysis(firebase_uid);

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_meal_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_contributions ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_nutrition_analysis ENABLE ROW LEVEL SECURITY;

-- Drop old policies
DROP POLICY IF EXISTS "users_policy" ON users;
DROP POLICY IF EXISTS "user_profiles_policy" ON user_profiles;
DROP POLICY IF EXISTS "user_meal_history_policy" ON user_meal_history;
DROP POLICY IF EXISTS "scan_history_policy" ON scan_history;
DROP POLICY IF EXISTS "user_contributions_policy" ON user_contributions;
DROP POLICY IF EXISTS "user_nutrition_analysis_policy" ON user_nutrition_analysis;

-- Create new RLS policies using Firebase UID
CREATE POLICY "user_profiles_policy" ON user_profiles
FOR ALL USING (firebase_uid = auth.jwt()->>'sub');

CREATE POLICY "user_meal_history_policy" ON user_meal_history
FOR ALL USING (firebase_uid = auth.jwt()->>'sub');

CREATE POLICY "scan_history_policy" ON scan_history
FOR ALL USING (firebase_uid = auth.jwt()->>'sub');

CREATE POLICY "user_contributions_policy" ON user_contributions
FOR ALL USING (firebase_uid = auth.jwt()->>'sub');

CREATE POLICY "user_nutrition_analysis_policy" ON user_nutrition_analysis
FOR ALL USING (firebase_uid = auth.jwt()->>'sub');

-- Service role bypass policies (for Python backend)
CREATE POLICY "service_user_profiles" ON user_profiles
FOR ALL TO service_role USING (true);

CREATE POLICY "service_user_meal_history" ON user_meal_history
FOR ALL TO service_role USING (true);

CREATE POLICY "service_scan_history" ON scan_history
FOR ALL TO service_role USING (true);

CREATE POLICY "service_user_contributions" ON user_contributions
FOR ALL TO service_role USING (true);

CREATE POLICY "service_user_nutrition_analysis" ON user_nutrition_analysis
FOR ALL TO service_role USING (true);

-- Grant permissions
GRANT ALL ON user_profiles TO authenticated;
GRANT ALL ON user_meal_history TO authenticated;
GRANT ALL ON scan_history TO authenticated;
GRANT ALL ON user_contributions TO authenticated;
GRANT ALL ON user_nutrition_analysis TO authenticated;

-- Create function for updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
CREATE TRIGGER update_user_profiles_updated_at
BEFORE UPDATE ON user_profiles
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

SELECT 'Clean schema created successfully! 🎉 Single user_profiles table with Firebase UID.' as result;