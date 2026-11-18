import Link from "next/link";

import { Brand } from "@/components/brand";

const columns = [
  {
    label: "Product",
    links: [
      { href: "/#features", label: "Features" },
      { href: "/#automation", label: "Automation" },
      { href: "/command", label: "Commands" },
      { href: "/#insights", label: "Insights" },
      { href: "/login", label: "Dashboard" },
    ],
  },
  {
    label: "Legal",
    links: [
      { href: "/terms", label: "Terms of Service" },
      { href: "/privacy", label: "Privacy Policy" },
    ],
  },
  {
    label: "Project",
    links: [
      {
        href: "https://github.com/Hxze-prog/Triumph-Bot",
        label: "GitHub",
      },
      {
        href: "https://github.com/Hxze-prog/Triumph-Bot/issues",
        label: "Support",
      },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-navy-800/80 bg-navy-950">
      <div className="mx-auto grid w-full max-w-6xl gap-10 px-4 py-14 sm:px-6 md:grid-cols-[1.4fr_repeat(3,1fr)]">
        <div>
          <Brand />
          <p className="mt-5 max-w-xs text-sm leading-relaxed text-mist-400">
            A command center for Discord communities: moderation, onboarding,
            logging, automation, temporary voice, and server insight.
          </p>
        </div>
        {columns.map((column) => (
          <div key={column.label}>
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-mist-500">
              {column.label}
            </p>
            <ul className="mt-4 space-y-2.5 text-sm">
              {column.links.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-mist-400 transition hover:text-mist-100"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="border-t border-navy-800/70">
        <div className="mx-auto flex w-full max-w-6xl flex-col gap-2 px-4 py-6 text-xs text-mist-500 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p>© {new Date().getFullYear()} Triumph. All rights reserved.</p>
          <p>Triumph is not affiliated with Discord Inc.</p>
        </div>
      </div>
    </footer>
  );
}
