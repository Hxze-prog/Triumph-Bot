import type { ReactNode } from "react";

export function Panel({
  title,
  description,
  action,
  children,
  className = "",
  bodyClassName = "",
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section
      className={`rounded-2xl border border-navy-700/80 bg-navy-900/60 shadow-[0_24px_60px_-40px_rgba(6,9,23,0.9)] backdrop-blur ${className}`}
    >
      {title || description || action ? (
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-navy-700/70 px-5 py-4 sm:px-6">
          <div>
            {title ? (
              <h2 className="font-display text-base font-semibold tracking-wide text-mist-100">
                {title}
              </h2>
            ) : null}
            {description ? (
              <p className="mt-1 text-sm text-mist-400">{description}</p>
            ) : null}
          </div>
          {action}
        </header>
      ) : null}
      <div className={`px-5 py-5 sm:px-6 ${bodyClassName}`}>{children}</div>
    </section>
  );
}
