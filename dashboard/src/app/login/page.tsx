import type { Metadata } from "next";
import Link from "next/link";

import { Brand } from "@/components/brand";
import { Badge } from "@/components/badge";
import { LoginForm } from "@/components/login-form";
import { isSupabaseConfigured } from "@/lib/env";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Sign in to the Triumph dashboard with Discord.",
};

function safeNext(value: string | undefined): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return "/dashboard";
  }
  return value;
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; error?: string }>;
}) {
  const params = await searchParams;
  const next = safeNext(params.next);
  const error = params.error;

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
      <div className="flex flex-col justify-between px-5 py-8 sm:px-10 sm:py-10">
        <div className="flex items-center justify-between">
          <Brand />
          <Link
            href="/"
            className="text-sm text-mist-400 transition hover:text-mist-100"
          >
            Back to site
          </Link>
        </div>

        <div className="mx-auto w-full max-w-md py-14">
          <Badge tone="gold">Administrator access</Badge>
          <h1 className="mt-5 font-display text-3xl font-semibold tracking-wide text-white">
            Sign in to Triumph
          </h1>
          <p className="mt-3 text-sm leading-relaxed text-mist-400">
            Use the Discord account that is registered as an administrator for
            your server. Access is verified against{" "}
            <code className="text-mist-300">dashboard_admins</code> and, when
            configured, live Discord membership and role checks.
          </p>

          {error ? (
            <p className="mt-5 rounded-xl border border-rose-400/25 bg-rose-400/5 px-4 py-3 text-sm text-rose-200">
              {decodeURIComponent(error)}
            </p>
          ) : null}

          <div className="mt-8">
            <LoginForm next={next} configured={isSupabaseConfigured} />
          </div>

          <p className="mt-6 text-xs leading-relaxed text-mist-500">
            By continuing you agree to the{" "}
            <Link href="/terms" className="text-gold-400 underline underline-offset-2">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/privacy" className="text-gold-400 underline underline-offset-2">
              Privacy Policy
            </Link>
            .
          </p>
        </div>

        <p className="text-xs text-mist-500">
          Having trouble? Confirm the Supabase Discord provider and redirect URLs,
          then ask a server owner to register your Discord ID.
        </p>
      </div>

      <div className="relative hidden overflow-hidden border-l border-navy-800/80 bg-navy-900/40 lg:block">
        <div
          aria-hidden
          className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(124,58,237,0.28),transparent_55%),radial-gradient(ellipse_at_bottom_left,rgba(212,175,55,0.14),transparent_50%)]"
        />
        <div className="relative flex h-full flex-col justify-center px-12 xl:px-16">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-gold-500">
            Command center
          </p>
          <h2 className="mt-4 max-w-md font-display text-3xl font-semibold leading-tight tracking-wide text-white">
            One account. One server. Everything in view.
          </h2>
          <ul className="mt-8 space-y-4 text-sm text-mist-300">
            {[
              "Overview of members, warnings, voice rooms, and automations",
              "Live statistics snapshots and a unified activity trail",
              "Server-scoped RLS so administrators see only their own data",
            ].map((item) => (
              <li key={item} className="flex items-start gap-3">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-gold-500" />
                {item}
              </li>
            ))}
          </ul>
          <div className="mt-12 rounded-2xl border border-navy-700/80 bg-navy-950/60 p-5 text-xs text-mist-400">
            <p className="uppercase tracking-[0.22em] text-mist-500">
              Access checklist
            </p>
            <p className="mt-3">
              Discord OAuth provider enabled in Supabase · redirect URLs allowed ·
              a dashboard_admins row linked to your Discord ID.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
