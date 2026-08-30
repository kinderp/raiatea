import { describe, expect, it } from 'vitest';

import {
  TauriApplicationTransport,
  type TauriInvoke,
} from './TauriApplicationTransport';


describe('TauriApplicationTransport', () => {
  it('maps only a Raiatea bridge method and params to the desktop command', async () => {
    const calls: Array<{ command: string; args?: Record<string, unknown> }> = [];
    const fakeInvoke: TauriInvoke = async <T>(
      command: string,
      args?: Record<string, unknown>,
    ): Promise<T> => {
      calls.push({ command, args });
      return {
        bridge_version: 'raiatea.gui-application-bridge.0.1.0',
        method: 'gateway.status',
        payload: { mode: 'live', label: 'Local Raiatea', detail: 'Connected.' },
      } as T;
    };

    const transport = new TauriApplicationTransport(fakeInvoke);
    const response = await transport.request('gateway.status', {});

    expect(calls).toEqual([
      {
        command: 'raiatea_application_request',
        args: { method: 'gateway.status', params: {} },
      },
    ]);
    expect(response).toMatchObject({ method: 'gateway.status' });
  });
});
