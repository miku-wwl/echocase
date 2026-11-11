import { ApiError } from "../api/client";
export default function Message({ error }: { error: unknown }) {
  if (!error) return null;
  return (
    <div role="alert" className="notice error">
      <span>{error instanceof Error ? error.message : "操作未完成。"}</span>
      {error instanceof ApiError && error.traceId && (
        <small>追踪编号：{error.traceId}</small>
      )}
    </div>
  );
}
