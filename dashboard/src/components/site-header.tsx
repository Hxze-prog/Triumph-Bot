import Link from "next/link";

import { Brand } from "@/components/brand";
import { IconArrow } from "@/components/icons";

const links = [
  { href: "/#features", label: "Features" },
  { href: "/#automation", label: "Automation" },
  { href: "/command", label: "Commands" },
  { href: "/#insights", label: "Insights" },
  { href: "/#security", label: "Security" },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-navy-800/80 bg-navy-950/80 backdrop-blur">
      <div className="mx-auto flex h-20 w-full max-w-6xl items-center justify-between gap-6 px-4 sm:px-6">
        <Brand />
        <nav className="hidden items-center gap-8 text-sm text-mist-400 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="transition hover:text-mist-100"
            >
              {link.label}
            </Link>
          ))}
        </nav>
        <Link
          href="/login"
          className="inline-flex items-center gap-2 rounded-xl border border-gold-500/40 bg-gold-500/10 px-4 py-2 text-sm font-medium text-gold-400 transition hover:bg-gold-500/20"
        >
          Open dashboard
          <IconArrow className="h-4 w-4" />
        </Link>
      </div>
    </header>
  );
}
