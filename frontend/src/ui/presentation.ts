import type { LibraryPage, SearchPage } from '../gateway/models';

export interface SearchBannerModel {
  kind: 'matches' | 'blocked';
  message: string;
}

export function searchBannerModel(search: SearchPage): SearchBannerModel {
  if (search.freshness !== 'fresh') {
    return {
      kind: 'blocked',
      message: `Search blocked: ${search.blocked_reason ?? 'current index unavailable'}. No current results are being shown.`,
    };
  }
  const query = search.interpreted_plan.criteria[0]?.value ?? 'structured query';
  return {
    kind: 'matches',
    message: `Search: ${query} · ${search.total_known_matches ?? 0} match(es)`,
  };
}

export function visibleLibraryPage(
  library: LibraryPage,
  search: SearchPage | null,
): LibraryPage {
  if (search === null) {
    return library;
  }
  if (search.freshness !== 'fresh') {
    return {
      ...library,
      total_known_items: 0,
      items: [],
    };
  }
  return {
    ...library,
    total_known_items: search.total_known_matches ?? 0,
    items: search.items.map((row) => row.item),
  };
}
