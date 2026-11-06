"use client";
import { Field } from "./ui";
import type { Campaign } from "./types";
export function emptyCampaign(): Campaign {
  return {
    name: "",
    region: "",
    medium: "",
    language: "",
    category: "",
    generation_provider: "",
    intended_use_date: new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Karachi",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }).format(new Date()),
  };
}
export default function CampaignForm({
  value,
  onChange,
}: {
  value: Campaign;
  onChange: (value: Campaign) => void;
}) {
  const update = (key: keyof Campaign, v: string) =>
    onChange({ ...value, [key]: v });
  return (
    <div className="form-grid">
      <Field label="Campaign name">
        <input
          required
          minLength={2}
          maxLength={160}
          value={value.name}
          onChange={(e) => update("name", e.target.value)}
          placeholder="Northstar launch"
        />
      </Field>
      <Field label="Intended use date">
        <input
          type="date"
          required
          value={value.intended_use_date}
          onChange={(e) => update("intended_use_date", e.target.value)}
        />
      </Field>
      <Field label="Declared country / region">
        <input
          maxLength={100}
          value={value.region || ""}
          onChange={(e) => update("region", e.target.value)}
          placeholder="US"
        />
      </Field>
      <Field label="Platform / medium">
        <input
          maxLength={100}
          value={value.medium || ""}
          onChange={(e) => update("medium", e.target.value)}
          placeholder="online advertising"
        />
      </Field>
      <Field label="Declared language">
        <input
          maxLength={100}
          value={value.language || ""}
          onChange={(e) => update("language", e.target.value)}
          placeholder="English"
        />
      </Field>
      <Field label="Campaign category">
        <input
          maxLength={100}
          value={value.category || ""}
          onChange={(e) => update("category", e.target.value)}
          placeholder="consumer products"
        />
      </Field>
      <Field label="Generation provider (optional)">
        <input
          maxLength={120}
          value={value.generation_provider || ""}
          onChange={(e) => update("generation_provider", e.target.value)}
          placeholder="Provider or recording source"
        />
      </Field>
    </div>
  );
}
