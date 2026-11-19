# Test-to-Production Guild Migration

This runbook moves Triumph Bot from the test Discord server to the real
production server using a **clean production start**.

> **Status:** executed 2026-11-19. Production guild is
> `1565983272217874535` (`♛ 𝙏𝙍𝙄𝙄𝙐𝙈𝙋𝙃`), owned by `1064601909266239710`.
> The test guild row and all cascaded test data were deleted. Vercel
> `DISCORD_GUILD_ID` was updated and redeployed. Remaining: update Render
> `DISCORD_GUILD_ID`, then verify dashboard login and real-guild settings.

## Scope

The migration intentionally does **not** copy test server configuration or
history. After a verified backup, the test guild row is deleted and every
guild-scoped row cascades with it. The real server is configured fresh through
the dashboard.

Not migrated:

- members and member numbers
- warnings and moderation history
- activity/moderation logs and statistics snapshots
- temporary voice records
- polls, reaction-role mappings, and automations
- test welcome/logging/automod/temp-voice settings

Preserved:

- Supabase schema, functions, grants, and RLS policies
- Supabase Auth users and Discord identities
- the dashboard admin identity, copied to the real guild

> This is a destructive database operation. Keep the backup and the test Discord
> server intact until production verification passes.

## Required inputs

| Input | Example | Notes |
| --- | --- | --- |
| `TEST_GUILD_ID` | `1569030756515323974` | Deleted test server |
| `REAL_GUILD_ID` | `1565983272217874535` | Production Discord server |
| `REAL_GUILD_NAME` | `♛ 𝙏𝙍𝙄𝙄𝙐𝙈𝙋𝙃` | Initial `guilds.name` value |
| `REAL_OWNER_ID` | `1064601909266239710` | Discord user ID of the real server owner |
| Admin Discord ID | `1111664537846951946` | Remains the dashboard administrator |

## 1. Pre-flight

### 1.1 Back up Supabase

Do both:

1. Confirm a current backup under **Supabase Dashboard > Database > Backups**.
2. Create a logical export using **Supabase Dashboard > Database > Backups** or
   `pg_dump` from a machine that has it installed. Store the export outside this
   repository.

Never commit a database export. It may contain member IDs, moderation records,
and other private data.

### 1.2 Inspect the current state

Run in the Supabase SQL editor:

```sql
select id, name, owner_id, created_at
from public.guilds
order by created_at;

select user_id, discord_id, guild_id, role
from public.dashboard_admins
order by guild_id, discord_id;

select
  (select count(*) from public.members
    where guild_id = 1569030756515323974) as members,
  (select count(*) from public.warnings
    where guild_id = 1569030756515323974) as warnings,
  (select count(*) from public.moderation_logs
    where guild_id = 1569030756515323974) as moderation_logs,
  (select count(*) from public.activity_logs
    where guild_id = 1569030756515323974) as activity_logs;
```

Confirm at least one `dashboard_admins` row exists for the test guild. The
migration copies these rows to the real guild before deleting the test data.

### 1.3 Prepare Discord

1. Remove the bot from the test server:
   **Server Settings > Integrations > Triumph Bot > Manage > Kick**.
   Removing the bot prevents test rows from being recreated after cleanup.
2. Invite the bot to the real server with the required permissions:
   - View Channels
   - Send Messages and Embed Links
   - Read Message History
   - Manage Messages and Manage Channels
   - Manage Roles
   - Kick Members, Ban Members, Moderate Members
   - Move Members
   - Manage Server
3. Keep the bot role above any role it must assign or moderate.
4. Confirm Server Members Intent and Message Content Intent remain enabled in the
   Discord Developer Portal.
5. Keep the test Discord server itself available as a rollback target; only the
   bot membership and database rows are removed.

## 2. Run the migration

The executed migration record is
[`supabase/scripts/guild_migration_1565983272217874535.sql`](../supabase/scripts/guild_migration_1565983272217874535.sql).
The reusable template remains
[`supabase/scripts/guild_migration_clean_start.sql`](../supabase/scripts/guild_migration_clean_start.sql).
Both are outside `supabase/migrations/`, so they never run automatically.

1. Open the file and replace every `<PLACEHOLDER>` value.
2. Run the whole transaction in the Supabase SQL editor.
3. Confirm the transaction committed without errors.
4. Run the verification queries at the bottom of the template.

What the transaction does:

1. Inserts the real guild into `public.guilds`.
2. Inserts default `public.guild_settings` for the real guild.
3. Copies every `dashboard_admins` row from the test guild to the real guild,
   preserving `user_id`, `discord_id`, and role.
4. Aborts if no admin row was copied.
5. Deletes the test `public.guilds` row. Foreign keys cascade to all
   guild-scoped tables.
6. Commits atomically.

## 3. Re-point production configuration

### Render

Update the `DISCORD_GUILD_ID` environment variable to `<REAL_GUILD_ID>` and save.
Render redeploys the service. Keep `DISCORD_TOKEN`, `SUPABASE_URL`, and
`SUPABASE_SERVICE_ROLE_KEY` unchanged.

The bot itself is multi-guild; `DISCORD_GUILD_ID` is not a guild allowlist. The
database cleanup plus removing the bot from the test server is what makes the
real guild the only active server.

### Vercel

Update `DISCORD_GUILD_ID` to `<REAL_GUILD_ID>` for Production and redeploy.
`DISCORD_GUILD_ID` selects the preferred admin guild in
`dashboard/src/lib/auth.ts`; the dashboard otherwise falls back to the first
admin row.

Optional: set `DISCORD_BOT_TOKEN` in Vercel to enable server-side guild
membership/role verification and channel/role dropdowns. If set, it must be the
same bot token used by Render.

## 4. Configure the real server

1. Open `https://triumph-bot-bice.vercel.app/login` and sign in with the Discord
   account copied to the real guild.
2. Confirm the dashboard header shows the real server.
3. Configure settings fresh:
   - prefix
   - welcome and goodbye channels/messages
   - autoroles
   - logging channels
   - automod rules
   - temporary voice trigger/category/template
   - dashboard admin roles, if role gating is desired
4. Create reaction roles, polls, and automations only after the base settings
   are verified.
5. Allow up to 30 seconds for the bot settings cache and automation scheduler to
   pick up changes.

## 5. Verification

### 5.1 Health and deployment

```powershell
.\scripts\verify_deployment.ps1 `
  -DashboardUrl "https://triumph-bot-bice.vercel.app" `
  -BotHealthUrl "https://triumph-bot.onrender.com/health"
```

Expected after removing the bot from the test server:

- `bot_ready=true`
- `guilds=1` for a single production guild
- all dashboard pages pass

### 5.2 Database

Run the verification queries from the migration template. Expected:

- `public.guilds` contains the real guild ID.
- `public.guild_settings` contains the real guild ID.
- `public.dashboard_admins` contains the real guild ID.
- all test-guild counts are zero.

### 5.3 Dashboard and bot

- Dashboard login resolves to the real guild.
- Saving a setting updates `guild_settings`.
- The bot reflects the change within 30 seconds.
- Welcome, logging, moderation, temp voice, and automation smoke tests pass on
  the real server.
- Anonymous Supabase reads still return zero rows.
- Authenticated cross-guild isolation is verified during Phase 14.

### 5.4 Documentation

After the real guild ID is known, update:

- `docs/DEPLOYMENT.md` environment tables and admin SQL
- `SETUP_DASHBOARD_ADMIN.txt`
- `Live_verification.md` and `Live_verification.txt` guild header
- `task.txt` Phase 15 migration checkboxes

## 6. Rollback

Before verification completes, the test guild can be restored:

1. Restore the Supabase backup taken in step 1.1.
2. Re-invite the bot to the test Discord server.
3. Revert `DISCORD_GUILD_ID` in Render and Vercel to
   `1569030756515323974`.
4. Redeploy both services.
5. Confirm `/health` and dashboard access against the test guild.

After test data is deleted and overwritten by production activity, restore from
the backup rather than attempting to merge rows. If a managed Supabase backup is
not available, use the logical JSON export; restoring it requires manual
insertion in foreign-key order.

## 7. Post-migration checklist

- [x] Logical data export created and stored outside the repository.
- [x] Bot removed from the test server.
- [x] Bot present and authorized on the real server (Administrator verified; role hierarchy still applies).
- [x] Real guild, settings, and admin rows created.
- [x] Test guild rows deleted and all cascaded counts are zero.
- [x] Vercel guild ID updated and production redeployed.
- [ ] Render guild ID updated.
- [ ] Dashboard login resolves to the real server.
- [x] Deployment verification script passes.
- [x] Unauthenticated dashboard access redirects to `/login`; anonymous REST reads return zero rows.
- [ ] Real-server settings, logging, and moderation smoke tests pass.
- [x] Documentation and live-verification guild headers updated.
- [ ] Backup retention and rollback point recorded.
