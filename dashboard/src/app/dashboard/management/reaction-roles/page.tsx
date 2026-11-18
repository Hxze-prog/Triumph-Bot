import Link from "next/link";
import { redirect } from "next/navigation";

import { EmptyState } from "@/components/empty-state";
import { IconArrow } from "@/components/icons";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { PreviewNotice } from "@/components/preview-notice";
import { requireDashboardAccess } from "@/lib/auth";
import { formatDate } from "@/lib/format";
import { getReactionRoles } from "@/lib/queries";

export default async function ReactionRolesPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const mappings = await getReactionRoles(access.guild.id);

  return (
    <>
      <PageHeader
        eyebrow="Management"
        title="Reaction roles"
        description="Emoji-to-role mappings attached to messages. Removal of the message or emoji cleans up the mapping."
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
      <PreviewNotice feature="Reaction role management" />

      <Panel
        title="Mappings"
        description={`${mappings.length} active mapping(s).`}
        bodyClassName={mappings.length === 0 ? "" : "px-0 py-0 sm:px-0"}
      >
        {mappings.length === 0 ? (
          <EmptyState
            title="No reaction roles configured"
            description="Create one in Discord with !reactionrole add <message_id|link> <emoji> @role."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="text-[11px] uppercase tracking-[0.16em] text-mist-500">
                <tr className="border-b border-navy-800">
                  <th className="px-5 py-3 font-medium sm:px-6">Emoji</th>
                  <th className="px-4 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Message</th>
                  <th className="px-4 py-3 font-medium">Channel</th>
                  <th className="px-5 py-3 font-medium sm:px-6">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-800/70">
                {mappings.map((mapping) => (
                  <tr key={mapping.id}>
                    <td className="px-5 py-3 text-lg sm:px-6">
                      {mapping.emoji}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-mist-300">
                      {mapping.role_id}
                    </td>
                    <td className="px-4 py-3">
                      <a
                        href={`https://discord.com/channels/${access.guild.id}/${mapping.channel_id}/${mapping.message_id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="font-mono text-xs text-gold-400 underline underline-offset-2"
                      >
                        {mapping.message_id}
                      </a>
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-mist-300">
                      {mapping.channel_id}
                    </td>
                    <td className="px-5 py-3 text-xs text-mist-400 sm:px-6">
                      {formatDate(mapping.created_at)}
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
          <code className="text-gold-400">!reactionrole add</code> ·{" "}
          <code className="text-gold-400">!reactionrole remove</code> ·{" "}
          <code className="text-gold-400">!reactionrole list</code>. The bot
          reacts with the configured emoji and manages role assignment through raw
          reaction events.
        </p>
      </Panel>
    </>
  );
}
