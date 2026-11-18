"use client";

import { useEffect } from "react";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="rounded-2xl border border-rose-400/25 bg-rose-400/5 p-8">
      <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-rose-300">
        Dashboard error
      </p>
      <h2 className="mt-2 font-display text-xl font-semibold text-white">
        This view could not be loaded
      </h2>
      <p className="mt-3 text-sm leading-relaxed text-mist-300">
        Supabase may be unreachable, or the database migrations and RLS policies
        may not be applied. Retry the request, then check the project status.
      </p>
      <button
        type="button"
        onClick={reset}
        className="mt-5 rounded-xl bg-gold-500 px-4 py-2 text-sm font-semibold text-navy-950 transition hover:bg-gold-400"
      >
        Try again
      </button>
    </div>
  );
}
