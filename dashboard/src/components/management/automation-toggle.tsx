"use client";

import { useRouter } from "next/navigation";
import { useActionState, useEffect } from "react";

import { setAutomationEnabled } from "@/app/dashboard/management/actions";
import { idleActionState } from "@/lib/settings";

export function AutomationToggle({
  id,
  enabled,
}: {
  id: number;
  enabled: boolean;
}) {
  const [state, action, pending] = useActionState(
    setAutomationEnabled,
    idleActionState,
  );
  const router = useRouter();

  useEffect(() => {
    if (state.status === "success") {
      router.refresh();
    }
  }, [state, router]);

  return (
    <form action={action}>
      <input type="hidden" name="id" value={id} />
      <input type="hidden" name="enabled" value={enabled ? "false" : "true"} />
      <button
        type="submit"
        disabled={pending}
        className={`inline-flex items-center justify-center rounded-lg border px-3 py-1.5 text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-60 ${
          enabled
            ? "border-navy-700 bg-navy-800/60 text-mist-300 hover:border-rose-400/40 hover:text-rose-200"
            : "border-gold-500/40 bg-gold-500/10 text-gold-400 hover:bg-gold-500/20"
        }`}
      >
        {pending ? "Saving…" : enabled ? "Pause" : "Enable"}
      </button>
      {state.status === "error" ? (
        <p className="mt-1 max-w-[180px] text-[11px] leading-snug text-rose-300">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
