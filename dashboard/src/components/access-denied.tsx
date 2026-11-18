import Link from "next/link";

import { Brand } from "@/components/brand";
import { IconLogout } from "@/components/icons";

export function AccessDenied({
  reason,
  userName,
}: {
  reason: string;
  userName?: string | null;
}) {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-16">
      <div className="w-full max-w-lg rounded-2xl border border-navy-700 bg-navy-900/70 p-8 shadow-[0_40px_100px_-60px_rgba(0,0,0,0.9)]">
        <Brand href={null} />
        <p className="mt-8 text-[11px] font-semibold uppercase tracking-[0.28em] text-gold-500">
          Dashboard access
        </p>
        <h1 className="mt-2 font-display text-2xl font-semibold text-white">
          Access could not be granted
        </h1>
        {userName ? (
          <p className="mt-2 text-sm text-mist-400">Signed in as {userName}.</p>
        ) : null}
        <p className="mt-4 rounded-xl border border-rose-400/20 bg-rose-400/5 px-4 py-3 text-sm leading-relaxed text-mist-300">
          {reason}
        </p>
        <div className="mt-6 space-y-3 text-sm text-mist-400">
          <p>
            Dashboard access requires a Supabase Discord session plus a matching
            row in <code className="text-mist-300">dashboard_admins</code>.
          </p>
          <p>
            Ask a server owner to register your Discord ID, or confirm the
            Supabase Auth Discord provider is enabled.
          </p>
        </div>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-xl border border-navy-700 px-4 py-2 text-sm text-mist-300 transition hover:border-gold-500/40 hover:text-mist-100"
          >
            Back to site
          </Link>
          <form action="/auth/signout" method="post">
            <button
              type="submit"
              className="inline-flex items-center gap-2 rounded-xl border border-gold-500/40 bg-gold-500/10 px-4 py-2 text-sm font-medium text-gold-400 transition hover:bg-gold-500/20"
            >
              <IconLogout className="h-4 w-4" />
              Sign out
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
