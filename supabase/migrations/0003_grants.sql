-- Triumph Bot - 0003 Grants
-- Tables created via the SQL editor may not inherit Supabase default privileges.
-- PostgREST roles need explicit USAGE + table grants or you get:
--   42501 "permission denied for table ..."
-- RLS (0002) still restricts what anon/authenticated can actually read or write.

begin;

grant usage on schema public to anon, authenticated, service_role;

-- service_role: full server-side access (bypasses RLS)
grant select, insert, update, delete on all tables in schema public to service_role;
grant usage, select on all sequences in schema public to service_role;

-- authenticated: dashboard access, still filtered by RLS policies
grant select, insert, update, delete on all tables in schema public to authenticated;
grant usage, select on all sequences in schema public to authenticated;

-- anon: select only, RLS yields no rows (used for pre-auth dashboard checks)
grant select on all tables in schema public to anon;

-- RPCs
grant execute on function public.is_dashboard_admin(bigint) to anon, authenticated, service_role;
grant execute on function public.next_member_number(bigint) to service_role;

-- Keep grants consistent for future objects created by this role.
alter default privileges in schema public grant select on tables to anon;
alter default privileges in schema public grant select, insert, update, delete on tables to authenticated;
alter default privileges in schema public grant select, insert, update, delete on tables to service_role;
alter default privileges in schema public grant usage, select on sequences to anon, authenticated, service_role;

commit;
