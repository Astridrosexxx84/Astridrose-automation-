-- Phase 2: reject stale authenticated writes after version-aware clients are deployed.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
declare
  request_role text;
  client_sync_version text;
begin
  request_role := pg_catalog.current_setting('request.jwt.claim.role', true);
  client_sync_version := coalesce(pg_catalog.current_setting('request.headers', true), '{}')::jsonb ->> 'x-brain-sync-version';

  if request_role = 'authenticated' then
    if client_sync_version is distinct from '1' then
      raise exception using
        errcode = '40001',
        message = 'Cloud sync conflict: refresh the app to use safe sync, then retry.';
    end if;
    if new.sync_version is distinct from old.sync_version then
      raise exception using
        errcode = '40001',
        message = 'Cloud sync conflict: this record changed on the server. Refresh and retry.';
    end if;
  end if;

  new.sync_version := old.sync_version + 1;
  new.updated_at := pg_catalog.now();
  return new;
end;
$$;
