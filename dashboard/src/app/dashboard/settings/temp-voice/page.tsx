import Link from "next/link";
import { redirect } from "next/navigation";

import { Badge } from "@/components/badge";
import { EmptyState } from "@/components/empty-state";
import { IconArrow } from "@/components/icons";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { TempVoiceSettingsForm } from "@/components/settings/temp-voice-form";
import { requireDashboardAccess } from "@/lib/auth";
import { fetchGuildDirectory } from "@/lib/discord";
import { getSettings, getTempVoice } from "@/lib/queries";
import { defaultGuildSettings } from "@/lib/settings";

export default async function TempVoiceSettingsPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const [stored, directory, channels] = await Promise.all([
    getSettings(access.guild.id),
    fetchGuildDirectory(access.guild.id),
    getTempVoice(access.guild.id),
  ]);

  return (
    <>
      <PageHeader
        eyebrow="Settings"
        title="Temporary voice"
        description="Join-to-create rooms with owner controls and automatic cleanup."
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

      <TempVoiceSettingsForm
        settings={stored ?? defaultGuildSettings}
        directory={directory}
      />

      <Panel
        title="Active rooms"
        description={`${channels.length} room(s) currently tracked.`}
      >
        {channels.length === 0 ? (
          <EmptyState
            title="No active rooms"
            description="Rooms appear here while members occupy them."
          />
        ) : (
          <ul className="divide-y divide-navy-800/70">
            {channels.map((channel) => (
              <li
                key={channel.channel_id}
                className="flex flex-wrap items-center justify-between gap-3 py-3 first:pt-0 last:pb-0"
              >
                <div>
                  <p className="text-sm font-medium text-mist-200">
                    {channel.channel_name || `Channel ${channel.channel_id}`}
                  </p>
                  <p className="mt-0.5 font-mono text-xs text-mist-500">
                    owner {channel.owner_id}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Badge tone={channel.is_locked ? "danger" : "success"}>
                    {channel.is_locked ? "Locked" : "Open"}
                  </Badge>
                  <Badge tone="muted">
                    {channel.user_limit > 0
                      ? `${channel.user_limit} max`
                      : "No limit"}
                  </Badge>
                </div>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      <Panel title="Owner commands">
        <p className="text-sm text-mist-300">
          Room owners control their channel with{" "}
          <code className="text-gold-400">!tempvoice name|size|lock|unlock|kick|claim|delete</code>.
          Administrators configure the system with{" "}
          <code className="text-gold-400">!tempvoice setup</code>,{" "}
          <code className="text-gold-400">!tempvoice defaultlimit</code>, and{" "}
          <code className="text-gold-400">!tempvoice template</code>.
        </p>
      </Panel>
    </>
  );
}
