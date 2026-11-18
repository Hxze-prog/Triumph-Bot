import Link from "next/link";
import { redirect } from "next/navigation";

import { Badge } from "@/components/badge";
import { IconArrow, IconClock, IconMic, IconRoles, IconWarning } from "@/components/icons";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { PreviewNotice } from "@/components/preview-notice";
import { requireDashboardAccess } from "@/lib/auth";
import { getAutomations, getReactionRoles, getTempVoice, getWarnings } from "@/lib/queries";

export default async function ManagementOverviewPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const [automations, reactionRoles, tempVoice, warnings] = await Promise.all([
    getAutomations(access.guild.id),
    getReactionRoles(access.guild.id),
    getTempVoice(access.guild.id),
    getWarnings(access.guild.id),
  ]);

  const enabled = automations.filter((item) => item.enabled).length;

  const cards = [
    {
      href: "/dashboard/management/automations",
      icon: IconClock,
      title: "Automations",
      value: `${automations.length}`,
      hint: `${enabled} enabled · ${automations.length - enabled} paused`,
    },
    {
      href: "/dashboard/management/reaction-roles",
      icon: IconRoles,
      title: "Reaction roles",
      value: `${reactionRoles.length}`,
      hint: "Message and emoji mappings",
    },
    {
      href: "/dashboard/management/warnings",
      icon: IconWarning,
      title: "Active warnings",
      value: `${warnings.length}`,
      hint: "Warnings not yet deactivated",
    },
    {
      href: "/dashboard/settings/temp-voice",
      icon: IconMic,
      title: "Temp voice rooms",
      value: `${tempVoice.length}`,
      hint: "Currently active channels",
    },
  ];

  return (
    <>
      <PageHeader
        eyebrow="Management"
        title="Server operations"
        description="Automations, self-serve roles, and moderation records at a glance."
      />
      <PreviewNotice feature="Management view" />

      <div className="grid gap-4 sm:grid-cols-2">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Link
              key={card.href}
              href={card.href}
              className="group rounded-2xl border border-navy-700/80 bg-navy-900/50 p-5 transition hover:border-gold-500/30 hover:bg-navy-900/80"
            >
              <div className="flex items-start justify-between">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-royal-400/20 bg-royal-700/20 text-royal-400 transition group-hover:border-gold-500/30 group-hover:text-gold-400">
                  <Icon className="h-5 w-5" />
                </span>
                <Badge tone="muted">Open</Badge>
              </div>
              <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.2em] text-mist-500">
                {card.title}
              </p>
              <p className="mt-1 font-display text-3xl font-semibold text-white">
                {card.value}
              </p>
              <p className="mt-1 text-xs text-mist-400">{card.hint}</p>
              <span className="mt-4 inline-flex items-center gap-1.5 text-xs text-gold-400">
                Manage
                <IconArrow className="h-3.5 w-3.5" />
              </span>
            </Link>
          );
        })}
      </div>

      <Panel title="Discord commands">
        <p className="text-sm text-mist-300">
          Creation and editing stay in Discord for this phase:{" "}
          <code className="text-gold-400">!automation</code>,{" "}
          <code className="text-gold-400">!reactionrole</code>,{" "}
          <code className="text-gold-400">!warnings</code>, and{" "}
          <code className="text-gold-400">!tempvoice</code>. Phase 12 adds
          dashboard write actions with cache invalidation.
        </p>
      </Panel>
    </>
  );
}
