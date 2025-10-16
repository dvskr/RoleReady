-- Step 8: Collaborators, Targeted Versions & Pricing Database Setup
-- Run these commands in your Supabase SQL editor

-- Add parent_id column to resumes for targeted versions
alter table public.resumes add column if not exists parent_id uuid references public.resumes(id);

-- Create collaborators table for sharing resumes
create table if not exists public.collaborators (
  id uuid primary key default gen_random_uuid(),
  resume_id uuid not null references public.resumes(id) on delete cascade,
  inviter_id uuid not null references auth.users(id) on delete cascade,
  invitee_email text not null,
  role text check (role in ('viewer','commenter','editor')) default 'viewer',
  accepted boolean default false,
  invite_token uuid default gen_random_uuid(),
  created_at timestamptz default now()
);

-- Enable RLS on collaborators
alter table public.collaborators enable row level security;

-- RLS policies for collaborators
create policy "collaborators_own_read"
  on public.collaborators for select
  using (
    auth.uid() = inviter_id or 
    auth.uid() = (select user_id from public.resumes r where r.id=resume_id) or
    invitee_email = (select email from auth.users where id = auth.uid())
  );

create policy "collaborators_own_insert"
  on public.collaborators for insert with check (auth.uid() = inviter_id);

create policy "collaborators_own_update"
  on public.collaborators for update 
  using (auth.uid() = inviter_id or invitee_email = (select email from auth.users where id = auth.uid()));

create policy "collaborators_own_delete"
  on public.collaborators for delete using (auth.uid() = inviter_id);

-- Create billing tiers table
create table if not exists public.user_tiers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  tier text check (tier in ('free','pro','recruiter')) default 'free',
  subscription_id text,
  status text check (status in ('active','cancelled','expired')) default 'active',
  expires_at timestamptz,
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(user_id)
);

-- Enable RLS on user_tiers
alter table public.user_tiers enable row level security;

-- RLS policies for user_tiers
create policy "user_tiers_own_read" on public.user_tiers 
  for select using ( user_id = auth.uid() );

create policy "user_tiers_own_write" on public.user_tiers 
  for insert with check ( user_id = auth.uid() );

create policy "user_tiers_own_update" on public.user_tiers 
  for update using ( user_id = auth.uid() );

-- Create usage tracking table
create table if not exists public.usage_tracking (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  action text not null,
  resource_type text not null,
  resource_id uuid,
  metadata jsonb default '{}',
  created_at timestamptz default now()
);

-- Enable RLS on usage_tracking
alter table public.usage_tracking enable row level security;

-- RLS policies for usage_tracking
create policy "usage_tracking_own_read" on public.usage_tracking 
  for select using ( user_id = auth.uid() );

create policy "usage_tracking_own_write" on public.usage_tracking 
  for insert with check ( user_id = auth.uid() );

-- Indexes for performance
create index if not exists idx_collaborators_resume_id on public.collaborators(resume_id);
create index if not exists idx_collaborators_invitee_email on public.collaborators(invitee_email);
create index if not exists idx_collaborators_invite_token on public.collaborators(invite_token);
create index if not exists idx_resumes_parent_id on public.resumes(parent_id);
create index if not exists idx_user_tiers_user_id on public.user_tiers(user_id);
create index if not exists idx_usage_tracking_user_id on public.usage_tracking(user_id);
create index if not exists idx_usage_tracking_created_at on public.usage_tracking(created_at desc);

-- Function to check if user can access resume
create or replace function can_access_resume(resume_uuid uuid)
returns boolean as $$
begin
  -- Owner can access
  if exists(select 1 from public.resumes where id = resume_uuid and user_id = auth.uid()) then
    return true;
  end if;
  
  -- Collaborator can access
  if exists(
    select 1 from public.collaborators c 
    where c.resume_id = resume_uuid 
    and c.accepted = true
    and (c.invitee_email = (select email from auth.users where id = auth.uid()))
  ) then
    return true;
  end if;
  
  return false;
end;
$$ language plpgsql security definer;

-- Function to get user role for resume
create or replace function get_resume_role(resume_uuid uuid)
returns text as $$
begin
  -- Owner
  if exists(select 1 from public.resumes where id = resume_uuid and user_id = auth.uid()) then
    return 'owner';
  end if;
  
  -- Collaborator
  if exists(
    select 1 from public.collaborators c 
    where c.resume_id = resume_uuid 
    and c.accepted = true
    and (c.invitee_email = (select email from auth.users where id = auth.uid()))
  ) then
    return (select role from public.collaborators c 
            where c.resume_id = resume_uuid 
            and c.accepted = true
            and (c.invitee_email = (select email from auth.users where id = auth.uid()))
            limit 1);
  end if;
  
  return null;
end;
$$ language plpgsql security definer;

-- Update resumes RLS to include collaborator access
drop policy if exists "resumes_own_read" on public.resumes;
create policy "resumes_own_read" on public.resumes 
  for select using (can_access_resume(id));

-- Update comments RLS to include collaborator access
drop policy if exists "comments_own_read" on public.comments;
create policy "comments_own_read" on public.comments 
  for select using (
    can_access_resume(resume_id) and
    (user_id = auth.uid() or get_resume_role(resume_id) in ('owner', 'editor', 'commenter'))
  );

-- Update comments write policy for collaborators
drop policy if exists "comments_own_write" on public.comments;
create policy "comments_own_write" on public.comments 
  for insert with check (
    can_access_resume(resume_id) and
    (user_id = auth.uid() and get_resume_role(resume_id) in ('owner', 'editor', 'commenter'))
  );
