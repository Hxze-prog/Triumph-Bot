export type NavIconKey =
  | "grid"
  | "chart"
  | "list"
  | "sliders"
  | "welcome"
  | "shield"
  | "hash"
  | "mic"
  | "clock"
  | "roles"
  | "warning"
  | "user";

export type NavItem = {
  href: string;
  label: string;
  icon: NavIconKey;
};

export type NavSection = {
  label: string;
  items: NavItem[];
};

export const navSections: NavSection[] = [
  {
    label: "Overview",
    items: [{ href: "/dashboard", label: "Command center", icon: "grid" }],
  },
  {
    label: "Insights",
    items: [
      { href: "/dashboard/statistics", label: "Statistics", icon: "chart" },
      { href: "/dashboard/activity", label: "Activity logs", icon: "list" },
    ],
  },
  {
    label: "Settings",
    items: [
      { href: "/dashboard/settings", label: "Overview", icon: "sliders" },
      { href: "/dashboard/settings/welcome", label: "Welcome", icon: "welcome" },
      { href: "/dashboard/settings/moderation", label: "Moderation", icon: "shield" },
      { href: "/dashboard/settings/logging", label: "Logging", icon: "hash" },
      { href: "/dashboard/settings/temp-voice", label: "Temp voice", icon: "mic" },
    ],
  },
  {
    label: "Management",
    items: [
      { href: "/dashboard/management", label: "Overview", icon: "user" },
      { href: "/dashboard/management/automations", label: "Automations", icon: "clock" },
      { href: "/dashboard/management/reaction-roles", label: "Reaction roles", icon: "roles" },
      { href: "/dashboard/management/warnings", label: "Warnings", icon: "warning" },
    ],
  },
];
