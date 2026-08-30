import type {
  GatewayStatus,
  LibraryPage,
  QueryPlan,
  RepresentationPage,
  SearchPage,
  SourceDetail,
} from './models';

export interface PageRequest {
  pageSize?: number;
  cursor?: string | null;
}

export interface RaiateaGateway {
  status(): GatewayStatus;
  libraryPage(request?: PageRequest): Promise<LibraryPage>;
  sourceDetail(itemRef: string): Promise<SourceDetail>;
  searchPage(plan: QueryPlan, request?: PageRequest): Promise<SearchPage>;
  representationPage(
    representationId: string,
    request?: PageRequest,
  ): Promise<RepresentationPage>;
}
