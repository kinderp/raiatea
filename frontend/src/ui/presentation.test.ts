import { describe, expect, it } from 'vitest';

import type { LibraryItem, LibraryPage, SearchPage } from '../gateway/models';
import { searchBannerModel, visibleLibraryPage } from './presentation';

function item(ref: string): LibraryItem {
  return {
    item_ref: ref,
    catalog_entry_ref: `catalog:${ref}`,
    source_ref_id: `source:${ref}`,
    logical_candidate_ref: `logical:${ref}`,
    stored_instance_ref: `stored:${ref}`,
    display: {
      title: null,
      fallback_name: `${ref}.pdf`,
      media_type: 'application/pdf',
      kind: 'document-source',
    },
    location: {
      scope_ref: 'scope:test',
      current_relative_location: `${ref}.pdf`,
      availability: 'known-present',
      history_count: 0,
    },
    content: {
      byte_length: 1,
      fingerprint_summary: `sha256:${'0'.repeat(64)}`,
    },
    extraction: { state: 'not-established' },
    freshness: { catalog: 'fresh', content: 'not-established' },
    warnings: { state: 'not-established', count: null, highest_severity: null },
    capabilities: ['view-history'],
  };
}

function library(): LibraryPage {
  return {
    catalog_freshness: 'fresh',
    counts_basis: 'current',
    basis: 'basis',
    total_known_items: 2,
    cursor: null,
    next_cursor: null,
    items: [item('one'), item('two')],
  };
}

describe('search presentation truth boundary', () => {
  it('renders fresh zero results as a real empty result', () => {
    const search: SearchPage = {
      freshness: 'fresh',
      blocked_reason: null,
      interpreted_plan: {
        criteria: [{ field: 'extracted_text', operator: 'contains', value: 'missing' }],
        sort_field: 'source_ref_id',
        descending: false,
      },
      total_known_matches: 0,
      cursor: null,
      next_cursor: null,
      items: [],
    };
    expect(searchBannerModel(search)).toEqual({
      kind: 'matches',
      message: 'Search: missing · 0 match(es)',
    });
    expect(visibleLibraryPage(library(), search).items).toHaveLength(0);
  });

  it('renders stale search as blocked and withholds any supplied rows', () => {
    const search: SearchPage = {
      freshness: 'stale',
      blocked_reason: 'index-not-current',
      interpreted_plan: { criteria: [], sort_field: 'source_ref_id', descending: false },
      total_known_matches: null,
      cursor: null,
      next_cursor: null,
      items: [{ item: item('should-not-render'), matched_content_refs: [], match_snippets: [] }],
    };
    expect(searchBannerModel(search)).toEqual({
      kind: 'blocked',
      message: 'Search blocked: index-not-current. No current results are being shown.',
    });
    expect(visibleLibraryPage(library(), search).items).toEqual([]);
  });
});
