"use client";

import { useActionState } from "react";

import { saveTempVoiceSettings } from "@/app/dashboard/settings/actions";
import { Panel } from "@/components/panel";
import { ChannelSelect, Field, inputClass } from "@/components/settings/field";
import { SaveBar } from "@/components/settings/save-bar";
import type { GuildDirectory } from "@/lib/discord";
import type { GuildSettings } from "@/lib/queries";
import { idleActionState } from "@/lib/settings";

export function TempVoiceSettingsForm({
  settings,
  directory,
}: {
  settings: GuildSettings;
  directory: GuildDirectory;
}) {
  const [state, action] = useActionState(
    saveTempVoiceSettings,
    idleActionState,
  );

  return (
    <form action={action} className="space-y-6">
      <Panel
        title="Join-to-create"
        description="Members join the trigger channel and receive their own temporary room."
      >
        <div className="grid gap-5 sm:grid-cols-2">
          <Field
            label="Trigger channel"
            hint="Voice or stage channel that creates a room."
          >
            <ChannelSelect
              name="temp_voice_trigger_channel_id"
              defaultValue={settings.temp_voice_trigger_channel_id}
              options={directory.voiceChannels}
              available={directory.available}
            />
          </Field>
          <Field label="Category" hint="New rooms are created inside it.">
            <ChannelSelect
              name="temp_voice_category_id"
              defaultValue={settings.temp_voice_category_id}
              options={directory.categories}
              available={directory.available}
            />
          </Field>
          <Field
            label="Default member limit"
            hint="0 means unlimited. Discord allows 0–99."
          >
            <input
              type="number"
              name="temp_voice_default_limit"
              min={0}
              max={99}
              step={1}
              defaultValue={settings.temp_voice_default_limit}
              className={inputClass}
            />
          </Field>
          <Field
            label="Name template"
            hint="Supports {user}, {display_name}, and {member_number}. Max 100 characters."
          >
            <input
              name="temp_voice_name_template"
              defaultValue={settings.temp_voice_name_template}
              placeholder="{user}'s Channel"
              maxLength={100}
              className={inputClass}
            />
          </Field>
        </div>
        {!directory.available ? (
          <p className="mt-5 rounded-xl border border-amber-400/25 bg-amber-400/5 px-4 py-3 text-xs text-amber-200/90">
            {directory.reason} Paste channel IDs such as{" "}
            <code className="text-amber-100">123456789012345678</code>.
          </p>
        ) : null}
      </Panel>

      <SaveBar
        state={state}
        label="Save temporary voice"
        note="Applies to new room creations after the 30 second cache refresh."
      />
    </form>
  );
}
