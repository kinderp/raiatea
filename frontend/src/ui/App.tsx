import { FormEvent, useEffect, useMemo, useState } from 'react';

import { demoGateway } from '../gateway/demoGateway';
import type {
  LibraryItem,
  LibraryPage,
  QueryPlan,
  SearchPage,
  SourceDetail,
} from '../gateway/models';
import type { RaiateaGateway } from '../gateway/RaiateaGateway';
import { DockLayout } from './DockLayout';
import { Panel } from './Panel';
import { createPanelCapabilities } from './panels';

const gateway: RaiateaGateway = demoGateway;
const fixedPanel = createPanelCapabilities();

type Surface = 'home' | 'library' | 'explore' | 'world' | 'activity';

const nav: Array<{ id: Surface; label: string; marker?: string }> = [
  { id: 'home', label: 'Home' },
  { id: 'library', label: 'Library' },
  { id: 'explore', label: 'Explore', marker: 'future' },
  { id: 'world', label: 'World / Observatory', marker: 'future' },
  { id: 'activity', label: 'Activity', marker: 'future' },
];

function formatBytes(value: number | null): string {
  if (value === null) return 'Unknown size';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function mediaLabel(mediaType: string): string {
  if (mediaType === 'application/pdf') return 'PDF';
  if (mediaType === 'application/epub+zip') return 'EPUB';
  return mediaType;
}

function LibraryList({
  page,
  selected,
  onSelect,
}: {
  page: LibraryPage;
  selected: string | null;
  onSelect: (item: LibraryItem) => void;
}) {
  return (
    <div className="library-list" role="list" aria-label="Library sources">
      {page.items.map((item) => {
        const provider = item.extraction.provider_profile_summary?.provider_id;
        return (
          <button
            type="button"
            key={item.item_ref}
            className={`source-row${selected === item.item_ref ? ' source-row--selected' : ''}`}
            onClick={() => onSelect(item)}
            role="listitem"
          >
            <span className="source-row__type">{mediaLabel(item.display.media_type)}</span>
            <span className="source-row__main">
              <strong>{item.display.title ?? item.display.fallback_name}</strong>
              <span>{item.location.current_relative_location ?? 'Location unavailable'}</span>
            </span>
            <span className="source-row__meta">
              <span>{formatBytes(item.content.byte_length)}</span>
              <span>{provider ?? 'Not extracted'}</span>
            </span>
          </button>
        );
      })}
    </div>
  );
}

function SourceContent({ detail }: { detail: SourceDetail | null }) {
  if (detail === null) {
    return <div className="empty-state">Select a Source to inspect it.</div>;
  }
  const extraction = detail.current_extractions[0];
  const representation = detail.representations[0];
  return (
    <div className="source-content">
      <div className="source-heading">
        <div className="source-heading__type">{mediaLabel(detail.media_type)}</div>
        <div>
          <h1>{detail.display.title ?? detail.display.fallback_name}</h1>
          <p>{detail.locations[0]?.current_relative_location ?? 'No current Location'}</p>
        </div>
      </div>
      <div className="lens-tabs" aria-label="Source lenses">
        {detail.available_panels.map((panel) => (
          <span key={panel} className={panel === 'semantic' ? 'lens-tab lens-tab--active' : 'lens-tab'}>
            {panel}
          </span>
        ))}
      </div>
      <div className="semantic-preview">
        <div className="semantic-preview__label">Normalized representation</div>
        <h3>Evidence-bearing content is ready for the renderer bridge.</h3>
        <p>
          This first frontend slice renders the application read-model boundary only. It does not read E-05 or Provider-native records directly.
        </p>
        <dl className="metric-grid">
          <div><dt>Units</dt><dd>{representation?.unit_count ?? '—'}</dd></div>
          <div><dt>Coordinates</dt><dd>{representation?.coordinate_families.join(', ') || 'not established'}</dd></div>
          <div><dt>Provider</dt><dd>{extraction?.provider.provider_id ?? '—'}</dd></div>
          <div><dt>Route</dt><dd>{extraction?.provider.route_profile ?? '—'}</dd></div>
        </dl>
      </div>
    </div>
  );
}

function Inspector({ item, detail }: { item: LibraryItem | null; detail: SourceDetail | null }) {
  if (item === null) {
    return <div className="empty-state">Inspector follows the current context.</div>;
  }
  return (
    <div className="inspector-stack">
      <div className="inspector-section">
        <span className="inspector-label">Current state</span>
        <strong>{item.freshness.content}</strong>
        <small>Catalog: {item.freshness.catalog}</small>
      </div>
      <div className="inspector-section">
        <span className="inspector-label">Identity</span>
        <code>{item.logical_candidate_ref}</code>
        <small>Provisional catalog candidate</small>
      </div>
      <div className="inspector-section">
        <span className="inspector-label">Processing</span>
        <strong>{detail?.current_extractions[0]?.provider.provider_id ?? 'Not established'}</strong>
        <small>{detail?.current_extractions[0]?.provider.route_profile ?? 'No current route'}</small>
      </div>
      <div className="inspector-section">
        <span className="inspector-label">Warnings</span>
        <strong>{item.warnings.state === 'measured' ? item.warnings.count : 'Not established'}</strong>
      </div>
      <div className="inspector-section">
        <span className="inspector-label">Available panels</span>
        <div className="tag-cloud">
          {(detail?.available_panels ?? item.capabilities).map((value) => (
            <span key={value}>{value}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

function Placeholder({ title, description }: { title: string; description: string }) {
  return (
    <div className="future-surface">
      <span>Future Raiatea surface</span>
      <h1>{title}</h1>
      <p>{description}</p>
      <div className="future-surface__rule">Not connected in GUI vertical slice #217.</div>
    </div>
  );
}

export function App() {
  const status = gateway.status();
  const [surface, setSurface] = useState<Surface>('library');
  const [library, setLibrary] = useState<LibraryPage | null>(null);
  const [selectedItem, setSelectedItem] = useState<LibraryItem | null>(null);
  const [detail, setDetail] = useState<SourceDetail | null>(null);
  const [searchText, setSearchText] = useState('');
  const [search, setSearch] = useState<SearchPage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    gateway.libraryPage({ pageSize: 50 }).then((page) => {
      if (!live) return;
      setLibrary(page);
      const first = page.items[0];
      if (first !== undefined) setSelectedItem(first);
    }).catch((reason: unknown) => {
      if (live) setError(reason instanceof Error ? reason.message : 'Library load failed');
    });
    return () => { live = false; };
  }, []);

  useEffect(() => {
    if (selectedItem === null) {
      setDetail(null);
      return;
    }
    let live = true;
    gateway.sourceDetail(selectedItem.item_ref).then((value) => {
      if (live) setDetail(value);
    }).catch((reason: unknown) => {
      if (live) setError(reason instanceof Error ? reason.message : 'Detail load failed');
    });
    return () => { live = false; };
  }, [selectedItem]);

  const summary = useMemo(() => {
    const items = library?.items ?? [];
    return {
      total: library?.total_known_items ?? 0,
      pdf: items.filter((item) => item.display.media_type === 'application/pdf').length,
      epub: items.filter((item) => item.display.media_type === 'application/epub+zip').length,
      extracted: items.filter((item) => item.extraction.state === 'current').length,
    };
  }, [library]);

  async function runSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const value = searchText.trim();
    if (value.length === 0) {
      setSearch(null);
      return;
    }
    const plan: QueryPlan = {
      criteria: [{ field: 'extracted_text', operator: 'contains', value }],
      sort_field: 'source_ref_id',
      descending: false,
    };
    try {
      setSearch(await gateway.searchPage(plan, { pageSize: 50 }));
      setSurface('library');
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : 'Search failed');
    }
  }

  const primary = (() => {
    if (surface === 'home') {
      return (
        <Panel id="home-overview" title="Today in Raiatea" region="primary" capabilities={fixedPanel} eyebrow="Home">
          <div className="summary-grid">
            <article><span>Known Sources</span><strong>{summary.total}</strong></article>
            <article><span>PDF</span><strong>{summary.pdf}</strong></article>
            <article><span>EPUB</span><strong>{summary.epub}</strong></article>
            <article><span>Extracted</span><strong>{summary.extracted}</strong></article>
          </div>
          <p className="home-note">The production Home will expose only facts established by the Application Layer. Observatory intelligence is intentionally absent from this first slice.</p>
        </Panel>
      );
    }
    if (surface === 'explore') {
      return <Panel id="explore" title="Explore" region="primary" capabilities={fixedPanel}><Placeholder title="Explore the Knowledge Universe" description="Actors, ideas, movements, topics, fields, technologies, events and processes will live here after the knowledge-object layer exists." /></Panel>;
    }
    if (surface === 'world') {
      return <Panel id="world" title="World / Observatory" region="primary" capabilities={fixedPanel}><Placeholder title="Reality Observatory" description="Present Radar, cross-theme relations, State of the World and Horizon remain future capabilities, not demo truth." /></Panel>;
    }
    if (surface === 'activity') {
      return <Panel id="activity" title="Activity" region="primary" capabilities={fixedPanel}><Placeholder title="Activity" description="Processing runs, reconciliation, warnings and changes will be projected here through dedicated read models." /></Panel>;
    }
    return (
      <Panel id="library" title="Library" region="primary" capabilities={fixedPanel} eyebrow={library?.catalog_freshness ?? 'loading'}>
        {search === null ? null : (
          <div className="search-result-banner">
            Search: <strong>{search.interpreted_plan.criteria[0]?.value}</strong> · {search.total_known_matches ?? 0} match(es)
          </div>
        )}
        {library === null ? <div className="empty-state">Loading Library…</div> : (
          <LibraryList
            page={search === null ? library : {
              ...library,
              total_known_items: search.total_known_matches ?? 0,
              items: search.items.map((row) => row.item),
            }}
            selected={selectedItem?.item_ref ?? null}
            onSelect={setSelectedItem}
          />
        )}
      </Panel>
    );
  })();

  const secondary = surface === 'library' ? (
    <Panel id="source-detail" title="Source Detail" region="secondary" capabilities={fixedPanel} eyebrow="Profile · Evidence · Provenance">
      <SourceContent detail={detail} />
    </Panel>
  ) : undefined;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand__mark">R</div>
          <div><strong>RAIATEA</strong><span>Knowledge Navigator</span></div>
        </div>
        <nav aria-label="Main navigation">
          {nav.map((item) => (
            <button
              key={item.id}
              type="button"
              className={surface === item.id ? 'nav-item nav-item--active' : 'nav-item'}
              onClick={() => setSurface(item.id)}
            >
              <span>{item.label}</span>
              {item.marker === undefined ? null : <small>{item.marker}</small>}
            </button>
          ))}
        </nav>
        <div className="sidebar__footer">
          <span>GUI slice</span>
          <strong>#217</strong>
          <small>Docking disabled by design</small>
        </div>
      </aside>

      <main className="workspace-shell">
        <header className="topbar">
          <form className="global-search" onSubmit={runSearch}>
            <input
              aria-label="Search extracted text"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="Search extracted text…"
            />
            <button type="submit">Search</button>
            {search === null ? null : <button type="button" className="button-quiet" onClick={() => setSearch(null)}>Clear</button>}
          </form>
          <div className="gateway-badge" data-mode={status.mode}>
            <span>{status.label}</span>
            <small>{status.mode}</small>
          </div>
        </header>

        <div className="demo-notice" role="status">
          <strong>Prototype renderer data.</strong> {status.detail}
        </div>
        {error === null ? null : <div className="error-notice">{error}</div>}

        <DockLayout
          primary={primary}
          secondary={secondary}
          inspector={
            <Panel id="inspector" title="Inspector" region="inspector" capabilities={fixedPanel} eyebrow="Context">
              <Inspector item={selectedItem} detail={detail} />
            </Panel>
          }
        />
      </main>
    </div>
  );
}
