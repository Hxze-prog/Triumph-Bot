import Link from "next/link";
import { redirect } from "next/navigation";

import { IconArrow } from "@/components/icons";
import { PageHeader } from "@/components/page-header";
import { WelcomeSettingsForm } from "@/components/settings/welcome-form";
import { requireDashboardAccess } from "@/lib/auth";
import { fetchGuildDirectory } from "@/lib/discord";
import { getSettings } from "@/lib/queries";
import { defaultGuildSettings } from "@/lib/settings";

export default async function WelcomeSettingsPage() {
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
        title="Welcome & goodbye"
        description="Edit greeting behavior for new members and departures."
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
      <WelcomeSettingsForm
        settings={stored ?? defaultGuildSettings}
        directory={directory}
      />
    </>
  );
}
