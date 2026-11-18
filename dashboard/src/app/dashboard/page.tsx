import Link from "next/link";
import { redirect } from "next/navigation";

import { Badge } from "@/components/badge";
import { EmptyState } from "@/components/empty-state";
import {
  IconArrow,
  IconChart,
  IconClock,
  IconList,
  IconMic,
  IconRoles,
  IconShield,
  IconUser,
  IconWarning,
} from "@/components/icons";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { StatCard } from "@/components/stat-card";
import { requireDashboardAccess } from "@/lib/auth";
import { eventLabel, eventTone } from "@/lib/events";
import { formatDateTime, formatNumber } from "@/lib/format";
import { getOverview } from "@/lib/queries";

export default async function DashboardOverviewPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const overview = await getOverview(access.guild.id);
  const stats = overview.latestStats;

  return (
    <>
      <PageHeader
        eyebrow="Overview"
        title={`Command center`}
        description={`Live operational state for ${access.guild.name}. Counts are read directly from Supabase with your administrator scope.`}
        actions={
          <Badge tone={access.verification.state === "verified" ? "success" : "muted"}>
            {access.verification.state === "verified"
              ? "Discord verified"
              : "Verification limited"}
          </Badge>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <StatCard
          label="Members"
          value={formatNumber(stats?.member_count ?? overview.counts.members)}
          hint={
            stats
              ? `${formatNumber(stats.human_count)} humans · ${formatNumber(
                  stats.bot_count,
                )} bots`
              : "From the latest statistics snapshot"
          }
          icon={<IconUser className="h-5 w-5" />}
          accent
        />
        <StatCard
          label="Active warnings"
          value={formatNumber(overview.counts.activeWarnings)}
          hint="Warnings that have not been deactivated"
          icon={<IconWarning className="h-5 w-5" />}
        />
        <StatCard
          label="Temp voice rooms"
          value={formatNumber(overview.counts.tempVoice)}
          hint="Channels currently tracked as active"
          icon={<IconMic className="h-5 w-5" />}
        />
        <StatCard
          label="Automations"
          value={formatNumber(overview.counts.automations)}
          hint="Stored jobs across every automation type"
          icon={<IconClock className="h-5 w-5" />}
        />
        <StatCard
          label="Reaction roles"
          value={formatNumber(overview.counts.reactionRoles)}
          hint="Message and emoji mappings"
          icon={<IconRoles className="h-5 w-5" />}
        />
        <StatCard
          label="Activity events"
          value={formatNumber(overview.counts.activityEvents)}
          hint="Rows recorded in the activity trail"
          icon={<IconList className="h-5 w-5" />}
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <Panel
          title="Recent activity"
          description="The newest events recorded by the logging and moderation systems."
          action={
            <Link
              href="/dashboard/activity"
              className="inline-flex items-center gap-1.5 text-sm text-gold-400 transition hover:text-gold-500"
            >
              View all
              <IconArrow className="h-4 w-4" />
            </Link>
          }
        >
          {overview.recentActivity.length === 0 ? (
            <EmptyState
              title="No activity recorded yet"
              description="Enable log channels with !logs set, or run a moderation command, and the trail will populate here."
            />
          ) : (
            <ul className="divide-y divide-navy-800/70">
              {overview.recentActivity.map((event) => (
                <li
                  key={event.id}
                  className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
                >
                  <div className="flex items-center gap-3">
                    <Badge tone={eventTone(event.event_type)}>
                      {eventLabel(event.event_type)}
                    </Badge>
                    <span className="text-sm text-mist-300">
                      {event.actor_id ? `actor ${event.actor_id}` : "system"}
                      {event.target_id ? ` → ${event.target_id}` : ""}
                    </span>
                  </div>
                  <span className="text-xs text-mist-500">
                    {formatDateTime(event.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Panel>

        <div className="space-y-6">
          <Panel title="Jump back in">
            <div className="space-y-2">
              {[
                {
                  href: "/dashboard/statistics",
                  label: "Statistics",
                  icon: IconChart,
                },
                {
                  href: "/dashboard/settings/logging",
                  label: "Logging channels",
                  icon: IconList,
                },
                {
                  href: "/dashboard/management/automations",
                  label: "Automations",
                  icon: IconClock,
                },
                {
                  href: "/dashboard/settings/moderation",
                  label: "Moderation rules",
                  icon: IconShield,
                },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="flex items-center justify-between rounded-xl border border-navy-800 bg-navy-950/50 px-3.5 py-3 text-sm text-mist-300 transition hover:border-gold-500/30 hover:text-mist-100"
                  >
                    <span className="flex items-center gap-3">
                      <Icon className="h-4 w-4 text-gold-500" />
                      {item.label}
                    </span>
                    <IconArrow className="h-4 w-4 text-mist-500" />
                  </Link>
                );
              })}
            </div>
          </Panel>

          <Panel title="Verification">
            <p className="text-sm leading-relaxed text-mist-300">
              {access.verification.detail}
            </p>
            <dl className="mt-4 space-y-2 text-xs text-mist-500">
              <div className="flex justify-between gap-3">
                <dt>Discord ID</dt>
                <dd className="text-mist-300">{access.user.discordId ?? "—"}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt>Dashboard role</dt>
                <dd className="text-mist-300">{access.user.role}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt>Guild ID</dt>
                <dd className="font-mono text-mist-300">{access.guild.id}</dd>
              </div>
            </dl>
          </Panel>
        </div>
      </div>
    </>
  );
}
