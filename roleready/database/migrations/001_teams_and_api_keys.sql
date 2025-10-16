-- Step 9: Team Workspaces and Public API
-- Migration: Create teams, team_members, and api_keys tables

-- Teams table
CREATE TABLE IF NOT EXISTS public.teams (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  owner_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  description text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

-- Team members table
CREATE TABLE IF NOT EXISTS public.team_members (
  team_id uuid REFERENCES public.teams(id) ON DELETE CASCADE,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  role text CHECK (role IN ('owner','editor','viewer')) DEFAULT 'editor',
  invited_at timestamptz DEFAULT now(),
  joined_at timestamptz,
  PRIMARY KEY (team_id, user_id)
);

-- API keys table
CREATE TABLE IF NOT EXISTS public.api_keys (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  key text NOT NULL UNIQUE,
  name text NOT NULL DEFAULT 'Default API Key',
  last_used_at timestamptz,
  created_at timestamptz DEFAULT now(),
  expires_at timestamptz
);

-- Add team_id to resumes table
ALTER TABLE public.resumes 
ADD COLUMN IF NOT EXISTS team_id uuid REFERENCES public.teams(id) ON DELETE SET NULL;

-- Add team_id to comments table
ALTER TABLE public.comments 
ADD COLUMN IF NOT EXISTS team_id uuid REFERENCES public.teams(id) ON DELETE CASCADE;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_teams_owner_id ON public.teams(owner_id);
CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON public.team_members(team_id);
CREATE INDEX IF NOT EXISTS idx_team_members_user_id ON public.team_members(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON public.api_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_key ON public.api_keys(key);
CREATE INDEX IF NOT EXISTS idx_resumes_team_id ON public.resumes(team_id);
CREATE INDEX IF NOT EXISTS idx_comments_team_id ON public.comments(team_id);

-- Row Level Security (RLS) policies
ALTER TABLE public.teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.team_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.api_keys ENABLE ROW LEVEL SECURITY;

-- Teams policies
CREATE POLICY "Users can view teams they are members of" ON public.teams
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.team_members 
      WHERE team_members.team_id = teams.id 
      AND team_members.user_id = auth.uid()
    )
  );

CREATE POLICY "Team owners can update their teams" ON public.teams
  FOR UPDATE USING (
    owner_id = auth.uid()
  );

CREATE POLICY "Team owners can delete their teams" ON public.teams
  FOR DELETE USING (
    owner_id = auth.uid()
  );

-- Team members policies
CREATE POLICY "Users can view team members of teams they belong to" ON public.team_members
  FOR SELECT USING (
    EXISTS (
      SELECT 1 FROM public.team_members tm
      WHERE tm.team_id = team_members.team_id 
      AND tm.user_id = auth.uid()
    )
  );

CREATE POLICY "Team owners can manage team members" ON public.team_members
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM public.teams 
      WHERE teams.id = team_members.team_id 
      AND teams.owner_id = auth.uid()
    )
  );

-- API keys policies
CREATE POLICY "Users can manage their own API keys" ON public.api_keys
  FOR ALL USING (
    user_id = auth.uid()
  );

-- Functions for team management
CREATE OR REPLACE FUNCTION public.create_team(team_name text, team_description text DEFAULT NULL)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  team_uuid uuid;
BEGIN
  INSERT INTO public.teams (name, owner_id, description)
  VALUES (team_name, auth.uid(), team_description)
  RETURNING id INTO team_uuid;
  
  -- Add creator as owner
  INSERT INTO public.team_members (team_id, user_id, role, joined_at)
  VALUES (team_uuid, auth.uid(), 'owner', now());
  
  RETURN team_uuid;
END;
$$;

CREATE OR REPLACE FUNCTION public.invite_team_member(team_uuid uuid, user_email text, member_role text DEFAULT 'editor')
RETURNS boolean
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  target_user_id uuid;
BEGIN
  -- Get user ID from email
  SELECT id INTO target_user_id 
  FROM auth.users 
  WHERE email = user_email;
  
  IF target_user_id IS NULL THEN
    RETURN false;
  END IF;
  
  -- Check if inviter is team owner
  IF NOT EXISTS (
    SELECT 1 FROM public.teams 
    WHERE id = team_uuid AND owner_id = auth.uid()
  ) THEN
    RETURN false;
  END IF;
  
  -- Insert team member
  INSERT INTO public.team_members (team_id, user_id, role)
  VALUES (team_uuid, target_user_id, member_role)
  ON CONFLICT (team_id, user_id) DO UPDATE SET role = EXCLUDED.role;
  
  RETURN true;
END;
$$;

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_teams_updated_at 
  BEFORE UPDATE ON public.teams 
  FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
