-- Brain App core schema (not yet applied to a Supabase project).
-- Private-by-default: authenticated users can access only rows they own.
-- Never put service-role keys in browser code or this public repository.

create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.brain_projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  name text not null check (length(trim(name)) between 1 and 160),
  description text not null default '',
  status text not null default 'active' check (status in ('active','paused','archived')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.brain_tasks (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  project_id uuid references public.brain_projects(id) on delete set null,
  title text not null check (length(trim(title)) between 1 and 240),
  goal text not null default '',
  context text not null default '',
  status text not null default 'queued' check (status in ('queued','running','blocked','review','completed','failed','cancelled')),
  priority smallint not null default 3 check (priority between 1 and 5),
  assigned_worker text,
  result_summary text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.brain_worker_runs (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users(id) on delete cascade,
  task_id uuid not null references public.brain_tasks(id) on delete cascade,
  provider text not null,
  model text,
  status text not null default 'queued' check (status in ('queued','running','succeeded','failed','skipped')),
  attempt integer not null default 1 check (attempt > 0),
  request_payload jsonb not null default '{}'::jsonb,
  response_payload jsonb,
  error_category text,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists public.brain_task_events (
  id bigint generated always as identity primary key,
  owner_id uuid not null references auth.users(id) on delete cascade,
  task_id uuid not null references public.brain_tasks(id) on delete cascade,
  event_type text not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists brain_projects_owner_updated_idx
  on public.brain_projects (owner_id, updated_at desc);
create index if not exists brain_tasks_owner_status_updated_idx
  on public.brain_tasks (owner_id, status, updated_at desc);
create index if not exists brain_tasks_project_idx
  on public.brain_tasks (project_id);
create index if not exists brain_worker_runs_task_created_idx
  on public.brain_worker_runs (task_id, created_at desc);
create index if not exists brain_task_events_task_created_idx
  on public.brain_task_events (task_id, created_at desc);

drop trigger if exists brain_projects_set_updated_at on public.brain_projects;
create trigger brain_projects_set_updated_at before update on public.brain_projects
for each row execute function public.set_updated_at();

drop trigger if exists brain_tasks_set_updated_at on public.brain_tasks;
create trigger brain_tasks_set_updated_at before update on public.brain_tasks
for each row execute function public.set_updated_at();

alter table public.brain_projects enable row level security;
alter table public.brain_tasks enable row level security;
alter table public.brain_worker_runs enable row level security;
alter table public.brain_task_events enable row level security;

drop policy if exists "owners manage their projects" on public.brain_projects;
create policy "owners manage their projects" on public.brain_projects
for all to authenticated
using (owner_id = (select auth.uid()))
with check (owner_id = (select auth.uid()));

drop policy if exists "owners manage their tasks" on public.brain_tasks;
create policy "owners manage their tasks" on public.brain_tasks
for all to authenticated
using (owner_id = (select auth.uid()))
with check (
  owner_id = (select auth.uid())
  and (
    project_id is null
    or exists (
      select 1 from public.brain_projects p
      where p.id = project_id and p.owner_id = (select auth.uid())
    )
  )
);

drop policy if exists "owners manage their worker runs" on public.brain_worker_runs;
create policy "owners manage their worker runs" on public.brain_worker_runs
for all to authenticated
using (owner_id = (select auth.uid()))
with check (
  owner_id = (select auth.uid())
  and exists (
    select 1 from public.brain_tasks t
    where t.id = task_id and t.owner_id = (select auth.uid())
  )
);

drop policy if exists "owners manage their task events" on public.brain_task_events;
create policy "owners manage their task events" on public.brain_task_events
for all to authenticated
using (owner_id = (select auth.uid()))
with check (
  owner_id = (select auth.uid())
  and exists (
    select 1 from public.brain_tasks t
    where t.id = task_id and t.owner_id = (select auth.uid())
  )
);

comment on table public.brain_projects is 'User-owned Brain App projects.';
comment on table public.brain_tasks is 'Durable user-owned task queue; not browser-local-only.';
comment on table public.brain_worker_runs is 'Private per-provider execution attempts and outputs.';
comment on table public.brain_task_events is 'Private append-style task audit events.';
