-- Triumph Bot - 0001 Initial Schema
-- Creates extensions, helper functions, tables, FKs, indexes, and triggers.
-- Safe to run in Supabase SQL editor or via migration tooling.

begin;

create extension if not exists pgcrypto;

-- -----------------------------------------------------------------------------
-- Helper functions
-- -----------------------------------------------------------------------------

-- Auto-update updated_at timestamps.
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- -----------------------------------------------------------------------------
-- Tables
-- -----------------------------------------------------------------------------

-- Guild registry and per-guild member counter.
create table if not exists public.guilds (
  id bigint primary key,
  name text,
  icon_url text,
  owner_id bigint,
  member_counter bigint not null default 0 check (member_counter >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Per-guild configuration used by bot and dashboard.
create table if not exists public.guild_settings (
  guild_id bigint primary key references public.guilds(id) on delete cascade,
  prefix text not null default '!',

  -- Welcome / goodbye
  welcome_enabled boolean not null default false,
  welcome_channel_id bigint,
  welcome_message text,
  welcome_embed_enabled boolean not null default true,
  welcome_banner_enabled boolean not null default true,
  welcome_banner_template text,
  welcome_dm_enabled boolean not null default false,
  welcome_dm_message text,
  goodbye_enabled boolean not null default false,
  goodbye_channel_id bigint,
  goodbye_message text,

  -- Roles
  auto_role_ids bigint[] not null default '{}'::bigint[],

  -- Logging channels (per event type)
  log_join_leave_channel_id bigint,
  log_message_delete_channel_id bigint,
  log_message_edit_channel_id bigint,
  log_role_change_channel_id bigint,
  log_nickname_change_channel_id bigint,
  log_voice_channel_id bigint,
  log_moderation_channel_id bigint,
  log_channel_events_channel_id bigint,

  -- Temporary voice
  temp_voice_category_id bigint,
  temp_voice_trigger_channel_id bigint,
  temp_voice_default_limit integer not null default 0 check (temp_voice_default_limit >= 0),
  temp_voice_name_template text not null default '{user}''s Channel',

  -- Automoderation
  automod_anti_spam_enabled boolean not null default false,
  automod_anti_link_enabled boolean not null default false,
  automod_anti_invite_enabled boolean not null default false,
  automod_spam_threshold integer not null default 5 check (automod_spam_threshold > 0),
  automod_spam_interval_seconds integer not null default 5 check (automod_spam_interval_seconds > 0),
  automod_timeout_seconds integer not null default 60 check (automod_timeout_seconds >= 0),

  -- Dashboard access roles (Discord role IDs allowed to manage via dashboard)
  dashboard_admin_role_ids bigint[] not null default '{}'::bigint[],

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Member records (one row per guild member seen by the bot).
create table if not exists public.members (
  guild_id bigint not null references public.guilds(id) on delete cascade,
  user_id bigint not null,
  member_number bigint,
  username text,
  display_name text,
  avatar_url text,
  account_created_at timestamptz,
  joined_at timestamptz,
  left_at timestamptz,
  is_bot boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (guild_id, user_id)
);

-- Moderation warnings.
create table if not exists public.warnings (
  id bigserial primary key,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  user_id bigint not null,
  moderator_id bigint,
  reason text not null,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

-- Moderation action history.
create table if not exists public.moderation_logs (
  id bigserial primary key,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  action text not null,
  target_id bigint,
  moderator_id bigint,
  reason text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Active/historical temporary voice channels.
create table if not exists public.temp_voice_channels (
  channel_id bigint primary key,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  owner_id bigint not null,
  channel_name text,
  user_limit integer not null default 0 check (user_limit >= 0),
  is_locked boolean not null default false,
  created_at timestamptz not null default now(),
  deleted_at timestamptz
);

-- Reaction role mappings.
create table if not exists public.reaction_roles (
  id bigserial primary key,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  message_id bigint not null,
  channel_id bigint not null,
  emoji text not null,
  role_id bigint not null,
  created_at timestamptz not null default now(),
  unique (message_id, emoji)
);

-- Scheduled/automated actions.
create table if not exists public.automations (
  id bigserial primary key,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  type text not null,
  name text not null,
  channel_id bigint,
  cron text,
  payload jsonb not null default '{}'::jsonb,
  enabled boolean not null default true,
  last_run_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Polls created by the bot.
create table if not exists public.polls (
  id bigserial primary key,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  channel_id bigint not null,
  message_id bigint,
  question text not null,
  options jsonb not null default '[]'::jsonb,
  ends_at timestamptz,
  created_by bigint,
  closed boolean not null default false,
  created_at timestamptz not null default now()
);

-- General activity/event log (for dashboard and audit trail).
create table if not exists public.activity_logs (
  id bigserial primary key,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  event_type text not null,
  actor_id bigint,
  target_id bigint,
  channel_id bigint,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Periodic server statistics snapshots.
create table if not exists public.server_stats (
  id bigserial primary key,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  recorded_at timestamptz not null default now(),
  member_count integer,
  human_count integer,
  bot_count integer,
  online_count integer,
  channel_count integer,
  role_count integer,
  boost_count integer
);

-- Dashboard administrators (Supabase auth user <-> Discord guild access).
create table if not exists public.dashboard_admins (
  user_id uuid not null references auth.users(id) on delete cascade,
  discord_id bigint not null,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  role text not null default 'admin',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, guild_id),
  unique (discord_id, guild_id)
);

-- -----------------------------------------------------------------------------
-- Indexes
-- -----------------------------------------------------------------------------

-- Log/history tables: newest-first queries per guild.
create index if not exists idx_warnings_guild_created_at on public.warnings (guild_id, created_at desc);
create index if not exists idx_moderation_logs_guild_created_at on public.moderation_logs (guild_id, created_at desc);
create index if not exists idx_activity_logs_guild_created_at on public.activity_logs (guild_id, created_at desc);
create index if not exists idx_server_stats_guild_recorded_at on public.server_stats (guild_id, recorded_at desc);
create index if not exists idx_polls_guild_created_at on public.polls (guild_id, created_at desc);

-- Member lookups and numbering.
create index if not exists idx_members_guild_member_number on public.members (guild_id, member_number);
create index if not exists idx_members_guild_joined_at on public.members (guild_id, joined_at desc);

-- Moderation/warnings lookups.
create index if not exists idx_warnings_guild_user_active on public.warnings (guild_id, user_id, active);
create index if not exists idx_moderation_logs_guild_target on public.moderation_logs (guild_id, target_id, created_at desc);

-- Feature tables.
create index if not exists idx_temp_voice_guild_active on public.temp_voice_channels (guild_id) where deleted_at is null;
create index if not exists idx_temp_voice_owner on public.temp_voice_channels (guild_id, owner_id) where deleted_at is null;
create index if not exists idx_reaction_roles_guild_message on public.reaction_roles (guild_id, message_id);
create index if not exists idx_automations_guild_enabled on public.automations (guild_id, enabled);
create index if not exists idx_automations_guild_type on public.automations (guild_id, type);

-- Dashboard/admin lookups.
create index if not exists idx_dashboard_admins_guild on public.dashboard_admins (guild_id);
create index if not exists idx_dashboard_admins_discord on public.dashboard_admins (discord_id);

-- -----------------------------------------------------------------------------
-- Triggers
-- -----------------------------------------------------------------------------

drop trigger if exists trg_guilds_set_updated_at on public.guilds;
create trigger trg_guilds_set_updated_at
before update on public.guilds
for each row execute function public.set_updated_at();

drop trigger if exists trg_guild_settings_set_updated_at on public.guild_settings;
create trigger trg_guild_settings_set_updated_at
before update on public.guild_settings
for each row execute function public.set_updated_at();

drop trigger if exists trg_members_set_updated_at on public.members;
create trigger trg_members_set_updated_at
before update on public.members
for each row execute function public.set_updated_at();

drop trigger if exists trg_automations_set_updated_at on public.automations;
create trigger trg_automations_set_updated_at
before update on public.automations
for each row execute function public.set_updated_at();

drop trigger if exists trg_dashboard_admins_set_updated_at on public.dashboard_admins;
create trigger trg_dashboard_admins_set_updated_at
before update on public.dashboard_admins
for each row execute function public.set_updated_at();

-- -----------------------------------------------------------------------------
-- RPC / helper functions that depend on tables
-- -----------------------------------------------------------------------------

-- Race-free per-guild member numbering.
create or replace function public.next_member_number(p_guild_id bigint)
returns bigint
language plpgsql
security definer
set search_path = public
as $$
declare
  next_num bigint;
begin
  insert into public.guilds (id)
  values (p_guild_id)
  on conflict (id) do nothing;

  update public.guilds
  set member_counter = member_counter + 1,
      updated_at = now()
  where id = p_guild_id
  returning member_counter into next_num;

  return next_num;
end;
$$;

comment on function public.next_member_number(bigint)
  is 'Atomically increments and returns the guild member counter. Used by the bot for automatic member numbering.';

-- Dashboard admin check used by RLS policies.
create or replace function public.is_dashboard_admin(p_guild_id bigint)
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (
    select 1
    from public.dashboard_admins da
    where da.user_id = auth.uid()
      and da.guild_id = p_guild_id
  );
$$;

comment on function public.is_dashboard_admin(bigint)
  is 'Returns true if the current authenticated user is a dashboard admin for the given guild.';

commit;
