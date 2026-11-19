-- Triumph Bot - clean test-to-production guild migration
--
-- DESTRUCTIVE: this deletes the test guild row and cascades all test data.
-- Run only after reading docs/MIGRATION.md and verifying a Supabase backup.
-- This file is intentionally outside supabase/migrations so it never runs
-- automatically.
--
-- Replace every <PLACEHOLDER> before running.

-- <TEST_GUILD_ID>    current test guild, for example 1569030756515323974
-- <REAL_GUILD_ID>    production Discord guild ID
-- <REAL_GUILD_NAME>  production Discord guild name
-- <REAL_OWNER_ID>    production Discord guild owner user ID

begin;

do $$
begin
  if <TEST_GUILD_ID> = <REAL_GUILD_ID> then
    raise exception 'TEST_GUILD_ID and REAL_GUILD_ID must be different';
  end if;
end $$;

-- 1. Create the production guild and default settings.
insert into public.guilds (id, name, owner_id)
values (<REAL_GUILD_ID>, '<REAL_GUILD_NAME>', <REAL_OWNER_ID>)
on conflict (id) do update
set name = excluded.name,
    owner_id = excluded.owner_id;

insert into public.guild_settings (guild_id)
values (<REAL_GUILD_ID>)
on conflict (guild_id) do nothing;

-- 2. Preserve dashboard access by copying the test admin rows to production.
insert into public.dashboard_admins (user_id, discord_id, guild_id, role)
select user_id, discord_id, <REAL_GUILD_ID>, role
from public.dashboard_admins
where guild_id = <TEST_GUILD_ID>
on conflict (user_id, guild_id) do update
set discord_id = excluded.discord_id,
    role = excluded.role;

do $$
begin
  if not exists (
    select 1
    from public.dashboard_admins
    where guild_id = <REAL_GUILD_ID>
  ) then
    raise exception 'No dashboard admin row was copied to the production guild';
  end if;
end $$;

-- 3. Delete the test guild. All guild-scoped tables use ON DELETE CASCADE.
delete from public.guilds
where id = <TEST_GUILD_ID>;

commit;

-- 4. Production rows.
select id, name, owner_id, created_at
from public.guilds
where id = <REAL_GUILD_ID>;

select guild_id, prefix, created_at, updated_at
from public.guild_settings
where guild_id = <REAL_GUILD_ID>;

select user_id, discord_id, guild_id, role
from public.dashboard_admins
where guild_id = <REAL_GUILD_ID>
order by discord_id;

-- 5. Test-guild counts must all be zero.
select 'guilds' as source, count(*) as remaining
from public.guilds where id = <TEST_GUILD_ID>
union all
select 'guild_settings', count(*)
from public.guild_settings where guild_id = <TEST_GUILD_ID>
union all
select 'members', count(*)
from public.members where guild_id = <TEST_GUILD_ID>
union all
select 'warnings', count(*)
from public.warnings where guild_id = <TEST_GUILD_ID>
union all
select 'moderation_logs', count(*)
from public.moderation_logs where guild_id = <TEST_GUILD_ID>
union all
select 'temp_voice_channels', count(*)
from public.temp_voice_channels where guild_id = <TEST_GUILD_ID>
union all
select 'reaction_roles', count(*)
from public.reaction_roles where guild_id = <TEST_GUILD_ID>
union all
select 'automations', count(*)
from public.automations where guild_id = <TEST_GUILD_ID>
union all
select 'polls', count(*)
from public.polls where guild_id = <TEST_GUILD_ID>
union all
select 'activity_logs', count(*)
from public.activity_logs where guild_id = <TEST_GUILD_ID>
union all
select 'server_stats', count(*)
from public.server_stats where guild_id = <TEST_GUILD_ID>
union all
select 'dashboard_admins', count(*)
from public.dashboard_admins where guild_id = <TEST_GUILD_ID>;
