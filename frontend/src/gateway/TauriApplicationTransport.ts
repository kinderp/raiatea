import type { GuiBridgeMethod } from './bridgeValidation';
import type { ApplicationTransport } from './LiveRaiateaGateway';

export type TauriInvoke = <T>(
  command: string,
  args?: Record<string, unknown>,
) => Promise<T>;

interface RaiateaTauriGlobal {
  core: {
    invoke: TauriInvoke;
  };
}

declare global {
  interface Window {
    __TAURI__?: RaiateaTauriGlobal;
  }
}

function desktopInvoke<T>(
  command: string,
  args?: Record<string, unknown>,
): Promise<T> {
  const invoke = window.__TAURI__?.core.invoke;
  if (invoke === undefined) {
    return Promise.reject(new Error('tauri-desktop-core-unavailable'));
  }
  return invoke<T>(command, args);
}

export class TauriApplicationTransport implements ApplicationTransport {
  constructor(private readonly invokeCommand: TauriInvoke = desktopInvoke) {}

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
