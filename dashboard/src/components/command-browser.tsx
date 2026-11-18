"use client";

import { useMemo, useState, type ReactNode } from "react";

import { Badge } from "@/components/badge";
import type { BotCommand, CommandGroup } from "@/lib/commands";

function permissionTone(permission: string | undefined) {
  const value = (permission ?? "Everyone").toLowerCase();
  if (value === "everyone") return "muted" as const;
  if (value.includes("owner")) return "danger" as const;
  return "royal" as const;
}

function matches(command: BotCommand, query: string): boolean {
  if (!query) return true;
  const haystack = [
    command.name,
    command.usage,
    command.description,
    ...(command.aliases ?? []),
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query);
}

export function CommandBrowser({
  groups,
  total,
}: {
  groups: CommandGroup[];
  total: number;
}) {
  const [query, setQuery] = useState("");
  const [active, setActive] = useState("all");

  const normalized = query.trim().toLowerCase();

  const filtered = useMemo(
    () =>
      groups
        .filter((group) => active === "all" || group.id === active)
        .map((group) => ({
          ...group,
          commands: group.commands.filter((command) =>
            matches(command, normalized),
          ),
        }))
        .filter((group) => group.commands.length > 0),
    [groups, active, normalized],
  );

  const visible = filtered.reduce(
    (sum, group) => sum + group.commands.length,
    0,
  );

  return (
    <div>
      <div className="flex flex-col gap-3 rounded-2xl border border-navy-700/80 bg-navy-900/50 p-4 sm:flex-row sm:items-center sm:justify-between">
        <label className="relative w-full sm:max-w-sm">
          <span className="sr-only">Search commands</span>
          <svg
            aria-hidden
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-mist-500"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" strokeLinecap="round" />
          </svg>
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by name, usage, or alias"
            className="w-full rounded-xl border border-navy-700 bg-navy-950/80 py-2.5 pl-9 pr-3 text-sm text-mist-100 outline-none transition placeholder:text-mist-500 focus:border-gold-500/50"
          />
        </label>
        <p className="text-xs uppercase tracking-[0.16em] text-mist-500">
          {visible} of {total} commands
        </p>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <FilterButton
          active={active === "all"}
          onClick={() => setActive("all")}
        >
          All
        </FilterButton>
        {groups.map((group) => (
          <FilterButton
            key={group.id}
            active={active === group.id}
            onClick={() => setActive(group.id)}
          >
            {group.title}
          </FilterButton>
        ))}
      </div>

      <div className="mt-10 space-y-12">
        {filtered.map((group) => (
          <section key={group.id} id={group.id} className="scroll-mt-28">
            <div className="flex flex-wrap items-end justify-between gap-3 border-b border-navy-800 pb-4">
              <div>
                <h2 className="font-display text-xl font-semibold tracking-wide text-white">
                  {group.title}
                </h2>
                <p className="mt-1 text-sm text-mist-400">{group.description}</p>
              </div>
              <span className="text-[11px] uppercase tracking-[0.18em] text-mist-500">
                {group.commands.length} command
                {group.commands.length === 1 ? "" : "s"}
              </span>
            </div>
            <div className="mt-5 grid gap-3 md:grid-cols-2">
              {group.commands.map((command) => (
                <article
                  key={command.name}
                  className="rounded-2xl border border-navy-700/80 bg-navy-900/50 p-5 transition hover:border-gold-500/30 hover:bg-navy-900/80"
                >
                  <div className="flex items-start justify-between gap-3">
                    <h3 className="font-mono text-sm font-medium text-gold-400">
                      {command.name}
                    </h3>
                    <Badge tone={permissionTone(command.permission)}>
                      {command.permission ?? "Everyone"}
                    </Badge>
                  </div>
                  <code className="mt-3 block overflow-x-auto rounded-lg border border-navy-800 bg-navy-950/80 px-3 py-2 font-mono text-xs text-mist-200">
                    {command.usage}
                  </code>
                  <p className="mt-3 text-sm leading-relaxed text-mist-400">
                    {command.description}
                  </p>
                  {command.aliases?.length ? (
                    <p className="mt-3 text-xs text-mist-500">
                      Aliases:{" "}
                      <span className="text-mist-300">
                        {command.aliases.join(", ")}
                      </span>
                    </p>
                  ) : null}
                </article>
              ))}
            </div>
          </section>
        ))}

        {filtered.length === 0 ? (
          <div className="rounded-2xl border border-navy-700/80 bg-navy-900/40 px-6 py-14 text-center">
            <p className="font-display text-lg text-mist-200">
              No commands match that search.
            </p>
            <p className="mt-2 text-sm text-mist-500">
              Try a different name, alias, or category.
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function FilterButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full border px-3.5 py-1.5 text-xs font-medium transition ${
        active
          ? "border-gold-500/50 bg-gold-500/15 text-gold-400"
          : "border-navy-700 bg-navy-900/40 text-mist-400 hover:border-gold-500/30 hover:text-mist-100"
      }`}
    >
      {children}
    </button>
  );
}
