import type {
  CatalogFreshness,
  EvidenceEnvelopeView,
  ExtractionSummary,
  GatewayStatus,
  LibraryItem,
  LibraryPage,
  QueryCriterion,
  QueryField,
  QueryPlan,
  RepresentationPage,
  RepresentationSummary,
  RepresentationUnit,
  SearchPage,
  SearchRow,
  SourceDetail,
  WarningSummary,
} from './models';

export const GUI_BRIDGE_VERSION = 'raiatea.gui-application-bridge.0.1.0';

export const GUI_BRIDGE_METHODS = [
  'gateway.status',
  'library.page',
  'source.detail',
  'search.page',
  'representation.page',
] as const;

export type GuiBridgeMethod = (typeof GUI_BRIDGE_METHODS)[number];

const forbiddenHostAuthorityKeys = new Set([
  'path',
  'filepath',
  'file_path',
  'host_path',
  'filesystem_path',
  'absolute_path',
  'root',
  'scope_root',
  'catalog_store',
  'catalog_store_path',
  'source_path',
  'working_directory',
  'cwd',
]);

const queryFields = new Set<QueryField>([
  'source_ref_id',
  'media_type',
  'extracted_text',
  'semantic_type',
  'resource',
  'provider_id',
  'route_profile',
]);
const queryOperators = new Set(['eq', 'contains', 'has']);
const querySortFields = new Set(['source_ref_id', 'media_type', 'unit_count']);
const catalogFreshnessStates = new Set<CatalogFreshness>([
  'fresh',
  'reconcile-required',
  'unknown',
]);

export class BridgeValidationError extends Error {}

type JsonRecord = Record<string, unknown>;

function fail(message: string): never {
  throw new BridgeValidationError(message);
}

function record(value: unknown, label: string): JsonRecord {
  if (typeof value !== 'object' || value === null || Array.isArray(value)) {
    fail(`${label}-must-be-object`);
  }
  return value as JsonRecord;
}

function stringValue(value: unknown, label: string): string {
  if (typeof value !== 'string' || value.length === 0) {
    fail(`${label}-must-be-string`);
  }
  return value;
}

function nullableString(value: unknown, label: string): string | null {
  if (value === null) return null;
  return stringValue(value, label);
}

function numberValue(value: unknown, label: string): number {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < 0) {
    fail(`${label}-must-be-nonnegative-integer`);
  }
  return value;
}

function nullableNumber(value: unknown, label: string): number | null {
  if (value === null) return null;
  return numberValue(value, label);
}

function booleanValue(value: unknown, label: string): boolean {
  if (typeof value !== 'boolean') fail(`${label}-must-be-boolean`);
  return value;
}

function stringArray(value: unknown, label: string): string[] {
  if (!Array.isArray(value)) fail(`${label}-must-be-array`);
  return value.map((entry, index) => stringValue(entry, `${label}-${index}`));
}

function objectArray(value: unknown, label: string): JsonRecord[] {
  if (!Array.isArray(value)) fail(`${label}-must-be-array`);
  return value.map((entry, index) => record(entry, `${label}-${index}`));
}

function assertNoHostAuthority(value: unknown, trail = 'payload'): void {
  if (Array.isArray(value)) {
    value.forEach((child, index) => assertNoHostAuthority(child, `${trail}[${index}]`));
    return;
  }
  if (typeof value !== 'object' || value === null) return;
  for (const [key, child] of Object.entries(value)) {
    const normalized = key.trim().toLocaleLowerCase().replaceAll('-', '_');
    if (forbiddenHostAuthorityKeys.has(normalized)) {
      fail(`bridge-host-authority-field-forbidden:${trail}.${key}`);
    }
    assertNoHostAuthority(child, `${trail}.${key}`);
  }
}

function relativeLocation(value: unknown): string | null {
  const location = nullableString(value, 'current-relative-location');
  if (location === null) return null;
  if (
    location.startsWith('/') ||
    location.startsWith('~') ||
    location.includes('\\') ||
    /^[A-Za-z]:/.test(location)
  ) {
    fail('current-relative-location-must-be-relative');
  }
  const parts = location.split('/');
  if (parts.some((part) => part.length === 0 || part === '.' || part === '..')) {
    fail('current-relative-location-invalid');
  }
  return location;
}

function fingerprint(value: unknown): string | null {
  const observed = nullableString(value, 'fingerprint-summary');
  if (observed === null) return null;
  if (!/^sha256:[0-9a-f]{64}$/.test(observed)) {
    fail('fingerprint-summary-invalid');
  }
  return observed;
}

function validateWarningSummary(value: unknown): WarningSummary {
  const row = record(value, 'warning-summary');
  const state = stringValue(row.state, 'warning-state');
  if (state !== 'measured' && state !== 'not-established') {
    fail('warning-state-invalid');
  }
  const count = nullableNumber(row.count, 'warning-count');
  const highest = nullableString(row.highest_severity, 'warning-highest-severity');
  if (state === 'not-established' && count !== null) {
    fail('warning-count-must-be-null-when-not-established');
  }
  return { state, count, highest_severity: highest };
}

function validateCatalogFreshness(value: unknown): CatalogFreshness {
  const state = stringValue(value, 'catalog-freshness') as CatalogFreshness;
  if (!catalogFreshnessStates.has(state)) fail('catalog-freshness-invalid');
  return state;
}

function validateLocation(value: unknown): LibraryItem['location'] {
  const row = record(value, 'library-location');
  return {
    scope_ref: stringValue(row.scope_ref, 'location-scope-ref'),
    current_relative_location: relativeLocation(row.current_relative_location),
    availability: stringValue(row.availability, 'location-availability'),
    history_count: numberValue(row.history_count, 'location-history-count'),
  };
}

function validateContent(value: unknown): LibraryItem['content'] {
  const row = record(value, 'library-content');
  return {
    byte_length: nullableNumber(row.byte_length, 'content-byte-length'),
    fingerprint_summary: fingerprint(row.fingerprint_summary),
  };
}

function validateDisplay(value: unknown): LibraryItem['display'] {
  const row = record(value, 'library-display');
  if (row.kind !== 'document-source') fail('display-kind-invalid');
  return {
    title: nullableString(row.title, 'display-title'),
    fallback_name: stringValue(row.fallback_name, 'display-fallback-name'),
    media_type: stringValue(row.media_type, 'display-media-type'),
    kind: 'document-source',
  };
}

function validateExtractionProjection(value: unknown): LibraryItem['extraction'] {
  const row = record(value, 'library-extraction');
  const state = stringValue(row.state, 'library-extraction-state');
  if (state === 'not-established') return { state };
  if (state !== 'current') fail('library-extraction-state-invalid');
  const currentRepresentation = stringValue(
    row.current_representation_id,
    'current-representation-id',
  );
  const providerRow = record(row.provider_profile_summary, 'provider-profile-summary');
  const provider: NonNullable<LibraryItem['extraction']['provider_profile_summary']> = {};
  if (providerRow.provider_id !== undefined) {
    provider.provider_id = stringValue(providerRow.provider_id, 'provider-id');
  }
  if (providerRow.version !== undefined) {
    provider.version = stringValue(providerRow.version, 'provider-version');
  }
  if (providerRow.route_profile !== undefined) {
    provider.route_profile = stringValue(providerRow.route_profile, 'route-profile');
  }
  return {
    state,
    current_representation_id: currentRepresentation,
    provider_profile_summary: provider,
  };
}

export function validateLibraryItem(value: unknown): LibraryItem {
  assertNoHostAuthority(value);
  const row = record(value, 'library-item');
  const sourceRef = nullableString(row.source_ref_id, 'source-ref-id');
  const freshnessRow = record(row.freshness, 'item-freshness');
  const catalog = validateCatalogFreshness(freshnessRow.catalog);
  const contentState = stringValue(freshnessRow.content, 'content-freshness');
  if (contentState !== 'current' && contentState !== 'not-established') {
    fail('content-freshness-invalid');
  }
  const extraction = validateExtractionProjection(row.extraction);
  const capabilities = stringArray(row.capabilities, 'capabilities');
  if (
    catalog !== 'fresh' &&
    (sourceRef !== null ||
      contentState === 'current' ||
      extraction.state === 'current' ||
      capabilities.includes('view-original') ||
      capabilities.includes('request-extraction'))
  ) {
    fail('nonfresh-item-cannot-claim-current-source');
  }
  return {
    item_ref: stringValue(row.item_ref, 'item-ref'),
    catalog_entry_ref: stringValue(row.catalog_entry_ref, 'catalog-entry-ref'),
    source_ref_id: sourceRef,
    logical_candidate_ref: stringValue(
      row.logical_candidate_ref,
      'logical-candidate-ref',
    ),
    stored_instance_ref: stringValue(row.stored_instance_ref, 'stored-instance-ref'),
    display: validateDisplay(row.display),
    location: validateLocation(row.location),
    content: validateContent(row.content),
    extraction,
    freshness: { catalog, content: contentState },
    warnings: validateWarningSummary(row.warnings),
    capabilities,
  };
}

export function validateLibraryPage(value: unknown): LibraryPage {
  assertNoHostAuthority(value);
  const row = record(value, 'library-page');
  const freshness = validateCatalogFreshness(row.catalog_freshness);
  const countsBasis = stringValue(row.counts_basis, 'counts-basis');
  if (countsBasis !== 'current' && countsBasis !== 'last-known') {
    fail('counts-basis-invalid');
  }
  if ((freshness === 'fresh') !== (countsBasis === 'current')) {
    fail('library-freshness-counts-basis-mismatch');
  }
  if (!Array.isArray(row.items)) fail('library-items-must-be-array');
  const items = row.items.map((item) => validateLibraryItem(item));
  const total = numberValue(row.total_known_items, 'total-known-items');
  if (total < items.length) fail('total-known-items-smaller-than-page');
  return {
    catalog_freshness: freshness,
    counts_basis: countsBasis,
    basis: stringValue(row.basis, 'library-basis'),
    total_known_items: total,
    cursor: nullableString(row.cursor, 'library-cursor'),
    next_cursor: nullableString(row.next_cursor, 'library-next-cursor'),
    items,
  };
}

function validateRepresentationSummary(value: unknown): RepresentationSummary {
  const row = record(value, 'representation-summary');
  const evidence = record(row.evidence_state_by_family, 'evidence-state-by-family');
  const normalizedEvidence: Record<string, string[]> = {};
  for (const [key, states] of Object.entries(evidence)) {
    normalizedEvidence[key] = stringArray(states, `evidence-state-${key}`);
  }
  return {
    representation_id: stringValue(row.representation_id, 'representation-id'),
    unit_count: numberValue(row.unit_count, 'representation-unit-count'),
    coordinate_families: stringArray(
      row.coordinate_families,
      'coordinate-families',
    ),
    evidence_state_by_family: normalizedEvidence,
  };
}

function validateExtractionSummary(value: unknown): ExtractionSummary {
  const row = record(value, 'extraction-summary');
  if (row.state !== 'current') fail('extraction-summary-state-invalid');
  const providerRaw = record(row.provider, 'extraction-provider');
  const provider: ExtractionSummary['provider'] = {};
  for (const key of ['provider_id', 'version', 'route_profile'] as const) {
    if (providerRaw[key] !== undefined) {
      provider[key] = stringValue(providerRaw[key], `extraction-provider-${key}`);
    }
  }
  const diagnostics = record(row.diagnostics, 'diagnostics');
  const diagnosticState = stringValue(diagnostics.state, 'diagnostics-state');
  if (diagnosticState !== 'measured' && diagnosticState !== 'not-established') {
    fail('diagnostics-state-invalid');
  }
  const bySeverityRaw = record(diagnostics.by_severity, 'diagnostics-by-severity');
  const bySeverity: Record<string, number> = {};
  for (const [key, count] of Object.entries(bySeverityRaw)) {
    bySeverity[key] = numberValue(count, `diagnostic-count-${key}`);
  }
  return {
    state: 'current',
    state_family: stringValue(row.state_family, 'state-family'),
    source_ref_id: stringValue(row.source_ref_id, 'extraction-source-ref-id'),
    provider,
    run: record(row.run, 'processing-run-summary'),
    representation: validateRepresentationSummary(row.representation),
    rights: row.rights === null ? null : record(row.rights, 'rights-summary'),
    provenance: record(row.provenance, 'provenance-summary'),
    diagnostics: {
      state: diagnosticState,
      count: nullableNumber(diagnostics.count, 'diagnostics-count'),
      by_severity: bySeverity,
      items: objectArray(diagnostics.items, 'diagnostic-items'),
    },
    warnings: validateWarningSummary(row.warnings),
  };
}

export function validateSourceDetail(value: unknown): SourceDetail {
  assertNoHostAuthority(value);
  const row = record(value, 'source-detail');
  const freshness = validateCatalogFreshness(row.catalog_freshness);
  if (!Array.isArray(row.locations)) fail('source-detail-locations-must-be-array');
  if (!Array.isArray(row.current_extractions)) {
    fail('current-extractions-must-be-array');
  }
  if (!Array.isArray(row.representations)) fail('representations-must-be-array');
  const sourceRef = nullableString(row.source_ref_id, 'source-detail-source-ref-id');
  const extractions = row.current_extractions.map((entry) =>
    validateExtractionSummary(entry),
  );
  const representations = row.representations.map((entry) =>
    validateRepresentationSummary(entry),
  );
  const panels = stringArray(row.available_panels, 'available-panels');
  const actions = stringArray(row.available_actions, 'available-actions');
  if (
    freshness !== 'fresh' &&
    (sourceRef !== null ||
      extractions.length > 0 ||
      representations.length > 0 ||
      panels.includes('original') ||
      actions.length > 0)
  ) {
    fail('nonfresh-source-detail-cannot-claim-current-content');
  }
  return {
    item_ref: stringValue(row.item_ref, 'source-detail-item-ref'),
    catalog_entry_ref: stringValue(row.catalog_entry_ref, 'source-detail-catalog-ref'),
    logical_candidate_ref: stringValue(
      row.logical_candidate_ref,
      'source-detail-logical-candidate-ref',
    ),
    stored_instance_ref: stringValue(
      row.stored_instance_ref,
      'source-detail-stored-instance-ref',
    ),
    source_ref_id: sourceRef,
    display: validateDisplay(row.display),
    locations: row.locations.map((entry) => validateLocation(entry)),
    availability: stringValue(row.availability, 'source-detail-availability'),
    media_type: stringValue(row.media_type, 'source-detail-media-type'),
    content_identity: validateContent(row.content_identity),
    catalog_freshness: freshness,
    current_extractions: extractions,
    representations,
    evidence_summaries: objectArray(row.evidence_summaries, 'evidence-summaries'),
    processing_runs: objectArray(row.processing_runs, 'processing-runs'),
    provenance_summary:
      row.provenance_summary === null
        ? null
        : record(row.provenance_summary, 'source-detail-provenance'),
    rights_summary:
      row.rights_summary === null
        ? null
        : record(row.rights_summary, 'source-detail-rights'),
    diagnostics: validateExtractionSummary({
      state: 'current',
      state_family: 'validator',
      source_ref_id: sourceRef ?? 'not-current',
      provider: {},
      run: {},
      representation: {
        representation_id: 'validator',
        unit_count: 0,
        coordinate_families: [],
        evidence_state_by_family: {},
      },
      rights: null,
      provenance: {},
      diagnostics: row.diagnostics,
      warnings: row.warning_summary,
    }).diagnostics,
    warnings: objectArray(row.warnings, 'source-detail-warnings'),
    warning_summary: validateWarningSummary(row.warning_summary),
    available_panels: panels,
    available_actions: actions,
  };
}

function validateQueryCriterion(value: unknown): QueryCriterion {
  const row = record(value, 'query-criterion');
  const field = stringValue(row.field, 'query-field') as QueryField;
  if (!queryFields.has(field)) fail('query-field-invalid');
  const operator = stringValue(row.operator, 'query-operator');
  if (!queryOperators.has(operator)) fail('query-operator-invalid');
  return {
    field,
    operator: operator as QueryCriterion['operator'],
    value: stringValue(row.value, 'query-value'),
  };
}

export function validateQueryPlan(value: unknown): QueryPlan {
  const row = record(value, 'query-plan');
  if (!Array.isArray(row.criteria)) fail('query-criteria-must-be-array');
  const sortField = stringValue(row.sort_field, 'query-sort-field');
  if (!querySortFields.has(sortField)) fail('query-sort-field-invalid');
  return {
    criteria: row.criteria.map((criterion) => validateQueryCriterion(criterion)),
    sort_field: sortField as QueryPlan['sort_field'],
    descending: booleanValue(row.descending, 'query-descending'),
  };
}

function validateSearchRow(value: unknown): SearchRow {
  const row = record(value, 'search-row');
  return {
    item: validateLibraryItem(row.item),
    matched_content_refs: stringArray(row.matched_content_refs, 'matched-content-refs'),
    match_snippets: stringArray(row.match_snippets, 'match-snippets'),
  };
}

export function validateSearchPage(value: unknown): SearchPage {
  assertNoHostAuthority(value);
  const row = record(value, 'search-page');
  const freshness = stringValue(row.freshness, 'search-freshness');
  if (freshness !== 'fresh' && freshness !== 'stale') fail('search-freshness-invalid');
  if (!Array.isArray(row.items)) fail('search-items-must-be-array');
  const items = row.items.map((entry) => validateSearchRow(entry));
  const blocked = nullableString(row.blocked_reason, 'search-blocked-reason');
  const total = nullableNumber(row.total_known_matches, 'total-known-matches');
  if (freshness === 'stale') {
    if (blocked === null || total !== null || items.length !== 0) {
      fail('stale-search-must-withhold-current-results');
    }
  } else if (blocked !== null || total === null) {
    fail('fresh-search-state-invalid');
  }
  return {
    freshness,
    blocked_reason: blocked,
    interpreted_plan: validateQueryPlan(row.interpreted_plan),
    total_known_matches: total,
    cursor: nullableString(row.cursor, 'search-cursor'),
    next_cursor: nullableString(row.next_cursor, 'search-next-cursor'),
    items,
  };
}

function validateEvidenceEnvelope(value: unknown, label: string): EvidenceEnvelopeView {
  const row = record(value, label);
  const envelope: EvidenceEnvelopeView = {
    state: stringValue(row.state, `${label}-state`),
  };
  if (row.value_state !== undefined) {
    envelope.value_state = stringValue(row.value_state, `${label}-value-state`);
  }
  if (row.value !== undefined) envelope.value = row.value;
  return envelope;
}

function validateRepresentationUnit(value: unknown): RepresentationUnit {
  const row = record(value, 'representation-unit');
  return {
    unit_ref: stringValue(row.unit_ref, 'representation-unit-ref'),
    surface: validateEvidenceEnvelope(row.surface, 'surface-envelope'),
    semantic_role: validateEvidenceEnvelope(row.semantic_role, 'semantic-envelope'),
    coordinate: validateEvidenceEnvelope(row.coordinate, 'coordinate-envelope'),
  };
}

export function validateRepresentationPage(value: unknown): RepresentationPage {
  assertNoHostAuthority(value);
  const row = record(value, 'representation-page');
  if (!Array.isArray(row.units)) fail('representation-units-must-be-array');
  return {
    representation_id: stringValue(row.representation_id, 'representation-page-id'),
    basis: stringValue(row.basis, 'representation-basis'),
    cursor: nullableString(row.cursor, 'representation-cursor'),
    next_cursor: nullableString(row.next_cursor, 'representation-next-cursor'),
    units: row.units.map((unit) => validateRepresentationUnit(unit)),
  };
}

export function validateGatewayStatus(value: unknown): GatewayStatus {
  assertNoHostAuthority(value);
  const row = record(value, 'gateway-status');
  const mode = stringValue(row.mode, 'gateway-mode');
  if (mode !== 'demo' && mode !== 'live') fail('gateway-mode-invalid');
  return {
    mode,
    label: stringValue(row.label, 'gateway-label'),
    detail: stringValue(row.detail, 'gateway-detail'),
  };
}

export interface BridgeResultEnvelope {
  bridge_version: typeof GUI_BRIDGE_VERSION;
  method: GuiBridgeMethod;
  payload: unknown;
}

export function validateBridgeEnvelope(
  value: unknown,
  expectedMethod: GuiBridgeMethod,
): BridgeResultEnvelope {
  assertNoHostAuthority(value);
  const row = record(value, 'bridge-envelope');
  if (row.bridge_version !== GUI_BRIDGE_VERSION) fail('bridge-version-unsupported');
  if (row.method !== expectedMethod) fail('bridge-method-mismatch');
  return {
    bridge_version: GUI_BRIDGE_VERSION,
    method: expectedMethod,
    payload: row.payload,
  };
}
