import Link from "next/link";
import { redirect } from "next/navigation";

import { IconArrow } from "@/components/icons";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { LoggingSettingsForm } from "@/components/settings/logging-form";
import { requireDashboardAccess } from "@/lib/auth";
import { fetchGuildDirectory } from "@/lib/discord";
import { getSettings } from "@/lib/queries";
import { defaultGuildSettings } from "@/lib/settings";

export default async function LoggingSettingsPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const [stored, directory] = await Promise.all([
    getSettings(access.guild.id),
    fetchGuildDirectory(access.guild.id),
  ]);

  return (
    <>
      <PageHeader
        eyebrow="Settings"
        title="Logging"
        description="Each event type writes to its own channel and is mirrored into the activity trail."
        actions={
          <Link
            href="/dashboard/settings"
            className="inline-flex items-center gap-1.5 text-sm text-gold-400 hover:text-gold-500"
          >
            <IconArrow className="h-4 w-4 rotate-180" />
            All settings
          </Link>
        }
      />

      <LoggingSettingsForm
        settings={stored ?? defaultGuildSettings}
        directory={directory}
      />

      <Panel title="Discord commands">
        <p className="text-sm text-mist-300">
          The same settings are available with{" "}
          <code className="text-gold-400">!logs set &lt;event&gt; #channel</code>,{" "}
          <code className="text-gold-400">!logs set &lt;event&gt; off</code>,{" "}
          <code className="text-gold-400">!logs test &lt;event&gt;</code>, and{" "}
          <code className="text-gold-400">!logs history [event] [limit]</code>.
        </p>
      </Panel>
    </>
  );
}
