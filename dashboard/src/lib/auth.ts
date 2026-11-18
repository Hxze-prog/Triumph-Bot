import type { User } from "@supabase/supabase-js";

import {
  type MembershipVerification,
  verifyDiscordMembership,
} from "@/lib/discord";
import { discordGuildId } from "@/lib/env";
import { createClient as createServerClient, isConfigured } from "@/lib/supabase/server";

export type DashboardUser = {
  name: string;
  avatarUrl: string | null;
  discordId: string | null;
  role: string;
};

export type DashboardGuild = {
  id: string;
  name: string;
};

export type DashboardAccess =
  | { status: "unauthenticated" }
  | { status: "forbidden"; reason: string; user: DashboardUser | null }
  | {
      status: "ok";
      user: DashboardUser;
      guild: DashboardGuild;
      verification: MembershipVerification;
    };

type AdminRow = {
  guild_id: string;
  discord_id: string;
  role: string;
};

function displayName(user: User): string {
  const metadata = user.user_metadata ?? {};
  return (
    (metadata.full_name as string | undefined) ??
    (metadata.name as string | undefined) ??
    (metadata.user_name as string | undefined) ??
    (metadata.preferred_username as string | undefined) ??
    user.email ??
    "Discord user"
  );
}

function discordIdOf(user: User): string | null {
  const metadata = user.user_metadata ?? {};
  const fromMetadata =
    (metadata.provider_id as string | undefined) ??
    (metadata.discord_id as string | undefined);
  if (fromMetadata) {
    return String(fromMetadata);
  }
  const identity = user.identities?.find((item) => item.provider === "discord");
  return identity ? String(identity.id) : null;
}

function baseUser(user: User, role = "admin"): DashboardUser {
  return {
    name: displayName(user),
    avatarUrl: (user.user_metadata?.avatar_url as string | undefined) ?? null,
    discordId: discordIdOf(user),
    role,
  };
}

/**
 * Resolve the signed-in user's dashboard access.
 *
 * Authorization order:
 * 1. Supabase session exists.
 * 2. A dashboard_admins row belongs to auth.uid().
 * 3. Provider identity matches the stored Discord id.
 * 4. Optional live Discord check for guild membership and admin role.
 */
export async function requireDashboardAccess(): Promise<DashboardAccess> {
  if (!isConfigured()) {
    return {
      status: "forbidden",
      reason:
        "Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY.",
      user: null,
    };
  }

  let supabase;
  try {
    supabase = await createServerClient();
  } catch (error) {
    return {
      status: "forbidden",
      reason:
        error instanceof Error
          ? error.message
          : "Supabase client could not be created.",
      user: null,
    };
  }

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) {
    return { status: "unauthenticated" };
  }

  const discordId = discordIdOf(user);
  const basic = baseUser(user);

  const { data: adminRows, error: adminError } = await supabase
    .from("dashboard_admins")
    .select("guild_id::text, discord_id::text, role")
    .eq("user_id", user.id);

  if (adminError) {
    return {
      status: "forbidden",
      reason:
        "Could not read dashboard access records. Confirm the database migrations and RLS policies are applied.",
      user: basic,
    };
  }

  const admins = (adminRows ?? []) as unknown as AdminRow[];
  if (admins.length === 0) {
    return {
      status: "forbidden",
      reason:
        "This Discord account is not registered as a dashboard administrator for any server.",
      user: basic,
    };
  }

  const preferredGuild = discordGuildId;
  const admin =
    (preferredGuild
      ? admins.find((row) => String(row.guild_id) === preferredGuild)
      : undefined) ?? admins[0];

  const userWithRole = baseUser(user, admin.role || "admin");

  if (discordId && String(admin.discord_id) !== String(discordId)) {
    return {
      status: "forbidden",
      reason:
        "Your Discord identity does not match the registered dashboard administrator record. Sign in with the correct Discord account.",
      user: userWithRole,
    };
  }

  const guildId = String(admin.guild_id);

  const [{ data: guildRow }, { data: memberRow }, { data: settingsRow }] =
    await Promise.all([
      supabase.from("guilds").select("name").eq("id", guildId).maybeSingle(),
      supabase
        .from("members")
        .select("left_at")
        .eq("guild_id", guildId)
        .eq("user_id", String(admin.discord_id))
        .maybeSingle(),
      supabase
        .from("guild_settings")
        .select("dashboard_admin_role_ids")
        .eq("guild_id", guildId)
        .maybeSingle(),
    ]);

  if (memberRow?.left_at) {
    return {
      status: "forbidden",
      reason:
        "Your member record shows you have left the server. Rejoin the Discord server before using the dashboard.",
      user: userWithRole,
    };
  }

  const adminRoleIds =
    (settingsRow?.dashboard_admin_role_ids as Array<string | number> | null) ?? [];

  const verification = await verifyDiscordMembership(
    guildId,
    String(admin.discord_id),
    adminRoleIds,
  );

  if (verification.state === "not_member") {
    return {
      status: "forbidden",
      reason: verification.detail,
      user: userWithRole,
    };
  }
  if (verification.state === "missing_role") {
    return {
      status: "forbidden",
      reason: verification.detail,
      user: userWithRole,
    };
  }

  return {
    status: "ok",
    user: userWithRole,
    guild: {
      id: guildId,
      name: (guildRow?.name as string | undefined) ?? "Discord server",
    },
    verification,
  };
}
