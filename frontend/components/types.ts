export type Role = "artist" | "studio";
export interface Evidence {
  field: string;
  page: number;
  quote: string;
  verified?: boolean;
  origin?: string;
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
  source_review?: {
    citations: Evidence[];
    review_reasons: string[];
    missing_fields: string[];
  } | null;
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
  eligible_for_charge: boolean;
  approval_current: boolean;
  artist_name?: string;
  studio_name?: string;
  license_title?: string;
  campaign_name?: string;
  compliance_status?: string;
  invoice_status?: string;
  payment_provider?: string;
  received_amount?: string;
  outstanding_amount?: string;
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
  eligible_for_charge: boolean;
  policy_version: number;
  primary_reason?: string;
  next_action?: string;
  assessment_reused?: boolean;
  latest_attempt_failed?: boolean;
  content_input_hash?: string;
  satisfied_conditions?: { rule: string; explanation: string }[];
  unresolved_conditions?: string[];
  billing_usage?: {
    canonical_asset_id: string;
    disposition: string;
    reconciliation_required: boolean;
    unresolved: unknown[];
    member_asset_ids: string[];
  };
  rule_checks?: {
    rule: string;
    outcome: string;
    explanation: string;
    kind?: string;
    condition?: string;
  }[];
  substantiated_violations?: { rule: string; explanation: string }[];
  overlap?: { asset_id: string; kind: string; basis: string }[];
  source_review?: {
    missing_fields: string[];
    recovered_condition_citations: number;
  };
  provider_receipt?: {
    service?: string;
    mode?: string;
    returned_model?: string | null;
    response_id?: string | null;
    succeeded_at?: string;
  };
  transcription_provider: string;
  transcription_mode: string;
  assessment_fixture: boolean;
  authorization: {
    status?: string;
    identity_confirmed?: boolean;
    use_authorized?: boolean;
    method?: string;
  };
}
export interface UsageAuthorization {
  id: string;
  artist_id: string;
  status: string;
  identity_confirmed: boolean;
  use_authorized: boolean;
  note: string;
  updated_at: string;
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
  authorization?: UsageAuthorization | null;
  invoice?: Invoice | null;
  processing_state?: string;
  compliance_state?: string;
  authorization_state?: string;
  royalty_state?: string;
  invoice_state?: string;
  workflow_stage?: string;
  next_action?: string;
}
export interface ComparedAsset {
  id: string;
  name: string;
  license_id: string;
  license_version: number;
  campaign_name: string;
  duration_seconds: string | null;
  spoken_seconds: string | null;
  transcript: string;
  royalty_status: string | null;
  invoice_status: string | null;
}
export interface OverlapDecisionRecord {
  id: string;
  asset_id: string;
  related_asset_id: string;
  decision: "SAME_USAGE" | "SEPARATE_USAGE" | "UNCERTAIN";
  reviewer_id: string;
  note: string;
  created_at: string;
  license_version: number;
  evidence_hash: string;
  previous_id: string | null;
  canonical_asset_id: string;
  state?: string;
}
export interface OverlapPair {
  current: ComparedAsset;
  related: ComparedAsset;
  evidence: {
    kind: string;
    basis: string;
    matched_words?: number;
    current_excerpt?: string;
    related_excerpt?: string;
  };
  review: OverlapDecisionRecord | null;
  history: OverlapDecisionRecord[];
}
export interface OverlapDetail {
  asset_id: string;
  pairs: OverlapPair[];
  incoming: { asset_id: string; decision: string; state: string }[];
  usage: {
    canonical_asset_id: string;
    disposition: string;
    reconciliation_required: boolean;
    unresolved: unknown[];
  } | null;
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
  eligible_for_send?: boolean;
  provider?: "mock" | "paypal_sandbox";
  simulated?: boolean;
  notice?: string;
  sandbox?: {
    issuer: string;
    invoice_number: string;
    provider_status: string;
    payment_url: string | null;
    due_date: string | null;
    paid_amount: string;
    due_amount: string | null;
    refunded_amount: string;
    last_synced_at: string | null;
    error: string | null;
    transactions: Record<string, unknown>[];
  } | null;
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
    {
      proposed: string;
      approved: string;
      paid_simulated: string;
      paid_sandbox?: string;
      outstanding?: string;
    }
  >;
  license_count: number;
  asset_count: number;
  review_count: number;
  pending_approvals: number;
  rows: Royalty[];
  active_license_count?: number;
  outstanding_invoice_count?: number;
  included_usage_count?: number;
  review_queue?: Asset[];
}
export interface Integrations {
  demo_mode: boolean;
  gemini: { configured: boolean; model: string };
  groq: { configured: boolean; model: string };
  audio_tools: { ffmpeg: boolean; ffprobe: boolean };
  speaker_verification: { enabled: boolean; status: string };
  paypal: string;
  payment_provider?: "mock" | "paypal_sandbox";
  payment_notice?: string;
  paypal_configuration?: {
    credentials_configured: boolean;
    merchant_configured: boolean;
    buyer_configured: boolean;
    drafts_enabled: boolean;
    sending_enabled: boolean;
    webhook_configured: boolean;
  };
  fixtures_available: boolean;
}
