import type { Metadata } from "next";
import { Cinzel, Inter } from "next/font/google";

import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const cinzel = Cinzel({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-cinzel",
  display: "swap",
});

const appUrl = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(appUrl),
  title: {
    default: "Triumph — Discord management, elevated",
    template: "%s | Triumph",
  },
  description:
    "Triumph is a Discord management platform for moderation, onboarding, logging, automation, temporary voice, and server insights.",
  openGraph: {
    title: "Triumph — Discord management, elevated",
    description:
      "A command center for serious Discord communities: moderation, onboarding, logging, automation, and live server insight.",
    url: appUrl,
    siteName: "Triumph",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Triumph — Discord management, elevated",
    description:
      "A command center for serious Discord communities: moderation, onboarding, logging, automation, and live server insight.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${inter.variable} ${cinzel.variable}`}>
      <body className="min-h-screen bg-navy-950 text-mist-100 antialiased">
        {children}
      </body>
    </html>
  );
}
