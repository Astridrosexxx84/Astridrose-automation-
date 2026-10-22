-- Keep the checked-in schema aligned with the task fields used by app.js.
-- Idempotent so this is safe when reconciling an existing database.
alter table public.brain_tasks
  add column if not exists current_worker text not null default '',
  add column if not exists next_worker text not null default '',
  add column if not exists current_output text not null default '',
  add column if not exists next_action text not null default '';
