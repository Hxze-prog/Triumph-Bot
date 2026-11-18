import type { GuildSettings } from "@/lib/queries";

export type ActionState = {
  status: "idle" | "success" | "error";
  message: string;
};

export const idleActionState: ActionState = { status: "idle", message: "" };

export const defaultGuildSettings: GuildSettings = {
  prefix: "!",
  welcome_enabled: false,
  welcome_channel_id: null,
  welcome_message: null,
  welcome_embed_enabled: true,
  welcome_banner_enabled: true,
  welcome_banner_template: null,
  welcome_dm_enabled: false,
  welcome_dm_message: null,
  goodbye_enabled: false,
  goodbye_channel_id: null,
  goodbye_message: null,
  auto_role_ids: [],
  dashboard_admin_role_ids: [],
  temp_voice_category_id: null,
  temp_voice_trigger_channel_id: null,
  temp_voice_default_limit: 0,
  temp_voice_name_template: "{user}'s Channel",
  automod_anti_spam_enabled: false,
  automod_anti_link_enabled: false,
  automod_anti_invite_enabled: false,
  automod_spam_threshold: 5,
  automod_spam_interval_seconds: 5,
  automod_timeout_seconds: 60,
  log_join_leave_channel_id: null,
  log_message_delete_channel_id: null,
  log_message_edit_channel_id: null,
  log_role_change_channel_id: null,
  log_nickname_change_channel_id: null,
  log_voice_channel_id: null,
  log_moderation_channel_id: null,
  log_channel_events_channel_id: null,
};

export const logEventFields = [
  {
    key: "log_join_leave_channel_id",
    event: "join_leave",
    label: "Join / Leave",
    description: "Member joins and departures",
  },
  {
    key: "log_message_delete_channel_id",
    event: "message_delete",
    label: "Message Delete",
    description: "Deleted and bulk-deleted messages",
  },
  {
    key: "log_message_edit_channel_id",
    event: "message_edit",
    label: "Message Edit",
    description: "Edited messages with before and after",
  },
  {
    key: "log_role_change_channel_id",
    event: "role_change",
    label: "Role Change",
    description: "Roles added or removed",
  },
  {
    key: "log_nickname_change_channel_id",
    event: "nickname_change",
    label: "Nickname Change",
    description: "Display name updates",
  },
  {
    key: "log_voice_channel_id",
    event: "voice",
    label: "Voice Activity",
    description: "Voice joins, leaves, and moves",
  },
  {
    key: "log_moderation_channel_id",
    event: "moderation",
    label: "Moderation",
    description: "Moderation actions and reasons",
  },
  {
    key: "log_channel_events_channel_id",
    event: "channel_events",
    label: "Channel Events",
    description: "Channel creation and deletion",
  },
] as const satisfies ReadonlyArray<{
  key: keyof GuildSettings;
  event: string;
  label: string;
  description: string;
}>;
