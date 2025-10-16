-- Step 7: Collaboration and Analytics Database Setup
-- Run these commands in your Supabase SQL editor

-- Comments table for collaboration
create table if not exists public.comments (
  id uuid primary key default gen_random_uuid(),
  resume_id uuid references public.resumes(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  anchor_from int not null,
  anchor_to int not null,
  text text not null,
  resolved boolean default false,
  parent_id uuid references public.comments(id) on delete cascade,
  created_at timestamptz default now()
);

-- Enable RLS on comments
alter table public.comments enable row level security;

-- RLS policies for comments
create policy "comments_own_read" on public.comments 
for select using (
  exists(select 1 from public.resumes r where r.id=comments.resume_id and r.user_id=auth.uid()) 
  or comments.user_id=auth.uid()
);

create policy "comments_own_write" on public.comments 
for insert with check ( user_id = auth.uid() );

create policy "comments_own_update" on public.comments 
for update using ( user_id = auth.uid() );

create policy "comments_own_delete" on public.comments 
for delete using ( user_id = auth.uid() );

-- Analytics table for tracking scores over time
create table if not exists public.analytics (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  resume_id uuid references public.resumes(id) on delete cascade,
  score float not null,
  coverage float not null default 0.0,
  jd_keywords text[] default '{}',
  missing_keywords text[] default '{}',
  mode text not null default 'semantic',
  created_at timestamptz default now()
);

-- Enable RLS on analytics
alter table public.analytics enable row level security;

-- RLS policies for analytics
create policy "analytics_own_read" on public.analytics 
for select using ( user_id = auth.uid() );

create policy "analytics_own_write" on public.analytics 
for insert with check ( user_id = auth.uid() );

create policy "analytics_own_update" on public.analytics 
for update using ( user_id = auth.uid() );

create policy "analytics_own_delete" on public.analytics 
for delete using ( user_id = auth.uid() );

-- User profiles table for extension autofill
create table if not exists public.user_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  name text,
  email text,
  phone text,
  location text,
  linkedin_url text,
  github_url text,
  summary text,
  skills text[] default '{}',
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  unique(user_id)
);

-- Enable RLS on user_profiles
alter table public.user_profiles enable row level security;

-- RLS policies for user_profiles
create policy "user_profiles_own_read" on public.user_profiles 
for select using ( user_id = auth.uid() );

create policy "user_profiles_own_write" on public.user_profiles 
for insert with check ( user_id = auth.uid() );

create policy "user_profiles_own_update" on public.user_profiles 
for update using ( user_id = auth.uid() );

create policy "user_profiles_own_delete" on public.user_profiles 
for delete using ( user_id = auth.uid() );

-- Indexes for performance
create index if not exists idx_comments_resume_id on public.comments(resume_id);
create index if not exists idx_comments_user_id on public.comments(user_id);
create index if not exists idx_analytics_user_id on public.analytics(user_id);
create index if not exists idx_analytics_created_at on public.analytics(created_at desc);
create index if not exists idx_user_profiles_user_id on public.user_profiles(user_id);
