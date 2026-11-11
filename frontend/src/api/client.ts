import type { components } from "./schema";
export type Session = components["schemas"]["SessionView"];
export type Evidence = components["schemas"]["EvidenceView"];
export type Case = components["schemas"]["CaseSummary"];
export type User = components["schemas"]["UserView"];
export type ReviseLinkRequest = components["schemas"]["ReviseLinkRequest"];
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
export async function refreshCsrf() {
  const r = await fetch("/api/auth/csrf", { credentials: "same-origin" });
  if (!r.ok)
    throw new ApiError(r.status, "csrf_unavailable", "暂时无法连接服务。");
  csrf = (await r.json()).token;
}
export async function request<T>(
  url: string,
  options: {
    method?: string;
    body?: unknown;
    key?: string;
    version?: number;
    signal?: AbortSignal;
  } = {},
): Promise<T> {
  const method = options.method ?? "GET";
  if (method !== "GET" && !csrf) await refreshCsrf();
  const headers: Record<string, string> = { Accept: "application/json" };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (method !== "GET") headers["X-CSRF-TOKEN"] = csrf!;
  if (options.key) headers["Idempotency-Key"] = options.key;
  if (options.version !== undefined)
    headers["If-Match"] = `"${options.version}"`;
  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers,
      credentials: "same-origin",
      signal: options.signal,
      body:
        options.body === undefined ? undefined : JSON.stringify(options.body),
    });
  } catch (error) {
    // Query cancellation is intentional; it is not an ambiguous write failure.
    if (options.signal?.aborted) throw error;
    throw new ApiError(
      0,
      "network_error",
      "连接中断，保存结果尚未确认。恢复连接后可重试同一次操作。",
    );
  }
  if (!response.ok) {
    const p = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      p.title ?? "request_failed",
      p.detail ??
        (response.status === 401 ? "请重新登录。" : "请求未完成，请稍后再试。"),
      p.traceId,
    );
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
