import Link from "next/link";
import { redirect } from "next/navigation";

import { Badge } from "@/components/badge";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import {
  IconArrow,
  IconClock,
  IconHash,
  IconMic,
  IconShield,
  IconWelcome,
} from "@/components/icons";
import { requireDashboardAccess } from "@/lib/auth";
import { getSettings } from "@/lib/queries";

const logColumns = [
  "log_join_leave_channel_id",
  "log_message_delete_channel_id",
  "log_message_edit_channel_id",
  "log_role_change_channel_id",
  "log_nickname_change_channel_id",
  "log_voice_channel_id",
  "log_moderation_channel_id",
  "log_channel_events_channel_id",
] as const;

export default async function SettingsOverviewPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const settings = await getSettings(access.guild.id);
  const logConfigured = settings
    ? logColumns.filter((column) => Boolean(settings[column])).length
    : 0;

  const cards = [
    {
      href: "/dashboard/settings/welcome",
      icon: IconWelcome,
      title: "Welcome & goodbye",
      description: "Greeting channels, messages, banners, direct messages.",
      status: (
        <Badge tone={settings?.welcome_enabled ? "success" : "muted"}>
          Welcome {settings?.welcome_enabled ? "on" : "off"}
        </Badge>
      ),
    },
    {
      href: "/dashboard/settings/moderation",
      icon: IconShield,
      title: "Moderation & automod",
      description: "Timeouts, warning defaults, and automoderation rules.",
      status: (
        <Badge
          tone={
            settings?.automod_anti_spam_enabled ||
            settings?.automod_anti_link_enabled ||
            settings?.automod_anti_invite_enabled
              ? "success"
              : "muted"
          }
        >
          AutoMod{" "}
          {settings?.automod_anti_spam_enabled ||
          settings?.automod_anti_link_enabled ||
          settings?.automod_anti_invite_enabled
            ? "on"
            : "off"}
        </Badge>
      ),
    },
    {
      href: "/dashboard/settings/logging",
      icon: IconHash,
      title: "Logging",
      description: "Per-event destinations for the activity trail.",
      status: (
        <Badge tone={logConfigured > 0 ? "success" : "muted"}>
          {logConfigured}/8 channels
        </Badge>
      ),
    },
    {
      href: "/dashboard/settings/temp-voice",
      icon: IconMic,
      title: "Temporary voice",
      description: "Trigger room, category, name template, and default limit.",
      status: (
        <Badge
          tone={settings?.temp_voice_trigger_channel_id ? "success" : "muted"}
        >
          {settings?.temp_voice_trigger_channel_id ? "Configured" : "Not set"}
        </Badge>
      ),
    },
    {
      href: "/dashboard/management/automations",
      icon: IconClock,
      title: "Automations",
      description: "Schedules, hooks, and keyword responders.",
      status: <Badge tone="royal">Manage</Badge>,
    },
  ];

  return (
    <>
      <PageHeader
        eyebrow="Settings"
        title="Server configuration"
        description="Edit the configuration the bot uses. Values are saved to Supabase and picked up by the bot's 30 second settings cache."
      />

      {!settings ? (
        <Panel title="No settings row yet">
          <p className="text-sm leading-relaxed text-mist-300">
            The bot creates a guild settings row the first time it loads this
            server, or when a command writes configuration. Run a settings
            command in Discord and refresh this page.
          </p>
        </Panel>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.href}
              href={card.href}
              className="group rounded-2xl border border-navy-700/80 bg-navy-900/50 p-5 transition hover:border-gold-500/30 hover:bg-navy-900/80"
            >
              <div className="flex items-start justify-between gap-3">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-royal-400/20 bg-royal-700/20 text-royal-400 transition group-hover:border-gold-500/30 group-hover:text-gold-400">
                  <Icon className="h-5 w-5" />
                </span>
                {card.status}
              </div>
              <h2 className="mt-4 font-display text-base font-semibold tracking-wide text-mist-100">
                {card.title}
              </h2>
              <p className="mt-1.5 text-sm text-mist-400">{card.description}</p>
              <span className="mt-4 inline-flex items-center gap-1.5 text-xs text-gold-400">
                Manage
                <IconArrow className="h-3.5 w-3.5" />
              </span>
            </Link>
          );
        })}
      </div>
    </>
  );
}
