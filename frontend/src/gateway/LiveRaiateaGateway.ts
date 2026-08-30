import {
  type GuiBridgeMethod,
  validateBridgeEnvelope,
  validateGatewayStatus,
  validateLibraryPage,
  validateRepresentationPage,
  validateSearchPage,
  validateSourceDetail,
} from './bridgeValidation';
import type { PageRequest, RaiateaGateway } from './RaiateaGateway';
import type {
  GatewayStatus,
  LibraryPage,
  QueryPlan,
  RepresentationPage,
  SearchPage,
  SourceDetail,
} from './models';

export interface ApplicationTransport {
  /**
   * Send one Raiatea-specific application request and return the sidecar result
   * envelope as unknown JSON. The renderer neither launches processes nor owns
   * JSON-RPC correlation/framing; a future desktop-core adapter does that.
   */
  request(method: GuiBridgeMethod, params: Record<string, unknown>): Promise<unknown>;
}

function pageParams(request: PageRequest = {}): Record<string, unknown> {
  const params: Record<string, unknown> = {};
  if (request.pageSize !== undefined) params.page_size = request.pageSize;
  if (request.cursor !== undefined) params.cursor = request.cursor;
  return params;
}

export class LiveRaiateaGateway implements RaiateaGateway {
  constructor(private readonly transport: ApplicationTransport) {}

  private async payload(method: GuiBridgeMethod, params: Record<string, unknown>): Promise<unknown> {
    const raw = await this.transport.request(method, params);
    return validateBridgeEnvelope(raw, method).payload;
  }

  async status(): Promise<GatewayStatus> {
    return validateGatewayStatus(await this.payload('gateway.status', {}));
  }

  async libraryPage(request: PageRequest = {}): Promise<LibraryPage> {
    return validateLibraryPage(
      await this.payload('library.page', pageParams(request)),
    );
  }

  async sourceDetail(itemRef: string): Promise<SourceDetail> {
    return validateSourceDetail(
      await this.payload('source.detail', { item_ref: itemRef }),
    );
  }

  async searchPage(
    plan: QueryPlan,
    request: PageRequest = {},
  ): Promise<SearchPage> {
    return validateSearchPage(
      await this.payload('search.page', {
        plan,
        ...pageParams(request),
      }),
    );
  }

  async representationPage(
    representationId: string,
    request: PageRequest = {},
  ): Promise<RepresentationPage> {
    return validateRepresentationPage(
      await this.payload('representation.page', {
        representation_id: representationId,
        ...pageParams(request),
      }),
    );
  }
}
