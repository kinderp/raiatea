import { describe, expect, it } from 'vitest';

import libraryFixture from './fixtures/bridge-library-page.json';
import {
  type ApplicationTransport,
  LiveRaiateaGateway,
} from './LiveRaiateaGateway';
import type { GuiBridgeMethod } from './bridgeValidation';

interface Call {
  method: GuiBridgeMethod;
  params: Record<string, unknown>;
}

class FakeTransport implements ApplicationTransport {
  readonly calls: Call[] = [];

  async request(
    method: GuiBridgeMethod,
    params: Record<string, unknown>,
  ): Promise<unknown> {
    this.calls.push({ method, params });
    if (method === 'gateway.status') {
      return envelope(method, {
        mode: 'live',
        label: 'Local Raiatea',
        detail: 'Connected.',
      });
    }
    if (method === 'library.page') return libraryFixture;
    if (method === 'source.detail') {
      const item = libraryFixture.payload.items[0]!;
      return envelope(method, {
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
        current_extractions: [],
        representations: [],
        evidence_summaries: [],
        processing_runs: [],
        provenance_summary: null,
        rights_summary: null,
        diagnostics: {
          state: 'not-established',
          count: null,
          by_severity: {},
          items: [],
        },
        warnings: [],
        warning_summary: {
          state: 'not-established',
          count: null,
          highest_severity: null,
        },
        available_panels: ['original', 'history'],
        available_actions: ['request-extraction'],
      });
    }
    if (method === 'search.page') {
      return envelope(method, {
        freshness: 'fresh',
        blocked_reason: null,
        interpreted_plan: params.plan,
        total_known_matches: 1,
        cursor: null,
        next_cursor: null,
        items: [
          {
            item: libraryFixture.payload.items[0],
            matched_content_refs: ['unit:fixture'],
            match_snippets: [],
          },
        ],
      });
    }
    return envelope(method, {
      representation_id: params.representation_id,
      basis: 'sha256:3333333333333333333333333333333333333333333333333333333333333333',
      cursor: null,
      next_cursor: null,
      units: [
        {
          unit_ref: 'unit:fixture',
          surface: { state: 'present', value_state: 'populated', value: 'Fixture' },
          semantic_role: {
            state: 'present',
            value_state: 'populated',
            value: 'heading',
          },
          coordinate: {
            state: 'present',
            value_state: 'populated',
            value: { kind: 'epub-logical', resource: 'OEBPS/ch1.xhtml' },
          },
        },
      ],
    });
  }
}

function envelope(method: GuiBridgeMethod, payload: unknown): unknown {
  return {
    bridge_version: 'raiatea.gui-application-bridge.0.1.0',
    method,
    payload,
  };
}

describe('LiveRaiateaGateway', () => {
  it('maps all read methods without exposing process or JSON-RPC mechanics', async () => {
    const transport = new FakeTransport();
    const gateway = new LiveRaiateaGateway(transport);
    const plan = {
      criteria: [
        { field: 'extracted_text' as const, operator: 'contains' as const, value: 'Fixture' },
      ],
      sort_field: 'source_ref_id' as const,
      descending: false,
    };

    expect((await gateway.status()).mode).toBe('live');
    expect((await gateway.libraryPage({ pageSize: 25, cursor: null })).items).toHaveLength(1);
    await gateway.sourceDetail('app-item:fixture');
    expect((await gateway.searchPage(plan, { pageSize: 10 })).freshness).toBe('fresh');
    expect(
      (await gateway.representationPage('representation:fixture', { pageSize: 5 }))
        .units,
    ).toHaveLength(1);

    expect(transport.calls).toEqual([
      { method: 'gateway.status', params: {} },
      { method: 'library.page', params: { page_size: 25, cursor: null } },
      { method: 'source.detail', params: { item_ref: 'app-item:fixture' } },
      { method: 'search.page', params: { plan, page_size: 10 } },
      {
        method: 'representation.page',
        params: { representation_id: 'representation:fixture', page_size: 5 },
      },
    ]);
  });

  it('rejects method-mismatched envelopes', async () => {
    const transport: ApplicationTransport = {
      async request() {
        return envelope('gateway.status', {
          catalog_freshness: 'fresh',
          counts_basis: 'current',
          basis: 'basis',
          total_known_items: 0,
          cursor: null,
          next_cursor: null,
          items: [],
        });
      },
    };
    await expect(new LiveRaiateaGateway(transport).libraryPage()).rejects.toThrow(
      'bridge-method-mismatch',
    );
  });

  it('rejects host authority delivered by a compromised transport', async () => {
    const transport: ApplicationTransport = {
      async request(method) {
        return envelope(method, {
          ...libraryFixture.payload,
          nested: { host_path: '/tmp/private' },
        });
      },
    };
    await expect(new LiveRaiateaGateway(transport).libraryPage()).rejects.toThrow(
      /host-authority/,
    );
  });
});
