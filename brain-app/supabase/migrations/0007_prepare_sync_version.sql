-- Phase 1: add row revisions and keep them advancing while the new client rolls out.
-- Enforcement is enabled separately after the version-aware app is deployed.
alter table public.brain_projects
  add column if not exists sync_version bigint not null default 1;
alter table public.brain_tasks
  add column if not exists sync_version bigint not null default 1;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.sync_version := old.sync_version + 1;
  new.updated_at := pg_catalog.now();
  return new;
end;
$$;
