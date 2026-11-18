import type { SVGProps } from "react";

import type { NavIconKey } from "@/lib/nav";

type IconProps = SVGProps<SVGSVGElement>;

const base: IconProps = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.7,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
};

export function IconGrid(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  );
}

export function IconChart(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 20V10" />
      <path d="M10 20V4" />
      <path d="M16 20v-7" />
      <path d="M22 20H2" />
    </svg>
  );
}

export function IconList(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M8 6h13" />
      <path d="M8 12h13" />
      <path d="M8 18h13" />
      <circle cx="3.5" cy="6" r="1" />
      <circle cx="3.5" cy="12" r="1" />
      <circle cx="3.5" cy="18" r="1" />
    </svg>
  );
}

export function IconSliders(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 6h10" />
      <path d="M18 6h2" />
      <circle cx="16" cy="6" r="2" />
      <path d="M4 12h4" />
      <path d="M12 12h8" />
      <circle cx="10" cy="12" r="2" />
      <path d="M4 18h12" />
      <path d="M20 18h0" />
      <circle cx="18" cy="18" r="2" />
    </svg>
  );
}

export function IconWelcome(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3v3" />
      <path d="M12 18v3" />
      <path d="M4.2 7.2 6.3 9.3" />
      <path d="m17.7 14.7 2.1 2.1" />
      <path d="M3 12h3" />
      <path d="M18 12h3" />
      <circle cx="12" cy="12" r="4" />
    </svg>
  );
}

export function IconShield(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3 5 6v5c0 4.5 3 8.4 7 10 4-1.6 7-5.5 7-10V6l-7-3Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function IconHash(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 3 8 21" />
      <path d="M16 3l-2 18" />
      <path d="M4 9h16" />
      <path d="M3 15h16" />
    </svg>
  );
}

export function IconMic(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0" />
      <path d="M12 18v3" />
      <path d="M8 21h8" />
    </svg>
  );
}

export function IconClock(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </svg>
  );
}

export function IconRoles(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3 9.5 8.2 4 9l4 3.9-1 5.6L12 15.8 17 18.5l-1-5.6L20 9l-5.5-.8Z" />
    </svg>
  );
}

export function IconWarning(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 4 3 20h18L12 4Z" />
      <path d="M12 10v4" />
      <path d="M12 17h.01" />
    </svg>
  );
}

export function IconUser(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4.5 21a7.5 7.5 0 0 1 15 0" />
    </svg>
  );
}

export function IconMenu(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 7h16" />
      <path d="M4 12h16" />
      <path d="M4 17h16" />
    </svg>
  );
}

export function IconClose(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m6 6 12 12" />
      <path d="m18 6-12 12" />
    </svg>
  );
}

export function IconLogout(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M10 4H5v16h5" />
      <path d="M14 8l4 4-4 4" />
      <path d="M8 12h10" />
    </svg>
  );
}

export function IconArrow(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M5 12h14" />
      <path d="m13 6 6 6-6 6" />
    </svg>
  );
}

export function IconCheck(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m4 12 5 5L20 6" />
    </svg>
  );
}

export function IconDiscord(props: IconProps) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden {...props}>
      <path d="M19.5 5.3A16 16 0 0 0 15.6 4l-.5 1a13 13 0 0 0-6.2 0L8.4 4a16 16 0 0 0-3.9 1.3C2.1 8.6 1.5 11.8 1.8 15a15 15 0 0 0 4.8 2.4l1-1.6c-.5-.2-1-.5-1.5-.8l.4-.3c2.9 1.4 6.1 1.4 9 0l.4.3c-.5.3-1 .6-1.5.8l1 1.6A15 15 0 0 0 22.2 15c.4-3.7-.5-6.9-2.7-9.7ZM8.7 13.3c-.9 0-1.6-.8-1.6-1.8s.7-1.8 1.6-1.8 1.7.8 1.6 1.8c0 1-.7 1.8-1.6 1.8Zm6.6 0c-.9 0-1.6-.8-1.6-1.8s.7-1.8 1.6-1.8 1.7.8 1.6 1.8c0 1-.7 1.8-1.6 1.8Z" />
    </svg>
  );
}

const ICONS: Record<NavIconKey, (props: IconProps) => React.JSX.Element> = {
  grid: IconGrid,
  chart: IconChart,
  list: IconList,
  sliders: IconSliders,
  welcome: IconWelcome,
  shield: IconShield,
  hash: IconHash,
  mic: IconMic,
  clock: IconClock,
  roles: IconRoles,
  warning: IconWarning,
  user: IconUser,
};

export function NavIcon({
  name,
  ...props
}: IconProps & { name: NavIconKey }) {
  const Component = ICONS[name];
  return <Component {...props} />;
}
