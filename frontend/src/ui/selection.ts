import type { LibraryItem, LibraryPage, SearchPage } from '../gateway/models';

export function firstLibrarySelection(page: LibraryPage | null): LibraryItem | null {
  return page?.items[0] ?? null;
}

export function firstSearchSelection(page: SearchPage): LibraryItem | null {
  if (page.freshness !== 'fresh') {
    return null;
  }
  return page.items[0]?.item ?? null;
}
