import type { PageRequest, RaiateaGateway } from './RaiateaGateway';
import type {
  GatewayStatus,
  LibraryItem,
  LibraryPage,
  QueryPlan,
  SearchPage,
  SourceDetail,
} from './models';

interface DemoRecord {
  item: LibraryItem;
  searchText: string;
  detail: SourceDetail;
}

const measuredNoWarnings = {
  state: 'measured' as const,
  count: 0,
  highest_severity: null,
};

function syntheticFingerprint(seed: string): string {
  // Demo-only deterministic value that still respects the application read-model
  // contract: sha256: followed by exactly 64 lowercase hexadecimal characters.
  // It is not presented as a cryptographic digest of real user content.
  let state = 0x811c9dc5;
  for (const character of seed) {
    state ^= character.codePointAt(0) ?? 0;
    state = Math.imul(state, 0x01000193) >>> 0;
  }
  const word = state.toString(16).padStart(8, '0');
  return `sha256:${word.repeat(8)}`;
}

function makeItem(
  id: string,
  name: string,
  mediaType: string,
  location: string,
  providerId: string,
  routeProfile: string,
): LibraryItem {
  return {
    item_ref: `app-item:${id}`,
    catalog_entry_ref: `catalog:${id}`,
    source_ref_id: `source-ref:${id}`,
    logical_candidate_ref: `logical-candidate:${id}`,
    stored_instance_ref: `stored-instance:${id}`,
    display: {
      title: null,
      fallback_name: name,
      media_type: mediaType,
      kind: 'document-source',
    },
    location: {
      scope_ref: 'scope:demo-library',
      current_relative_location: location,
      availability: 'known-present',
      history_count: id === 'kuhn' ? 1 : 0,
    },
    content: {
      byte_length: id === 'ai-infra' ? 2_540_812 : 684_221,
      fingerprint_summary: syntheticFingerprint(id),
    },
    extraction: {
      state: 'current',
      current_representation_id: `representation:${id}`,
      provider_profile_summary: {
        provider_id: providerId,
        version: providerId === 'poppler' ? '25.06' : 'stdlib',
        route_profile: routeProfile,
      },
    },
    freshness: {
      catalog: 'fresh',
      content: 'current',
    },
    warnings: measuredNoWarnings,
    capabilities: [
      'view-history',
      'view-original',
      'request-extraction',
      'view-semantic',
      'view-provider-evidence',
      'view-processing',
      'view-provenance',
    ],
  };
}

function makeDetail(item: LibraryItem): SourceDetail {
  const provider = item.extraction.provider_profile_summary ?? {};
  const representation = {
    representation_id:
      item.extraction.current_representation_id ?? 'representation:missing',
    unit_count: item.display.media_type === 'application/pdf' ? 128 : 74,
    coordinate_families:
      item.display.media_type === 'application/pdf'
        ? ['pdf-page-geometry']
        : ['epub-logical'],
    evidence_state_by_family: {
      surface: ['present'],
      semantic_role: ['present'],
      coordinate: ['present'],
    },
  };
  const extraction = {
    state: 'current' as const,
    state_family:
      item.display.media_type === 'application/pdf'
        ? 'pdf1b-poppler'
        : 'vs1d-epub',
    source_ref_id: item.source_ref_id ?? '',
    provider,
    run: { outcome: { execution: 'completed' } },
    representation,
    rights: { processing_disposition: 'known-permitted' },
    provenance: {
      provider_id: provider.provider_id,
      route_profile: provider.route_profile,
    },
    diagnostics: {
      state: 'measured' as const,
      count: 0,
      by_severity: {},
      items: [],
    },
    warnings: measuredNoWarnings,
  };
  return {
    item_ref: item.item_ref,
    catalog_entry_ref: item.catalog_entry_ref,
    logical_candidate_ref: item.logical_candidate_ref,
    stored_instance_ref: item.stored_instance_ref,
    source_ref_id: item.source_ref_id,
    display: item.display,
    locations: [item.location],
    availability: item.location.availability,
    media_type: item.display.media_type,
    content_identity: item.content,
    catalog_freshness: 'fresh',
    current_extractions: [extraction],
    representations: [representation],
    evidence_summaries: [{ provider }],
    processing_runs: [extraction.run],
    provenance_summary: extraction.provenance,
    rights_summary: extraction.rights,
    diagnostics: extraction.diagnostics,
    warnings: [],
    warning_summary: measuredNoWarnings,
    available_panels: [
      'original',
      'history',
      'semantic',
      'provider-evidence',
      'processing',
      'provenance',
    ],
    available_actions: ['reprocess'],
  };
}

const kuhn = makeItem(
  'kuhn',
  'The Structure of Scientific Revolutions.epub',
  'application/epub+zip',
  'Books/Science/kuhn.epub',
  'python-stdlib',
  'direct-epub-stdlib',
);
const aiInfrastructure = makeItem(
  'ai-infra',
  'AI Infrastructure 2026.pdf',
  'application/pdf',
  'Research/AI/ai-infrastructure-2026.pdf',
  'poppler',
  'poppler-pdftohtml-xml-native',
);
const energy = makeItem(
  'energy',
  'Energy Systems Notes.epub',
  'application/epub+zip',
  'Notes/Energy/energy-systems.epub',
  'python-stdlib',
  'direct-epub-stdlib',
);

const records: DemoRecord[] = [
  {
    item: kuhn,
    searchText:
      'paradigm scientific revolutions normal science anomaly research history',
    detail: makeDetail(kuhn),
  },
  {
    item: aiInfrastructure,
    searchText:
      'artificial intelligence data centres semiconductors energy infrastructure compute',
    detail: makeDetail(aiInfrastructure),
  },
  {
    item: energy,
    searchText:
      'energy grid storage batteries electricity transition systems infrastructure',
    detail: makeDetail(energy),
  },
];

function page<T>(rows: T[], request: PageRequest = {}): {
  rows: T[];
  cursor: string | null;
  nextCursor: string | null;
} {
  const pageSize = request.pageSize ?? 50;
  if (!Number.isInteger(pageSize) || pageSize <= 0) {
    throw new Error('demo-page-size-invalid');
  }
  const offset = request.cursor === null || request.cursor === undefined
    ? 0
    : Number.parseInt(request.cursor.replace('demo-cursor:', ''), 10);
  if (!Number.isInteger(offset) || offset < 0) {
    throw new Error('demo-cursor-invalid');
  }
  const end = Math.min(rows.length, offset + pageSize);
  return {
    rows: rows.slice(offset, end),
    cursor: request.cursor ?? null,
    nextCursor: end < rows.length ? `demo-cursor:${end}` : null,
  };
}

function criterionMatches(record: DemoRecord, plan: QueryPlan): boolean {
  return plan.criteria.every((criterion) => {
    const expected = criterion.value.toLocaleLowerCase();
    if (criterion.field === 'extracted_text' && criterion.operator === 'contains') {
      return record.searchText.toLocaleLowerCase().includes(expected);
    }
    if (criterion.field === 'media_type' && criterion.operator === 'eq') {
      return record.item.display.media_type.toLocaleLowerCase() === expected;
    }
    if (criterion.field === 'source_ref_id' && criterion.operator === 'eq') {
      return record.item.source_ref_id?.toLocaleLowerCase() === expected;
    }
    if (criterion.field === 'provider_id' && criterion.operator === 'eq') {
      return (
        record.item.extraction.provider_profile_summary?.provider_id?.toLocaleLowerCase() ===
        expected
      );
    }
    if (criterion.field === 'route_profile' && criterion.operator === 'eq') {
      return (
        record.item.extraction.provider_profile_summary?.route_profile?.toLocaleLowerCase() ===
        expected
      );
    }
    return false;
  });
}

function sortValue(record: DemoRecord, plan: QueryPlan): string | number {
  if (plan.sort_field === 'source_ref_id') {
    return record.item.source_ref_id ?? '';
  }
  if (plan.sort_field === 'media_type') {
    return record.item.display.media_type;
  }
  return record.detail.representations[0]?.unit_count ?? 0;
}

function sortedMatches(plan: QueryPlan): DemoRecord[] {
  const matches = records.filter((record) => criterionMatches(record, plan));
  matches.sort((left, right) => {
    const a = sortValue(left, plan);
    const b = sortValue(right, plan);
    const comparison = typeof a === 'number' && typeof b === 'number'
      ? a - b
      : String(a).localeCompare(String(b));
    if (comparison !== 0) {
      return plan.descending ? -comparison : comparison;
    }
    return left.item.item_ref.localeCompare(right.item.item_ref);
  });
  return matches;
}

export class DemoRaiateaGateway implements RaiateaGateway {
  status(): GatewayStatus {
    return {
      mode: 'demo',
      label: 'Prototype data',
      detail:
        'Renderer-only deterministic fixtures. No claim is backed by your Raiatea library.',
    };
  }

  async libraryPage(request: PageRequest = {}): Promise<LibraryPage> {
    const selected = page(records.map((record) => record.item), request);
    return {
      catalog_freshness: 'fresh',
      counts_basis: 'current',
      basis: 'demo-basis:library-v1',
      total_known_items: records.length,
      cursor: selected.cursor,
      next_cursor: selected.nextCursor,
      items: selected.rows,
    };
  }

  async sourceDetail(itemRef: string): Promise<SourceDetail> {
    const record = records.find((candidate) => candidate.item.item_ref === itemRef);
    if (record === undefined) {
      throw new Error('demo-item-not-found');
    }
    return record.detail;
  }

  async searchPage(
    plan: QueryPlan,
    request: PageRequest = {},
  ): Promise<SearchPage> {
    const matches = sortedMatches(plan);
    const selected = page(matches, request);
    return {
      freshness: 'fresh',
      blocked_reason: null,
      interpreted_plan: plan,
      total_known_matches: matches.length,
      cursor: selected.cursor,
      next_cursor: selected.nextCursor,
      items: selected.rows.map((record) => ({
        item: record.item,
        matched_content_refs: [],
        match_snippets: [],
      })),
    };
  }
}

export const demoGateway = new DemoRaiateaGateway();
