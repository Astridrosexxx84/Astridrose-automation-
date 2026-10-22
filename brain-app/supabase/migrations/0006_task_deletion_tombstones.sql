-- Preserve task deletion intent across devices so stale local copies cannot
-- resurrect a task after another device deletes it.
alter table public.brain_tasks
  add column if not exists deleted_at timestamptz;
