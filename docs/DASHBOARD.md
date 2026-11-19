# Dashboard Usage

Production dashboard: <https://triumph-bot-bice.vercel.app>

Public pages:

- `/` — product overview
- `/command` — searchable reference for all 95 commands
- `/terms` — terms of use
- `/privacy` — privacy policy
- `/login` — Discord sign-in

The authenticated area starts at `/dashboard`.

## Access requirements

A user can open the dashboard only when all of these are true:

1. Discord OAuth succeeds through Supabase Auth.
2. A `public.dashboard_admins` row exists for the Supabase auth user ID and the
   selected guild.
3. The Discord identity on the auth user matches the row's `discord_id`.
4. If `DISCORD_BOT_TOKEN` is configured in Vercel, the user is still a member of
   the guild. If `guild_settings.dashboard_admin_role_ids` is non-empty, the user
   must also have one of those roles.
5. The `members` row for the user does not show `left_at`.

Unauthenticated visits to `/dashboard` redirect to
`/login?next=%2Fdashboard`. Users without access see the access-denied screen
with the reason returned by the authorization check.

## Navigation

### Overview

- **Command center** (`/dashboard`) — member, warning, temp-voice, automation,
  reaction-role, and activity counts; latest statistics snapshot; recent activity.
- **Statistics** (`/dashboard/statistics`) — member composition and snapshot
  history.
- **Activity logs** (`/dashboard/activity`) — recent stored activity events.

### Settings

- **Overview** (`/dashboard/settings`) — server summary and settings links.
- **Welcome** (`/dashboard/settings/welcome`) — welcome/goodbye enablement,
  channels, messages, banner template, DM text, and placeholder guidance.
- **Moderation** (`/dashboard/settings/moderation`) — automod toggles, spam
  threshold, spam window, timeout duration, and prefix.
- **Logging** (`/dashboard/settings/logging`) — one channel per event:
  join/leave, message delete, message edit, role change, nickname change, voice,
  moderation, and channel events.
- **Temp voice** (`/dashboard/settings/temp-voice`) — trigger channel, category,
  default limit, and room-name template.

### Management

- **Server operations** (`/dashboard/management`) — current server state and the
  matching Discord commands.
- **Automations** (`/dashboard/management/automations`) — list automations and
  enable or pause them.
- **Reaction roles** (`/dashboard/management/reaction-roles`) — review mappings.
- **Warnings** (`/dashboard/management/warnings`) — review warning history.

## Common tasks

### Change the prefix

1. Open **Settings > Moderation**.
2. Update the prefix.
3. Save.
4. The bot reads the new value within the 30-second settings cache window.

### Configure welcome and goodbye

1. Open **Settings > Welcome**.
2. Select text or announcement channels from the dropdowns. If the dropdown is
   unavailable, paste the Discord channel ID.
3. Enter the message and optional banner template.
4. Use `{user}`, `{server}`, `{member_count}`, and `{member_number}` as
   placeholders.
5. Save. Test with `!welcome test` and `!goodbye test`.

### Configure logging

1. Open **Settings > Logging**.
2. Set one channel per event, or leave a field blank to disable that event.
3. Save.
4. Run `!logs test <event>` in Discord to verify delivery.

### Configure temporary voice

1. Create the trigger voice channel and optional category in Discord.
2. Open **Settings > Temp voice**.
3. Select the trigger and category.
4. Set the default limit (`0` means unlimited) and name template.
5. Save, then join the trigger channel to verify a room is created.

### Pause an automation

1. Open **Management > Automations**.
2. Toggle the automation row.
3. The scheduler reloads every 30 seconds.
4. Confirm the automation's `enabled` value in Supabase if the bot does not react.

### Review warnings and activity

- Warnings are read from `public.warnings`.
- Activity is read from `public.activity_logs` and is populated by the bot.
- Moderation history is available in Discord through `!modlogs`.

## Roles and channel pickers

When `DISCORD_BOT_TOKEN` is set in Vercel, the dashboard uses the Discord API to
populate channel and role dropdowns for the selected guild. The token is
server-only and must never use a `NEXT_PUBLIC_` prefix.

If the Discord API is unavailable, paste numeric IDs directly. Enable Discord
Developer Mode under **User Settings > Advanced** to copy IDs.

## Safety and access

- Dashboard writes are performed through server actions after access checks.
- Supabase RLS limits authenticated reads to guilds where the user is an admin.
- The Supabase service-role key is never exposed to the browser.
- Anonymous Supabase reads return zero rows.
- Sign out at `/auth/signout`.
- To revoke a dashboard user, delete their `dashboard_admins` row and, if
  applicable, remove the verified Discord role.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Redirect loop or OAuth failure | Supabase Site URL, `/auth/callback` allowlist, and Discord redirect URL |
| “Not registered as a dashboard administrator” | `dashboard_admins` row for the Supabase `user_id` and guild |
| Wrong server shown | Vercel `DISCORD_GUILD_ID` and the user's admin rows |
| “Identity does not match” | Row's `discord_id` versus the Discord identity on the auth user |
| Member shows as left | `members.left_at` for that guild/user |
| Role required but missing | `guild_settings.dashboard_admin_role_ids` and Discord role membership |
| Channel/role dropdown empty | `DISCORD_BOT_TOKEN` in Vercel and bot access to the guild |
| Settings do not reach Discord | Wait 30 seconds, then check bot logs and `guild_settings` |
| Empty dashboard | RLS, admin row, and selected guild ID |
| Build-time env changed | Redeploy Vercel after changing `NEXT_PUBLIC_*` values |

See [DEPLOYMENT.md](DEPLOYMENT.md) for environment setup and
[MIGRATION.md](MIGRATION.md) for test-to-production cutover.
