alter table public.dogs add column if not exists breed_source text not null default 'unknown';
alter table public.dogs add column if not exists breed_confidence numeric;
alter table public.dogs add column if not exists breed_predictions jsonb not null default '[]'::jsonb;
alter table public.dogs add column if not exists breed_behavior_profile jsonb not null default '{}'::jsonb;
