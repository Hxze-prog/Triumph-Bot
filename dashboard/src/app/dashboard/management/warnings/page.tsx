import Link from "next/link";
import { redirect } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { IconArrow } from "@/components/icons";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { PreviewNotice } from "@/components/preview-notice";
import { requireDashboardAccess } from "@/lib/auth";
import { formatDateTime, truncate } from "@/lib/format";
import { getWarnings } from "@/lib/queries";

export default async function WarningsPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const warnings = await getWarnings(access.guild.id);

  return (
    <>
      <PageHeader
        eyebrow="Management"
        title="Active warnings"
        description="Warning records that have not been deactivated. Deactivate one in Discord with !unwarn."
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
      <PreviewNotice feature="Warning records" />

      <Panel
        title="Warnings"
        description={`${warnings.length} active warning(s).`}
        bodyClassName={warnings.length === 0 ? "" : "px-0 py-0 sm:px-0"}
      >
        {warnings.length === 0 ? (
          <EmptyState
            title="No active warnings"
            description="Warnings issued with !warn appear here until they are removed."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-[11px] uppercase tracking-[0.16em] text-mist-500">
                <tr className="border-b border-navy-800">
                  <th className="px-5 py-3 font-medium sm:px-6">Member</th>
                  <th className="px-4 py-3 font-medium">Moderator</th>
                  <th className="px-4 py-3 font-medium">Reason</th>
                  <th className="px-4 py-3 font-medium">Warning</th>
                  <th className="px-5 py-3 font-medium sm:px-6">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/70">
                {warnings.map((warning) => (
                  <tr key={warning.id} className="align-top">
                    <td className="px-5 py-3 font-mono text-xs text-mist-200 sm:px-6">
                      {warning.user_id}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-mist-300">
                      {warning.moderator_id ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-mist-300">
                      {truncate(warning.reason, 120)}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-mist-500">
                      #{warning.id}
                    </td>
                    <td className="px-5 py-3 text-xs text-mist-400 sm:px-6">
                      {formatDateTime(warning.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Panel>

      <Panel title="Commands">
        <p className="text-sm text-mist-300">
          <code className="text-gold-400">!warn @user [reason]</code> ·{" "}
          <code className="text-gold-400">!warnings @user</code> ·{" "}
          <code className="text-gold-400">!unwarn @user &lt;id|latest&gt;</code>.
          Every moderation action is also mirrored to the activity trail.
        </p>
      </Panel>
    </>
  );
}
