import { describe, expect, it } from 'vitest';

import { createPanelCapabilities, initialPanelCapabilities } from './panels';

describe('panel capability contract', () => {
  it('keeps docking and movement disabled in the first slice', () => {
    expect(initialPanelCapabilities).toEqual({
      resizable: false,
      movable: false,
      dockable: false,
      tabbable: false,
      closable: false,
      floatable: false,
    });
  });

  it('can evolve capabilities without changing panel content', () => {
    const future = createPanelCapabilities({
      resizable: true,
      movable: true,
      dockable: true,
      tabbable: true,
    });
    expect(future.movable).toBe(true);
    expect(future.floatable).toBe(false);
  });
});
