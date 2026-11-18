import type { ReactNode } from "react";

export type BadgeTone = "gold" | "royal" | "success" | "danger" | "muted";

const TONES: Record<BadgeTone, string> = {
  gold: "border-gold-500/30 bg-gold-500/10 text-gold-400",
  royal: "border-royal-400/30 bg-royal-400/10 text-royal-400",
  success: "border-emerald-400/30 bg-emerald-400/10 text-emerald-300",
  danger: "border-rose-400/30 bg-rose-400/10 text-rose-300",
  muted: "border-navy-700 bg-navy-800/60 text-mist-400",
};

export function Badge({
  children,
  tone = "muted",
  className = "",
}: {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.14em] ${TONES[tone]} ${className}`}
    >
      {children}
    </span>
  );
}
