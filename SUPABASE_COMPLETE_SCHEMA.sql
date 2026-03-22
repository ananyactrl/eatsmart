-- EatSmartly Supabase Database Schema
-- This schema stores user authentication data and health profiles

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table to store Firebase user information
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    firebase_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    display_name TEXT,
    photo_url TEXT,
    email_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE,
    last_sign_in TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- User profiles table for comprehensive health data
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    firebase_user_id TEXT UNIQUE NOT NULL REFERENCES users(firebase_user_id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    profile_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Meal history table
CREATE TABLE IF NOT EXISTS meal_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    firebase_user_id TEXT NOT NULL REFERENCES users(firebase_user_id) ON DELETE CASCADE,
    meal_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Food scans history table
CREATE TABLE IF NOT EXISTS food_scans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    firebase_user_id TEXT NOT NULL REFERENCES users(firebase_user_id) ON DELETE CASCADE,
    scan_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_firebase_id ON users(firebase_user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_firebase_id ON user_profiles(firebase_user_id);
CREATE INDEX IF NOT EXISTS idx_meal_history_firebase_id ON meal_history(firebase_user_id);
CREATE INDEX IF NOT EXISTS idx_meal_history_created_at ON meal_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_food_scans_firebase_id ON food_scans(firebase_user_id);
CREATE INDEX IF NOT EXISTS idx_food_scans_created_at ON food_scans(created_at DESC);

-- RLS (Row Level Security) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_scans ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view and update their own data" ON users
    FOR ALL USING (firebase_user_id = current_setting('app.current_user_id'));

-- RLS Policies for user_profiles table
CREATE POLICY "Users can manage their own profiles" ON user_profiles
    FOR ALL USING (firebase_user_id = current_setting('app.current_user_id'));

-- RLS Policies for meal_history table
CREATE POLICY "Users can manage their own meal history" ON meal_history
    FOR ALL USING (firebase_user_id = current_setting('app.current_user_id'));

-- RLS Policies for food_scans table
CREATE POLICY "Users can manage their own food scans" ON food_scans
    FOR ALL USING (firebase_user_id = current_setting('app.current_user_id'));

-- Functions for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions (adjust as needed for your setup)
-- These grants are for the authenticated users
GRANT ALL ON users TO authenticated;
GRANT ALL ON user_profiles TO authenticated;
GRANT ALL ON meal_history TO authenticated;
GRANT ALL ON food_scans TO authenticated;

-- Grant usage on sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Insert some sample data (optional - for testing)
-- You can remove this section in production

-- Example health conditions for reference
CREATE TABLE IF NOT EXISTS health_conditions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    dietary_guidelines TEXT[]
);

-- Insert sample health conditions
INSERT INTO health_conditions (name, description, dietary_guidelines) VALUES
('diabetes', 'Diabetes mellitus management', ARRAY['low-glycemic foods', 'controlled carbohydrate intake', 'high fiber foods']),
('hypertension', 'High blood pressure management', ARRAY['low sodium', 'DASH diet', 'potassium-rich foods']),
('pcos', 'Polycystic Ovary Syndrome', ARRAY['low-glycemic foods', 'anti-inflammatory foods', 'omega-3 rich foods']),
('thyroid', 'Thyroid disorders', ARRAY['iodine-rich foods', 'selenium sources', 'avoid goitrogens']),
('heart_disease', 'Cardiovascular disease', ARRAY['low saturated fat', 'omega-3 fatty acids', 'whole grains'])
ON CONFLICT (name) DO NOTHING;

-- Example allergens table
CREATE TABLE IF NOT EXISTS allergens (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    common_sources TEXT[],
    hidden_sources TEXT[]
);

-- Insert sample allergens
INSERT INTO allergens (name, common_sources, hidden_sources) VALUES
('nuts', ARRAY['almonds', 'walnuts', 'cashews', 'peanuts'], ARRAY['nut oil', 'marzipan', 'nougat']),
('dairy', ARRAY['milk', 'cheese', 'yogurt', 'butter'], ARRAY['casein', 'whey', 'lactose']),
('gluten', ARRAY['wheat', 'barley', 'rye', 'oats'], ARRAY['malt', 'brewer''s yeast', 'modified food starch']),
('shellfish', ARRAY['shrimp', 'crab', 'lobster', 'oysters'], ARRAY['fish sauce', 'worcestershire sauce', 'caesar dressing']),
('soy', ARRAY['soy sauce', 'tofu', 'tempeh', 'edamame'], ARRAY['lecithin', 'mono-diglycerides', 'natural flavoring'])
ON CONFLICT (name) DO NOTHING;

-- Comments for documentation
COMMENT ON TABLE users IS 'Stores Firebase user authentication data synced from Firebase Auth';
COMMENT ON TABLE user_profiles IS 'Stores comprehensive health profiles with BMR/TDEE calculations and preferences';
COMMENT ON TABLE meal_history IS 'Stores user meal planning history and nutrition tracking data';
COMMENT ON TABLE food_scans IS 'Stores barcode scan results and food analysis history';
COMMENT ON TABLE health_conditions IS 'Reference table for health conditions and dietary guidelines';
COMMENT ON TABLE allergens IS 'Reference table for allergens and their common/hidden sources';


-- Create a function to safely set current user context (for RLS)
CREATE OR REPLACE FUNCTION set_current_user_id(firebase_uid TEXT)
RETURNS void as $$
BEGIN
  PERFORM set_config('app.current_user_id', firebase_uid, true);
END;
$$ language plpgsql;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'EatSmartly Supabase database schema created successfully! 🎉';
END $$;