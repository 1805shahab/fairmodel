import type { Asset, Audit, Evidence, Terms } from "./types";

export interface ReviewCase {
  id: string;
  asset_id: string;
  decision: string;
  category: string;
  note: string;
  status: string;
  created_at: string;
  updated_at: string;
  license_version: number;
  evidence_refs: string[];
  stale: boolean;
  requires_reconciliation: boolean;
  asset_name?: string;
  campaign_name?: string;
  events: {
    id: string;
    kind: string;
    note: string;
    actor_name: string;
    created_at: string;
  }[];
}
export interface Passport {
  id: string;
  asset_id: string;
  snapshot_at: string;
  disclaimer: string;
  private: boolean;
  asset: Asset;
  artist: { id: string; name: string };
  studio: { id: string; name: string };
  license: {
    id: string;
    title: string;
    version: number;
    approved_at: string | null;
    terms: Terms | null;
    source_review: { citations: Evidence[]; review_reasons: string[] };
  };
  audio_evidence: {
    sha256: string;
    hash_note: string;
    analysis_id: string | null;
    analysis_revision: string | null;
    processing: string;
    measured_at: string | null;
  };
  provenance: { transcription: string; compliance: string };
  history: {
    id: string;
    kind: string;
    created_at: string;
    origin: string;
    revision_hash: string;
    snapshot: {
      id: string;
      updated_at: string;
      status?: string;
      result?: {
        status?: string;
        provider?: string;
        latest_attempt_failed?: boolean;
      };
      note?: string;
      identity_confirmed?: boolean;
      use_authorized?: boolean;
    };
  }[];
  history_note: string;
  cases: ReviewCase[];
  charge_approvals: {
    id: string;
    artist_id: string;
    created_at: string;
    evidence_hash: string;
    note: string;
  }[];
  audit: (Audit & { actor_name: string })[];
  stages: { label: string; state: string; detail: string }[];
}

export interface Estimate {
  estimate_only: boolean;
  notice: string;
  scope_status: string;
  snapshot_at: string;
  license_version: number;
  calculation: import("./types").Calculation | null;
  reasons: string[];
  requirements: string[];
  citations: Evidence[];
  checks: { rule: string; outcome: string; explanation: string }[];
}
