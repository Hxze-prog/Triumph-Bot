-- Triumph Bot - executed clean test-to-production guild migration
--
-- Production guild: 1565983272217874535 (♛ 𝙏𝙍𝙄𝙄𝙐𝙈𝙋𝙃)
-- Test guild:       1569030756515323974 (deleted 2026-11-19)
--
-- The cutover was executed on 2026-11-19 with a logical data export stored
-- outside the repository. This idempotent SQL record is retained for audit and
-- recovery. It is intentionally outside supabase/migrations.

begin;

do $$
begin
  if 1569030756515323974 = 1565983272217874535 then
    raise exception 'TEST_GUILD_ID and REAL_GUILD_ID must be different';
  end if;
end $$;

insert into public.guilds (id, name, owner_id)
values (1565983272217874535, '♛ 𝙏𝙍𝙄𝙄𝙐𝙈𝙋𝙃', 1064601909266239710)
on conflict (id) do update
set name = excluded.name,
    owner_id = excluded.owner_id;

insert into public.guild_settings (guild_id)
values (1565983272217874535)
on conflict (guild_id) do nothing;

insert into public.dashboard_admins (user_id, discord_id, guild_id, role)
select user_id, discord_id, 1565983272217874535, role
from public.dashboard_admins
where guild_id = 1569030756515323974
on conflict (user_id, guild_id) do update
set discord_id = excluded.discord_id,
    role = excluded.role;

do $$
begin
  if not exists (
    select 1
    from public.dashboard_admins
    where guild_id = 1565983272217874535
  ) then
    raise exception 'No dashboard admin row exists for the production guild';
  end if;
end $$;

delete from public.guilds
where id = 1569030756515323974;

commit;

select id, name, owner_id, created_at
from public.guilds
where id = 1565983272217874535;

select guild_id, prefix, created_at, updated_at
from public.guild_settings
where guild_id = 1565983272217874535;

select user_id, discord_id, guild_id, role
from public.dashboard_admins
where guild_id = 1565983272217874535
order by discord_id;

select 'guilds' as source, count(*) as remaining
from public.guilds where id = 1569030756515323974
union all
select 'guild_settings', count(*)
from public.guild_settings where guild_id = 1569030756515323974
union all
select 'members', count(*)
from public.members where guild_id = 1569030756515323974
union all
select 'warnings', count(*)
from public.warnings where guild_id = 1569030756515323974
union all
select 'moderation_logs', count(*)
from public.moderation_logs where guild_id = 1569030756515323974
union all
select 'temp_voice_channels', count(*)
from public.temp_voice_channels where guild_id = 1569030756515323974
union all
select 'reaction_roles', count(*)
from public.reaction_roles where guild_id = 1569030756515323974
union all
select 'automations', count(*)
from public.automations where guild_id = 1569030756515323974
union all
select 'polls', count(*)
from public.polls where guild_id = 1569030756515323974
union all
select 'activity_logs', count(*)
from public.activity_logs where guild_id = 1569030756515323974
union all
select 'server_stats', count(*)
from public.server_stats where guild_id = 1569030756515323974
union all
select 'dashboard_admins', count(*)
from public.dashboard_admins where guild_id = 1569030756515323974;
