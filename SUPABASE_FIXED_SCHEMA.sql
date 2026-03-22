-- EatSmartly Supabase Database Schema (Fixed Version)
-- Run this in your Supabase SQL Editor

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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    last_sign_in TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- User profiles table for comprehensive health data
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    firebase_user_id TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    profile_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Meal history table
CREATE TABLE IF NOT EXISTS meal_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    firebase_user_id TEXT NOT NULL,
    meal_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Food scans history table
CREATE TABLE IF NOT EXISTS food_scans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    firebase_user_id TEXT NOT NULL,
    scan_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

-- Add foreign key constraints after tables are created
ALTER TABLE user_profiles
ADD CONSTRAINT fk_user_profiles_firebase_user_id
FOREIGN KEY (firebase_user_id) REFERENCES users(firebase_user_id) ON DELETE CASCADE;

ALTER TABLE meal_history
ADD CONSTRAINT fk_meal_history_firebase_user_id
FOREIGN KEY (firebase_user_id) REFERENCES users(firebase_user_id) ON DELETE CASCADE;

ALTER TABLE food_scans
ADD CONSTRAINT fk_food_scans_firebase_user_id
FOREIGN KEY (firebase_user_id) REFERENCES users(firebase_user_id) ON DELETE CASCADE;

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_firebase_id ON users(firebase_user_id);
CREATE INDEX IF NOT EXISTS idx_user_profiles_firebase_id ON user_profiles(firebase_user_id);
CREATE INDEX IF NOT EXISTS idx_meal_history_firebase_id ON meal_history(firebase_user_id);
CREATE INDEX IF NOT EXISTS idx_meal_history_created_at ON meal_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_food_scans_firebase_id ON food_scans(firebase_user_id);
CREATE INDEX IF NOT EXISTS idx_food_scans_created_at ON food_scans(created_at DESC);

-- Enable RLS (Row Level Security) - Note: This disables direct access without policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE meal_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE food_scans ENABLE ROW LEVEL SECURITY;

-- Create policies that allow authenticated users to access their own data
-- These policies use auth.uid() which is Supabase's built-in function for Firebase Auth integration
CREATE POLICY "users_policy" ON users FOR ALL USING (firebase_user_id = auth.jwt()->>'sub');
CREATE POLICY "user_profiles_policy" ON user_profiles FOR ALL USING (firebase_user_id = auth.jwt()->>'sub');
CREATE POLICY "meal_history_policy" ON meal_history FOR ALL USING (firebase_user_id = auth.jwt()->>'sub');
CREATE POLICY "food_scans_policy" ON food_scans FOR ALL USING (firebase_user_id = auth.jwt()->>'sub');

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

-- Grant necessary permissions
GRANT ALL ON users TO authenticated;
GRANT ALL ON user_profiles TO authenticated;
GRANT ALL ON meal_history TO authenticated;
GRANT ALL ON food_scans TO authenticated;

-- Grant usage on sequences
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- Success message
SELECT 'EatSmartly database schema created successfully! 🎉' as result;