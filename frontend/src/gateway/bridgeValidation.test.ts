import { describe, expect, it } from 'vitest';

import libraryFixture from './fixtures/bridge-library-page.json';
import {
  BridgeValidationError,
  validateBridgeEnvelope,
  validateLibraryPage,
  validateSearchPage,
} from './bridgeValidation';

describe('GUI bridge runtime validation', () => {
  it('accepts the shared Python/TypeScript Library fixture', () => {
    const envelope = validateBridgeEnvelope(libraryFixture, 'library.page');
    const page = validateLibraryPage(envelope.payload);
    expect(page.catalog_freshness).toBe('fresh');
    expect(page.items[0]?.location.current_relative_location).toBe(
      'Books/fixture.epub',
    );
  });

  it('rejects host authority recursively', () => {
    expect(() =>
      validateBridgeEnvelope(
        {
          bridge_version: 'raiatea.gui-application-bridge.0.1.0',
          method: 'library.page',
          payload: { nested: { host_path: '/tmp/private' } },
        },
        'library.page',
      ),
    ).toThrow(BridgeValidationError);
  });

  it('rejects absolute and traversing display Locations', () => {
    for (const badLocation of ['/tmp/book.epub', '../book.epub', 'C:\\book.epub']) {
      const copy = structuredClone(libraryFixture);
      copy.payload.items[0]!.location.current_relative_location = badLocation;
      expect(() => validateLibraryPage(copy.payload)).toThrow(
        /current-relative-location/,
      );
    }
  });

  it('rejects a non-fresh Library item that still claims current extraction', () => {
    const copy = structuredClone(libraryFixture);
    copy.payload.catalog_freshness = 'reconcile-required';
    copy.payload.counts_basis = 'last-known';
    const item = copy.payload.items[0]!;
    item.source_ref_id = null;
    item.freshness.catalog = 'reconcile-required';
    item.freshness.content = 'not-established';
    item.capabilities = ['view-history'];
    item.extraction = {
      state: 'current',
      current_representation_id: 'representation:stale',
      provider_profile_summary: {
        provider_id: 'test-provider',
        route_profile: 'test-route',
      },
    };
    expect(() => validateLibraryPage(copy.payload)).toThrow(
      'nonfresh-item-cannot-claim-current-source',
    );
  });

  it('rejects stale search carrying current rows', () => {
    expect(() =>
      validateSearchPage({
        freshness: 'stale',
        blocked_reason: 'index-not-current',
        interpreted_plan: {
          criteria: [],
          sort_field: 'source_ref_id',
          descending: false,
        },
        total_known_matches: null,
        cursor: null,
        next_cursor: null,
        items: [
          {
            item: libraryFixture.payload.items[0],
            matched_content_refs: [],
            match_snippets: [],
          },
        ],
      }),
    ).toThrow('stale-search-must-withhold-current-results');
  });
});
