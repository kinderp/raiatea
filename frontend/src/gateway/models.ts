export type CatalogFreshness = 'fresh' | 'reconcile-required' | 'unknown';
export type EvidenceMeasurementState = 'measured' | 'not-established';

export interface WarningSummary {
  state: EvidenceMeasurementState;
  count: number | null;
  highest_severity: string | null;
}

export interface LibraryItem {
  item_ref: string;
  catalog_entry_ref: string;
  source_ref_id: string | null;
  logical_candidate_ref: string;
  stored_instance_ref: string;
  display: {
    title: string | null;
    fallback_name: string;
    media_type: string;
    kind: 'document-source';
  };
  location: {
    scope_ref: string;
    current_relative_location: string | null;
    availability: string;
    history_count: number;
  };
  content: {
    byte_length: number | null;
    fingerprint_summary: string | null;
  };
  extraction: {
    state: 'current' | 'not-established';
    current_representation_id?: string;
    provider_profile_summary?: {
      provider_id?: string;
      version?: string;
      route_profile?: string;
    };
  };
  freshness: {
    catalog: CatalogFreshness;
    content: 'current' | 'not-established';
  };
  warnings: WarningSummary;
  capabilities: string[];
}

export interface LibraryPage {
  catalog_freshness: CatalogFreshness;
  counts_basis: 'current' | 'last-known';
  basis: string;
  total_known_items: number;
  cursor: string | null;
  next_cursor: string | null;
  items: LibraryItem[];
}

export interface RepresentationSummary {
  representation_id: string;
  unit_count: number;
  coordinate_families: string[];
  evidence_state_by_family: Record<string, string[]>;
}

export interface ExtractionSummary {
  state: 'current';
  state_family: string;
  source_ref_id: string;
  provider: {
    provider_id?: string;
    version?: string;
    route_profile?: string;
  };
  run: Record<string, unknown>;
  representation: RepresentationSummary;
  rights: Record<string, unknown> | null;
  provenance: Record<string, unknown>;
  diagnostics: {
    state: EvidenceMeasurementState;
    count: number | null;
    by_severity: Record<string, number>;
    items: Array<Record<string, unknown>>;
  };
  warnings: WarningSummary;
}

export interface SourceDetail {
  item_ref: string;
  catalog_entry_ref: string;
  logical_candidate_ref: string;
  stored_instance_ref: string;
  source_ref_id: string | null;
  display: LibraryItem['display'];
  locations: LibraryItem['location'][];
  availability: string;
  media_type: string;
  content_identity: LibraryItem['content'];
  catalog_freshness: CatalogFreshness;
  current_extractions: ExtractionSummary[];
  representations: RepresentationSummary[];
  evidence_summaries: Array<Record<string, unknown>>;
  processing_runs: Array<Record<string, unknown>>;
  provenance_summary: Record<string, unknown> | null;
  rights_summary: Record<string, unknown> | null;
  diagnostics: ExtractionSummary['diagnostics'];
  warnings: Array<Record<string, unknown>>;
  warning_summary: WarningSummary;
  available_panels: string[];
  available_actions: string[];
}

export type QueryField =
  | 'source_ref_id'
  | 'media_type'
  | 'extracted_text'
  | 'semantic_type'
  | 'resource'
  | 'provider_id'
  | 'route_profile';

export interface QueryCriterion {
  field: QueryField;
  operator: 'eq' | 'contains' | 'has';
  value: string;
}

export interface QueryPlan {
  criteria: QueryCriterion[];
  sort_field: 'source_ref_id' | 'media_type' | 'unit_count';
  descending: boolean;
}

export interface SearchRow {
  item: LibraryItem;
  matched_content_refs: string[];
  match_snippets: string[];
}

export interface SearchPage {
  freshness: 'fresh' | 'stale';
  blocked_reason: string | null;
  interpreted_plan: QueryPlan;
  total_known_matches: number | null;
  cursor: string | null;
  next_cursor: string | null;
  items: SearchRow[];
}

export interface GatewayStatus {
  mode: 'demo' | 'live';
  label: string;
  detail: string;
}
