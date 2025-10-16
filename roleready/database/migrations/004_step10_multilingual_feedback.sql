-- Step 10: Multilingual Support, Continuous Learning, and Career Intelligence
-- This migration adds support for multilingual resumes, AI feedback collection,
-- career path analysis, and enterprise features

-- Add language column to resumes table
ALTER TABLE public.resumes 
ADD COLUMN IF NOT EXISTS language VARCHAR(2) DEFAULT 'en',
ADD COLUMN IF NOT EXISTS language_name VARCHAR(50),
ADD COLUMN IF NOT EXISTS translated_content JSONB,
ADD COLUMN IF NOT EXISTS multilingual_embeddings JSONB;

-- Create index for language-based queries
CREATE INDEX IF NOT EXISTS idx_resumes_language ON public.resumes(language);

-- Model feedback collection table for continuous learning
CREATE TABLE IF NOT EXISTS public.model_feedback (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES public.resumes(id) ON DELETE CASCADE,
    source TEXT NOT NULL, -- 'rewrite', 'suggestion', 'manual_edit', etc.
    suggestion TEXT NOT NULL,
    final TEXT NOT NULL,
    accepted BOOLEAN NOT NULL,
    confidence_score DECIMAL(3,2),
    model_version VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for feedback analysis
CREATE INDEX IF NOT EXISTS idx_model_feedback_user_id ON public.model_feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_model_feedback_created_at ON public.model_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_model_feedback_accepted ON public.model_feedback(accepted);
CREATE INDEX IF NOT EXISTS idx_model_feedback_source ON public.model_feedback(source);

-- Career path advisor data
CREATE TABLE IF NOT EXISTS public.career_insights (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES public.resumes(id) ON DELETE CASCADE,
    domain TEXT NOT NULL, -- 'data_science', 'software_engineering', etc.
    missing_skills TEXT[],
    recommended_skills TEXT[],
    skill_gaps JSONB,
    learning_paths JSONB,
    alignment_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for career insights
CREATE INDEX IF NOT EXISTS idx_career_insights_user_id ON public.career_insights(user_id);
CREATE INDEX IF NOT EXISTS idx_career_insights_domain ON public.career_insights(domain);
CREATE INDEX IF NOT EXISTS idx_career_insights_alignment_score ON public.career_insights(alignment_score);

-- Job descriptions corpus for recruiter matching
CREATE TABLE IF NOT EXISTS public.job_descriptions (
    id BIGSERIAL PRIMARY KEY,
    team_id UUID REFERENCES public.teams(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    company TEXT,
    description TEXT NOT NULL,
    requirements TEXT[],
    skills TEXT[],
    location TEXT,
    salary_range JSONB,
    experience_level TEXT,
    job_type TEXT, -- 'full-time', 'part-time', 'contract', etc.
    remote_friendly BOOLEAN DEFAULT FALSE,
    embeddings JSONB,
    language VARCHAR(2) DEFAULT 'en',
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for job descriptions
CREATE INDEX IF NOT EXISTS idx_job_descriptions_team_id ON public.job_descriptions(team_id);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_title ON public.job_descriptions(title);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_company ON public.job_descriptions(company);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_experience_level ON public.job_descriptions(experience_level);
CREATE INDEX IF NOT EXISTS idx_job_descriptions_language ON public.job_descriptions(language);

-- Candidate matching results
CREATE TABLE IF NOT EXISTS public.candidate_matches (
    id BIGSERIAL PRIMARY KEY,
    job_description_id BIGINT REFERENCES public.job_descriptions(id) ON DELETE CASCADE,
    resume_id UUID REFERENCES public.resumes(id) ON DELETE CASCADE,
    match_score DECIMAL(3,2) NOT NULL,
    skill_alignment DECIMAL(3,2),
    experience_alignment DECIMAL(3,2),
    overall_fit DECIMAL(3,2),
    matched_skills TEXT[],
    missing_skills TEXT[],
    notes TEXT,
    status TEXT DEFAULT 'pending', -- 'pending', 'reviewed', 'shortlisted', 'rejected'
    reviewed_by UUID REFERENCES auth.users(id),
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for candidate matches
CREATE INDEX IF NOT EXISTS idx_candidate_matches_job_id ON public.candidate_matches(job_description_id);
CREATE INDEX IF NOT EXISTS idx_candidate_matches_resume_id ON public.candidate_matches(resume_id);
CREATE INDEX IF NOT EXISTS idx_candidate_matches_match_score ON public.candidate_matches(match_score);
CREATE INDEX IF NOT EXISTS idx_candidate_matches_status ON public.candidate_matches(status);

-- Enterprise analytics and usage tracking
CREATE TABLE IF NOT EXISTS public.enterprise_analytics (
    id BIGSERIAL PRIMARY KEY,
    team_id UUID REFERENCES public.teams(id) ON DELETE CASCADE,
    metric_name TEXT NOT NULL,
    metric_value JSONB NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for analytics
CREATE INDEX IF NOT EXISTS idx_enterprise_analytics_team_id ON public.enterprise_analytics(team_id);
CREATE INDEX IF NOT EXISTS idx_enterprise_analytics_metric_name ON public.enterprise_analytics(metric_name);
CREATE INDEX IF NOT EXISTS idx_enterprise_analytics_period ON public.enterprise_analytics(period_start, period_end);

-- Learning paths and course recommendations
CREATE TABLE IF NOT EXISTS public.learning_paths (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    skill_domain TEXT NOT NULL,
    target_skills TEXT[] NOT NULL,
    recommended_courses JSONB,
    progress JSONB,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for learning paths
CREATE INDEX IF NOT EXISTS idx_learning_paths_user_id ON public.learning_paths(user_id);
CREATE INDEX IF NOT EXISTS idx_learning_paths_skill_domain ON public.learning_paths(skill_domain);

-- Multilingual content cache
CREATE TABLE IF NOT EXISTS public.translation_cache (
    id BIGSERIAL PRIMARY KEY,
    source_text_hash VARCHAR(64) NOT NULL,
    source_text TEXT NOT NULL,
    source_language VARCHAR(2) NOT NULL,
    target_language VARCHAR(2) NOT NULL,
    translated_text TEXT NOT NULL,
    model_version VARCHAR(50),
    confidence_score DECIMAL(3,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Index for translation cache
CREATE INDEX IF NOT EXISTS idx_translation_cache_hash ON public.translation_cache(source_text_hash);
CREATE INDEX IF NOT EXISTS idx_translation_cache_languages ON public.translation_cache(source_language, target_language);
CREATE INDEX IF NOT EXISTS idx_translation_cache_expires ON public.translation_cache(expires_at);

-- RLS policies for new tables
ALTER TABLE public.model_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.career_insights ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.job_descriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.candidate_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.enterprise_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.learning_paths ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.translation_cache ENABLE ROW LEVEL SECURITY;

-- RLS policies for model_feedback
CREATE POLICY "Users can view their own feedback" ON public.model_feedback
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own feedback" ON public.model_feedback
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS policies for career_insights
CREATE POLICY "Users can view their own career insights" ON public.career_insights
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own career insights" ON public.career_insights
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS policies for job_descriptions
CREATE POLICY "Team members can view team job descriptions" ON public.job_descriptions
    FOR SELECT USING (
        team_id IN (
            SELECT team_id FROM public.team_members 
            WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Team members can insert job descriptions" ON public.job_descriptions
    FOR INSERT WITH CHECK (
        team_id IN (
            SELECT team_id FROM public.team_members 
            WHERE user_id = auth.uid()
        )
    );

-- RLS policies for candidate_matches
CREATE POLICY "Team members can view candidate matches" ON public.candidate_matches
    FOR SELECT USING (
        job_description_id IN (
            SELECT jd.id FROM public.job_descriptions jd
            JOIN public.team_members tm ON jd.team_id = tm.team_id
            WHERE tm.user_id = auth.uid()
        )
    );

-- RLS policies for enterprise_analytics
CREATE POLICY "Team members can view team analytics" ON public.enterprise_analytics
    FOR SELECT USING (
        team_id IN (
            SELECT team_id FROM public.team_members 
            WHERE user_id = auth.uid()
        )
    );

-- RLS policies for learning_paths
CREATE POLICY "Users can view their own learning paths" ON public.learning_paths
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own learning paths" ON public.learning_paths
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- RLS policies for translation_cache (public read, authenticated write)
CREATE POLICY "Anyone can read translation cache" ON public.translation_cache
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can insert translations" ON public.translation_cache
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_model_feedback_updated_at 
    BEFORE UPDATE ON public.model_feedback 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_career_insights_updated_at 
    BEFORE UPDATE ON public.career_insights 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_job_descriptions_updated_at 
    BEFORE UPDATE ON public.job_descriptions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_learning_paths_updated_at 
    BEFORE UPDATE ON public.learning_paths 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Cleanup function for expired translation cache
CREATE OR REPLACE FUNCTION cleanup_expired_translations()
RETURNS void AS $$
BEGIN
    DELETE FROM public.translation_cache 
    WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Add pgvector extension for vector similarity search (if not already added)
CREATE EXTENSION IF NOT EXISTS vector;
