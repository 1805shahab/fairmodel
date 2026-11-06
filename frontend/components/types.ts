export type Role = "artist" | "studio";
export interface Evidence {
  field: string;
  page: number;
  quote: string;
}
export interface Terms {
  artist: string | null;
  studio: string | null;
  start_date: string | null;
  end_date: string | null;
  permitted_media: string[] | null;
  territories: string[] | null;
  languages: string[] | null;
  campaigns: string[] | null;
  included_seconds: string | null;
  billing_basis: "per_asset" | "cumulative" | null;
  additional_rate: string | null;
  currency: "USD" | "EUR" | "GBP" | null;
  additional_usage_permitted: boolean | null;
  restricted_categories: string[] | null;
  special_conditions: string[];
  ambiguities: string[];
  evidence: Evidence[];
}
export interface License {
  id: string;
  title: string;
  status: string;
  artist_id: string;
  studio_id: string;
  version: number;
  terms: Terms;
  pages: { page: number; text: string }[];
  extraction_provider: string;
  error: string | null;
  created_at: string;
}
export interface Campaign {
  name: string;
  region: string | null;
  medium: string | null;
  language: string | null;
  category: string | null;
  generation_provider: string | null;
  intended_use_date: string;
}
export interface Calculation {
  spoken_seconds: string;
  prior_seconds: string;
  included_seconds: string;
  allowance_remaining: string;
  additional_seconds: string;
  rate: string;
  amount: string;
  currency: string;
  billing_basis: string;
  explanation: string;
  rounding: string;
}
export interface Royalty {
  id: string;
  asset_id: string;
  license_id: string;
  amount: string;
  currency: string;
  status: string;
  calculation: Calculation;
  created_at: string;
  decision_note: string | null;
}
export interface AudioResult {
  duration_seconds: string;
  spoken_seconds: string | null;
  format: string;
  sample_rate: number;
  channels: number;
  speech_segments: { start: number; end: number }[];
  transcript: string;
  timestamps: { start: number; end: number; text: string }[];
  provider: string;
  vad: string;
  measurement_note: string;
  measurement_uncertain: boolean;
  demo_fixture: boolean;
  speaker: { status: string; score: number | null; note: string };
}
export interface ReportResult {
  status: string;
  reasons: string[];
  calculation: Calculation | null;
  findings: {
    findings: {
      category: string;
      passage: string;
      explanation: string;
      possible_conflict: boolean;
      needs_review: boolean;
    }[];
    uncertainty: string[];
  };
  provider: string;
  metadata_note: string;
  legal_note: string;
  source_pages: Evidence[];
}
export interface Asset {
  id: string;
  license_id: string;
  license_version: number;
  original_name: string;
  campaign: Campaign;
  status: string;
  error: string | null;
  created_at: string;
  analysis?: { result: AudioResult } | null;
  report?: { result: ReportResult } | null;
  royalty?: Royalty | null;
}
export interface Invoice {
  id: string;
  provider_id: string;
  royalty_id: string;
  amount: string;
  currency: string;
  recipient: string;
  status: string;
  created_at: string;
  events?: { id: string; kind: string; created_at: string }[];
}
export interface Audit {
  id: string;
  action: string;
  entity_id: string;
  created_at: string;
  detail: Record<string, unknown>;
}
export interface Analytics {
  totals_by_currency: Record<
    string,
    { proposed: string; approved: string; paid_simulated: string }
  >;
  license_count: number;
  asset_count: number;
  review_count: number;
  pending_approvals: number;
  rows: Royalty[];
}
export interface Integrations {
  gemini: { configured: boolean; model: string };
  groq: { configured: boolean; model: string };
  audio_tools: { ffmpeg: boolean; ffprobe: boolean };
  speaker_verification: { enabled: boolean; status: string };
  paypal: string;
  fixtures_available: boolean;
}
