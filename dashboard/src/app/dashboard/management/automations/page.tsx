import Link from "next/link";
import { redirect } from "next/navigation";

import { Badge } from "@/components/badge";
import { EmptyState } from "@/components/empty-state";
import { IconArrow } from "@/components/icons";
import { AutomationToggle } from "@/components/management/automation-toggle";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { requireDashboardAccess } from "@/lib/auth";
import { formatDateTime, channelLabel } from "@/lib/format";
import { getAutomations } from "@/lib/queries";

function typeLabel(type: string): string {
  return type
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default async function AutomationsPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const automations = await getAutomations(access.guild.id);
  const enabled = automations.filter((item) => item.enabled).length;

  return (
    <>
      <PageHeader
        eyebrow="Management"
        title="Automations"
        description="Stored jobs and hooks. Changes sync to the bot within 30 seconds; scheduled jobs are restored from Supabase whenever the bot starts."
        actions={
          <Link
            href="/dashboard/management"
            className="inline-flex items-center gap-1.5 text-sm text-gold-400 hover:text-gold-500"
          >
            <IconArrow className="h-4 w-4 rotate-180" />
            Management
          </Link>
        }
      />

      <Panel
        title="Registered automations"
        description={`${automations.length} total · ${enabled} enabled · ${automations.length - enabled} paused`}
        bodyClassName={automations.length === 0 ? "" : "px-0 py-0 sm:px-0"}
      >
        {automations.length === 0 ? (
          <EmptyState
            title="No automations yet"
            description="Create one in Discord with !automation, for example an announcement on a UTC cron schedule."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px] text-left text-sm">
              <thead className="text-[11px] uppercase tracking-[0.16em] text-mist-500">
                <tr className="border-b border-navy-800">
                  <th className="px-5 py-3 font-medium sm:px-6">Name</th>
                  <th className="px-4 py-3 font-medium">Type</th>
                  <th className="px-4 py-3 font-medium">Channel</th>
                  <th className="px-4 py-3 font-medium">Schedule</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Last run</th>
                  <th className="px-5 py-3 font-medium sm:px-6">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/70">
                {automations.map((item) => (
                  <tr key={item.id} className="align-top">
                    <td className="px-5 py-3 sm:px-6">
                      <p className="font-medium text-mist-200">{item.name}</p>
                      <p className="mt-0.5 font-mono text-xs text-mist-500">
                        id {item.id}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone="royal">{typeLabel(item.type)}</Badge>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-mist-300">
                      {channelLabel(item.channel_id)}
                    </td>
                    <td className="px-4 py-3">
                      {item.cron ? (
                        <code className="text-xs text-gold-400">{item.cron}</code>
                      ) : (
                        <span className="text-xs text-mist-500">Event hook</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone={item.enabled ? "success" : "muted"}>
                        {item.enabled ? "Enabled" : "Paused"}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-xs text-mist-400">
                      {formatDateTime(item.last_run_at)}
                    </td>
                    <td className="px-5 py-3 sm:px-6">
                      <AutomationToggle id={item.id} enabled={item.enabled} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel title="Create and remove from Discord">
        <p className="text-sm leading-relaxed text-mist-300">
          <code className="text-gold-400">!automation list</code> ·{" "}
          <code className="text-gold-400">!automation status</code> ·{" "}
          <code className="text-gold-400">!automation toggle &lt;id|name&gt;</code> ·{" "}
          <code className="text-gold-400">!automation remove &lt;id|name&gt;</code>.
          New automations are created with{" "}
          <code className="text-gold-400">!automation announcement|message|reminder|stats|autorole|welcome|goodbye|response</code>{" "}
          using five-field UTC cron expressions for scheduled jobs.
        </p>
      </Panel>
    </>
  );
}
