-- Small, safe performance fix: index owner foreign keys used by cascading deletes
-- and owner-scoped audit/run queries. No data is changed.
create index if not exists brain_worker_runs_owner_idx
  on public.brain_worker_runs (owner_id);
create index if not exists brain_task_events_owner_idx
  on public.brain_task_events (owner_id);
