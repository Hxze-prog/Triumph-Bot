-- Triumph Bot - 0002 RLS Policies
-- Enables Row Level Security and defines dashboard access policies.
-- Bot/server code uses the service_role key which bypasses RLS.
-- Dashboard uses anon key + authenticated user JWT; access is limited to rows
-- for guilds where the user is recorded in public.dashboard_admins.

begin;

-- -----------------------------------------------------------------------------
-- Enable RLS
-- -----------------------------------------------------------------------------

alter table public.guilds enable row level security;
alter table public.guild_settings enable row level security;
alter table public.members enable row level security;
alter table public.warnings enable row level security;
alter table public.moderation_logs enable row level security;
alter table public.temp_voice_channels enable row level security;
alter table public.reaction_roles enable row level security;
alter table public.automations enable row level security;
alter table public.polls enable row level security;
alter table public.activity_logs enable row level security;
alter table public.server_stats enable row level security;
alter table public.dashboard_admins enable row level security;

-- Force RLS for table owners as well (optional hardening). Service role still bypasses.
alter table public.guilds force row level security;
alter table public.guild_settings force row level security;
alter table public.members force row level security;
alter table public.warnings force row level security;
alter table public.moderation_logs force row level security;
alter table public.temp_voice_channels force row level security;
alter table public.reaction_roles force row level security;
alter table public.automations force row level security;
alter table public.polls force row level security;
alter table public.activity_logs force row level security;
alter table public.server_stats force row level security;
alter table public.dashboard_admins force row level security;

-- -----------------------------------------------------------------------------
-- dashboard_admins: users can read their own admin rows only.
-- Writes are performed by trusted server actions using service_role after
-- Discord identity/membership/role verification.
-- -----------------------------------------------------------------------------

drop policy if exists dashboard_admins_select_own on public.dashboard_admins;
create policy dashboard_admins_select_own
  on public.dashboard_admins
  for select
  to authenticated
  using (user_id = auth.uid());

-- No insert/update/delete policies for anon/authenticated roles.
-- (Service role bypasses RLS and can manage rows.)

-- -----------------------------------------------------------------------------
-- Guild-scoped tables
-- Dashboard admins may read data for their guilds.
-- Dashboard-managed configuration tables also allow insert/update/delete for admins.
-- Bot-generated history/log tables are read-only from dashboard (writes via service_role).
-- -----------------------------------------------------------------------------

-- guilds
drop policy if exists guilds_select_admin on public.guilds;
create policy guilds_select_admin
  on public.guilds
  for select
  to authenticated
  using (public.is_dashboard_admin(id));

drop policy if exists guilds_update_admin on public.guilds;
create policy guilds_update_admin
  on public.guilds
  for update
  to authenticated
  using (public.is_dashboard_admin(id))
  with check (public.is_dashboard_admin(id));

-- guild_settings (dashboard manages settings)
drop policy if exists guild_settings_select_admin on public.guild_settings;
create policy guild_settings_select_admin
  on public.guild_settings
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

drop policy if exists guild_settings_insert_admin on public.guild_settings;
create policy guild_settings_insert_admin
  on public.guild_settings
  for insert
  to authenticated
  with check (public.is_dashboard_admin(guild_id));

drop policy if exists guild_settings_update_admin on public.guild_settings;
create policy guild_settings_update_admin
  on public.guild_settings
  for update
  to authenticated
  using (public.is_dashboard_admin(guild_id))
  with check (public.is_dashboard_admin(guild_id));

-- members (read-only in dashboard; bot/service writes)
drop policy if exists members_select_admin on public.members;
create policy members_select_admin
  on public.members
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

-- warnings (read in dashboard; bot/service writes; allow admin delete/deactivate via update if needed later)
drop policy if exists warnings_select_admin on public.warnings;
create policy warnings_select_admin
  on public.warnings
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

-- moderation_logs (read-only in dashboard)
drop policy if exists moderation_logs_select_admin on public.moderation_logs;
create policy moderation_logs_select_admin
  on public.moderation_logs
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

-- temp_voice_channels (read in dashboard; bot/service manages lifecycle)
drop policy if exists temp_voice_channels_select_admin on public.temp_voice_channels;
create policy temp_voice_channels_select_admin
  on public.temp_voice_channels
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

-- reaction_roles (dashboard can manage)
drop policy if exists reaction_roles_select_admin on public.reaction_roles;
create policy reaction_roles_select_admin
  on public.reaction_roles
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

drop policy if exists reaction_roles_insert_admin on public.reaction_roles;
create policy reaction_roles_insert_admin
  on public.reaction_roles
  for insert
  to authenticated
  with check (public.is_dashboard_admin(guild_id));

drop policy if exists reaction_roles_update_admin on public.reaction_roles;
create policy reaction_roles_update_admin
  on public.reaction_roles
  for update
  to authenticated
  using (public.is_dashboard_admin(guild_id))
  with check (public.is_dashboard_admin(guild_id));

drop policy if exists reaction_roles_delete_admin on public.reaction_roles;
create policy reaction_roles_delete_admin
  on public.reaction_roles
  for delete
  to authenticated
  using (public.is_dashboard_admin(guild_id));

-- automations (dashboard can manage)
drop policy if exists automations_select_admin on public.automations;
create policy automations_select_admin
  on public.automations
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

drop policy if exists automations_insert_admin on public.automations;
create policy automations_insert_admin
  on public.automations
  for insert
  to authenticated
  with check (public.is_dashboard_admin(guild_id));

drop policy if exists automations_update_admin on public.automations;
create policy automations_update_admin
  on public.automations
  for update
  to authenticated
  using (public.is_dashboard_admin(guild_id))
  with check (public.is_dashboard_admin(guild_id));

drop policy if exists automations_delete_admin on public.automations;
create policy automations_delete_admin
  on public.automations
  for delete
  to authenticated
  using (public.is_dashboard_admin(guild_id));

-- polls (read in dashboard; bot creates/updates via service role)
drop policy if exists polls_select_admin on public.polls;
create policy polls_select_admin
  on public.polls
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

-- activity_logs (read-only in dashboard)
drop policy if exists activity_logs_select_admin on public.activity_logs;
create policy activity_logs_select_admin
  on public.activity_logs
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

-- server_stats (read-only in dashboard)
drop policy if exists server_stats_select_admin on public.server_stats;
create policy server_stats_select_admin
  on public.server_stats
  for select
  to authenticated
  using (public.is_dashboard_admin(guild_id));

-- -----------------------------------------------------------------------------
-- Grants
-- service_role bypasses RLS but explicit grants are harmless. The anon/authenticated
-- roles rely on PostgREST/Supabase defaults; we keep privileges minimal.
-- -----------------------------------------------------------------------------

-- Allow authenticated users to call is_dashboard_admin (used implicitly by policies; explicit execute is fine).
grant execute on function public.is_dashboard_admin(bigint) to authenticated;
grant execute on function public.is_dashboard_admin(bigint) to anon;

-- next_member_number is intended for bot/service use only.
revoke all on function public.next_member_number(bigint) from public;
revoke all on function public.next_member_number(bigint) from anon;
revoke all on function public.next_member_number(bigint) from authenticated;
grant execute on function public.next_member_number(bigint) to service_role;

commit;
