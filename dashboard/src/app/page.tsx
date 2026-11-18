import Image from "next/image";
import Link from "next/link";

import { Badge } from "@/components/badge";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import {
  IconArrow,
  IconChart,
  IconCheck,
  IconClock,
  IconHash,
  IconList,
  IconMic,
  IconRoles,
  IconShield,
  IconWarning,
  IconWelcome,
} from "@/components/icons";

const features = [
  {
    icon: IconShield,
    title: "Moderation",
    body: "Bans, kicks, timeouts, warnings, purge, and channel locks with permission checks and structured records.",
  },
  {
    icon: IconWarning,
    title: "AutoModeration",
    body: "Anti-spam, anti-link, and anti-invite rules with configurable thresholds, timeouts, and a curated allowlist.",
  },
  {
    icon: IconWelcome,
    title: "Onboarding",
    body: "Welcome cards, banner rendering, goodbye messages, autoroles, direct messages, and automatic member numbering.",
  },
  {
    icon: IconHash,
    title: "Logging",
    body: "Per-event channels for joins, leaves, message edits and deletes, role changes, nicknames, voice, and channels.",
  },
  {
    icon: IconClock,
    title: "Automation",
    body: "Cron-based announcements, reminders, recurring messages, stat reports, and keyword auto responders in UTC.",
  },
  {
    icon: IconMic,
    title: "Temporary voice",
    body: "Join-to-create channels with owner rename, size limits, lock, unlock, kick, claim, and automatic cleanup.",
  },
  {
    icon: IconRoles,
    title: "Reaction roles",
    body: "Self-serve roles mapped to message reactions, with automatic cleanup when messages or reactions disappear.",
  },
  {
    icon: IconChart,
    title: "Server insights",
    body: "Member and channel snapshots, historical statistics, and a full activity trail stored in Supabase.",
  },
];

const highlights = [
  "Discord OAuth with administrator verification",
  "Row Level Security scoped per server",
  "Audit trail for every dashboard and bot action",
];

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />

      <main className="flex-1">
        <section className="relative overflow-hidden">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(124,58,237,0.22),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(212,175,55,0.12),transparent_50%)]"
          />
          <div className="relative mx-auto grid w-full max-w-6xl gap-14 px-4 pb-20 pt-16 sm:px-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:pt-24">
            <div>
              <Badge tone="gold">Discord command center</Badge>
              <h1 className="mt-6 font-display text-4xl font-semibold leading-[1.08] tracking-wide text-white sm:text-5xl lg:text-6xl">
                Run your server
                <span className="block bg-gradient-to-r from-gold-400 via-gold-500 to-royal-400 bg-clip-text text-transparent">
                  like a standard.
                </span>
              </h1>
              <p className="mt-6 max-w-xl text-base leading-relaxed text-mist-300 sm:text-lg">
                Triumph brings moderation, onboarding, logging, automation, and
                live server insight into one deliberate system. The bot does the
                work. The dashboard shows you everything.
              </p>
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 rounded-xl bg-gold-500 px-5 py-3 text-sm font-semibold text-navy-950 transition hover:bg-gold-400"
                >
                  Open the dashboard
                  <IconArrow className="h-4 w-4" />
                </Link>
                <Link
                  href="https://github.com/Hxze-prog/Triumph-Bot"
                  className="inline-flex items-center gap-2 rounded-xl border border-navy-700 px-5 py-3 text-sm font-medium text-mist-300 transition hover:border-gold-500/40 hover:text-mist-100"
                >
                  View the repository
                </Link>
              </div>
              <ul className="mt-10 space-y-2.5 text-sm text-mist-400">
                {highlights.map((item) => (
                  <li key={item} className="flex items-center gap-2.5">
                    <IconCheck className="h-4 w-4 text-gold-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>

            <div className="relative">
              <div className="absolute -inset-6 rounded-[2rem] bg-gradient-to-br from-royal-700/30 via-transparent to-gold-500/20 blur-2xl" />
              <div className="relative overflow-hidden rounded-[1.75rem] border border-navy-700 bg-navy-900/70 p-8 shadow-[0_60px_140px_-80px_rgba(0,0,0,1)]">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] uppercase tracking-[0.28em] text-mist-500">
                    Command center
                  </p>
                  <div className="flex gap-1.5">
                    <span className="h-2 w-2 rounded-full bg-gold-500/70" />
                    <span className="h-2 w-2 rounded-full bg-royal-400/70" />
                    <span className="h-2 w-2 rounded-full bg-mist-500/40" />
                  </div>
                </div>
                <div className="mt-6 flex items-center gap-4">
                  <span className="flex h-16 w-16 items-center justify-center rounded-2xl border border-gold-500/30 bg-navy-950 p-2">
                    <Image
                      src="/triumph-icon.png"
                      alt="Triumph"
                      width={64}
                      height={64}
                      className="h-full w-full object-contain"
                      priority
                    />
                  </span>
                  <div>
                    <p className="font-display text-lg font-semibold tracking-[0.18em] text-mist-100">
                      TRIUMPH
                    </p>
                    <p className="text-xs text-mist-500">
                      Moderation · Onboarding · Insight
                    </p>
                  </div>
                </div>
                <div className="mt-7 grid grid-cols-2 gap-3 text-sm">
                  {[
                    ["Modules online", "10"],
                    ["Scheduled jobs", "UTC"],
                    ["Access model", "RLS"],
                    ["Audit stream", "Live"],
                  ].map(([label, value]) => (
                    <div
                      key={label}
                      className="rounded-xl border border-navy-700/80 bg-navy-950/60 px-4 py-3"
                    >
                      <p className="text-[10px] uppercase tracking-[0.18em] text-mist-500">
                        {label}
                      </p>
                      <p className="mt-1 font-display text-lg font-semibold text-gold-400">
                        {value}
                      </p>
                    </div>
                  ))}
                </div>
                <div className="mt-6 space-y-2">
                  {[
                    ["welcome", "member joined · card queued"],
                    ["logging", "message edit captured"],
                    ["automation", "reminder fired on schedule"],
                  ].map(([tag, text]) => (
                    <div
                      key={tag}
                      className="flex items-center gap-3 rounded-lg border border-navy-800 bg-navy-900/60 px-3 py-2 text-xs text-mist-400"
                    >
                      <span className="rounded-md bg-royal-700/30 px-2 py-0.5 font-medium uppercase tracking-[0.12em] text-royal-400">
                        {tag}
                      </span>
                      {text}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="mx-auto w-full max-w-6xl px-4 py-20 sm:px-6">
          <div className="max-w-2xl">
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-gold-500">
              What ships
            </p>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-wide text-white sm:text-4xl">
              Every system your server actually needs.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-mist-400 sm:text-base">
              Each module stores its configuration and history in Supabase, so
              the bot, the dashboard, and your moderators stay on the same page.
            </p>
          </div>
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div
                  key={feature.title}
                  className="group rounded-2xl border border-navy-700/80 bg-navy-900/50 p-5 transition hover:border-gold-500/30 hover:bg-navy-900/80"
                >
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-royal-400/20 bg-royal-700/20 text-royal-400 transition group-hover:border-gold-500/30 group-hover:text-gold-400">
                    <Icon className="h-5 w-5" />
                  </span>
                  <h3 className="mt-4 font-display text-base font-semibold tracking-wide text-mist-100">
                    {feature.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-mist-400">
                    {feature.body}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        <section
          id="automation"
          className="border-y border-navy-800/80 bg-navy-900/30"
        >
          <div className="mx-auto grid w-full max-w-6xl gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:items-center">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-gold-500">
                Automation
              </p>
              <h2 className="mt-3 font-display text-3xl font-semibold tracking-wide text-white sm:text-4xl">
                Set it once. Let the schedule carry it.
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-mist-400 sm:text-base">
                Announcements, reminders, recurring messages, and statistics
                reports run on a five-field UTC cron. Jobs are restored from the
                database on every restart, so downtime does not erase the plan.
              </p>
              <ul className="mt-6 space-y-3 text-sm text-mist-300">
                {[
                  "Quote the cron expression and let the scheduler handle the rest",
                  "Placeholders for member count, mention, display name, and time",
                  "Keyword auto responders with per-automation cooldowns",
                  "Welcome, goodbye, and autorole hooks that run instantly",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2.5">
                    <IconCheck className="mt-0.5 h-4 w-4 shrink-0 text-gold-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="overflow-hidden rounded-2xl border border-navy-700 bg-navy-950/80">
              <div className="border-b border-navy-800 px-5 py-3 text-[10px] uppercase tracking-[0.24em] text-mist-500">
                Scheduled automation
              </div>
              <pre className="overflow-x-auto px-5 py-6 text-xs leading-relaxed text-mist-300">
                <code>{`!automation announcement daily-brief "0 9 * * *" #staff
  "Good morning, {guild}. {member_count} members checked in."

!automation stats weekly-report "0 18 * * 0" #analytics

!automation response support "how do i appeal|appeal"
  "Open a ticket and a moderator will review it."`}</code>
              </pre>
            </div>
          </div>
        </section>

        <section
          id="insights"
          className="mx-auto grid w-full max-w-6xl gap-12 px-4 py-20 sm:px-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-center"
        >
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-gold-500">
              Insights
            </p>
            <h2 className="mt-3 font-display text-3xl font-semibold tracking-wide text-white sm:text-4xl">
              See the server, not just the commands.
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-mist-400 sm:text-base">
              Statistics snapshots, active warnings, temporary voice occupancy,
              reaction role mappings, and the activity stream are all readable
              from the dashboard with the same permissions the bot respects.
            </p>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              {
                icon: IconChart,
                title: "Statistics",
                body: "Member, human, bot, channel, role, and boost counts over time.",
              },
              {
                icon: IconList,
                title: "Activity",
                body: "A unified trail of joins, edits, moderation, and voice events.",
              },
              {
                icon: IconWarning,
                title: "Warnings",
                body: "Active warning records with moderator, reason, and timestamp.",
              },
              {
                icon: IconMic,
                title: "Voice rooms",
                body: "Live temporary channels, owners, limits, and lock state.",
              },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.title}
                  className="rounded-2xl border border-navy-700/80 bg-navy-900/50 p-5"
                >
                  <Icon className="h-5 w-5 text-gold-500" />
                  <h3 className="mt-3 font-display text-sm font-semibold tracking-wide text-mist-100">
                    {item.title}
                  </h3>
                  <p className="mt-1.5 text-sm text-mist-400">{item.body}</p>
                </div>
              );
            })}
          </div>
        </section>

        <section
          id="security"
          className="border-t border-navy-800/80 bg-navy-900/30"
        >
          <div className="mx-auto w-full max-w-6xl px-4 py-20 sm:px-6">
            <div className="grid gap-10 rounded-3xl border border-gold-500/20 bg-gradient-to-br from-navy-900/80 to-royal-700/15 p-8 sm:p-10 lg:grid-cols-[1fr_auto] lg:items-center">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-gold-500">
                  Access control
                </p>
                <h2 className="mt-3 font-display text-2xl font-semibold tracking-wide text-white sm:text-3xl">
                  Discord identity, recorded authorization, row-level security.
                </h2>
                <p className="mt-3 max-w-2xl text-sm leading-relaxed text-mist-400">
                  Sign-in uses Supabase Auth with the Discord provider. Access is
                  granted only when a matching row exists in{" "}
                  <code className="text-mist-300">dashboard_admins</code>, and
                  every table is protected by RLS scoped to your administrator
                  membership. No shared passwords, no open endpoints.
                </p>
              </div>
              <Link
                href="/login"
                className="inline-flex items-center gap-2 rounded-xl bg-gold-500 px-5 py-3 text-sm font-semibold text-navy-950 transition hover:bg-gold-400"
              >
                Continue with Discord
                <IconDiscordInline />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}

function IconDiscordInline() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden className="h-4 w-4">
      <path d="M19.5 5.3A16 16 0 0 0 15.6 4l-.5 1a13 13 0 0 0-6.2 0L8.4 4a16 16 0 0 0-3.9 1.3C2.1 8.6 1.5 11.8 1.8 15a15 15 0 0 0 4.8 2.4l1-1.6c-.5-.2-1-.5-1.5-.8l.4-.3c2.9 1.4 6.1 1.4 9 0l.4.3c-.5.3-1 .6-1.5.8l1 1.6A15 15 0 0 0 22.2 15c.4-3.7-.5-6.9-2.7-9.7ZM8.7 13.3c-.9 0-1.6-.8-1.6-1.8s.7-1.8 1.6-1.8 1.7.8 1.6 1.8c0 1-.7 1.8-1.6 1.8Zm6.6 0c-.9 0-1.6-.8-1.6-1.8s.7-1.8 1.6-1.8 1.7.8 1.6 1.8c0 1-.7 1.8-1.6 1.8Z" />
    </svg>
  );
}
