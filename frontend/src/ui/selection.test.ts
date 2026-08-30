import { describe, expect, it } from 'vitest';

import type { LibraryItem, LibraryPage, SearchPage } from '../gateway/models';
import { firstLibrarySelection, firstSearchSelection } from './selection';

function item(ref: string): LibraryItem {
  return {
    item_ref: ref,
    catalog_entry_ref: `catalog:${ref}`,
    source_ref_id: `source:${ref}`,
    logical_candidate_ref: `logical:${ref}`,
    stored_instance_ref: `stored:${ref}`,
    display: {
      title: null,
      fallback_name: `${ref}.epub`,
      media_type: 'application/epub+zip',
      kind: 'document-source',
    },
    location: {
      scope_ref: 'scope:test',
      current_relative_location: `${ref}.epub`,
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

describe('visible selection policy', () => {
  it('selects the first Library item when clearing search', () => {
    const first = item('first');
    const page: LibraryPage = {
      catalog_freshness: 'fresh',
      counts_basis: 'current',
      basis: 'basis',
      total_known_items: 2,
      cursor: null,
      next_cursor: null,
      items: [first, item('second')],
    };
    expect(firstLibrarySelection(page)?.item_ref).toBe(first.item_ref);
    expect(firstLibrarySelection(null)).toBeNull();
  });

  it('moves context to the first visible fresh search result or clears it', () => {
    const match = item('match');
    const base: Omit<SearchPage, 'items' | 'total_known_matches'> = {
      freshness: 'fresh',
      blocked_reason: null,
      interpreted_plan: { criteria: [], sort_field: 'source_ref_id', descending: false },
      cursor: null,
      next_cursor: null,
    };
    expect(firstSearchSelection({
      ...base,
      total_known_matches: 1,
      items: [{ item: match, matched_content_refs: [], match_snippets: [] }],
    })?.item_ref).toBe(match.item_ref);
    expect(firstSearchSelection({ ...base, total_known_matches: 0, items: [] })).toBeNull();
  });

  it('never promotes context from a stale search page', () => {
    const match = item('stale-match');
    const stale: SearchPage = {
      freshness: 'stale',
      blocked_reason: 'index-not-current',
      interpreted_plan: { criteria: [], sort_field: 'source_ref_id', descending: false },
      total_known_matches: null,
      cursor: null,
      next_cursor: null,
      // Defensive test: even if a future/malformed adapter supplied rows, stale
      // search state must not become selected current context.
      items: [{ item: match, matched_content_refs: [], match_snippets: [] }],
    };
    expect(firstSearchSelection(stale)).toBeNull();
  });
});
