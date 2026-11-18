"use server";

import { revalidatePath } from "next/cache";

import { requireDashboardAccess } from "@/lib/auth";
import type { ActionState } from "@/lib/settings";
import { logEventFields } from "@/lib/settings";
import { createClient } from "@/lib/supabase/server";

const MAX_MESSAGE_LENGTH = 2000;
const MAX_TIMEOUT_SECONDS = 28 * 24 * 60 * 60;
const SNOWFLAKE = /^\d{15,20}$/;

function readText(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === "string" ? value.trim() : "";
}

function isChecked(formData: FormData, key: string): boolean {
  const value = formData.get(key);
  return value === "on" || value === "true";
}

function optionalSnowflake(
  formData: FormData,
  key: string,
  label: string,
  errors: string[],
): string | null {
  const value = readText(formData, key);
  if (!value) {
    return null;
  }
  if (!SNOWFLAKE.test(value)) {
    errors.push(`${label} must be a Discord ID (digits only).`);
    return null;
  }
  return value;
}

function optionalText(
  formData: FormData,
  key: string,
  label: string,
  maxLength: number,
  errors: string[],
): string | null {
  const value = readText(formData, key);
  if (value.length > maxLength) {
    errors.push(`${label} must be ${maxLength} characters or fewer.`);
    return null;
  }
  return value || null;
}

function integerValue(
  formData: FormData,
  key: string,
  label: string,
  min: number,
  max: number,
  errors: string[],
): number {
  const raw = readText(formData, key);
  const value = Number(raw);
  if (!raw || !Number.isInteger(value) || value < min || value > max) {
    errors.push(`${label} must be a whole number between ${min} and ${max}.`);
    return min;
  }
  return value;
}

async function persist(
  guildId: string,
  values: Record<string, unknown>,
): Promise<string | null> {
  const supabase = await createClient();
  const { data, error } = await supabase
    .from("guild_settings")
    .upsert({ guild_id: guildId, ...values }, { onConflict: "guild_id" })
    .select("guild_id");

  if (error) {
    return `Could not save settings: ${error.message}`;
  }
  if (!data || data.length === 0) {
    return "Could not save settings. Confirm the database migrations and RLS policies are applied.";
  }
  return null;
}

function refreshSettings(path: string) {
  revalidatePath("/dashboard", "layout");
  revalidatePath(path);
}

async function accessOrError(): Promise<
  { ok: true; guildId: string } | { ok: false; state: ActionState }
> {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    return {
      ok: false,
      state: {
        status: "error",
        message:
          "Your session is not authorized for this server. Sign in again and retry.",
      },
    };
  }
  return { ok: true, guildId: access.guild.id };
}

export async function saveWelcomeSettings(
  _state: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const access = await accessOrError();
  if (!access.ok) {
    return access.state;
  }

  const errors: string[] = [];
  const welcomeEnabled = isChecked(formData, "welcome_enabled");
  const welcomeChannel = optionalSnowflake(
    formData,
    "welcome_channel_id",
    "Welcome channel",
    errors,
  );
  const goodbyeEnabled = isChecked(formData, "goodbye_enabled");
  const goodbyeChannel = optionalSnowflake(
    formData,
    "goodbye_channel_id",
    "Goodbye channel",
    errors,
  );

  if (welcomeEnabled && !welcomeChannel) {
    errors.push("Choose a welcome channel before enabling welcomes.");
  }
  if (goodbyeEnabled && !goodbyeChannel) {
    errors.push("Choose a goodbye channel before enabling goodbyes.");
  }

  const values = {
    welcome_enabled: welcomeEnabled,
    welcome_channel_id: welcomeChannel,
    welcome_message: optionalText(
      formData,
      "welcome_message",
      "Welcome message",
      MAX_MESSAGE_LENGTH,
      errors,
    ),
    welcome_embed_enabled: isChecked(formData, "welcome_embed_enabled"),
    welcome_banner_enabled: isChecked(formData, "welcome_banner_enabled"),
    welcome_banner_template: optionalText(
      formData,
      "welcome_banner_template",
      "Banner template",
      MAX_MESSAGE_LENGTH,
      errors,
    ),
    welcome_dm_enabled: isChecked(formData, "welcome_dm_enabled"),
    welcome_dm_message: optionalText(
      formData,
      "welcome_dm_message",
      "Welcome direct message",
      MAX_MESSAGE_LENGTH,
      errors,
    ),
    goodbye_enabled: goodbyeEnabled,
    goodbye_channel_id: goodbyeChannel,
    goodbye_message: optionalText(
      formData,
      "goodbye_message",
      "Goodbye message",
      MAX_MESSAGE_LENGTH,
      errors,
    ),
  };

  if (errors.length > 0) {
    return { status: "error", message: errors.join(" ") };
  }

  const error = await persist(access.guildId, values);
  if (error) {
    return { status: "error", message: error };
  }

  refreshSettings("/dashboard/settings/welcome");
  return {
    status: "success",
    message:
      "Welcome and goodbye settings saved. The bot applies them within 30 seconds.",
  };
}

export async function saveAutomodSettings(
  _state: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const access = await accessOrError();
  if (!access.ok) {
    return access.state;
  }

  const errors: string[] = [];
  const values = {
    automod_anti_spam_enabled: isChecked(formData, "automod_anti_spam_enabled"),
    automod_anti_link_enabled: isChecked(formData, "automod_anti_link_enabled"),
    automod_anti_invite_enabled: isChecked(
      formData,
      "automod_anti_invite_enabled",
    ),
    automod_spam_threshold: integerValue(
      formData,
      "automod_spam_threshold",
      "Spam threshold",
      1,
      50,
      errors,
    ),
    automod_spam_interval_seconds: integerValue(
      formData,
      "automod_spam_interval_seconds",
      "Spam interval",
      1,
      3600,
      errors,
    ),
    automod_timeout_seconds: integerValue(
      formData,
      "automod_timeout_seconds",
      "Spam timeout",
      0,
      MAX_TIMEOUT_SECONDS,
      errors,
    ),
  };

  if (errors.length > 0) {
    return { status: "error", message: errors.join(" ") };
  }

  const error = await persist(access.guildId, values);
  if (error) {
    return { status: "error", message: error };
  }

  refreshSettings("/dashboard/settings/moderation");
  return {
    status: "success",
    message:
      "Automoderation settings saved. The bot applies them within 30 seconds.",
  };
}

export async function saveLoggingSettings(
  _state: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const access = await accessOrError();
  if (!access.ok) {
    return access.state;
  }

  const errors: string[] = [];
  const values: Record<string, unknown> = {};
  for (const field of logEventFields) {
    values[field.key] = optionalSnowflake(
      formData,
      field.key,
      `${field.label} channel`,
      errors,
    );
  }

  if (errors.length > 0) {
    return { status: "error", message: errors.join(" ") };
  }

  const error = await persist(access.guildId, values);
  if (error) {
    return { status: "error", message: error };
  }

  refreshSettings("/dashboard/settings/logging");
  return {
    status: "success",
    message:
      "Logging channels saved. New events are delivered within 30 seconds.",
  };
}

export async function saveTempVoiceSettings(
  _state: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const access = await accessOrError();
  if (!access.ok) {
    return access.state;
  }

  const errors: string[] = [];
  const template = readText(formData, "temp_voice_name_template");
  if (!template || template.length > 100) {
    errors.push(
      "Name template must be between 1 and 100 characters. Use {user} or {display_name}.",
    );
  }

  const values = {
    temp_voice_trigger_channel_id: optionalSnowflake(
      formData,
      "temp_voice_trigger_channel_id",
      "Trigger channel",
      errors,
    ),
    temp_voice_category_id: optionalSnowflake(
      formData,
      "temp_voice_category_id",
      "Category",
      errors,
    ),
    temp_voice_default_limit: integerValue(
      formData,
      "temp_voice_default_limit",
      "Default limit",
      0,
      99,
      errors,
    ),
    temp_voice_name_template: template,
  };

  if (errors.length > 0) {
    return { status: "error", message: errors.join(" ") };
  }

  const error = await persist(access.guildId, values);
  if (error) {
    return { status: "error", message: error };
  }

  refreshSettings("/dashboard/settings/temp-voice");
  return {
    status: "success",
    message:
      "Temporary voice settings saved. The bot applies them within 30 seconds.",
  };
}
