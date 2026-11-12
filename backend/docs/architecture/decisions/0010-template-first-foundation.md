# ADR 0010 — 实际官方模板生成与业务迁移

日期：2026-11-12。状态：已实现，等待所有者独立工程审查。替代 ADR 0002 的“借鉴而不生成”选择；不改写旧 ADR、历史分支或 Phase 2B 教材。

原 README 明确要求 Jason Taylor CleanArchitecture 作为起点。此前自行重建相似分层不满足该要求。整改先完整 clone 官方仓库，固定 `v10.8.0` / `e5c08ecead8a52f6cf519477bf6c57668248c035`，安装官方精确包 `Clean.Architecture.Solution.Template@10.8.0`，再实际执行 `dotnet new ca-sln -cf react -db postgresql -n EchoCase`。171 个生成文件的原始摘要与独立基线分支共同保留真实来源。

从生成基线分出业务迁移分支。保留模板的 MediatR handler 扫描、日志预处理、异常/授权/验证/性能 behaviors、FluentValidation、IUser/CurrentUser/IdentityService、分层 DI、端点发现与稳定 operationId、React/Vite 与 NSwag Fetch 客户端能力。业务请求实际通过 ISender；旧业务服务仅作为 handler 内部的用例协调器，不再直接接入端点。

聚合、投影、指纹算法、EF 映射、迁移和 PostgreSQL Store 原样迁入。事务仍由 Store 拥有：同键锁 → 按身份查资源 → 查回执 → 比对版本 → 根/子变更、审计、回执同事务提交。MediatR 管线不读取回执、不创建第二层事务、不提前 SaveChanges。授权 behavior 是身份/角色/策略边界；资源所有权仍在事务内验证，早于历史响应返回。

移除 Todo/Weather 示例、Aspire/Shared/ServiceDefaults、Azure、容器发布和部署工作流。移除模板的 EnsureDeleted/EnsureCreated 开发初始化。保留既有 Identity 用户类型、Cookie 名称、认证合同和迁移链，避免用户/业务数据变换。应用层继续用 IInvestigationStore 而非 DbSet 型端口，以封装既有事务保证；去掉未使用的 AutoMapper、模板基类和事件拦截器，避免第二套审计/身份/事务模型。所有删改逐项登记在来源目录的转换清单。

将 NSwag 固定为 14.8.0，生成强类型方法和 DTO。应用适配器保留 same-origin credentials、防伪、强 If-Match、Idempotency-Key、取消和错误归一化。未知结果仍保留原操作，历史回执不倒退缓存版本。生成文件由规范化的实际 OpenAPI 得到；CI 同时校验离线重生成和运行 API 的合同。

旧 26 项单元、22 项集成和 9 项 E2E 的断言保留；新增 5 项集成检查只针对管线授权/验证、回放前所有权及模型漂移风险。完整教材不随此整改重写，单独登记影响，等待本工程基线接受。

2026-11-13 终审补充：模板性能行为原本会在 handler 返回后查询用户名。该步骤可能在事务已提交后失败，错误地将已提交写入返回为错误。保留模板的慢请求计时/日志，但只使用当前作用域身份，不在业务完成后再查数据库；新增真实提交后延迟超过 500ms、第二次身份查询必失败的回归来保护此边界。
