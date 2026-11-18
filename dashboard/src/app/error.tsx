"use client";

import { useEffect } from "react";

export default function GlobalError({
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
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-lg rounded-2xl border border-navy-700 bg-navy-900/70 p-8">
        <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-gold-500">
          Something went wrong
        </p>
        <h1 className="mt-2 font-display text-2xl font-semibold text-white">
          This page could not be rendered
        </h1>
        <p className="mt-3 text-sm leading-relaxed text-mist-400">
          The error has been logged by the dashboard. You can retry the render or
          return to the homepage.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            type="button"
            onClick={reset}
            className="rounded-xl bg-gold-500 px-4 py-2 text-sm font-semibold text-navy-950 transition hover:bg-gold-400"
          >
            Try again
          </button>
          <a
            href="/"
            className="rounded-xl border border-navy-700 px-4 py-2 text-sm text-mist-300 transition hover:border-gold-500/40 hover:text-mist-100"
          >
            Back to site
          </a>
        </div>
      </div>
    </div>
  );
}
