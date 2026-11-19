# Maintenance Procedures

Production services:

| Service | Purpose | Dashboard |
| --- | --- | --- |
| Render | Discord bot and `/health` API | Render service logs |
| Vercel | Next.js dashboard | Vercel deployments |
| Supabase | PostgreSQL, Auth, RLS | Supabase project |
| UptimeRobot | Availability checks | UptimeRobot monitors |

Live health: <https://triumph-bot.onrender.com/health>

Live dashboard: <https://triumph-bot-bice.vercel.app>

## Routine schedule

### Daily

- Confirm UptimeRobot shows both monitors up.
- Check Render for restart loops or repeated exceptions.
- Check the dashboard command center for unusual warning/activity spikes.
- Confirm backups are still running under Supabase Database > Backups.

### Weekly

- Review Vercel and Render deployments for failed builds or rolled-back releases.
- Review Supabase database usage, storage, and connection counts.
- Read new entries in `moderation_logs` and `activity_logs`.
- Run the deployment smoke check:

```powershell
.\scripts\verify_deployment.ps1 `
  -DashboardUrl "https://triumph-bot-bice.vercel.app" `
  -BotHealthUrl "https://triumph-bot.onrender.com/health"
```

### Monthly

- Create and store a logical database export outside the repository.
- Review dashboard administrators and remove stale `dashboard_admins` rows.
- Review Discord roles, channel permissions, and bot permissions.
- Check dependency updates for Next.js, React, Supabase, discord.py, Flask, and
  Pillow. Do not upgrade Next.js major versions without a full build and dashboard
  regression test.
- Rotate any credential that may have been exposed or shared.
- Review UptimeRobot alert contacts and test one notification.

## Availability checks

`/health` returns HTTP 200 while the Flask process is running, even if Discord is
not ready. Inspect fields:

- `status` should be `ok`.
- `discord_configured` should be `true`.
- `supabase_configured` should be `true`.
- `bot_ready` should be `true` after the gateway connects.
- `guilds` should match the expected number of servers.

Alert on HTTP failure. If keyword monitoring is available, use the exact fragment
`"bot_ready":true`, not the bare word `bot_ready`.

Render free services can spin down when idle. UptimeRobot keeps requests flowing,
but review Render workspace limits before promising 24/7 uptime.

## Database maintenance

### Backups

Keep both layers:

1. Supabase managed backups with the retention required by the project.
2. Periodic logical exports stored outside the repository.

Before a destructive migration, upgrade, or bulk cleanup, create a fresh backup
and record the restore point. Never commit a `.dump`, `.sql` export, or CSV
containing member data.

### Data hygiene

- Test guild data must not remain in production after migration. See
  [MIGRATION.md](MIGRATION.md).
- Delete stale temp-voice records only after confirming the channels are gone in
  Discord.
- Do not manually edit bot-generated history unless correcting a known incident.
- Keep Supabase Auth users; deleting them removes linked `dashboard_admins` rows.
- Use forward-only schema changes. Add files under `supabase/migrations/`; do not
  edit an applied migration.

### RLS

After any schema or policy change:

1. Re-run `supabase/migrations/0003_grants.sql` if grants were changed.
2. Verify anonymous REST reads return zero rows.
3. Verify an authenticated admin sees only their guild.
4. Verify a non-admin cannot read another guild.
5. Record the result in `Live_verification.md`.

## Secret rotation

Secrets live in Render and Vercel environment variables. They must never be
committed.

### Discord token

1. Reset the token in the Discord Developer Portal.
2. Update `DISCORD_TOKEN` in Render.
3. Update `DISCORD_BOT_TOKEN` in Vercel if used.
4. Redeploy both services.
5. Confirm `/health` reports `bot_ready=true`.
6. Revoke the old token only after the new one is healthy.

### Supabase service-role key

1. Rotate the key in Supabase.
2. Update `SUPABASE_SERVICE_ROLE_KEY` in Render.
3. Redeploy and verify `/health` reports `supabase_configured=true`.
4. Confirm the dashboard still reads data with the anon key.

### Supabase anon key

1. Rotate in Supabase.
2. Update `NEXT_PUBLIC_SUPABASE_ANON_KEY` in Vercel.
3. Redeploy Vercel; `NEXT_PUBLIC_*` values are embedded at build time.

## Incident response

1. Check UptimeRobot and `/health`.
2. Check Render logs for crash, token, gateway, or Supabase errors.
3. Check Vercel deployment status and function logs.
4. Check Supabase status, database usage, and auth errors.
5. If the bot is down, restart the Render service. A restart also exercises
   scheduler and temp-voice reconciliation.
6. If a bad deploy caused the incident, roll back:
   - Render: redeploy the previous successful commit.
   - Vercel: promote the previous deployment.
   - Supabase: restore a tested backup only during a planned window.
7. Record the cause, fix, and follow-up in `task.txt`.

## Rollback

- **Bot:** promote a previous Render deploy or revert the commit and redeploy.
- **Dashboard:** promote the previous Vercel deployment.
- **Database:** restore the latest verified backup. Prefer forward migrations for
  schema fixes.
- **Guild migration:** follow the rollback section in
  [MIGRATION.md](MIGRATION.md).

## Quality checks

Run before every release:

```powershell
cd bot
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m compileall .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\verify_command_inventory.py
```

```powershell
cd dashboard
npm run typecheck
npm run build
```

Keep the command inventory at 95 across the bot and dashboard. Update
[COMMANDS.md](COMMANDS.md) and `Live_verification.*` when commands change.

### Known dependency advisory

`npm audit --omit=dev` flags PostCSS advisories nested under Next.js 15.5.29.
The offered fix is a forced major upgrade to Next.js 16.4.6, which requires a
full dashboard regression pass. The affected CSS is repository-controlled, so
the practical exposure is low. Recheck the advisory after each Next.js release
and upgrade when a patched 15.x release is available or after testing 16.x.

Production responses include HSTS plus `X-Content-Type-Options`,
`X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy` from
`dashboard/next.config.ts`.

## Related documentation

- [Deployment](DEPLOYMENT.md)
- [Dashboard usage](DASHBOARD.md)
- [Command reference](COMMANDS.md)
- [Test-to-production migration](MIGRATION.md)
