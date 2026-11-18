"use server";

import { revalidatePath } from "next/cache";

import { requireDashboardAccess } from "@/lib/auth";
import type { ActionState } from "@/lib/settings";
import { createClient } from "@/lib/supabase/server";

function readText(formData: FormData, key: string): string {
  const value = formData.get(key);
  return typeof value === "string" ? value.trim() : "";
}

export async function setAutomationEnabled(
  _state: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const access = await requireDashboardAccess();
  if (access.status !== "ok") {
    return {
      status: "error",
      message:
        "Your session is not authorized for this server. Sign in again and retry.",
    };
  }

  const id = Number(readText(formData, "id"));
  const enabled = readText(formData, "enabled") === "true";
  if (!Number.isInteger(id) || id <= 0) {
    return { status: "error", message: "Invalid automation id." };
  }

  const supabase = await createClient();
  const { data, error } = await supabase
    .from("automations")
    .update({ enabled })
    .eq("id", id)
    .eq("guild_id", access.guild.id)
    .select("id, enabled")
    .maybeSingle();

  if (error) {
    return {
      status: "error",
      message: `Could not update automation #${id}: ${error.message}`,
    };
  }
  if (!data) {
    return {
      status: "error",
      message: `Automation #${id} no longer exists in this server.`,
    };
  }

  revalidatePath("/dashboard/management/automations");
  revalidatePath("/dashboard", "layout");

  return {
    status: "success",
    message: `Automation #${id} ${enabled ? "enabled" : "paused"}. The bot syncs within 30 seconds.`,
  };
}
