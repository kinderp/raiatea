import type { ReactNode } from 'react';

import type { PanelCapabilities, PanelRegion } from './panels';

interface PanelProps {
  id: string;
  title: string;
  region: PanelRegion;
  capabilities: PanelCapabilities;
  children: ReactNode;
  eyebrow?: string;
}

export function Panel({
  id,
  title,
  region,
  capabilities,
  children,
  eyebrow,
}: PanelProps) {
  return (
    <section
      className="panel"
      data-panel-id={id}
      data-panel-region={region}
      data-panel-movable={capabilities.movable}
      data-panel-resizable={capabilities.resizable}
      aria-labelledby={`${id}-title`}
    >
      <header className="panel__header">
        <div>
          {eyebrow === undefined ? null : (
            <div className="panel__eyebrow">{eyebrow}</div>
          )}
          <h2 id={`${id}-title`}>{title}</h2>
        </div>
        <span className="panel__layout-state" title="Layout movement is planned, not enabled">
          fixed v0
        </span>
      </header>
      <div className="panel__body">{children}</div>
    </section>
  );
}
