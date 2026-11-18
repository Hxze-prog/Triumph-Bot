"use client";

import { useActionState } from "react";

import { saveWelcomeSettings } from "@/app/dashboard/settings/actions";
import { Panel } from "@/components/panel";
import {
  ChannelSelect,
  CheckboxCard,
  Field,
  inputClass,
} from "@/components/settings/field";
import { SaveBar } from "@/components/settings/save-bar";
import type { GuildDirectory } from "@/lib/discord";
import type { GuildSettings } from "@/lib/queries";
import { idleActionState } from "@/lib/settings";

const PLACEHOLDER_HINT =
  "Supports {user}, {mention}, {name}, {display_name}, {server}, {member_count}, {member_number}, {created_at}, {joined_at}, {account_age}, {server_age}.";

export function WelcomeSettingsForm({
  settings,
  directory,
}: {
  settings: GuildSettings;
  directory: GuildDirectory;
}) {
  const [state, action] = useActionState(
    saveWelcomeSettings,
    idleActionState,
  );

  return (
    <form action={action} className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="Welcome">
          <div className="space-y-4">
            <CheckboxCard
              name="welcome_enabled"
              label="Enable welcome messages"
              hint="Post a greeting when a member joins."
              defaultChecked={settings.welcome_enabled}
            />
            <Field label="Welcome channel" hint="Text or announcement channel.">
              <ChannelSelect
                name="welcome_channel_id"
                defaultValue={settings.welcome_channel_id}
                options={directory.textChannels}
                available={directory.available}
              />
            </Field>
            <Field label="Message" hint={PLACEHOLDER_HINT}>
              <textarea
                name="welcome_message"
                rows={3}
                defaultValue={settings.welcome_message ?? ""}
                placeholder="Welcome {user} to **{server}**! You are member #{member_number}."
                className={inputClass}
              />
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              <CheckboxCard
                name="welcome_embed_enabled"
                label="Embed style"
                defaultChecked={settings.welcome_embed_enabled}
              />
              <CheckboxCard
                name="welcome_banner_enabled"
                label="Generated banner"
                defaultChecked={settings.welcome_banner_enabled}
              />
            </div>
            <Field
              label="Banner template"
              hint="Subtitle rendered onto the welcome image."
            >
              <input
                name="welcome_banner_template"
                defaultValue={settings.welcome_banner_template ?? ""}
                placeholder="You are member #{member_number}"
                className={inputClass}
              />
            </Field>
            <CheckboxCard
              name="welcome_dm_enabled"
              label="Send a direct message"
              hint="The bot DMs new members after joining."
              defaultChecked={settings.welcome_dm_enabled}
            />
            <Field label="Direct message text" hint={PLACEHOLDER_HINT}>
              <textarea
                name="welcome_dm_message"
                rows={3}
                defaultValue={settings.welcome_dm_message ?? ""}
                placeholder="Welcome to {server}, {name}!"
                className={inputClass}
              />
            </Field>
          </div>
        </Panel>

        <div className="space-y-6">
          <Panel title="Goodbye">
            <div className="space-y-4">
              <CheckboxCard
                name="goodbye_enabled"
                label="Enable goodbye messages"
                hint="Post a notice when a member leaves."
                defaultChecked={settings.goodbye_enabled}
              />
              <Field label="Goodbye channel">
                <ChannelSelect
                  name="goodbye_channel_id"
                  defaultValue={settings.goodbye_channel_id}
                  options={directory.textChannels}
                  available={directory.available}
                />
              </Field>
              <Field label="Message" hint={PLACEHOLDER_HINT}>
                <textarea
                  name="goodbye_message"
                  rows={3}
                  defaultValue={settings.goodbye_message ?? ""}
                  placeholder="**{name}** left **{server}**. We now have {member_count} members."
                  className={inputClass}
                />
              </Field>
            </div>
          </Panel>

          <Panel title="Sync and placeholders">
            <div className="space-y-3 text-sm leading-relaxed text-mist-300">
              <p>
                Saved values go straight to Supabase. The bot caches settings
                for 30 seconds, so changes apply automatically on the next
                event after that window.
              </p>
              <p>
                Autoroles and dashboard access roles are still managed from
                Discord with{" "}
                <code className="text-gold-400">!autorole</code>.
              </p>
              {!directory.available ? (
                <p className="rounded-xl border border-amber-400/25 bg-amber-400/5 px-4 py-3 text-xs text-amber-200/90">
                  {directory.reason} Paste a channel ID such as{" "}
                  <code className="text-amber-100">123456789012345678</code>.
                </p>
              ) : null}
            </div>
          </Panel>
        </div>
      </div>

      <SaveBar
        state={state}
        label="Save welcome & goodbye"
        note="Applies to new join and leave events within 30 seconds."
      />
    </form>
  );
}
