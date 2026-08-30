import { demoGateway } from './demoGateway';
import { LiveRaiateaGateway } from './LiveRaiateaGateway';
import type { RaiateaGateway } from './RaiateaGateway';
import { TauriApplicationTransport } from './TauriApplicationTransport';

export type GatewayMode = 'demo' | 'tauri';

export function createRaiateaGateway(mode: GatewayMode): RaiateaGateway {
  if (mode === 'tauri') {
    return new LiveRaiateaGateway(new TauriApplicationTransport());
  }
  return demoGateway;
}

function configuredMode(): GatewayMode {
  return import.meta.env.VITE_RAIATEA_GATEWAY === 'tauri' ? 'tauri' : 'demo';
}

export const gateway = createRaiateaGateway(configuredMode());
