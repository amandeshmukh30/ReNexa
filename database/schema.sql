-- ==============================================================================
-- ReNexa Phase 9B — Database Schema & Row Level Security (RLS)
-- ==============================================================================
-- Defines core entities, triggers, and user-isolated Row Level Security policies
-- for Supabase / PostgreSQL.
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. USER PROFILES
-- ------------------------------------------------------------------------------
-- Tied directly to Supabase auth.users UUID identity.
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    display_name VARCHAR(100),
    email VARCHAR(255),
    default_workspace VARCHAR(50) DEFAULT 'Home/Kitchen',
    default_skill VARCHAR(50) DEFAULT 'Beginner',
    default_budget VARCHAR(50) DEFAULT 'Free (₹0)'
);

-- Trigger to automatically populate user_profiles upon Supabase Auth sign-up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
  INSERT INTO public.user_profiles (id, email, display_name)
  VALUES (
    new.id,
    new.email,
    COALESCE(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1))
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN new;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- ------------------------------------------------------------------------------
-- 2. SCANS (Detection Metadata)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    detected_material VARCHAR(50) NOT NULL,
    model_label VARCHAR(100),
    confidence NUMERIC(5, 4),
    detected_object_count INTEGER DEFAULT 1 NOT NULL,
    confirmed_quantity INTEGER DEFAULT 1 NOT NULL,
    image_filename VARCHAR(255),
    session_id VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_scans_user_id ON scans(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_created_at ON scans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_scans_material ON scans(detected_material);

-- ------------------------------------------------------------------------------
-- 3. WASTE PROFILES (Structured Assessment)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS waste_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    material VARCHAR(50) NOT NULL,
    item VARCHAR(100) DEFAULT 'Unknown',
    condition VARCHAR(50) NOT NULL,
    contamination VARCHAR(50) NOT NULL,
    confirmed_quantity INTEGER DEFAULT 1 NOT NULL,
    user_confirmed BOOLEAN DEFAULT true NOT NULL,
    material_breakdown JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_waste_profiles_scan_id ON waste_profiles(scan_id);
CREATE INDEX IF NOT EXISTS idx_waste_profiles_material ON waste_profiles(material);

-- ------------------------------------------------------------------------------
-- 4. RECOMMENDATIONS (Phase 6 Top-K Ranked Pathways)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    pathway_id VARCHAR(50) NOT NULL,
    pathway_title VARCHAR(255) NOT NULL,
    pathway_type VARCHAR(50) NOT NULL,
    rank INTEGER NOT NULL,
    mcda_score NUMERIC(5, 2) NOT NULL,
    criterion_scores JSONB DEFAULT '{}'::jsonb,
    why_this JSONB DEFAULT '[]'::jsonb,
    why_not_this JSONB DEFAULT '[]'::jsonb,
    warnings JSONB DEFAULT '[]'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_recommendations_scan_id ON recommendations(scan_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_pathway_id ON recommendations(pathway_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_rank ON recommendations(rank);

-- ------------------------------------------------------------------------------
-- 5. EXECUTION FEEDBACK (Phase 8 Real-World Outcome Validation)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS execution_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES user_profiles(id) ON DELETE CASCADE,
    scan_id UUID REFERENCES scans(id) ON DELETE SET NULL,
    recommendation_id UUID REFERENCES recommendations(id) ON DELETE SET NULL,
    pathway_id VARCHAR(50) NOT NULL,
    pathway_title VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    attempt_status VARCHAR(50) NOT NULL,
    material VARCHAR(50),
    item VARCHAR(100),
    condition VARCHAR(50),
    contamination VARCHAR(50),
    quantity INTEGER DEFAULT 1,
    predicted_rank INTEGER,
    predicted_score NUMERIC(5, 2),
    estimated_time_minutes INTEGER,
    actual_time_minutes INTEGER,
    time_accuracy VARCHAR(50),
    missing_tools BOOLEAN DEFAULT false NOT NULL,
    missing_tools_details TEXT,
    missing_materials BOOLEAN DEFAULT false NOT NULL,
    missing_materials_details TEXT,
    safety_issue BOOLEAN DEFAULT false NOT NULL,
    safety_issue_details TEXT,
    failure_reason VARCHAR(50),
    user_rating INTEGER,
    would_try_again VARCHAR(20),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON execution_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_pathway_id ON execution_feedback(pathway_id);
CREATE INDEX IF NOT EXISTS idx_feedback_attempt_status ON execution_feedback(attempt_status);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON execution_feedback(created_at DESC);

-- ==============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==============================================================================

-- 1. Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE waste_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_feedback ENABLE ROW LEVEL SECURITY;

-- 2. user_profiles Policies
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON user_profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    USING (auth.uid() = id)
    WITH CHECK (auth.uid() = id);

-- 3. scans Policies
CREATE POLICY "Users can view own scans"
    ON scans FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own scans"
    ON scans FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own scans"
    ON scans FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own scans"
    ON scans FOR DELETE
    USING (auth.uid() = user_id);

-- 4. waste_profiles Policies (Access determined via parent scan ownership)
CREATE POLICY "Users can view waste profiles for own scans"
    ON waste_profiles FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM scans
            WHERE scans.id = waste_profiles.scan_id
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert waste profiles for own scans"
    ON waste_profiles FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM scans
            WHERE scans.id = waste_profiles.scan_id
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update waste profiles for own scans"
    ON waste_profiles FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM scans
            WHERE scans.id = waste_profiles.scan_id
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete waste profiles for own scans"
    ON waste_profiles FOR DELETE
    USING (
        EXISTS (
            SELECT 1 FROM scans
            WHERE scans.id = waste_profiles.scan_id
            AND scans.user_id = auth.uid()
        )
    );

-- 5. recommendations Policies (Access determined via parent scan ownership)
CREATE POLICY "Users can view recommendations for own scans"
    ON recommendations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM scans
            WHERE scans.id = recommendations.scan_id
            AND scans.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert recommendations for own scans"
    ON recommendations FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM scans
            WHERE scans.id = recommendations.scan_id
            AND scans.user_id = auth.uid()
        )
    );

-- 6. execution_feedback Policies
CREATE POLICY "Users can view own execution feedback"
    ON execution_feedback FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own execution feedback"
    ON execution_feedback FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own execution feedback"
    ON execution_feedback FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own execution feedback"
    ON execution_feedback FOR DELETE
    USING (auth.uid() = user_id);
