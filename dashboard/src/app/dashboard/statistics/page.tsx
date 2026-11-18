import { redirect } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { StatCard } from "@/components/stat-card";
import { requireDashboardAccess } from "@/lib/auth";
import { formatDateTime, formatNumber } from "@/lib/format";
import { getStatsHistory } from "@/lib/queries";

export default async function StatisticsPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const history = await getStatsHistory(access.guild.id);
  const latest = history[0] ?? null;

  const human = latest?.human_count ?? 0;
  const bots = latest?.bot_count ?? 0;
  const total = human + bots;
  const humanPct = total > 0 ? Math.round((human / total) * 100) : 0;
  const botPct = total > 0 ? 100 - humanPct : 0;

  return (
    <>
      <PageHeader
        eyebrow="Insights"
        title="Statistics"
        description="Snapshots written by !serverstats. Run the command periodically or through a scheduled automation to build a trend."
      />

      {latest ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Members"
            value={formatNumber(latest.member_count)}
            hint={`Recorded ${formatDateTime(latest.recorded_at)}`}
            accent
          />
          <StatCard
            label="Online"
            value={formatNumber(latest.online_count)}
            hint="Presence-derived when enabled"
          />
          <StatCard
            label="Channels"
            value={formatNumber(latest.channel_count)}
            hint={`${formatNumber(latest.role_count)} roles tracked`}
          />
          <StatCard
            label="Boosts"
            value={formatNumber(latest.boost_count)}
            hint="Premium boost count at snapshot time"
          />
        </div>
      ) : null}

      {latest ? (
        <Panel title="Member composition">
          <div className="space-y-5">
            <div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-mist-300">Humans</span>
                <span className="text-mist-400">
                  {formatNumber(human)} · {humanPct}%
                </span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-navy-800">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-gold-500 to-gold-400"
                  style={{ width: `${humanPct}%` }}
                />
              </div>
            </div>
            <div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-mist-300">Bots</span>
                <span className="text-mist-400">
                  {formatNumber(bots)} · {botPct}%
                </span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-navy-800">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-royal-600 to-royal-400"
                  style={{ width: `${botPct}%` }}
                />
              </div>
            </div>
          </div>
        </Panel>
      ) : null}

      <Panel
        title="Snapshot history"
        description={`Most recent ${history.length} snapshots, newest first.`}
      >
        {history.length === 0 ? (
          <EmptyState
            title="No statistics snapshots yet"
            description="Run !serverstats in Discord, or schedule the stats automation, to record the first snapshot."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-[11px] uppercase tracking-[0.16em] text-mist-500">
                <tr className="border-b border-navy-800">
                  <th className="py-2 pr-4 font-medium">Recorded</th>
                  <th className="py-2 pr-4 font-medium">Members</th>
                  <th className="py-2 pr-4 font-medium">Humans</th>
                  <th className="py-2 pr-4 font-medium">Bots</th>
                  <th className="py-2 pr-4 font-medium">Online</th>
                  <th className="py-2 pr-4 font-medium">Channels</th>
                  <th className="py-2 pr-4 font-medium">Roles</th>
                  <th className="py-2 font-medium">Boosts</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/70 text-mist-300">
                {history.map((row) => (
                  <tr key={row.id}>
                    <td className="py-3 pr-4 whitespace-nowrap">
                      {formatDateTime(row.recorded_at)}
                    </td>
                    <td className="py-3 pr-4">{formatNumber(row.member_count)}</td>
                    <td className="py-3 pr-4">{formatNumber(row.human_count)}</td>
                    <td className="py-3 pr-4">{formatNumber(row.bot_count)}</td>
                    <td className="py-3 pr-4">{formatNumber(row.online_count)}</td>
                    <td className="py-3 pr-4">{formatNumber(row.channel_count)}</td>
                    <td className="py-3 pr-4">{formatNumber(row.role_count)}</td>
                    <td className="py-3">{formatNumber(row.boost_count)}</td>
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
