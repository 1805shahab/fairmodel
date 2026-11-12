export interface VoiceGrant {
  provider?: "gemini" | "fish";
  id: string;
  reference_id: string;
  license_id: string;
  license_version: number;
  license_title: string;
  status: "ACTIVE" | "REVOKED" | "STALE";
  note: string;
  created_at: string;
}
export interface SpeechGeneration {
  provider?: "gemini" | "fish";
  id: string;
  grant_id: string;
  status: "RUNNING" | "SUCCEEDED" | "FAILED";
  asset_id: string | null;
  error: string | null;
  created_at: string;
  receipt: {
    service?: string;
    mode?: string;
    succeeded_at?: string;
    requested_model?: string;
    requested_replication_model?: string;
  };
}
