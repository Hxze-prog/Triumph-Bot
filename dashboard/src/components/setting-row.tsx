import type { ReactNode } from "react";

export function SettingRow({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 border-b border-navy-800/70 py-3.5 last:border-0">
      <div>
        <p className="text-sm font-medium text-mist-200">{label}</p>
        {hint ? <p className="mt-0.5 text-xs text-mist-500">{hint}</p> : null}
      </div>
      <div className="text-right text-sm text-mist-300">{value}</div>
    </div>
  );
}
