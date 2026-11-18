"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { Badge } from "@/components/badge";
import { Brand } from "@/components/brand";
import { IconClose, IconLogout, IconMenu, NavIcon } from "@/components/icons";
import { navSections } from "@/lib/nav";

type ShellUser = {
  name: string;
  avatarUrl: string | null;
  role: string;
};

type ShellGuild = {
  id: string;
  name: string;
};

type ShellVerification = {
  state: "verified" | "unavailable" | "not_member" | "missing_role";
  detail: string;
};

function isActive(pathname: string, href: string): boolean {
  if (
    href === "/dashboard" ||
    href.endsWith("/settings") ||
    href.endsWith("/management")
  ) {
    return pathname === href;
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function DashboardShell({
  user,
  guild,
  verification,
  children,
}: {
  user: ShellUser;
  guild: ShellGuild;
  verification: ShellVerification;
  children: ReactNode;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const nav = (
    <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
      {navSections.map((section) => (
        <div key={section.label}>
          <p className="px-3 text-[10px] font-semibold uppercase tracking-[0.24em] text-mist-500">
            {section.label}
          </p>
          <ul className="mt-2 space-y-1">
            {section.items.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm transition ${
                      active
                        ? "bg-royal-700/25 text-mist-100 shadow-[inset_0_0_0_1px_rgba(167,139,250,0.18)]"
                        : "text-mist-400 hover:bg-navy-800/60 hover:text-mist-100"
                    }`}
                  >
                    <NavIcon
                      name={item.icon}
                      className={`h-4 w-4 ${active ? "text-gold-400" : "text-mist-500"}`}
                    />
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );

  const sidebarBody = (
    <div className="flex h-full flex-col border-r border-navy-800/80 bg-navy-950/95">
      <div className="flex h-20 items-center justify-between px-4">
        <Brand />
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-lg border border-navy-700 p-2 text-mist-400 lg:hidden"
          aria-label="Close navigation"
        >
          <IconClose className="h-4 w-4" />
        </button>
      </div>
      {nav}
      <div className="border-t border-navy-800/80 p-3">
        <div className="flex items-center gap-3 rounded-xl bg-navy-900/60 px-3 py-3">
          {user.avatarUrl ? (
            <Image
              src={user.avatarUrl}
              alt={user.name}
              width={36}
              height={36}
              className="h-9 w-9 rounded-full border border-navy-700 object-cover"
            />
          ) : (
            <span className="flex h-9 w-9 items-center justify-center rounded-full border border-navy-700 bg-navy-800 text-sm font-semibold text-mist-300">
              {user.name.slice(0, 1).toUpperCase()}
            </span>
          )}
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-mist-100">
              {user.name}
            </p>
            <p className="text-[11px] uppercase tracking-[0.16em] text-mist-500">
              {user.role}
            </p>
          </div>
        </div>
        <form action="/auth/signout" method="post" className="mt-2">
          <button
            type="submit"
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm text-mist-400 transition hover:bg-navy-800/60 hover:text-mist-100"
          >
            <IconLogout className="h-4 w-4 text-mist-500" />
            Sign out
          </button>
        </form>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[18rem_1fr]">
      <aside className="hidden lg:block">{sidebarBody}</aside>

      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            className="absolute inset-0 bg-navy-950/80 backdrop-blur-sm"
            onClick={() => setOpen(false)}
            aria-label="Close navigation overlay"
          />
          <div className="absolute inset-y-0 left-0 w-72 max-w-[85vw]">
            {sidebarBody}
          </div>
        </div>
      ) : null}

      <div className="flex min-h-screen flex-col">
        <header className="sticky top-0 z-30 border-b border-navy-800/80 bg-navy-950/80 backdrop-blur">
          <div className="flex h-16 items-center justify-between gap-3 px-4 sm:px-6 lg:px-10">
            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setOpen(true)}
                className="rounded-lg border border-navy-700 p-2 text-mist-300 lg:hidden"
                aria-label="Open navigation"
              >
                <IconMenu className="h-4 w-4" />
              </button>
              <div className="min-w-0">
                <p className="text-[10px] uppercase tracking-[0.24em] text-mist-500">
                  Server
                </p>
                <p className="truncate font-display text-sm font-semibold tracking-wide text-mist-100">
                  {guild.name}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge
                tone={verification.state === "verified" ? "success" : "muted"}
              >
                {verification.state === "verified"
                  ? "Discord verified"
                  : "Verification limited"}
              </Badge>
              <Badge tone="gold">Phase 11</Badge>
            </div>
          </div>
        </header>

        <main className="flex-1 px-4 py-8 sm:px-6 lg:px-10">
          <div className="mx-auto w-full max-w-6xl space-y-8">{children}</div>
        </main>

        <footer className="border-t border-navy-800/70 px-4 py-5 text-xs text-mist-500 sm:px-6 lg:px-10">
          <div className="mx-auto flex w-full max-w-6xl flex-wrap items-center justify-between gap-2">
            <p>{verification.detail}</p>
            <p>Read-only preview · guild {guild.id}</p>
          </div>
        </footer>
      </div>
    </div>
  );
}
