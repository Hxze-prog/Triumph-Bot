import type { ReactNode } from "react";

import type { ActionState } from "@/lib/settings";

export const inputClass =
  "w-full rounded-lg border border-navy-700 bg-navy-950/70 px-3 py-2 text-sm text-mist-100 placeholder:text-mist-500 transition focus:border-gold-500/60 focus:outline-none disabled:opacity-60";

export function Field({
  label,
  hint,
  htmlFor,
  children,
  className = "",
}: {
  label: string;
  hint?: string;
  htmlFor?: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`space-y-1.5 ${className}`}>
      <label
        htmlFor={htmlFor}
        className="block text-sm font-medium text-mist-200"
      >
        {label}
      </label>
      {children}
      {hint ? <p className="text-xs text-mist-500">{hint}</p> : null}
    </div>
  );
}

export function CheckboxCard({
  name,
  label,
  hint,
  defaultChecked,
}: {
  name: string;
  label: string;
  hint?: string;
  defaultChecked?: boolean;
}) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-navy-700/70 bg-navy-950/40 p-3.5 transition hover:border-gold-500/30">
      <input
        type="checkbox"
        name={name}
        defaultChecked={defaultChecked}
        className="mt-0.5 h-4 w-4 rounded border-navy-600 bg-navy-900 accent-gold-500"
      />
      <span>
        <span className="block text-sm font-medium text-mist-200">{label}</span>
        {hint ? <span className="mt-0.5 block text-xs text-mist-500">{hint}</span> : null}
      </span>
    </label>
  );
}

export function ChannelSelect({
  name,
  defaultValue,
  options,
  available,
  noneLabel = "Not set",
}: {
  name: string;
  defaultValue: string | null;
  options: Array<{ id: string; name: string }>;
  available: boolean;
  noneLabel?: string;
}) {
  if (!available) {
    return (
      <input
        name={name}
        defaultValue={defaultValue ?? ""}
        placeholder="Discord channel ID"
        inputMode="numeric"
        className={inputClass}
      />
    );
  }

  const known = options.some((option) => option.id === defaultValue);
  return (
    <select name={name} defaultValue={defaultValue ?? ""} className={inputClass}>
      <option value="">{noneLabel}</option>
      {!known && defaultValue ? (
        <option value={defaultValue}>Unknown channel ({defaultValue})</option>
      ) : null}
      {options.map((option) => (
        <option key={option.id} value={option.id}>
          #{option.name}
        </option>
      ))}
    </select>
  );
}

export function ActionFeedback({ state }: { state: ActionState }) {
  if (state.status === "idle") {
    return null;
  }
  const tone =
    state.status === "success"
      ? "border-emerald-400/25 bg-emerald-400/5 text-emerald-200"
      : "border-rose-400/25 bg-rose-400/5 text-rose-200";
  return (
    <p
      aria-live="polite"
      className={`rounded-xl border px-4 py-3 text-sm ${tone}`}
    >
      {state.message}
    </p>
  );
}
