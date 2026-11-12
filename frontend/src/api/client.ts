import { EchoCaseApiClient } from "./generated";
import type {
  CaseSummary,
  EvidenceView,
  LinkRequest,
  NotesRequest,
  ReviseLinkRequest,
  SessionView,
  UserView,
  VerdictRequest,
} from "./generated";
export type Session = SessionView;
export type Evidence = EvidenceView;
export type Case = CaseSummary;
export type User = UserView;
export type { ReviseLinkRequest } from "./generated";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public traceId?: string,
  ) {
    super(message);
  }
}
let csrf: string | undefined;
type Context = { key?: string; version?: number; signal?: AbortSignal };

// NSwag owns paths, verbs, DTOs and parsing; this transport owns EchoCase's
// session and conditional-write protocol. Generated output is never edited.
export async function apiCall<T>(
  perform: (client: EchoCaseApiClient) => Promise<T>,
  context: Context = {},
): Promise<T> {
  let successfulResponse = false;
  let write = false;
  const client = new EchoCaseApiClient("", {
    fetch: async (url, init) => {
      write = !["GET", "HEAD", "OPTIONS"].includes(
        init?.method?.toUpperCase() ?? "GET",
      );
      if (write && !csrf) await refreshCsrf();
      const headers = new Headers(init?.headers);
      if (write) headers.set("X-CSRF-TOKEN", csrf!);
      if (context.key) headers.set("Idempotency-Key", context.key);
      if (context.version !== undefined)
        headers.set("If-Match", `"${context.version}"`);
      const response = await fetch(url, {
        ...init,
        headers,
        credentials: "same-origin",
        signal: context.signal ?? init?.signal,
      });
      if (!response.ok) {
        const problem = await response.json().catch(() => ({}));
        throw new ApiError(
          response.status,
          problem.title ?? "request_failed",
          problem.detail ??
            (response.status === 401
              ? "请重新登录。"
              : "请求未完成，请稍后再试。"),
          problem.traceId,
        );
      }
      successfulResponse = true;
      return response;
    },
  });
  try {
    return await perform(client);
  } catch (error) {
    if (context.signal?.aborted || error instanceof ApiError) throw error;
    if (successfulResponse)
      throw new ApiError(
        0,
        "response_unreadable",
        write
          ? "响应内容无法读取，保存结果尚未确认。可重试同一次操作。"
          : "响应内容无法读取，请重新加载。",
      );
    throw new ApiError(
      0,
      "network_error",
      "连接中断，保存结果尚未确认。恢复连接后可重试同一次操作。",
    );
  }
}
export async function refreshCsrf() {
  csrf = (await apiCall((client) => client.getCsrfToken())).token;
}

export type Action =
  | { kind: "examine"; evidenceId: string }
  | { kind: "link"; body: LinkRequest }
  | { kind: "revise-link"; linkId: string; body: ReviseLinkRequest }
  | { kind: "unlink"; linkId: string }
  | { kind: "notes"; body: NotesRequest }
  | { kind: "transition"; action: "review" | "resume" }
  | { kind: "verdict"; body: VerdictRequest };
export type Operation = Action & {
  version: number;
  key: string;
  draftRevision?: number;
};
export function executeOperation(id: string, op: Operation): Promise<Session> {
  return apiCall((client) => {
    switch (op.kind) {
      case "examine":
        return client.examineEvidence(id, op.evidenceId);
      case "link":
        return client.createLink(id, op.body);
      case "revise-link":
        return client.reviseLink(id, op.linkId, op.body);
      case "unlink":
        return client.removeLink(id, op.linkId);
      case "notes":
        return client.saveNotes(id, op.body);
      case "transition":
        return client.transitionInvestigation(id, op.action);
      case "verdict":
        return client.submitVerdict(id, op.body);
    }
  }, op);
}
