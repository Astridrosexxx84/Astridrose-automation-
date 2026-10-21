-- Prevent object-shadowing through a caller-controlled search_path.
-- Keep the trigger's behaviour unchanged while qualifying the clock function.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = pg_catalog.now();
  return new;
end;
$$;
