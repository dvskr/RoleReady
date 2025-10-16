# Step 5 Setup Instructions

## Environment Variables

### Frontend (.env.local)
Create `roleready/apps/web/.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

### Backend (.env)
Create `roleready/apps/api/.env`:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
OPENAI_API_KEY=your-openai-api-key
API_BASE_URL=http://localhost:8000/api
```

## Supabase Database Setup

Run these SQL commands in your Supabase SQL editor:

```sql
-- Users come from auth.users; optional profile table
create table if not exists public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text,
  avatar_url text,
  created_at timestamptz default now()
);

create table if not exists public.resumes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null default 'Untitled',
  content text not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.analytics (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  resume_id uuid references public.resumes(id) on delete cascade,
  score numeric,
  jd_keywords text[],
  created_at timestamptz default now()
);

-- Enable RLS
alter table public.profiles enable row level security;
alter table public.resumes enable row level security;
alter table public.analytics enable row level security;

-- Profiles: users can read/update themselves
create policy "profiles_own_read" on public.profiles
for select using ( auth.uid() = id );
create policy "profiles_own_update" on public.profiles
for update using ( auth.uid() = id );

-- Resumes: CRUD owned rows
create policy "resumes_own_read" on public.resumes
for select using ( auth.uid() = user_id );
create policy "resumes_own_insert" on public.resumes
for insert with check ( auth.uid() = user_id );
create policy "resumes_own_update" on public.resumes
for update using ( auth.uid() = user_id );
create policy "resumes_own_delete" on public.resumes
for delete using ( auth.uid() = user_id );

-- Analytics: read/write own rows
create policy "analytics_own_read" on public.analytics
for select using ( auth.uid() = user_id );
create policy "analytics_own_insert" on public.analytics
for insert with check ( auth.uid() = user_id );
```

## Chrome Extension Setup

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension/` folder from this repository
5. The RoleReady JD Scraper extension will appear in your extensions

## Testing the Complete Flow

1. Start both servers:
   ```bash
   # Terminal 1: API Server
   cd roleready/apps/api
   python -m uvicorn roleready_api.main:app --reload --port 8000

   # Terminal 2: Web App
   cd roleready/apps/web
   npm run dev
   ```

2. Test authentication:
   - Go to `http://localhost:3000/login`
   - Sign in with Google or email OTP
   - You should be redirected to the dashboard

3. Test resume management:
   - Create a new resume from the dashboard
   - Edit it in the editor
   - Save your changes

4. Test Chrome extension:
   - Go to a job posting on LinkedIn, Indeed, or Glassdoor
   - Click the RoleReady extension icon
   - It should open the editor with the JD preloaded

## Features Implemented

✅ **Authentication**: Google OAuth and Email OTP via Supabase  
✅ **User Dashboard**: List, create, and manage resumes  
✅ **Protected Routes**: AuthGate component for route protection  
✅ **JWT Verification**: Backend API authentication  
✅ **Resume Persistence**: Load/save resumes by ID  
✅ **Chrome Extension**: JD scraper for major job sites  
✅ **Smart Rewrite**: Enhanced with intelligent keyword distribution  

## Next Steps (Step 6 Preview)

- Autosave and version history
- Export to DOCX/PDF with templates
- Team features and sharing
- Analytics and metrics tracking
