-- Step 10: Billing Infrastructure (Parked for Beta)
-- Migration: Create subscription and billing tables for future use

-- Subscriptions table (parked for beta phase)
CREATE TABLE IF NOT EXISTS public.subscriptions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  plan_name text NOT NULL DEFAULT 'beta_free',
  status text CHECK (status IN ('active', 'inactive', 'cancelled', 'past_due', 'trialing')) DEFAULT 'active',
  stripe_subscription_id text,
  stripe_customer_id text,
  current_period_start timestamptz,
  current_period_end timestamptz,
  trial_ends_at timestamptz,
  cancel_at_period_end boolean DEFAULT false,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Feature usage tracking table
CREATE TABLE IF NOT EXISTS public.feature_usage (
  id bigserial PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  feature_name text NOT NULL,
  usage_count integer DEFAULT 0,
  period_start timestamptz DEFAULT now(),
  period_end timestamptz DEFAULT now() + interval '1 month',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Billing events log (for audit trail)
CREATE TABLE IF NOT EXISTS public.billing_events (
  id bigserial PRIMARY KEY,
  user_id uuid REFERENCES auth.users(id) ON DELETE SET NULL,
  event_type text NOT NULL, -- 'subscription_created', 'subscription_updated', 'payment_succeeded', etc.
  event_data jsonb,
  stripe_event_id text,
  processed_at timestamptz DEFAULT now(),
  created_at timestamptz DEFAULT now()
);

-- Payment methods table (for future Stripe integration)
CREATE TABLE IF NOT EXISTS public.payment_methods (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_payment_method_id text NOT NULL,
  type text NOT NULL, -- 'card', 'bank_account', etc.
  is_default boolean DEFAULT false,
  metadata jsonb,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_id ON public.subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_user_id ON public.feature_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_feature_usage_feature ON public.feature_usage(feature_name);
CREATE INDEX IF NOT EXISTS idx_feature_usage_period ON public.feature_usage(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_billing_events_user_id ON public.billing_events(user_id);
CREATE INDEX IF NOT EXISTS idx_billing_events_type ON public.billing_events(event_type);
CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id ON public.payment_methods(user_id);

-- Enable RLS
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.feature_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.billing_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.payment_methods ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own subscription" ON public.subscriptions
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can view their own feature usage" ON public.feature_usage
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can update their own feature usage" ON public.feature_usage
  FOR UPDATE USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own feature usage" ON public.feature_usage
  FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can view their own billing events" ON public.billing_events
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can view their own payment methods" ON public.payment_methods
  FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "Users can manage their own payment methods" ON public.payment_methods
  FOR ALL USING (user_id = auth.uid());

-- Functions for subscription management
CREATE OR REPLACE FUNCTION public.create_beta_subscription(p_user_id uuid)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  subscription_uuid uuid;
BEGIN
  -- Create beta subscription for user
  INSERT INTO public.subscriptions (user_id, plan_name, status, current_period_start, current_period_end)
  VALUES (
    p_user_id, 
    'beta_free', 
    'active',
    now(),
    now() + interval '1 year'  -- Long beta period
  )
  RETURNING id INTO subscription_uuid;
  
  -- Initialize feature usage tracking
  INSERT INTO public.feature_usage (user_id, feature_name, usage_count, period_start, period_end)
  VALUES 
    (p_user_id, 'resume_parsing', 0, now(), now() + interval '1 month'),
    (p_user_id, 'resume_rewriting', 0, now(), now() + interval '1 month'),
    (p_user_id, 'job_matching', 0, now(), now() + interval '1 month'),
    (p_user_id, 'career_advisor', 0, now(), now() + interval '1 month'),
    (p_user_id, 'api_access', 0, now(), now() + interval '1 month'),
    (p_user_id, 'team_collaboration', 0, now(), now() + interval '1 month'),
    (p_user_id, 'multilingual', 0, now(), now() + interval '1 month'),
    (p_user_id, 'export_formats', 0, now(), now() + interval '1 month');
  
  RETURN subscription_uuid;
END;
$$;

CREATE OR REPLACE FUNCTION public.track_feature_usage(
  p_user_id uuid,
  p_feature_name text,
  p_usage_count integer DEFAULT 1
)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Update feature usage (upsert)
  INSERT INTO public.feature_usage (user_id, feature_name, usage_count, period_start, period_end)
  VALUES (p_user_id, p_feature_name, p_usage_count, now(), now() + interval '1 month')
  ON CONFLICT (user_id, feature_name, period_start) 
  DO UPDATE SET 
    usage_count = feature_usage.usage_count + p_usage_count,
    updated_at = now();
END;
$$;

CREATE OR REPLACE FUNCTION public.get_user_usage_stats(p_user_id uuid)
RETURNS TABLE (
  feature_name text,
  current_usage bigint,
  period_start timestamptz,
  period_end timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN QUERY
  SELECT 
    fu.feature_name,
    fu.usage_count::bigint,
    fu.period_start,
    fu.period_end
  FROM public.feature_usage fu
  WHERE fu.user_id = p_user_id
    AND fu.period_start <= now()
    AND fu.period_end > now()
  ORDER BY fu.feature_name;
END;
$$;

-- Create triggers
CREATE TRIGGER update_subscriptions_updated_at 
  BEFORE UPDATE ON public.subscriptions 
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_feature_usage_updated_at 
  BEFORE UPDATE ON public.feature_usage 
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_payment_methods_updated_at 
  BEFORE UPDATE ON public.payment_methods 
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- Insert beta subscription for existing users (if any)
-- This would be run for existing users when the migration is applied
-- DO $$
-- BEGIN
--   INSERT INTO public.subscriptions (user_id, plan_name, status, current_period_start, current_period_end)
--   SELECT 
--     id as user_id,
--     'beta_free' as plan_name,
--     'active' as status,
--     now() as current_period_start,
--     now() + interval '1 year' as current_period_end
--   FROM auth.users
--   WHERE id NOT IN (SELECT user_id FROM public.subscriptions);
-- END $$;
