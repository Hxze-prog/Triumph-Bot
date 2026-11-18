# Deployment Runbook (Phase 13)

Production topology:

| Component | Host | Notes |
| --- | --- | --- |
| Discord bot + Flask health API | Render web service | `render.yaml`, `bot/` root directory |
| Dashboard | Vercel | Next.js app in `dashboard/` |
| Database + Auth | Supabase | PostgreSQL, RLS, Discord OAuth |
| Uptime monitoring | UptimeRobot | HTTP monitor for Render `/health` |

Phase 13 went live on 2026-11-19:

| Live endpoint | URL | Status |
| --- | --- | --- |
| Dashboard | <https://triumph-bot-bice.vercel.app> | Live; GitHub auto-deploy successful |
| Bot health | <https://triumph-bot.onrender.com/health> | `200`; `bot_ready=true`, `guilds=1` |
| Monitoring | UptimeRobot | Both 5-minute monitors up |

Discord OAuth, the production callback, Supabase connectivity, and anonymous RLS
blocking were verified against these endpoints. Restart persistence and the full
command smoke checks are tracked in Phase 14; backup/export execution remains an
operational maintenance action.

The procedures below remain the source of truth for rebuilds, key rotation, and
recovery.

> The local repository must be committed and pushed to
> `https://github.com/Hxze-prog/Triumph-Bot.git` before either host can deploy.
> Do not commit `.env`, `bot/.env`, `dashboard/.env.local`, or `session.txt`.

---

## 1. Supabase production database

### 1.1 Apply the schema

Apply these files in order in the Supabase SQL editor:

1. `supabase/migrations/0001_initial_schema.sql`
2. `supabase/migrations/0002_rls_policies.sql`
3. `supabase/migrations/0003_grants.sql`

All three are required. `0003_grants.sql` grants the dashboard's
`anon`/`authenticated` roles access to the tables created through the SQL editor.

### 1.2 Verify RLS

Run `supabase/tests/rls_checks.sql` in the SQL editor. Confirm:

- Service-role/postgres context can read all rows.
- An `authenticated` user cannot read or update another guild's rows.
- An `anon` user cannot read protected rows.
- Cleanup at the end of the test removes the temporary rows.

If a dashboard query fails with `42501 permission denied for table`, re-run
`0003_grants.sql`.

### 1.3 Collect production credentials

From Supabase Dashboard > Project Settings > API:

- Project URL: `https://<project-ref>.supabase.co`
- `anon` / publishable key: public; used by the Vercel dashboard.
- `service_role` key: secret; used only by the Render bot and trusted SQL.

Never expose `SUPABASE_SERVICE_ROLE_KEY` in a `NEXT_PUBLIC_*` variable, browser
code, or the repository.

### 1.4 Configure Discord authentication

1. In the Discord Developer Portal > OAuth2, add this redirect URL:
   `https://<project-ref>.supabase.co/auth/v1/callback`
2. In Supabase Dashboard > Authentication > Providers > Discord, enable the
   provider and enter the Discord client ID and client secret.
3. In Supabase Dashboard > Authentication > URL Configuration:
   - Site URL: `https://<dashboard-domain>`
   - Redirect URLs:
     - `https://<dashboard-domain>/auth/callback`
     - `http://localhost:3000/auth/callback` for local testing
4. Sign in once at `/login` so Supabase creates the Discord auth identity, then
   insert the first dashboard administrator in the SQL editor:

```sql
insert into public.dashboard_admins (user_id, discord_id, guild_id, role)
select u.id, 1111664537846951946, 1569030756515323974, 'admin'
from auth.users u
join auth.identities i on i.user_id = u.id
where i.provider = 'discord'
  and (i.identity_data->>'provider_id') = '1111664537846951946'
on conflict (user_id, guild_id) do update
set discord_id = excluded.discord_id,
    role = excluded.role;
```

The full bootstrap and verification SQL, including the `guilds` row fallback, is
in `SETUP_DASHBOARD_ADMIN.txt`.

### 1.5 Backup and export strategy

Use both layers:

1. **Supabase backups:** check Database > Backups in the Supabase dashboard and
   confirm the project's plan includes the desired retention. Restore through
   the dashboard when available.
2. **Logical export:** keep periodic `pg_dump` copies outside Supabase.

PowerShell example (use the connection string from Supabase Dashboard >
Connect; percent-encode special characters in the password):

```powershell
$env:SUPABASE_DB_URL = "postgresql://postgres.<project-ref>:<password>@<host>:5432/postgres"
$stamp = Get-Date -Format "yyyyMMdd-HHmm"
pg_dump $env:SUPABASE_DB_URL --schema=public --format=custom --file="backup-$stamp.dump"
```

Restore only after testing on a non-production project:

```powershell
pg_restore --clean --if-exists --no-owner --dbname $env:SUPABASE_DB_URL "backup-YYYYMMDD-HHmm.dump"
```

Store backups encrypted and retain at least one copy off the host running the
bot. Do not commit dumps to Git.

---

## 2. Render: Discord bot

`render.yaml` defines a Python web service with:

- Root directory: `bot`
- Build command: `pip install -r requirements.txt`
- Start command: `python main.py`
- Health check: `/health`
- Python: `3.12.10` (`runtime.txt` and `PYTHON_VERSION` agree)

### 2.1 Create the service

1. Push the repository to GitHub.
2. In Render, choose **New > Blueprint** and connect the repository. Render
   reads `render.yaml`.
3. If creating the service manually instead, use the values above and select
   the free plan if desired.

### 2.2 Set environment variables

| Variable | Required | Value |
| --- | --- | --- |
| `DISCORD_TOKEN` | Yes | Bot token from the Discord Developer Portal |
| `DISCORD_GUILD_ID` | Yes | `1569030756515323974` |
| `SUPABASE_URL` | Yes | `https://ycckkcglgfpdwjhrkiyr.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Supabase service-role key; secret |
| `BOT_PREFIX` | Yes | `!` |
| `LOG_LEVEL` | Yes | `INFO` |
| `PYTHON_VERSION` | Yes | `3.12.10` |
| `PYTHONUNBUFFERED` | Recommended | `1` for immediate log output |
| `PORT` | No | Render injects this automatically |
| `HOST` | No | Defaults to `0.0.0.0` |

Enable **Server Members Intent** and **Message Content Intent** for the bot in
the Discord Developer Portal. Invite the bot with the permissions required by
the enabled command modules.

### 2.3 Verify the deployment

```powershell
Invoke-RestMethod "https://<service-name>.onrender.com/health"
```

Expected fields:

- `status`: `ok`
- `discord_configured`: `true`
- `supabase_configured`: `true`
- `bot_ready`: `true` after the gateway connects
- `guilds`: at least `1`

In Render logs, confirm all cogs load, the gateway connects, the scheduler
starts, and temp-voice reconciliation completes. The health server always binds
to Render's injected `PORT`; do not hard-code `8080` in Render.

Render free web services can spin down when idle. The UptimeRobot monitor below
keeps a regular request flowing, but confirm the workspace's free-hour limits
before relying on 24/7 uptime.

---

## 3. Vercel: dashboard

### 3.1 Import the project

1. In Vercel, choose **Add New > Project** and import the GitHub repository.
2. Set **Root Directory** to `dashboard`.
3. Framework preset: **Next.js**.
4. Build command: `npm run build` (default).
5. Install command: default `npm install` / `npm ci`.

### 3.2 Set environment variables

Set these for Production (and Preview if desired):

| Variable | Required | Value |
| --- | --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | `https://ycckkcglgfpdwjhrkiyr.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | Supabase anon/publishable key |
| `NEXT_PUBLIC_APP_URL` | Yes | `https://<dashboard-domain>` (no trailing slash) |
| `DISCORD_BOT_TOKEN` | Optional | Server-only membership/role verification |
| `DISCORD_GUILD_ID` | Optional | `1569030756515323974` |

`NEXT_PUBLIC_*` values are embedded at build time. After changing them, trigger
a new deployment. Never put the Supabase service-role key in a public variable.

### 3.3 Domain and OAuth

1. Add the production domain in Vercel > Settings > Domains.
2. Update the Supabase Site URL and redirect URLs to that exact domain.
3. Confirm the Discord OAuth redirect points to the Supabase callback URL from
   section 1.4.

### 3.4 Verify the deployment

- `/`, `/command`, `/terms`, `/privacy`, and `/login` return `200`.
- `/dashboard` redirects unauthenticated visitors to `/login`.
- Discord login returns to `/auth/callback` and then `/dashboard`.
- The dashboard reads live Supabase data.
- Saving a settings form updates `guild_settings`; the bot reflects it within
  the 30-second settings cache window.
- Toggling an automation updates the dashboard and the bot scheduler within
  30 seconds.

---

## 4. UptimeRobot: monitoring

1. Create an account at UptimeRobot.
2. Add a new **HTTP(s)** monitor:
   - Friendly name: `Triumph Bot - Render health`
   - URL: `https://<service-name>.onrender.com/health`
   - Monitoring interval: **5 minutes**
   - Timeout: 30 seconds
   - Alert contacts: your email/Discord/SMS destination
3. Use HTTP `200` as the primary check. If keyword monitoring is available, use
   the exact fragment `"bot_ready":true` rather than the word `bot_ready`, so a
   `false` value is not treated as healthy. Otherwise rely on Render logs for
   gateway failures.
4. Add a second HTTP monitor for the Vercel dashboard root URL, also at
   5-minute intervals.
5. Trigger a test notification from UptimeRobot and confirm it arrives.

The health endpoint intentionally returns `200` when the Flask process is
running, even before Discord is ready. Use the `bot_ready` field or Render logs
to distinguish a process-health failure from a Discord gateway failure.

---

## 5. Production smoke test

After all services are live, run:

```powershell
.\scripts\verify_deployment.ps1 `
  -DashboardUrl "https://<dashboard-domain>" `
  -BotHealthUrl "https://<service-name>.onrender.com/health"
```

Then complete the manual checks:

- [ ] Bot is online in Discord and `!ping` responds.
- [ ] `!help` lists all ten modules.
- [ ] A settings change made in the dashboard reaches the bot within 30 seconds.
- [ ] An automation toggle survives a bot restart.
- [ ] Temp-voice reconciliation succeeds after a restart.
- [ ] Dashboard login works with a real Discord account.
- [ ] A non-admin dashboard account cannot access another guild's data.
- [ ] Render logs show no repeated exceptions.
- [ ] A Supabase backup/export has been created and stored securely.
- [ ] UptimeRobot reports both monitors as up.

Phase 13 is complete when the four platform tasks in `task.txt` are checked
against the live services, not merely when the local configuration passes. At
the 2026-11-19 close, Render health and UptimeRobot, Vercel deploy/login, and
Supabase RLS checks passed. Restart persistence and the remaining command smoke
checks are carried into Phase 14; backup/export execution remains operational.

---

## 6. Rollback and maintenance

- **Render:** redeploy the previous successful commit, or restart the service
  from the Render dashboard. A restart verifies scheduler and temp-voice
  recovery.
- **Vercel:** promote the previous deployment from the project's Deployments
  page.
- **Supabase:** restore a tested backup only during a planned maintenance
  window. Schema changes should be applied as forward migrations.
- **Secrets:** rotate Discord/Supabase keys by updating Render/Vercel
  environment variables and redeploying. Revoke the old key after the new
  deployment is healthy.

## 7. Troubleshooting

| Symptom | Check |
| --- | --- |
| Render deploy exits immediately | Start command `python main.py`, root directory `bot`, and `PORT` binding |
| `/health` returns 502 | Service still starting or crashed; inspect Render logs |
| `bot_ready` stays false | Invalid `DISCORD_TOKEN`, missing intents, or gateway/network error |
| `supabase_configured` false | Missing/invalid `SUPABASE_URL` or service-role key |
| Vercel build fails | Root directory is `dashboard`; `npm run build` passes locally |
| Dashboard shows configuration error | Supabase URL/anon key missing or wrong environment |
| Login loops or OAuth fails | Supabase redirect URLs and Discord callback URL must match exactly |
| `42501 permission denied` | Re-run `supabase/migrations/0003_grants.sql` |
| Dashboard is empty for an admin | `dashboard_admins` row missing for the guild/user pair |
| Bot sleeps on Render | Free-plan idle behavior; confirm uptime policy and monitor interval |
