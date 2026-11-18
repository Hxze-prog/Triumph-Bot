"use client";

import { useState } from "react";

import { IconDiscord } from "@/components/icons";
import { createClient } from "@/lib/supabase/client";

export function LoginForm({
  next,
  configured,
}: {
  next: string;
  configured: boolean;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function signIn() {
    setLoading(true);
    setError(null);
    try {
      const supabase = createClient();
      const redirectTo = `${window.location.origin}/auth/callback?next=${encodeURIComponent(next)}`;
      const { error: authError } = await supabase.auth.signInWithOAuth({
        provider: "discord",
        options: { redirectTo },
      });
      if (authError) {
        setError(authError.message);
        setLoading(false);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Sign in could not be started. Check the dashboard environment variables.",
      );
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <button
        type="button"
        onClick={signIn}
        disabled={!configured || loading}
        className="inline-flex w-full items-center justify-center gap-3 rounded-xl bg-[#5865F2] px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-[#4752c4] disabled:cursor-not-allowed disabled:opacity-50"
      >
        <IconDiscord className="h-5 w-5" />
        {loading ? "Redirecting to Discord…" : "Continue with Discord"}
      </button>
      {!configured ? (
        <p className="rounded-xl border border-amber-400/25 bg-amber-400/5 px-4 py-3 text-sm text-amber-200/90">
          Supabase environment variables are missing. Copy{" "}
          <code className="text-amber-100">.env.example</code> to{" "}
          <code className="text-amber-100">.env.local</code> and set the project
          URL and anon key.
        </p>
      ) : null}
      {error ? (
        <p className="rounded-xl border border-rose-400/25 bg-rose-400/5 px-4 py-3 text-sm text-rose-200">
          {error}
        </p>
      ) : null}
    </div>
  );
}
