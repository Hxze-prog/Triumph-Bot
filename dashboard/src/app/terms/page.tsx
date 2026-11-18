import type { Metadata } from "next";
import Link from "next/link";

import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export const metadata: Metadata = {
  title: "Terms of Service",
  description:
    "The terms that govern use of the Triumph Discord bot and web dashboard.",
};

const updated = "November 19, 2026";
const contact =
  "https://github.com/Hxze-prog/Triumph-Bot/issues";

export default function TermsPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <div className="mx-auto w-full max-w-3xl px-4 py-16 sm:px-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-gold-500">
            Legal
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold tracking-wide text-white sm:text-4xl">
            Terms of Service
          </h1>
          <p className="mt-2 text-sm text-mist-500">Last updated: {updated}</p>

          <div className="mt-6 rounded-xl border border-royal-400/25 bg-royal-700/15 px-4 py-3 text-sm text-mist-300">
            This document is a working template prepared for the Triumph project.
            Review it with qualified counsel and adapt it to your jurisdiction
            before relying on it in production.
          </div>

          <div className="legal mt-8">
            <p>
              These Terms of Service (&quot;Terms&quot;) govern your access to and
              use of the Triumph Discord bot, the Triumph web dashboard, and any
              related services (together, the &quot;Service&quot;). By inviting
              the bot to a Discord server, signing in to the dashboard, or
              otherwise using the Service, you agree to these Terms. If you do
              not agree, do not use the Service.
            </p>

            <h2>1. Who we are</h2>
            <p>
              The Service is operated by the Triumph project maintainers
              (&quot;Triumph&quot;, &quot;we&quot;, &quot;us&quot;, or
              &quot;our&quot;). Triumph is an independent project and is not
              affiliated with, endorsed by, or sponsored by Discord Inc.
            </p>

            <h2>2. The Service</h2>
            <p>
              Triumph provides Discord server management features, including
              moderation tools, automoderation, welcome and goodbye messaging,
              autoroles, logging, temporary voice channels, reaction roles,
              scheduled automations, statistics, and a web dashboard for
              configuration and insight. Features may be added, changed, limited,
              or removed at any time.
            </p>

            <h2>3. Eligibility and accounts</h2>
            <ul>
              <li>
                You must have a valid Discord account and comply with Discord&apos;s
                Terms of Service and Community Guidelines.
              </li>
              <li>
                Dashboard access uses Discord sign-in through Supabase Auth. You
                are responsible for activity performed through your account.
              </li>
              <li>
                To use the dashboard for a server, you must be recorded as an
                authorized administrator for that server and, where enabled,
                satisfy the server&apos;s configured administrator role checks.
              </li>
              <li>
                You must be at least the minimum age required to use Discord in
                your jurisdiction.
              </li>
            </ul>

            <h2>4. Server administrator responsibilities</h2>
            <p>
              If you add the bot to a Discord server or configure it through the
              dashboard, you represent that you have authority to do so. You are
              responsible for:
            </p>
            <ul>
              <li>
                the configuration you apply, including moderation thresholds,
                logging destinations, automation schedules, and role mappings;
              </li>
              <li>
                obtaining any notices or consents required from server members
                for logging, moderation records, and automated messaging;
              </li>
              <li>
                granting only the Discord permissions the bot needs and reviewing
                those permissions periodically.
              </li>
            </ul>

            <h2>5. Acceptable use</h2>
            <p>You agree not to use the Service to:</p>
            <ul>
              <li>
                violate any law, Discord policy, or the rights of another person;
              </li>
              <li>
                harass, threaten, defame, or discriminate against any person or
                group;
              </li>
              <li>
                distribute malware, spam, phishing content, or unsolicited bulk
                messaging;
              </li>
              <li>
                attempt to gain unauthorized access to the Service, other
                servers, accounts, or data;
              </li>
              <li>
                probe, scan, overload, or interfere with the Service or its
                infrastructure;
              </li>
              <li>
                reverse engineer or resell the Service except as permitted by
                applicable law;
              </li>
              <li>
                use the Service to collect or process sensitive personal data
                without a lawful basis.
              </li>
            </ul>
            <p>
              We may suspend or terminate access for conduct that we reasonably
              believe violates these Terms or creates risk for other users.
            </p>

            <h2>6. Bot permissions and automated actions</h2>
            <p>
              The bot acts only within the permissions granted to it in each
              server. Automated actions such as timeouts, message deletion, role
              assignment, channel creation, and scheduled messages are performed
              on your instruction or configuration. You acknowledge that
              automated moderation can produce false positives and should be
              tuned and monitored.
            </p>

            <h2>7. Fees</h2>
            <p>
              The Service is currently provided without charge. We may introduce
              paid features in the future. We will disclose pricing before
              charging for any feature, and you may choose not to use it.
            </p>

            <h2>8. Intellectual property</h2>
            <p>
              The Service, including its software, design, and documentation, is
              owned by the Triumph project and its contributors and is protected
              by applicable intellectual property laws. These Terms do not grant
              you ownership of the Service. Discord, Supabase, and other
              third-party marks belong to their respective owners.
            </p>
            <p>
              You retain ownership of the content you configure or submit. You
              grant us a limited license to store, process, and transmit that
              content solely to operate the Service.
            </p>

            <h2>9. Third-party services</h2>
            <p>
              The Service depends on third parties including Discord, Supabase,
              Render, Vercel, and UptimeRobot. Their availability, terms, and
              privacy practices are outside our control. Outages or policy changes
              at those providers may affect the Service.
            </p>

            <h2>10. Availability and changes</h2>
            <p>
              The Service is provided on an &quot;as available&quot; basis. We may
              perform maintenance, deploy updates, or change features without
              prior notice. We do not guarantee uninterrupted or error-free
              operation.
            </p>

            <h2>11. Termination</h2>
            <p>
              You may stop using the Service at any time by removing the bot from
              your server and signing out of the dashboard. We may suspend or
              terminate access if you violate these Terms, if required by law, or
              if continuing the Service would create security or legal risk.
              Provisions that by their nature should survive termination will
              survive.
            </p>

            <h2>12. Disclaimers</h2>
            <p>
              To the maximum extent permitted by law, the Service is provided
              &quot;as is&quot; and &quot;as available&quot; without warranties of
              any kind, whether express, implied, or statutory, including
              warranties of merchantability, fitness for a particular purpose,
              title, and non-infringement. We do not warrant that moderation
              decisions, automated messages, or statistics will be accurate,
              complete, or suitable for your needs.
            </p>

            <h2>13. Limitation of liability</h2>
            <p>
              To the maximum extent permitted by law, Triumph and its
              contributors will not be liable for indirect, incidental, special,
              consequential, exemplary, or punitive damages, or for lost profits,
              lost data, server disruption, or loss of goodwill, arising from or
              related to the Service. Where liability cannot be excluded, our
              aggregate liability will not exceed the greater of the amount you
              paid us in the twelve months before the claim or one hundred US
              dollars (USD 100).
            </p>

            <h2>14. Indemnity</h2>
            <p>
              You agree to indemnify and hold harmless Triumph and its
              contributors from claims, damages, liabilities, and expenses
              (including reasonable legal fees) arising from your use of the
              Service, your server configuration, or your violation of these
              Terms or applicable law.
            </p>

            <h2>15. Governing law and disputes</h2>
            <p>
              These Terms are governed by the laws applicable in the operator&apos;s
              place of establishment, without regard to conflict-of-law rules.
              Before filing a formal claim, you agree to contact us through the
              support channel so we can attempt to resolve the dispute
              informally.
            </p>

            <h2>16. Changes to these Terms</h2>
            <p>
              We may update these Terms from time to time. We will post the
              revised version on this page and update the date above. Material
              changes may also be announced in the project repository. Continued
              use of the Service after changes take effect constitutes acceptance
              of the revised Terms.
            </p>

            <h2>17. Contact</h2>
            <p>
              Questions about these Terms can be raised through the project issue
              tracker at{" "}
              <a href={contact} target="_blank" rel="noreferrer">
                github.com/Hxze-prog/Triumph-Bot/issues
              </a>
              . For privacy-specific requests, see the{" "}
              <Link href="/privacy">Privacy Policy</Link>.
            </p>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
