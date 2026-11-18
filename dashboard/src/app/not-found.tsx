import Link from "next/link";

import { Brand } from "@/components/brand";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-lg rounded-2xl border border-navy-700 bg-navy-900/70 p-8">
        <Brand href={null} />
        <p className="mt-8 text-[11px] font-semibold uppercase tracking-[0.28em] text-gold-500">
          404
        </p>
        <h1 className="mt-2 font-display text-2xl font-semibold text-white">
          Page not found
        </h1>
        <p className="mt-3 text-sm text-mist-400">
          The route you requested does not exist in the dashboard.
        </p>
        <Link
          href="/"
          className="mt-6 inline-flex rounded-xl bg-gold-500 px-4 py-2 text-sm font-semibold text-navy-950 transition hover:bg-gold-400"
        >
          Return home
        </Link>
      </div>
    </div>
  );
}
