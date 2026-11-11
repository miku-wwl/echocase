# API 合同

开发模式文档：`GET /openapi/v1.json`。生成客户端：在 frontend 运行 `npm run contract`，提交 schema.d.ts；该文件不经过 Prettier。构建使用严格 TypeScript，HTTP JSON 拒绝 null 必需参数与未知成员。

先 GET `/api/auth/csrf`，保留 Cookie 并读取 token。POST register/login/logout 均带 X-CSRF-TOKEN。登录后重新获取 token。认证票据 HttpOnly、SameSite Strict，生产 Secure；本地回环 HTTP 为 SameAsRequest。

所有调查写操作需要 `Idempotency-Key: <UUID-D>`；已有调查另需 `If-Match: "<正整数>"`。GET 与成功写入返回 `ETag: "<Version>"`。同键同请求返回原快照；同键不同请求 409。重放不保证快照最新，应随后 GET。

| 路由 | 方法 | 请求 |
|---|---|---|
| /api/auth/register, /login | POST | Email, Password |
| /api/auth/me | GET | 无 |
| /api/cases | GET | 无 |
| /api/investigations | GET / POST | POST: CaseId |
| /api/investigations/{id} | GET | 无 |
| …/evidence/{evidenceId}/examine | POST | 无 |
| …/links | POST | SourceId, TargetId, Kind |
| …/links/{linkId} | DELETE | 无 |
| …/notes | PUT | Notes |
| …/state/review, …/state/resume | POST | 无 |
| …/verdict | POST | Suspect, Reasoning, SupportingEvidence |

JSON 使用 camelCase。失败使用 Problem Details；400 合同/CSRF，401 身份，404 资源不可访问，409 键复用，412 版本冲突，422 领域规则，428 缺版本，429 限流，503 依赖不可用。traceId 可关联日志，不回传 SQL 或堆栈。

没有开放 CORS。API no-store，生产 OpenAPI 端点关闭。自定义 ETag 只支持单一强整数版本，不支持 If-Match 星号/弱值/多值。
# Phase 2A 合同增量

`PUT /api/investigations/{id}/links/{linkId}` 接收 `{ "kind": "Contradicts", "rationale": "至少二十个字符的判断解释…" }`。需要原有 Cookie、CSRF、UUID Idempotency-Key 与带引号 If-Match。仅 Active 可用；关联必须属于该调查；成功保留 ID/端点，根 Version 增加一次。解释 Trim 后按 Unicode scalar 计 20–500；类型只接受已有命名值。无变化或领域拒绝为 422，旧版本为 412，换正文误用成功键为 409。

LinkView 增加可空 `rationale` / `revisedAt`。旧关联与尚未首次修订的关联均为空；旧 POST 创建合同保持不变。存储回执缺少新增字段时仍可重放。API 新业务时间为 UTC 微秒精度，避免即时响应与 PostgreSQL 重读精度不同；旧回执不重写。ProblemDetails 的 traceId 与 X-Trace-Id 使用同一编号。
