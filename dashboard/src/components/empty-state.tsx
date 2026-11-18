import type { ReactNode } from "react";

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-navy-700 bg-navy-950/40 px-6 py-12 text-center">
      <p className="font-display text-base font-semibold tracking-wide text-mist-100">
        {title}
      </p>
      {description ? (
        <p className="mt-2 max-w-md text-sm text-mist-400">{description}</p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
