import { invoke } from '@tauri-apps/api/core';

import type { GuiBridgeMethod } from './bridgeValidation';
import type { ApplicationTransport } from './LiveRaiateaGateway';

export type TauriInvoke = <T>(
  command: string,
  args?: Record<string, unknown>,
) => Promise<T>;

export class TauriApplicationTransport implements ApplicationTransport {
  constructor(private readonly invokeCommand: TauriInvoke = invoke) {}

  async request(
    method: GuiBridgeMethod,
    params: Record<string, unknown>,
  ): Promise<unknown> {
    return this.invokeCommand<unknown>('raiatea_application_request', {
      method,
      params,
    });
  }
}
