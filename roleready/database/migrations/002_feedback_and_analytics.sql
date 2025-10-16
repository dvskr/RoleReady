-- Step 9: Model Feedback & Continuous Learning
-- Migration: Create feedback and analytics tables

-- Feedback table for capturing user edits
CREATE TABLE IF NOT EXISTS public.feedback (
  id bigserial PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  resume_id uuid REFERENCES public.resumes(id) ON DELETE CASCADE,
  team_id uuid REFERENCES public.teams(id) ON DELETE CASCADE,
  old_text text NOT NULL,
  new_text text NOT NULL,
  feedback_type text CHECK (feedback_type IN ('rewrite', 'manual_edit', 'rejection', 'improvement')) DEFAULT 'manual_edit',
  section text, -- 'summary', 'experience', 'skills', etc.
  created_at timestamptz DEFAULT now()
);

-- Usage analytics table
CREATE TABLE IF NOT EXISTS public.usage_analytics (
  id bigserial PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  team_id uuid REFERENCES public.teams(id) ON DELETE SET NULL,
  action text NOT NULL, -- 'parse', 'align', 'rewrite', 'export', 'share'
  metadata jsonb, -- Additional context like file size, processing time, etc.
  created_at timestamptz DEFAULT now()
);

-- API usage tracking
CREATE TABLE IF NOT EXISTS public.api_usage (
  id bigserial PRIMARY KEY,
  api_key_id uuid REFERENCES public.api_keys(id) ON DELETE CASCADE,
  endpoint text NOT NULL,
  method text NOT NULL,
  status_code integer,
  response_time_ms integer,
  request_size_bytes integer,
  response_size_bytes integer,
  user_agent text,
  ip_address inet,
  created_at timestamptz DEFAULT now()
);

-- Resume templates marketplace
CREATE TABLE IF NOT EXISTS public.resume_templates (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  creator_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  category text, -- 'modern', 'classic', 'creative', 'technical'
  preview_image_url text,
  template_data jsonb NOT NULL, -- Template structure and styling
  is_public boolean DEFAULT false,
  is_premium boolean DEFAULT false,
  price_cents integer DEFAULT 0, -- 0 for free templates
  download_count integer DEFAULT 0,
  rating_average numeric(3,2) DEFAULT 0,
  rating_count integer DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Template reviews
CREATE TABLE IF NOT EXISTS public.template_reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  template_id uuid REFERENCES public.resume_templates(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  rating integer CHECK (rating >= 1 AND rating <= 5),
  review_text text,
  created_at timestamptz DEFAULT now(),
  UNIQUE(template_id, user_id)
);

-- Audit log for compliance
CREATE TABLE IF NOT EXISTS public.audit_log (
  id bigserial PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  api_key_id uuid REFERENCES public.api_keys(id) ON DELETE SET NULL,
  action text NOT NULL,
  resource_type text, -- 'resume', 'team', 'api_key', etc.
  resource_id uuid,
  old_values jsonb,
  new_values jsonb,
  ip_address inet,
  user_agent text,
  created_at timestamptz DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_feedback_user_id ON public.feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_resume_id ON public.feedback(resume_id);
CREATE INDEX IF NOT EXISTS idx_feedback_created_at ON public.feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_user_id ON public.usage_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_action ON public.usage_analytics(action);
CREATE INDEX IF NOT EXISTS idx_usage_analytics_created_at ON public.usage_analytics(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_api_key_id ON public.api_usage(api_key_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON public.api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON public.api_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_resume_templates_creator_id ON public.resume_templates(creator_id);
CREATE INDEX IF NOT EXISTS idx_resume_templates_category ON public.resume_templates(category);
CREATE INDEX IF NOT EXISTS idx_resume_templates_is_public ON public.resume_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON public.audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON public.audit_log(created_at);

-- Enable RLS
ALTER TABLE public.feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_analytics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.resume_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.template_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own feedback" ON public.feedback
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create their own feedback" ON public.feedback
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can view their own analytics" ON public.usage_analytics
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can create their own analytics" ON public.usage_analytics
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "API key owners can view their usage" ON public.api_usage
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.api_keys 
      WHERE api_keys.id = api_usage.api_key_id 
      AND api_keys.user_id = auth.uid()
    )
  );

CREATE POLICY "Anyone can view public templates" ON public.resume_templates
  FOR SELECT USING (is_public = true OR creator_id = auth.uid());

CREATE POLICY "Creators can manage their templates" ON public.resume_templates
  FOR ALL USING (creator_id = auth.uid());

CREATE POLICY "Users can manage their own reviews" ON public.template_reviews
  FOR ALL USING (user_id = auth.uid());

-- Functions for analytics
CREATE OR REPLACE FUNCTION public.track_usage_analytics(
  p_user_id uuid,
  p_team_id uuid,
  p_action text,
  p_metadata jsonb DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO public.usage_analytics (user_id, team_id, action, metadata)
  VALUES (p_user_id, p_team_id, p_action, p_metadata);
END;
$$;

CREATE OR REPLACE FUNCTION public.record_feedback(
  p_user_id uuid,
  p_resume_id uuid,
  p_team_id uuid,
  p_old_text text,
  p_new_text text,
  p_feedback_type text DEFAULT 'manual_edit',
  p_section text DEFAULT NULL
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  INSERT INTO public.feedback (user_id, resume_id, team_id, old_text, new_text, feedback_type, section)
  VALUES (p_user_id, p_resume_id, p_team_id, p_old_text, p_new_text, p_feedback_type, p_section);
END;
$$;

-- Function to get team analytics
CREATE OR REPLACE FUNCTION public.get_team_analytics(p_team_id uuid, p_days integer DEFAULT 30)
RETURNS TABLE (
  action text,
  count bigint,
  unique_users bigint
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    ua.action,
    COUNT(*) as count,
    COUNT(DISTINCT ua.user_id) as unique_users
  FROM public.usage_analytics ua
  WHERE ua.team_id = p_team_id
    AND ua.created_at >= now() - interval '1 day' * p_days
  GROUP BY ua.action
  ORDER BY count DESC;
END;
$$;

-- Trigger to update template download count
CREATE OR REPLACE FUNCTION public.increment_template_downloads()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.resume_templates 
  SET download_count = download_count + 1
  WHERE id = NEW.template_id;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update template ratings
CREATE OR REPLACE FUNCTION public.update_template_rating()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE public.resume_templates 
  SET 
    rating_count = (
      SELECT COUNT(*) FROM public.template_reviews 
      WHERE template_id = COALESCE(NEW.template_id, OLD.template_id)
    ),
    rating_average = (
      SELECT AVG(rating)::numeric(3,2) FROM public.template_reviews 
      WHERE template_id = COALESCE(NEW.template_id, OLD.template_id)
    )
  WHERE id = COALESCE(NEW.template_id, OLD.template_id);
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER update_resume_templates_updated_at 
  BEFORE UPDATE ON public.resume_templates 
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_template_rating_trigger
  AFTER INSERT OR UPDATE OR DELETE ON public.template_reviews
  FOR EACH ROW EXECUTE FUNCTION public.update_template_rating();
