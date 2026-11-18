"use client";

import { useFormStatus } from "react-dom";

import { ActionFeedback } from "@/components/settings/field";
import type { ActionState } from "@/lib/settings";

function SubmitButton({ label }: { label: string }) {
  const { pending } = useFormStatus();
  return (
    <button
      type="submit"
      disabled={pending}
      className="inline-flex items-center justify-center rounded-xl bg-gold-500 px-5 py-2.5 text-sm font-semibold text-navy-950 transition hover:bg-gold-400 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {pending ? "Saving…" : label}
    </button>
  );
}

export function SaveBar({
  state,
  label = "Save changes",
  note,
}: {
  state: ActionState;
  label?: string;
  note?: string;
}) {
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-4">
        <SubmitButton label={label} />
        {note ? <p className="text-xs text-mist-500">{note}</p> : null}
      </div>
      <ActionFeedback state={state} />
    </div>
  );
}
