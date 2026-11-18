import { createClient } from "@/lib/supabase/server";

export type GuildSettings = {
  prefix: string;
  welcome_enabled: boolean;
  welcome_channel_id: string | null;
  welcome_message: string | null;
  welcome_embed_enabled: boolean;
  welcome_banner_enabled: boolean;
  welcome_banner_template: string | null;
  welcome_dm_enabled: boolean;
  welcome_dm_message: string | null;
  goodbye_enabled: boolean;
  goodbye_channel_id: string | null;
  goodbye_message: string | null;
  auto_role_ids: Array<string | number>;
  dashboard_admin_role_ids: Array<string | number>;
  temp_voice_category_id: string | null;
  temp_voice_trigger_channel_id: string | null;
  temp_voice_default_limit: number;
  temp_voice_name_template: string;
  automod_anti_spam_enabled: boolean;
  automod_anti_link_enabled: boolean;
  automod_anti_invite_enabled: boolean;
  automod_spam_threshold: number;
  automod_spam_interval_seconds: number;
  automod_timeout_seconds: number;
  log_join_leave_channel_id: string | null;
  log_message_delete_channel_id: string | null;
  log_message_edit_channel_id: string | null;
  log_role_change_channel_id: string | null;
  log_nickname_change_channel_id: string | null;
  log_voice_channel_id: string | null;
  log_moderation_channel_id: string | null;
  log_channel_events_channel_id: string | null;
};

export type ActivityRow = {
  id: number;
  event_type: string;
  actor_id: string | null;
  target_id: string | null;
  channel_id: string | null;
  created_at: string;
  payload: Record<string, unknown> | null;
};

export type WarningRow = {
  id: number;
  user_id: string;
  moderator_id: string | null;
  reason: string;
  active: boolean;
  created_at: string;
};

export type AutomationRow = {
  id: number;
  type: string;
  name: string;
  channel_id: string | null;
  cron: string | null;
  enabled: boolean;
  last_run_at: string | null;
  created_at: string;
};

export type ReactionRoleRow = {
  id: number;
  message_id: string;
  channel_id: string;
  emoji: string;
  role_id: string;
  created_at: string;
};

export type TempVoiceRow = {
  channel_id: string;
  owner_id: string;
  channel_name: string | null;
  user_limit: number;
  is_locked: boolean;
  created_at: string;
};

export type StatsRow = {
  id: number;
  recorded_at: string;
  member_count: number | null;
  human_count: number | null;
  bot_count: number | null;
  online_count: number | null;
  channel_count: number | null;
  role_count: number | null;
  boost_count: number | null;
};

export type Overview = {
  counts: {
    members: number;
    activeWarnings: number;
    tempVoice: number;
    automations: number;
    reactionRoles: number;
    activityEvents: number;
  };
  latestStats: StatsRow | null;
  recentActivity: ActivityRow[];
};

const activitySelect =
  "id, event_type, actor_id::text, target_id::text, channel_id::text, created_at, payload";

export async function getOverview(guildId: string): Promise<Overview> {
  const supabase = await createClient();

  const [
    members,
    warnings,
    tempVoice,
    automations,
    reactionRoles,
    activity,
    stats,
    recent,
  ] = await Promise.all([
    supabase
      .from("members")
      .select("*", { count: "exact", head: true })
      .eq("guild_id", guildId)
      .is("left_at", null),
    supabase
      .from("warnings")
      .select("*", { count: "exact", head: true })
      .eq("guild_id", guildId)
      .eq("active", true),
    supabase
      .from("temp_voice_channels")
      .select("*", { count: "exact", head: true })
      .eq("guild_id", guildId)
      .is("deleted_at", null),
    supabase
      .from("automations")
      .select("*", { count: "exact", head: true })
      .eq("guild_id", guildId),
    supabase
      .from("reaction_roles")
      .select("*", { count: "exact", head: true })
      .eq("guild_id", guildId),
    supabase
      .from("activity_logs")
      .select("*", { count: "exact", head: true })
      .eq("guild_id", guildId),
    supabase
      .from("server_stats")
      .select(
        "id, recorded_at, member_count, human_count, bot_count, online_count, channel_count, role_count, boost_count",
      )
      .eq("guild_id", guildId)
      .order("recorded_at", { ascending: false })
      .limit(1)
      .maybeSingle(),
    supabase
      .from("activity_logs")
      .select(activitySelect)
      .eq("guild_id", guildId)
      .order("created_at", { ascending: false })
      .limit(6),
  ]);

  return {
    counts: {
      members: members.count ?? 0,
      activeWarnings: warnings.count ?? 0,
      tempVoice: tempVoice.count ?? 0,
      automations: automations.count ?? 0,
      reactionRoles: reactionRoles.count ?? 0,
      activityEvents: activity.count ?? 0,
    },
    latestStats: (stats.data as StatsRow | null) ?? null,
    recentActivity: (recent.data ?? []) as unknown as ActivityRow[],
  };
}

export async function getSettings(guildId: string): Promise<GuildSettings | null> {
  const supabase = await createClient();

  const { data } = await supabase
    .from("guild_settings")
    .select(
      [
        "prefix",
        "welcome_enabled",
        "welcome_channel_id::text",
        "welcome_message",
        "welcome_embed_enabled",
        "welcome_banner_enabled",
        "welcome_banner_template",
        "welcome_dm_enabled",
        "welcome_dm_message",
        "goodbye_enabled",
        "goodbye_channel_id::text",
        "goodbye_message",
        "auto_role_ids",
        "dashboard_admin_role_ids",
        "temp_voice_category_id::text",
        "temp_voice_trigger_channel_id::text",
        "temp_voice_default_limit",
        "temp_voice_name_template",
        "automod_anti_spam_enabled",
        "automod_anti_link_enabled",
        "automod_anti_invite_enabled",
        "automod_spam_threshold",
        "automod_spam_interval_seconds",
        "automod_timeout_seconds",
        "log_join_leave_channel_id::text",
        "log_message_delete_channel_id::text",
        "log_message_edit_channel_id::text",
        "log_role_change_channel_id::text",
        "log_nickname_change_channel_id::text",
        "log_voice_channel_id::text",
        "log_moderation_channel_id::text",
        "log_channel_events_channel_id::text",
      ].join(", "),
    )
    .eq("guild_id", guildId)
    .maybeSingle();

  return (data as GuildSettings | null) ?? null;
}

export async function getActivity(
  guildId: string,
  limit = 50,
): Promise<ActivityRow[]> {
  const supabase = await createClient();

  const { data } = await supabase
    .from("activity_logs")
    .select(activitySelect)
    .eq("guild_id", guildId)
    .order("created_at", { ascending: false })
    .limit(limit);

  return (data ?? []) as unknown as ActivityRow[];
}

export async function getWarnings(guildId: string): Promise<WarningRow[]> {
  const supabase = await createClient();

  const { data } = await supabase
    .from("warnings")
    .select("id, user_id::text, moderator_id::text, reason, active, created_at")
    .eq("guild_id", guildId)
    .eq("active", true)
    .order("created_at", { ascending: false })
    .limit(100);

  return (data ?? []) as unknown as WarningRow[];
}

export async function getAutomations(guildId: string): Promise<AutomationRow[]> {
  const supabase = await createClient();

  const { data } = await supabase
    .from("automations")
    .select(
      "id, type, name, channel_id::text, cron, enabled, last_run_at, created_at",
    )
    .eq("guild_id", guildId)
    .order("created_at", { ascending: false });

  return (data ?? []) as unknown as AutomationRow[];
}

export async function getReactionRoles(
  guildId: string,
): Promise<ReactionRoleRow[]> {
  const supabase = await createClient();

  const { data } = await supabase
    .from("reaction_roles")
    .select(
      "id, message_id::text, channel_id::text, emoji, role_id::text, created_at",
    )
    .eq("guild_id", guildId)
    .order("created_at", { ascending: false });

  return (data ?? []) as unknown as ReactionRoleRow[];
}

export async function getTempVoice(
  guildId: string,
): Promise<TempVoiceRow[]> {
  const supabase = await createClient();

  const { data } = await supabase
    .from("temp_voice_channels")
    .select(
      "channel_id::text, owner_id::text, channel_name, user_limit, is_locked, created_at",
    )
    .eq("guild_id", guildId)
    .is("deleted_at", null)
    .order("created_at", { ascending: false });

  return (data ?? []) as unknown as TempVoiceRow[];
}

export async function getStatsHistory(
  guildId: string,
  limit = 24,
): Promise<StatsRow[]> {
  const supabase = await createClient();

  const { data } = await supabase
    .from("server_stats")
    .select(
      "id, recorded_at, member_count, human_count, bot_count, online_count, channel_count, role_count, boost_count",
    )
    .eq("guild_id", guildId)
    .order("recorded_at", { ascending: false })
    .limit(limit);

  return (data ?? []) as unknown as StatsRow[];
}
