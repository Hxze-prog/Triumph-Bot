import { redirect } from "next/navigation";

import { Badge } from "@/components/badge";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { requireDashboardAccess } from "@/lib/auth";
import { eventLabel, eventTone } from "@/lib/events";
import { formatDateTime, snowflake } from "@/lib/format";
import { getActivity } from "@/lib/queries";

export default async function ActivityPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const events = await getActivity(access.guild.id, 50);

  return (
    <>
      <PageHeader
        eyebrow="Insights"
        title="Activity logs"
        description="The unified trail written by logging and moderation. Channels are shown as Discord IDs because the dashboard reads stored records, not live channel names."
      />

      <Panel
        title="Latest events"
        description={`Showing up to 50 of the most recent records.`}
        bodyClassName={events.length === 0 ? "" : "px-0 py-0 sm:px-0"}
      >
        {events.length === 0 ? (
          <EmptyState
            title="No activity recorded yet"
            description="Configure log channels with !logs set <event> #channel, then trigger a Discord event."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-[11px] uppercase tracking-[0.16em] text-mist-500">
                <tr className="border-b border-navy-800">
                  <th className="px-5 py-3 font-medium sm:px-6">Event</th>
                  <th className="px-4 py-3 font-medium">Actor</th>
                  <th className="px-4 py-3 font-medium">Target</th>
                  <th className="px-4 py-3 font-medium">Channel</th>
                  <th className="px-5 py-3 font-medium sm:px-6">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/70">
                {events.map((event) => (
                  <tr key={event.id} className="align-top">
                    <td className="px-5 py-3 sm:px-6">
                      <Badge tone={eventTone(event.event_type)}>
                        {eventLabel(event.event_type)}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-mist-300">
                      {snowflake(event.actor_id)}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-mist-300">
                      {snowflake(event.target_id)}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-mist-300">
                      {snowflake(event.channel_id)}
                    </td>
                    <td className="px-5 py-3 text-xs text-mist-400 sm:px-6">
                      {formatDateTime(event.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>
    </>
  );
}
