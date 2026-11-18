"use client";

import { useActionState } from "react";

import { saveAutomodSettings } from "@/app/dashboard/settings/actions";
import { Panel } from "@/components/panel";
import {
  CheckboxCard,
  Field,
  inputClass,
} from "@/components/settings/field";
import { SaveBar } from "@/components/settings/save-bar";
import type { GuildSettings } from "@/lib/queries";
import { idleActionState } from "@/lib/settings";

export function AutomodSettingsForm({ settings }: { settings: GuildSettings }) {
  const [state, action] = useActionState(
    saveAutomodSettings,
    idleActionState,
  );

  return (
    <form action={action} className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <Panel title="AutoModeration">
          <div className="space-y-3">
            <CheckboxCard
              name="automod_anti_spam_enabled"
              label="Anti-spam"
              hint="Time out members who exceed the message threshold."
              defaultChecked={settings.automod_anti_spam_enabled}
            />
            <CheckboxCard
              name="automod_anti_link_enabled"
              label="Anti-link"
              hint="Delete links unless the domain is allowlisted."
              defaultChecked={settings.automod_anti_link_enabled}
            />
            <CheckboxCard
              name="automod_anti_invite_enabled"
              label="Anti-invite"
              hint="Delete Discord invite links."
              defaultChecked={settings.automod_anti_invite_enabled}
            />
          </div>
        </Panel>

        <Panel title="Spam thresholds">
          <div className="space-y-4">
            <Field
              label="Messages before triggering"
              hint="1–50 messages in the window."
            >
              <input
                type="number"
                name="automod_spam_threshold"
                min={1}
                max={50}
                step={1}
                defaultValue={settings.automod_spam_threshold}
                className={inputClass}
              />
            </Field>
            <Field
              label="Spam window (seconds)"
              hint="1 second to 1 hour. Messages inside this window are counted."
            >
              <input
                type="number"
                name="automod_spam_interval_seconds"
                min={1}
                max={3600}
                step={1}
                defaultValue={settings.automod_spam_interval_seconds}
                className={inputClass}
              />
            </Field>
            <Field
              label="Timeout duration (seconds)"
              hint="0 disables the timeout. Maximum is 28 days (2419200)."
            >
              <input
                type="number"
                name="automod_timeout_seconds"
                min={0}
                max={2419200}
                step={1}
                defaultValue={settings.automod_timeout_seconds}
                className={inputClass}
              />
            </Field>
            <p className="rounded-xl border border-navy-800 bg-navy-950/50 px-4 py-3 text-xs leading-relaxed text-mist-400">
              Discord caps timeouts at 28 days. The bot also clamps values
              before applying them.
            </p>
          </div>
        </Panel>
      </div>

      <SaveBar
        state={state}
        label="Save automoderation"
        note="Applies to new messages within 30 seconds."
      />
    </form>
  );
}
