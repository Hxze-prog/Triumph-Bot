import { discordBotToken } from "@/lib/env";

export type MembershipVerification = {
  state: "verified" | "unavailable" | "not_member" | "missing_role";
  detail: string;
};

const DISCORD_API = "https://discord.com/api/v10";

type GuildMember = {
  roles?: string[];
  nick?: string | null;
  user?: { username?: string };
};

export async function verifyDiscordMembership(
  guildId: string,
  discordId: string,
  adminRoleIds: Array<string | number> = [],
): Promise<MembershipVerification> {
  const token = discordBotToken;
  if (!token) {
    return {
      state: "unavailable",
      detail:
        "Server-side Discord verification is off (DISCORD_BOT_TOKEN not set). Access relies on dashboard_admins.",
    };
  }

  try {
    const response = await fetch(
      `${DISCORD_API}/guilds/${guildId}/members/${discordId}`,
      {
        headers: { Authorization: `Bot ${token}` },
        cache: "no-store",
      },
    );

    if (response.status === 404) {
      return {
        state: "not_member",
        detail: "You are not a member of the configured Discord server.",
      };
    }
    if (response.status === 401 || response.status === 403) {
      return {
        state: "unavailable",
        detail:
          "The bot token cannot read this guild. Check DISCORD_BOT_TOKEN and bot access.",
      };
    }
    if (!response.ok) {
      return {
        state: "unavailable",
        detail: `Discord API returned ${response.status}.`,
      };
    }

    const member = (await response.json()) as GuildMember;
    const memberRoles = new Set((member.roles ?? []).map(String));

    if (adminRoleIds.length > 0) {
      const allowed = adminRoleIds.some((roleId) => memberRoles.has(String(roleId)));
      if (!allowed) {
        return {
          state: "missing_role",
          detail:
            "Your Discord account does not have a role authorized for dashboard access.",
        };
      }
      return {
        state: "verified",
        detail: "Discord membership and admin role verified.",
      };
    }

    return {
      state: "verified",
      detail: "Discord membership verified.",
    };
  } catch {
    return {
      state: "unavailable",
      detail: "Discord API was unreachable; access relies on dashboard_admins.",
    };
  }
}

export type DiscordChannelOption = {
  id: string;
  name: string;
  position: number;
};

export type DiscordRoleOption = {
  id: string;
  name: string;
  position: number;
};

export type GuildDirectory = {
  available: boolean;
  reason: string | null;
  categories: DiscordChannelOption[];
  textChannels: DiscordChannelOption[];
  voiceChannels: DiscordChannelOption[];
  roles: DiscordRoleOption[];
};

type RawChannel = {
  id: string;
  name?: string;
  type?: number;
  position?: number;
};

type RawRole = {
  id: string;
  name?: string;
  position?: number;
};

const TEXT_CHANNEL_TYPES = new Set([0, 5]);
const VOICE_CHANNEL_TYPES = new Set([2, 13]);

function emptyDirectory(reason: string | null): GuildDirectory {
  return {
    available: false,
    reason,
    categories: [],
    textChannels: [],
    voiceChannels: [],
    roles: [],
  };
}

/**
 * Load channel and role options for dashboard forms using the bot token.
 * Falls back to manual ID entry when the token or API is unavailable.
 */
export async function fetchGuildDirectory(
  guildId: string,
): Promise<GuildDirectory> {
  const token = discordBotToken;
  if (!token) {
    return emptyDirectory(
      "DISCORD_BOT_TOKEN is not set, so channels and roles cannot be listed. Enter IDs manually.",
    );
  }
  if (!guildId) {
    return emptyDirectory("No guild is configured for this dashboard.");
  }

  try {
    const headers = { Authorization: `Bot ${token}` };
    const [channelsResponse, rolesResponse] = await Promise.all([
      fetch(`${DISCORD_API}/guilds/${guildId}/channels`, {
        headers,
        next: { revalidate: 60 },
      }),
      fetch(`${DISCORD_API}/guilds/${guildId}/roles`, {
        headers,
        next: { revalidate: 60 },
      }),
    ]);

    if (!channelsResponse.ok || !rolesResponse.ok) {
      return emptyDirectory(
        `Discord API returned ${channelsResponse.status}/${rolesResponse.status}. Check the bot token and guild access.`,
      );
    }

    const rawChannels = (await channelsResponse.json()) as RawChannel[];
    const rawRoles = (await rolesResponse.json()) as RawRole[];

    const channels = rawChannels
      .map((channel) => ({
        id: String(channel.id),
        name: channel.name ?? String(channel.id),
        type: channel.type ?? 0,
        position: channel.position ?? 0,
      }))
      .sort((a, b) => a.position - b.position);

    const roles = rawRoles
      .filter((role) => String(role.id) !== guildId)
      .map((role) => ({
        id: String(role.id),
        name: role.name ?? String(role.id),
        position: role.position ?? 0,
      }))
      .sort((a, b) => b.position - a.position);

    return {
      available: true,
      reason: null,
      categories: channels
        .filter((channel) => channel.type === 4)
        .map(({ id, name, position }) => ({ id, name, position })),
      textChannels: channels
        .filter((channel) => TEXT_CHANNEL_TYPES.has(channel.type))
        .map(({ id, name, position }) => ({ id, name, position })),
      voiceChannels: channels
        .filter((channel) => VOICE_CHANNEL_TYPES.has(channel.type))
        .map(({ id, name, position }) => ({ id, name, position })),
      roles,
    };
  } catch {
    return emptyDirectory(
      "Discord API was unreachable while loading channels and roles. Enter IDs manually.",
    );
  }
}
