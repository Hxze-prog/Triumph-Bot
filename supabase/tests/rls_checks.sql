-- Triumph Bot - RLS verification checklist (run in Supabase SQL editor)
-- Purpose: confirm anon/authenticated users cannot read or modify other guilds' data.
-- Note: service_role bypasses RLS; these checks are for anon/authenticated contexts.

-- 1) Preconditions: create two test guilds and an admin row for a known auth user.
-- Replace <AUTH_USER_UUID> and <GUILD_ID_ALLOWED> with real values from your project.
/*
insert into public.guilds (id, name) values (111111111111111111, 'Guild A'), (222222222222222222, 'Guild B')
on conflict (id) do nothing;
insert into public.guild_settings (guild_id) values (111111111111111111), (222222222222222222)
on conflict (guild_id) do nothing;
insert into public.dashboard_admins (user_id, discord_id, guild_id, role)
values ('<AUTH_USER_UUID>', 999999999999999999, 111111111111111111, 'admin')
on conflict (user_id, guild_id) do nothing;
insert into public.activity_logs (guild_id, event_type, payload)
values (111111111111111111, 'test.allowed', '{"ok":true}'::jsonb),
       (222222222222222222, 'test.denied', '{"ok":false}'::jsonb);
*/

-- 2) As postgres/service context (SQL editor default often runs as postgres): should see both rows.
-- select guild_id, event_type from public.activity_logs where event_type like 'test.%' order by guild_id;

-- 3) Simulate authenticated user context (adjust claims to match a real auth.users row):
/*
set local role authenticated;
set local request.jwt.claims = '{"sub":"<AUTH_USER_UUID>","role":"authenticated"}';
-- Should return only Guild A rows:
select guild_id, event_type from public.activity_logs where event_type like 'test.%' order by guild_id;
-- Should fail or affect 0 rows for Guild B:
update public.guild_settings set prefix = '?' where guild_id = 222222222222222222;
select guild_id, prefix from public.guild_settings where guild_id in (111111111111111111,222222222222222222);
reset role;
*/

-- 4) Simulate anon context:
/*
set local role anon;
-- Should return no rows:
select * from public.guilds;
select * from public.activity_logs;
select * from public.dashboard_admins;
reset role;
*/

-- 5) Cleanup test data:
/*
delete from public.activity_logs where event_type like 'test.%';
delete from public.dashboard_admins where guild_id in (111111111111111111,222222222222222222) and discord_id = 999999999999999999;
delete from public.guild_settings where guild_id in (111111111111111111,222222222222222222);
delete from public.guilds where id in (111111111111111111,222222222222222222);
*/
