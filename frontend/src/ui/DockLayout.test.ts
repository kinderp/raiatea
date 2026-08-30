import { describe, expect, it } from 'vitest';

import { dockLayoutColumnMode } from './DockLayout';

describe('DockLayout static-v0 column mode', () => {
  it('uses two columns without a secondary panel', () => {
    expect(dockLayoutColumnMode(false)).toBe('two');
  });

  it('uses three columns when the secondary panel is present', () => {
    expect(dockLayoutColumnMode(true)).toBe('three');
  });
});
