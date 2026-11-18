import Link from "next/link";
import { redirect } from "next/navigation";

import { IconArrow } from "@/components/icons";
import { PageHeader } from "@/components/page-header";
import { Panel } from "@/components/panel";
import { SettingRow } from "@/components/setting-row";
import { AutomodSettingsForm } from "@/components/settings/automod-form";
import { requireDashboardAccess } from "@/lib/auth";
import { getSettings } from "@/lib/queries";
import { defaultGuildSettings } from "@/lib/settings";

export default async function ModerationSettingsPage() {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    redirect("/login");
  }

  const settings = (await getSettings(access.guild.id)) ?? defaultGuildSettings;

  return (
    <>
      <PageHeader
        eyebrow="Settings"
        title="Moderation & automod"
        description="Automated enforcement thresholds and the roles that bypass them."
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

      <AutomodSettingsForm settings={settings} />

      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Roles and exemptions">
          <SettingRow
            label="Autoroles"
            value={`${settings.auto_role_ids?.length ?? 0} role(s)`}
            hint="Applied to humans on join"
          />
          <SettingRow
            label="Dashboard admin roles"
            value={`${settings.dashboard_admin_role_ids?.length ?? 0} role(s)`}
            hint="When set, dashboard access also requires one of these Discord roles"
          />
          <SettingRow
            label="Command prefix"
            value={<code className="text-gold-400">{settings.prefix}</code>}
          />
          <div className="mt-4 rounded-xl border border-navy-800 bg-navy-950/50 px-4 py-3 text-xs leading-relaxed text-mist-400">
            Exemptions are automatic: the server owner, administrators, and
            members with Manage Messages, Manage Server, Kick, Ban, or Moderate
            Members are skipped by automoderation.
          </div>
        </Panel>

        <Panel title="Discord commands">
          <p className="text-sm leading-relaxed text-mist-300">
            Autoroles stay in Discord:{" "}
            <code className="text-gold-400">!autorole add|remove|list</code>.
            Dashboard admin roles are granted in Supabase.{" "}
            <code className="text-gold-400">!automod spam|links|invites on|off</code>,{" "}
            <code className="text-gold-400">!automod threshold</code>,{" "}
            <code className="text-gold-400">!automod interval</code>, and{" "}
            <code className="text-gold-400">!automod timeout</code> mirror the
            form above. Moderation history is available with{" "}
            <code className="text-gold-400">!modlogs</code>.
          </p>
        </Panel>
      </div>
    </>
  );
}
