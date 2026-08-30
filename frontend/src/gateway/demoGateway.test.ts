import { describe, expect, it } from 'vitest';

import { DemoRaiateaGateway } from './demoGateway';
import type { QueryPlan } from './models';

const textPlan = (value: string): QueryPlan => ({
  criteria: [{ field: 'extracted_text', operator: 'contains', value }],
  sort_field: 'source_ref_id',
  descending: false,
});

describe('DemoRaiateaGateway', () => {
  it('labels itself as demo data', () => {
    expect(new DemoRaiateaGateway().status().mode).toBe('demo');
  });

  it('keeps synthetic fingerprints inside the application contract shape', async () => {
    const gateway = new DemoRaiateaGateway();
    const page = await gateway.libraryPage();
    for (const item of page.items) {
      expect(item.content.fingerprint_summary).toMatch(/^sha256:[0-9a-f]{64}$/);
    }
  });

  it('paginates deterministic Library rows', async () => {
    const gateway = new DemoRaiateaGateway();
    const first = await gateway.libraryPage({ pageSize: 1 });
    expect(first.items).toHaveLength(1);
    expect(first.next_cursor).not.toBeNull();

    const second = await gateway.libraryPage({
      pageSize: 1,
      cursor: first.next_cursor,
    });
    expect(second.items).toHaveLength(1);
    expect(second.items[0]?.item_ref).not.toBe(first.items[0]?.item_ref);
  });

  it('uses deterministic structured text criteria rather than NL interpretation', async () => {
    const gateway = new DemoRaiateaGateway();
    const result = await gateway.searchPage(textPlan('semiconductors'));
    expect(result.freshness).toBe('fresh');
    expect(result.items).toHaveLength(1);
    expect(result.items[0]?.item.display.media_type).toBe('application/pdf');
  });

  it('honors the structured sort field and direction', async () => {
    const gateway = new DemoRaiateaGateway();
    const result = await gateway.searchPage({
      criteria: [],
      sort_field: 'unit_count',
      descending: true,
    });
    expect(result.items).toHaveLength(3);
    expect(result.items[0]?.item.display.media_type).toBe('application/pdf');
  });

  it('returns a source-agnostic detail model', async () => {
    const gateway = new DemoRaiateaGateway();
    const page = await gateway.libraryPage();
    const pdf = page.items.find(
      (item) => item.display.media_type === 'application/pdf',
    );
    expect(pdf).toBeDefined();
    const detail = await gateway.sourceDetail(pdf!.item_ref);
    expect(detail.available_panels).toContain('semantic');
    expect(detail.representations[0]?.coordinate_families).toContain(
      'pdf-page-geometry',
    );
  });
});
