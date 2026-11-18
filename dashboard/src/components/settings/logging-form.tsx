"use client";

import { useActionState } from "react";

import { saveLoggingSettings } from "@/app/dashboard/settings/actions";
import { Panel } from "@/components/panel";
import { ChannelSelect, Field } from "@/components/settings/field";
import { SaveBar } from "@/components/settings/save-bar";
import type { GuildDirectory } from "@/lib/discord";
import type { GuildSettings } from "@/lib/queries";
import { idleActionState, logEventFields } from "@/lib/settings";

export function LoggingSettingsForm({
  settings,
  directory,
}: {
  settings: GuildSettings;
  directory: GuildDirectory;
}) {
  const [state, action] = useActionState(
    saveLoggingSettings,
    idleActionState,
  );

  const configured = logEventFields.filter((field) =>
    Boolean(settings[field.key]),
  ).length;

  return (
    <form action={action} className="space-y-6">
      <Panel
        title="Event channels"
        description={`${configured} of ${logEventFields.length} event types have a destination. Set a channel to enable an event.`}
      >
        <div className="grid gap-5 sm:grid-cols-2">
          {logEventFields.map((field) => (
            <Field
              key={field.key}
              label={field.label}
              hint={`${field.description} · ${field.event}`}
            >
              <ChannelSelect
                name={field.key}
                defaultValue={settings[field.key]}
                options={directory.textChannels}
                available={directory.available}
              />
            </Field>
          ))}
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
        label="Save logging channels"
        note="New events are routed after the bot refreshes its cache (30 seconds)."
      />
    </form>
  );
}
