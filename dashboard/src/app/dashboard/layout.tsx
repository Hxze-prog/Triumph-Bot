import { redirect } from "next/navigation";
import type { ReactNode } from "react";

import { AccessDenied } from "@/components/access-denied";
import { DashboardShell } from "@/components/dashboard-shell";
import { requireDashboardAccess } from "@/lib/auth";

export default async function DashboardLayout({
  children,
}: {
  children: ReactNode;
}) {
  const access = await requireDashboardAccess();

  if (access.status === "unauthenticated") {
    redirect("/login?next=/dashboard");
  }

  if (access.status === "forbidden") {
    return (
      <AccessDenied reason={access.reason} userName={access.user?.name ?? null} />
    );
  }

  return (
    <DashboardShell
      user={access.user}
      guild={access.guild}
      verification={access.verification}
    >
      {children}
    </DashboardShell>
  );
}
