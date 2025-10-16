-- Step 6: Database Versioning Setup
-- Run these commands in your Supabase SQL editor

-- Version snapshots for each resume
create table if not exists public.resume_versions (
  id uuid primary key default gen_random_uuid(),
  resume_id uuid not null references public.resumes(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  content text not null,
  created_at timestamptz default now()
);

-- Auto-snapshot previous content whenever resumes.content changes
create or replace function public.snapshot_resume()
returns trigger as $$
begin
  if TG_OP = 'UPDATE' and NEW.content is distinct from OLD.content then
    insert into public.resume_versions (resume_id, user_id, content)
    values (OLD.id, OLD.user_id, OLD.content);
  end if;
  return NEW;
end;
$$ language plpgsql security definer;

drop trigger if exists trg_snapshot_resume on public.resumes;
create trigger trg_snapshot_resume
  before update on public.resumes
  for each row execute function public.snapshot_resume();

-- Optional: manual snapshot RPC
create or replace function public.manual_snapshot(r_id uuid)
returns void as $$
declare owner uuid; body text;
begin
  select user_id, content into owner, body from public.resumes where id = r_id;
  insert into public.resume_versions(resume_id, user_id, content) values (r_id, owner, body);
end; $$ language plpgsql security definer;

-- Enable RLS on resume_versions
alter table public.resume_versions enable row level security;

-- RLS policies for resume_versions
create policy "resume_versions_own_read" on public.resume_versions
for select using ( auth.uid() = user_id );

-- Optional: Shared links table for read-only sharing
create table if not exists public.shared_links (
  id uuid primary key default gen_random_uuid(),
  resume_id uuid not null references public.resumes(id) on delete cascade,
  token text not null unique,
  created_at timestamptz default now(),
  expires_at timestamptz
);

-- Enable RLS on shared_links
alter table public.shared_links enable row level security;

-- RLS policies for shared_links
create policy "shared_links_own_read" on public.shared_links
for select using ( auth.uid() = (select user_id from public.resumes where id = resume_id) );

create policy "shared_links_own_insert" on public.shared_links
for insert with check ( auth.uid() = (select user_id from public.resumes where id = resume_id) );

create policy "shared_links_own_delete" on public.shared_links
for delete using ( auth.uid() = (select user_id from public.resumes where id = resume_id) );
