# Triumph Bot Command Reference

Triumph Bot uses prefix commands. The default prefix is `!`, configurable per
server in the dashboard. Examples below use `!`.

The live searchable reference is available at
`https://triumph-bot-bice.vercel.app/command`. The inventory contains **95
commands across 11 modules**.

Permission labels are the intended access level. Discord channel overrides,
role hierarchy, and the bot's own permissions still apply.

## General

- **`!ping`** — Check bot responsiveness and gateway latency. (`Everyone`)
- **`!serverinfo`** — Show owner, creation date, counts, boosts, and features.
  (`Everyone`) Aliases: `!guildinfo`
- **`!userinfo [@member]`** — Show account and membership details for a member.
  (`Everyone`) Aliases: `!whois`
- **`!avatar [@member]`** — Show global and server avatars. (`Everyone`) Aliases:
  `!av`
- **`!roleinfo <@role>`** — Show role color, position, permissions, and member
  count. (`Everyone`)
- **`!serverstats`** — Show live member, channel, role, and boost statistics and
  store a snapshot. (`Everyone`) Aliases: `!stats`
- **`!serverstats history [limit]`** — Show recent statistics snapshots; default
  5. (`Everyone`)

## Moderation

- **`!ban @member [reason]`** — Ban a member or user ID and record the action.
  (`Ban Members`)
- **`!unban <user_id> [reason]`** — Unban a user by their Discord ID.
  (`Ban Members`)
- **`!kick @member [reason]`** — Kick a member and record the action.
  (`Kick Members`)
- **`!timeout @member <duration> [reason]`** — Timeout a member. Examples: `10m`,
  `1h30m`, `2d`. (`Moderate Members`) Aliases: `!mute`
- **`!untimeout @member [reason]`** — Remove an active timeout.
  (`Moderate Members`) Aliases: `!unmute`
- **`!warn @member [reason]`** — Warn a member and store the warning in
  Supabase. (`Moderator`)
- **`!warnings @member`** — List a member's active warnings. (`Moderator`)
  Aliases: `!warns`
- **`!unwarn @member <id|latest> [reason]`** — Deactivate a warning by ID or the
  latest one. (`Moderator`)
- **`!clear <amount> [@member]`** — Delete recent messages, optionally only from
  one member. (`Manage Messages`) Aliases: `!purge`
- **`!lock [#channel|voice_channel]`** — Prevent `@everyone` from sending
  messages in a text channel or joining a voice channel. (`Manage Channels`)
  Aliases: `!lockdown`
- **`!unlock [#channel|voice_channel]`** — Remove the `@everyone` send-messages
  or voice-connect override. (`Manage Channels`)
- **`!modlog [#channel|off]`** — Set or disable the moderation log channel.
  (`Manage Server`)
- **`!modlogs [@member] [limit]`** — Show recent moderation history; default 10.
  (`Moderator`) Aliases: `!history`

## Welcome and onboarding

- **`!welcome`** — Show the current welcome configuration. (`Manage Server`)
- **`!welcome channel <#channel|off>`** — Set the welcome destination channel.
  (`Manage Server`)
- **`!welcome message <text>`** — Set the welcome text. Supports `{user}`,
  `{server}`, `{member_count}`, and `{member_number}`. (`Manage Server`)
- **`!welcome template <text>`** — Set the subtitle rendered onto the generated
  welcome banner. (`Manage Server`)
- **`!welcome toggle`** — Enable or disable welcome messages. (`Manage Server`)
- **`!welcome embed <on|off>`** — Toggle embed styling for welcome messages.
  (`Manage Server`)
- **`!welcome banner <on|off>`** — Toggle the generated welcome banner image.
  (`Manage Server`)
- **`!welcome dm <on|off>`** — Toggle direct messages to new members.
  (`Manage Server`)
- **`!welcome test [#channel|@member]`** — Preview the welcome output in a
  channel or DM. (`Manage Server`)
- **`!goodbye`** — Show the current goodbye configuration. (`Manage Server`)
- **`!goodbye channel <#channel|off>`** — Set the goodbye destination channel.
  (`Manage Server`)
- **`!goodbye message <text>`** — Set the goodbye text. (`Manage Server`)
- **`!goodbye toggle`** — Enable or disable goodbye messages. (`Manage Server`)
- **`!goodbye test [#channel|@member]`** — Preview the goodbye output in a
  channel or DM. (`Manage Server`)
- **`!autorole`** — Show roles applied automatically on join. (`Manage Server`)
- **`!autorole add @role`** — Add a role to the autorole list. (`Manage Server`)
- **`!autorole remove @role`** — Remove a role from the autorole list.
  (`Manage Server`)
- **`!autorole list`** — List configured autoroles. (`Manage Server`)
- **`!autorole clear`** — Remove all autoroles. (`Manage Server`)

## AutoModeration

- **`!automod`** — Show the current automod configuration. (`Manage Server`)
- **`!automod spam <on|off>`** — Enable or disable anti-spam. (`Manage Server`)
- **`!automod links <on|off>`** — Enable or disable link filtering; allowlisted
  domains pass. (`Manage Server`)
- **`!automod invites <on|off>`** — Enable or disable Discord invite blocking.
  (`Manage Server`)
- **`!automod threshold <1-50>`** — Set how many messages trigger a spam action.
  (`Manage Server`)
- **`!automod interval <seconds|duration>`** — Set the spam counting window, for
  example `5s` or `10`. (`Manage Server`)
- **`!automod timeout <duration|off>`** — Set the timeout applied to spammers,
  for example `10m`. (`Manage Server`)
- **`!automod status`** — Show the active automod rules. (`Manage Server`)

## Logging

- **`!logs`** — Show the configured channel for every event type. (`Everyone`)
  Aliases: `!logging`
- **`!logs status`** — Show the configured channel for every event type.
  (`Everyone`)
- **`!logs set <event> <#channel|off>`** — Set or disable the channel for an
  event. Events: `join_leave`, `message_delete`, `message_edit`, `role_change`,
  `nickname_change`, `voice`, `moderation`, `channel_events`.
  (`Manage Server`)
- **`!logs history [event] [limit]`** — Show recent stored activity logs; default
  10. (`Moderator`)
- **`!logs test <event>`** — Send a test log to the configured channel for an
  event. (`Manage Server`)

## Reaction roles

- **`!reactionrole`** — Show reaction-role mappings in this server.
  (`Manage Roles`) Aliases: `!rr`
- **`!reactionrole add <msg_id|link> <emoji> @role`** — Map an emoji on a message
  to a role. (`Manage Roles`)
- **`!reactionrole remove <msg_id|link> <emoji>`** — Remove an emoji-to-role
  mapping. (`Manage Roles`)
- **`!reactionrole list`** — List reaction-role mappings in this server.
  (`Manage Roles`)

## Server tools

- **`!slowmode <duration|off> [#channel]`** — Set channel slowmode, for example
  `10s`. (`Manage Channels`) Aliases: `!slow`
- **`!embed #channel "Title" "Description" [color] [image_url]`** — Post a custom
  embed. Use quotes for multi-word values. (`Manage Messages`) Aliases:
  `!sayembed`
- **`!poll Question | Option 1 | Option 2`** — Create a poll with 2–10 options.
  (`Manage Messages`)
- **`!poll results <message_id>`** — Show live results for a poll message in the
  channel. (`Manage Messages`)
- **`!poll end <message_id>`** — Close a poll and post its final results.
  (`Manage Messages`)

## Temporary voice

- **`!tempvoice`** — Show temporary voice configuration and active rooms.
  (`Everyone`) Aliases: `!tv`
- **`!tempvoice status`** — Show the trigger channel, category, limit, and
  template. (`Everyone`)
- **`!tempvoice setup <voice_channel> [category]`** — Set the join-to-create
  trigger channel and optional category. (`Manage Channels`)
- **`!tempvoice trigger <voice_channel>`** — Change the join-to-create trigger
  channel. (`Manage Channels`)
- **`!tempvoice category <category|none>`** — Set the creation category or use
  `none` for top level. (`Manage Channels`)
- **`!tempvoice defaultlimit <0-99>`** — Set the default member limit for new
  rooms; 0 means unlimited. (`Manage Channels`)
- **`!tempvoice template <text>`** — Set the room name template. Supports
  `{user}`, `{display_name}`, and `{member_number}`. (`Manage Channels`)
- **`!tempvoice name <name>`** — Rename your temporary channel. (`Room owner`)
- **`!tempvoice size <0-99>`** — Change your temporary channel member limit.
  (`Room owner`)
- **`!tempvoice lock`** — Prevent new members from joining your room.
  (`Room owner`)
- **`!tempvoice unlock`** — Allow members to join your room again.
  (`Room owner`)
- **`!tempvoice kick @member`** — Disconnect a member from your temporary
  channel. (`Room owner`)
- **`!tempvoice claim`** — Claim ownership when the previous owner left.
  (`Room member`)
- **`!tempvoice delete`** — Delete your temporary channel. (`Room owner`)

## Voice control

- **`!join <voice_channel>`** — Join a voice channel by ID or mention, or join
  your current voice channel if omitted. (`Move Members`)
- **`!leave`** — Disconnect the bot from its current voice channel.
  (`Move Members`)

## Automations

All schedule fields use five-field UTC cron expressions.

- **`!automation`** — List automations for this server. (`Manage Server`)
  Aliases: `!automations`, `!auto`
- **`!automation list`** — List automations with IDs, types, and schedules.
  (`Manage Server`)
- **`!automation status`** — Show scheduler status, cron help, and automation
  types. (`Manage Server`)
- **`!automation announcement <name> "<cron>" #channel <message>`** — Scheduled
  announcement. (`Manage Server`)
- **`!automation message <name> "<cron>" #channel <message>`** — Recurring
  automated message. (`Manage Server`)
- **`!automation reminder <name> "<cron>" #channel <message>`** — Recurring
  reminder; mentions in the message are allowed. (`Manage Server`)
- **`!automation stats <name> "<cron>" [#channel]`** — Schedule periodic server
  statistics snapshots. (`Manage Server`)
- **`!automation autorole <name> @role...`** — Assign roles automatically when
  members join. (`Manage Server`)
- **`!automation welcome <name> #channel <message>`** — Send an extra welcome
  message on join. (`Manage Server`)
- **`!automation goodbye <name> #channel <message>`** — Send an extra goodbye
  message when a member leaves. (`Manage Server`)
- **`!automation response <name> "<trigger>" <response>`** — Reply automatically
  when a message contains a trigger phrase. (`Manage Server`)
- **`!automation toggle <id|name>`** — Enable or pause an automation.
  (`Manage Server`)
- **`!automation remove <id|name>`** — Delete an automation. (`Manage Server`)

## Bot administration

- **`!botinfo`** — Show bot version, uptime, latency, and guild counts.
  (`Bot owner or server admin`)
- **`!dbping`** — Check Supabase connectivity using the service role.
  (`Bot owner or server admin`)
- **`!extensions`** — List loaded extensions and cogs.
  (`Bot owner or server admin`) Aliases: `!cogs`
- **`!prefix`** — Show the effective command prefix.
  (`Bot owner or server admin`)
- **`!reload <extension>`** — Reload a cog, for example `!reload general`.
  (`Bot owner`)
