# Supabase (Triumph Bot)

## Migrations
Apply in order in the Supabase SQL editor (or via your preferred migration workflow):

1. `migrations/0001_initial_schema.sql` - extensions, tables, FKs, indexes, triggers, `next_member_number`, `is_dashboard_admin`
2. `migrations/0002_rls_policies.sql` - enables RLS and creates dashboard access policies
3. `migrations/0003_grants.sql` - grants for `anon`/`authenticated`/`service_role` roles (fixes `42501 permission denied for table` when tables were created via SQL editor)

## Access model
- **Bot (Render):** uses `SUPABASE_SERVICE_ROLE_KEY` server-side only. Service role bypasses RLS for full read/write access.
- **Dashboard (Vercel):** uses `NEXT_PUBLIC_SUPABASE_ANON_KEY` with authenticated user JWTs. RLS restricts access to guilds where `auth.uid()` has a row in `public.dashboard_admins`.
- `dashboard_admins` rows should be created only by trusted server actions after Discord identity/guild membership/role verification.

## RLS verification
Use `tests/rls_checks.sql` in the Supabase SQL editor. It includes commented steps to:
- seed two test guilds and one allowed admin
- confirm service/postgres context sees all rows
- simulate `authenticated` user and confirm cross-guild reads/updates are blocked
- simulate `anon` and confirm no rows are visible
- clean up test data

## Applying without Supabase CLI
Supabase CLI is not installed in this environment. You can:
- Paste/run each migration in Supabase Dashboard -> SQL Editor (recommended now), or
- Install CLI later and use `npx supabase db push` / `supabase link`.

## Phase 2 completion criteria
- Migrations applied successfully to the project (0001, 0002, 0003)
- `tests/rls_checks.sql` executed and results confirm anon cannot read rows and authenticated users cannot access other guilds' rows
- Bot can connect using service role and perform a basic read/write smoke test (e.g. upsert `guilds`/`guild_settings`)
