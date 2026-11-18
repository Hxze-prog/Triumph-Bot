export type EventTone = "gold" | "royal" | "success" | "danger" | "muted";

const EVENT_LABELS: Record<string, string> = {
  join_leave: "Join / Leave",
  message_delete: "Message Delete",
  message_edit: "Message Edit",
  role_change: "Role Change",
  nickname_change: "Nickname Change",
  voice: "Voice Activity",
  channel_events: "Channel Events",
  moderation: "Moderation",
  automod: "AutoModeration",
};

const DANGER = new Set([
  "message_delete",
  "moderation",
  "automod",
  "ban",
  "unban",
  "kick",
  "timeout",
  "warn",
  "unwarn",
  "clear",
  "lock",
  "unlock",
]);

const ROYAL = new Set(["voice", "role_change", "nickname_change", "join_leave"]);

export function eventLabel(eventType: string): string {
  if (EVENT_LABELS[eventType]) {
    return EVENT_LABELS[eventType];
  }
  if (eventType === "untimeout") {
    return "Timeout Removed";
  }
  return eventType
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function eventTone(eventType: string): EventTone {
  if (DANGER.has(eventType)) {
    return "danger";
  }
  if (ROYAL.has(eventType)) {
    return "royal";
  }
  if (eventType.includes("join")) {
    return "success";
  }
  return "muted";
}
