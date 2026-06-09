-- Supabase starter schema for Dog Translator.

create table if not exists public.dogs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null,
  breed text,
  breed_source text not null default 'unknown',
  breed_confidence numeric,
  breed_predictions jsonb not null default '[]'::jsonb,
  breed_behavior_profile jsonb not null default '{}'::jsonb,
  age_years numeric,
  sex text,
  routines jsonb not null default '{}'::jsonb,
  known_habits jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.dogs add column if not exists breed_source text not null default 'unknown';
alter table public.dogs add column if not exists breed_confidence numeric;
alter table public.dogs add column if not exists breed_predictions jsonb not null default '[]'::jsonb;
alter table public.dogs add column if not exists breed_behavior_profile jsonb not null default '{}'::jsonb;

create table if not exists public.analysis_jobs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  dog_id uuid not null references public.dogs(id) on delete cascade,
  status text not null default 'queued',
  progress numeric not null default 0,
  storage_path text,
  context_tags jsonb not null default '[]'::jsonb,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.analysis_results (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null unique references public.analysis_jobs(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  dog_id uuid not null references public.dogs(id) on delete cascade,
  top_predictions jsonb not null default '[]'::jsonb,
  uncertainty_reason text,
  needs_feedback boolean not null default true,
  evidence_timeline jsonb not null default '[]'::jsonb,
  raw_signals jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.feedback (
  id uuid primary key default gen_random_uuid(),
  job_id uuid not null references public.analysis_jobs(id) on delete cascade,
  owner_id uuid not null references auth.users(id) on delete cascade,
  dog_id uuid not null references public.dogs(id) on delete cascade,
  selected_label text not null,
  is_correct boolean,
  note text,
  created_at timestamptz not null default now()
);

create table if not exists public.habit_summaries (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  dog_id uuid not null unique references public.dogs(id) on delete cascade,
  label_counts jsonb not null default '{}'::jsonb,
  recent_notes jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now()
);

alter table public.dogs enable row level security;
alter table public.analysis_jobs enable row level security;
alter table public.analysis_results enable row level security;
alter table public.feedback enable row level security;
alter table public.habit_summaries enable row level security;

drop policy if exists "owners manage dogs" on public.dogs;
create policy "owners manage dogs"
on public.dogs for all
using (auth.uid() = owner_id)
with check (auth.uid() = owner_id);

drop policy if exists "owners manage analysis jobs" on public.analysis_jobs;
create policy "owners manage analysis jobs"
on public.analysis_jobs for all
using (auth.uid() = owner_id)
with check (auth.uid() = owner_id);

drop policy if exists "owners manage analysis results" on public.analysis_results;
create policy "owners manage analysis results"
on public.analysis_results for all
using (auth.uid() = owner_id)
with check (auth.uid() = owner_id);

drop policy if exists "owners manage feedback" on public.feedback;
create policy "owners manage feedback"
on public.feedback for all
using (auth.uid() = owner_id)
with check (auth.uid() = owner_id);

drop policy if exists "owners manage habit summaries" on public.habit_summaries;
create policy "owners manage habit summaries"
on public.habit_summaries for all
using (auth.uid() = owner_id)
with check (auth.uid() = owner_id);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'dog-videos',
  'dog-videos',
  false,
  524288000,
  array['video/mp4', 'video/quicktime', 'video/x-m4v', 'audio/mpeg', 'audio/wav']
)
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

drop policy if exists "owners manage dog videos" on storage.objects;
create policy "owners manage dog videos"
on storage.objects for all
to authenticated
using (
  bucket_id = 'dog-videos'
  and (storage.foldername(name))[1] = auth.uid()::text
)
with check (
  bucket_id = 'dog-videos'
  and (storage.foldername(name))[1] = auth.uid()::text
);
