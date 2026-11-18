import type { ReactNode } from "react";

export function StatCard({
  label,
  value,
  hint,
  icon,
  accent = false,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border p-5 ${
        accent
          ? "border-gold-500/30 bg-gradient-to-br from-navy-900 via-navy-900 to-royal-700/25"
          : "border-navy-700/80 bg-navy-900/60"
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-mist-500">
          {label}
        </p>
        {icon ? <span className="text-gold-500">{icon}</span> : null}
      </div>
      <p className="mt-3 font-display text-3xl font-semibold text-white">
        {value}
      </p>
      {hint ? <p className="mt-2 text-xs text-mist-400">{hint}</p> : null}
    </div>
  );
}
