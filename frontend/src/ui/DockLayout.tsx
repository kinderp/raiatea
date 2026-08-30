import type { ReactNode } from 'react';

interface PanelHostProps {
  region: 'primary' | 'secondary' | 'inspector';
  children: ReactNode;
}

export function PanelHost({ region, children }: PanelHostProps) {
  return (
    <div className={`panel-host panel-host--${region}`} data-panel-host={region}>
      {children}
    </div>
  );
}

interface DockLayoutProps {
  primary: ReactNode;
  secondary?: ReactNode;
  inspector: ReactNode;
}

export type DockLayoutColumnMode = 'two' | 'three';

export function dockLayoutColumnMode(hasSecondary: boolean): DockLayoutColumnMode {
  return hasSecondary ? 'three' : 'two';
}

export function DockLayout({ primary, secondary, inspector }: DockLayoutProps) {
  const columnMode = dockLayoutColumnMode(secondary !== undefined);
  return (
    <div
      className={`dock-layout dock-layout--${columnMode}`}
      data-layout-mode="static-v0"
      data-layout-columns={columnMode}
    >
      <PanelHost region="primary">{primary}</PanelHost>
      {secondary === undefined ? null : (
        <PanelHost region="secondary">{secondary}</PanelHost>
      )}
      <PanelHost region="inspector">{inspector}</PanelHost>
    </div>
  );
}
