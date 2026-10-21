-- One active private worker execution per task. Prevents duplicate/concurrent
-- runs from racing to overwrite the same task result.
-- Dispatch first reconciles abandoned queued/running attempts for the task.
create unique index if not exists brain_worker_runs_one_active_per_task_idx
  on public.brain_worker_runs (task_id)
  where status in ('queued', 'running');
