import type { ReactNode } from 'react';

export interface PanelCapabilities {
  resizable: boolean;
  movable: boolean;
  dockable: boolean;
  tabbable: boolean;
  closable: boolean;
  floatable: boolean;
}

export const initialPanelCapabilities: Readonly<PanelCapabilities> = Object.freeze({
  resizable: false,
  movable: false,
  dockable: false,
  tabbable: false,
  closable: false,
  floatable: false,
});

export type PanelRegion = 'primary' | 'secondary' | 'inspector';

export interface PanelSpec {
  id: string;
  title: string;
  region: PanelRegion;
  capabilities: PanelCapabilities;
  content: ReactNode;
}

export function createPanelCapabilities(
  overrides: Partial<PanelCapabilities> = {},
): PanelCapabilities {
  return { ...initialPanelCapabilities, ...overrides };
}
