import type { Metadata } from "next";

import { Badge } from "@/components/badge";
import { CommandBrowser } from "@/components/command-browser";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { commandCount, commandGroups } from "@/lib/commands";

export const metadata: Metadata = {
  title: "Commands",
  description:
    "The complete Triumph command reference for moderation, onboarding, logging, automations, temporary voice, and server tools.",
};

export default function CommandsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />

      <main className="flex-1">
        <section className="relative overflow-hidden border-b border-navy-800/80">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,rgba(124,58,237,0.2),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(212,175,55,0.1),transparent_50%)]"
          />
          <div className="relative mx-auto w-full max-w-6xl px-4 pb-14 pt-16 sm:px-6 sm:pt-20">
            <Badge tone="gold">Command reference</Badge>
            <h1 className="mt-5 max-w-3xl font-display text-4xl font-semibold leading-[1.1] tracking-wide text-white sm:text-5xl">
              Every command,
              <span className="block bg-gradient-to-r from-gold-400 via-gold-500 to-royal-400 bg-clip-text text-transparent">
                in one place.
              </span>
            </h1>
            <p className="mt-5 max-w-2xl text-sm leading-relaxed text-mist-300 sm:text-base">
              {commandCount} commands across {commandGroups.length} modules.
              Commands use the <code className="text-gold-400">!</code> prefix by
              default; the effective prefix can be checked with{" "}
              <code className="text-gold-400">!prefix</code>. Permission labels
              show the minimum Discord permission or role required.
            </p>
            <div className="mt-8 grid max-w-2xl grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                ["Commands", String(commandCount)],
                ["Modules", String(commandGroups.length)],
                ["Prefix", "!"],
                ["Schedules", "UTC"],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="rounded-xl border border-navy-700/80 bg-navy-900/50 px-4 py-3"
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
          </div>
        </section>

        <section className="mx-auto w-full max-w-6xl px-4 py-14 sm:px-6 sm:py-16">
          <CommandBrowser groups={commandGroups} total={commandCount} />
        </section>

        <section className="border-t border-navy-800/80 bg-navy-900/30">
          <div className="mx-auto w-full max-w-6xl px-4 py-12 sm:px-6">
            <div className="rounded-2xl border border-gold-500/20 bg-gradient-to-br from-navy-900/80 to-royal-700/15 p-6 sm:p-8">
              <h2 className="font-display text-lg font-semibold tracking-wide text-white">
                A note on permissions
              </h2>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-mist-400">
                The bot checks its own role position and permissions before every
                action. Configuration commands require Manage Server, moderation
                commands require the listed Discord permission, and temporary
                voice owner commands only work inside the room you own. Anything
                prefixed with <code className="text-mist-300">!automation</code>{" "}
                runs on five-field UTC cron expressions, quoted in the command.
              </p>
            </div>
          </div>
        </section>
      </main>

      <SiteFooter />
    </div>
  );
}
