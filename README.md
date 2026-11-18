# Triumph Bot

Discord server management bot and web dashboard.

## Stack
- **Bot:** Python 3.12, discord.py, Flask (health), Supabase (PostgreSQL)
- **Dashboard:** Next.js + TypeScript + Tailwind (Vercel)
- **Database/Auth:** Supabase (PostgreSQL, Auth, RLS)
- **Hosting:** Render (bot), Vercel (dashboard), UptimeRobot (monitoring)

## Repository layout
- `bot/` — Discord bot, cogs, services, health endpoint
- `dashboard/` — Next.js web dashboard
- `supabase/` — migrations, RLS policies, SQL tests
- `docs/` — commands, dashboard, deployment, maintenance docs
- `task.txt` — phase-by-phase progress tracker

## Quick start (Phase 1)

### Prerequisites
- Python 3.12+
- Node.js (for dashboard, later phases)
- Discord application with bot token and intents enabled (Server Members, Message Content)
- Supabase project

### Bot setup
1. Create and activate a virtual environment in `bot/`:
   - `cd bot`
   - `py -3.12 -m venv .venv`
   - `.venv\Scripts\Activate.ps1`
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `../.env.example` values into `bot/.env` and fill real values.
4. Run: `python main.py`
5. Verify:
   - Bot appears online in Discord
   - `!ping` responds
   - `GET /health` returns `200 {"status":"ok",...}`

### Environment
See `.env.example` for all variables. Never commit `.env` files or secrets.

## Deployment (Phase 13)

Live since 2026-11-19:

- **Dashboard:** <https://triumph-bot-bice.vercel.app>
- **Bot health:** <https://triumph-bot.onrender.com/health>
- **Database/auth:** Supabase production project; Discord OAuth login and RLS
  isolation verified.
- **Monitoring:** UptimeRobot reports the Render health and Vercel dashboard
  monitors as up on 5-minute checks.
- **Automatic deploys:** Vercel GitHub integration reports a successful
  deployment; Render auto-deploy is enabled in `render.yaml`.

The deployment script passes all checks:

```powershell
.\scripts\verify_deployment.ps1 `
  -DashboardUrl "https://triumph-bot-bice.vercel.app" `
  -BotHealthUrl "https://triumph-bot.onrender.com/health"
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full runbook, environment
matrix, OAuth setup, backup/export strategy, rollback steps, and troubleshooting.

## Bot commands (current)
- Core: `!ping`, `!botinfo`, `!dbping`, `!extensions`, `!prefix`, `!reload <ext>` (owner)
- Welcome: `!welcome` (status), `!welcome channel #ch|off`, `!welcome message <text>`, `!welcome template <text>`, `!welcome toggle`, `!welcome embed|banner|dm on|off`, `!welcome test [@member|#channel]` (sends to the configured welcome channel)
- Goodbye: `!goodbye` (status), `!goodbye channel #ch|off`, `!goodbye message <text>`, `!goodbye toggle`, `!goodbye test [@member|#channel]` (sends to the configured goodbye channel)
- Autoroles: `!autorole` / `!autorole list`, `!autorole add @role`, `!autorole remove @role`, `!autorole clear`
- Placeholders: `{user}`, `{mention}`, `{name}`, `{display_name}`, `{server}`, `{member_count}`, `{member_number}`, `{created_at}`, `{joined_at}`, `{account_age}`, `{server_age}`
- Welcome banners use bundled DejaVu fonts (`bot/assets/fonts/`) so rendering is identical on Windows and Render.
- Moderation: `!ban @user [reason]`, `!unban <id> [reason]`, `!kick @user [reason]`, `!timeout @user <10m|1h30m|2d> [reason]`, `!untimeout @user [reason]`
- Warnings: `!warn @user [reason]`, `!warnings @user`, `!unwarn @user <id|latest>`
- Channels: `!clear <1-500> [@user]`, `!lock [#channel] [reason]`, `!unlock [#channel] [reason]`
- Mod logs: `!modlog [#channel|off]`, `!modlogs [@user] [limit]` (stored in Supabase `moderation_logs`)
- Automod: `!automod` (status), `!automod spam|links|invites on|off`, `!automod threshold <1-50>`, `!automod interval <5s|1m>`, `!automod timeout <10m|off>`
- Automod exemptions: server owner, administrators, and members with Manage Messages/Manage Server/Kick/Ban/Moderate Members.
- Anti-link allowlist: tenor.com, giphy.com, imgur.com, cdn.discordapp.com, media.discordapp.net, youtube.com, youtu.be, spotify.com, github.com, twitch.tv, klipy.com, streamable.com, wikimedia.org.
- Info: `!userinfo [@member]`, `!serverinfo`, `!avatar [@member]`, `!roleinfo @role`
- Utilities: `!slowmode <10s|1m|off> [#channel]`, `!embed #channel "Title" "Description" [#color] [image_url]`
- Polls: `!poll Question | Option 1 | Option 2 ...` (2-10 options), `!poll results <message_id>`, `!poll end <message_id>`
- Reaction roles: `!reactionrole add <message_id|link> <emoji> @role`, `!reactionrole remove <message_id|link> <emoji>`, `!reactionrole list`
- Statistics: `!serverstats` (saves a snapshot), `!serverstats history [limit]`
- Temp voice setup: `!tempvoice setup #trigger [#category]`, `!tempvoice trigger|category|defaultlimit|template`
- Temp voice owner: `!tempvoice name <name>`, `!tempvoice size <0-99>`, `!tempvoice lock|unlock`, `!tempvoice kick @member`, `!tempvoice claim`, `!tempvoice delete`, `!tempvoice status`
- Temp voice records live in Supabase `temp_voice_channels`; empty channels are deleted automatically and stale records reconciled on startup.
- Logging: `!logs status`, `!logs set <event> #channel`, `!logs set <event> off`, `!logs test <event>`, `!logs history [event] [limit]`
- Log events: join_leave, message_delete, message_edit, role_change, nickname_change, voice, moderation, channel_events (stored in `activity_logs`)
- Automations: `!automation list`, `!automation status`, `!automation toggle <id|name>`, `!automation remove <id|name>`
- Scheduled: `!automation announcement|message|reminder <name> "<cron>" #channel <message>`, `!automation stats <name> "<cron>" [#channel]`
- Hooks: `!automation autorole <name> @role...`, `!automation welcome|goodbye <name> #channel <message>`, `!automation response <name> <trigger> <reply>`
- Cron is 5-field UTC (quote it), e.g. `"0 9 * * *"`; placeholders: `{guild}`, `{member_count}`, `{user}`, `{display_name}`, `{mention}`, `{time}`; separate response triggers with `|`.

## Web dashboard (Phases 10–12)
- Stack: Next.js 15.5 (App Router), React 19, Tailwind CSS 4, TypeScript, `@supabase/ssr`.
- Branding: Triumph logo (`dashboard/public/triumph-icon.png`, `dashboard/src/app/icon.png`), navy/royal-purple/gold palette, Cinzel + Inter.
- Public routes: `/` (homepage), `/command` (searchable command reference), `/terms`, `/privacy`, `/login`.
- Dashboard routes: `/dashboard` (overview), `/dashboard/statistics`, `/dashboard/activity`, `/dashboard/settings` (welcome, moderation, logging, temp-voice), `/dashboard/management` (automations, reaction-roles, warnings).
- Phase 12 editing: welcome, moderation, logging, and temp-voice forms write to Supabase through server actions with RLS; automations can be enabled/paused from the dashboard.
- Sync model: the bot's settings cache TTL is 30 seconds; the automation scheduler reloads enabled jobs every 30 seconds and drops deleted or paused jobs.
- Reaction roles and warnings remain bot-managed and are shown read-only in the dashboard.
- Local setup:
  1. `cd dashboard`
  2. Copy `.env.example` to `.env.local` and set `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_APP_URL`.
  3. Optional server-side verification: `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID`.
  4. `npm install`, `npm run dev` (or `npm run build` + `npm run start`).
  5. Quality gates: `npm run typecheck`, `npm run build`.
- Supabase auth setup (required for login):
  1. Authentication → Providers → Discord: enable with the Discord application client ID/secret.
  2. Authentication → URL Configuration: allow `http://localhost:3000/auth/callback` and the production callback URL.
  3. Insert a `dashboard_admins` row with the Supabase `user_id`, Discord ID, and guild ID using the service-role key.
- Authorization flow: Supabase session → `dashboard_admins` row → Discord provider identity match → optional live guild membership and `dashboard_admin_role_ids` check.

## Development
- Complete one phase before starting the next (see `task.txt`).
- Test each feature before integration.
- Keep the hosting budget at ₱0 where free-tier limits allow.

## Status
See `task.txt` for current phase and checkpoint log.
