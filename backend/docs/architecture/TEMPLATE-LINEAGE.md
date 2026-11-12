# 真实官方模板来源与转换

## 固定来源与生成

| 项目 | 值 |
|---|---|
| 官方源 | https://github.com/jasontaylordev/CleanArchitecture |
| 上游 tag / commit | `v10.8.0` / `e5c08ecead8a52f6cf519477bf6c57668248c035` |
| 官方模板包 | `Clean.Architecture.Solution.Template@10.8.0` |
| 包 SHA-256 | `5cd6ffe4c31d61084b52fc8125f549be964c2b4daf57990a01e5c070ca6b278d` |
| 生成配置 | `dotnet new ca-sln -cf react -db postgresql -n EchoCase --no-update-check` |
| 独立 bootstrap 分支 | `codex/template-bootstrap-20261112` |
| bootstrap 审查提交 | `f1df1a3c3b95bae184600a0ccef629eccaa18080` |
| 业务迁移分支 | `codex/template-migration-20261112`，从上述基线线性派生 |
| 旧 EchoCase 来源 | `bf9de37b9bd4d5cc2c227af2c857360e048b15d1` |

先完整 clone 上游并 checkout 精确 tag，再安装精确 NuGet 包并使用真实 ca-sln 生成；不是从旧应用补写模板标识。bootstrap 保留全部 171 个生成文件的原始字节，包括模板生成的端口。另有 5 个来源/独立验证文件。基线建立后的清理提交删除了被忽略规则遗漏的旧构建产物；随后仅将书外验证 runner 固定为 Ubuntu 24.04。未改写任何历史。

`template-origin/generated-files.json` 是完整原始文件摘要；`lineage.json` 是生成参数；`transformations.json` 列出每个生成文件的最终归属及移除原因；`UPSTREAM-LICENSE` 保留 MIT 通知。原 `BASELINE.md` 保留建立基线时的本机观察；以下补充独立 CI 的实际结果。

## 生成基线的真实验证结果

本机 SDK 10.0.403 兼容模板 `global.json` 的 10.0.201 / latestFeature；活动应用继续固定 10.0.300。未修改生成方案还原并构建成功，React `npm ci`、原始 NSwag 和 Vite 构建成功。模板依赖受当前 NuGet 审计影响，默认 warnings-as-errors 会阻止还原；隔离基线验证明确使用 `-p:WarningsNotAsErrors=NU1902%3BNU1903`，审计未关闭，构建保留 126 条警告。该例外不进入活动应用。

[精确 bootstrap 提交的独立 CI](https://github.com/miku-wwl/echocase/actions/runs/43181797531) 完成逐文件摘要、还原、构建、React/NSwag 和全部原测试尝试。Domain 6、Application unit 8、Application functional 19 均通过；Infrastructure integration 空项目没有测试用例。Web acceptance 6 项中 5 通过，`UserCanLogInWithValidCredentials` 等待 `a:has-text('Log out')` 超时。该运行整体是 failure，未改测试或跳过失败案例以改绿，也不将超时归因为未经验证的环境/应用原因。此前 ubuntu-latest 升至 26.04 导致旧 Playwright 不支持，书外 runner 已固定至 24.04。

因此基线的来源、生成、编译和功能测试已验证，原模板示例浏览器全集存在一个已知未通过项。它是独立保留的模板观察；活动 EchoCase 不保留此示例登录 UI，自己的原有 9 项浏览器回归另行验证。bootstrap 中生成的 Azure 工作流从未执行；活动分支完全移除它。

## 真正使用的模板机制

| 生成来源 | 活动源码与实际职责 |
|---|---|
| `src/Application/DependencyInjection.cs` | `backend/EchoCase.Application/DependencyInjection.cs`：扫描真实 EchoCase handlers/validators，注册原管线顺序 |
| `Common/Behaviours/*` | Logging preprocessor；UnhandledException → Authorization → Validation → Performance；正文/密码不作为请求对象写入日志 |
| `Common/Interfaces/IUser`、`IIdentityService`、Security/Models | 原用户端口、Authorize 元数据、Identity 结果类型，参与实际授权与身份服务 |
| `src/Infrastructure/Identity/*`、DI | IdentityService 改用既有 Investigator；EF Identity store、roles/claims 服务由作用域注入 |
| `src/Web/Services/CurrentUser` | 从已认证 HttpContext 读取 Id；请求体不能指定 owner |
| `src/Web/Infrastructure/*` | IEndpointGroup 扫描、命名 handler、OpenAPI operationId；实际注册 Investigations 端点 |
| React + `ClientApp/nswag.json` | 顶层 `frontend/` 的真实业务界面；固定 NSwag，实际合同生成 Fetch 方法与 DTO |
| 官方测试模式 | 独立 NUnit、真实 PostgreSQL、WebApplicationFactory；新增直接从 scope 取得 ISender 的管线回归 |

例：`PUT /api/investigations/{id}/notes` → `Endpoints/Investigations.SaveNotes` → `ISender.Send(SaveNotesCommand)` → 模板预处理/behaviors → `SaveNotesHandler` → `InvestigationService.Notes` → 原 `IInvestigationStore.WriteAsync` → 原 PostgreSQL 事务。没有第二套旧 HTTP 用例入口，也没有保留 Todo API/另一套 DbContext/另一套生产前端。

## 适配与版本取舍

- 原生成项目迁入 backend，SPA 迁至 frontend，测试集中在 test，历史书保留 manual。生产 solution 只有四个业务项目；测试只向应用引用。
- 保留中央包管理。应用 EF/Identity/OpenAPI 继续用原验证版本 10.0.15，Npgsql 10.0.3；MediatR/FV 更新并固定为 14.3.0/12.2.0，NSwag 14.8.0。锁文件保留，活动还原未关闭审计或降低安全警告。
- 不继承模板样例的 int 主键/BaseEntity/领域事件去重写已有 Guid 聚合。Domain 保持纯 .NET；不使用无用途的 AutoMapper 或 MSBuild 工具依赖。
- Application 以事务语义端口 IInvestigationStore 访问持久化，不直接依赖 EF。模板审计/事件拦截器由既有 Store 的原子审计替代，避免额外保存或改变提交边界。
- 既有 EchoDbContext、Investigator、所有映射和三条迁移保持。没有重建数据库、导出导入业务数据或更换身份表；模型无待生成迁移。开发启动仍不自动迁移。
- 身份 API 保留 EchoCase 原 Cookie、CSRF 和错误语义，不启用模板样例的开放注册/默认管理员种子、无条件 CORS 或默认数据库删除重建。
- 前端接口名来自 OpenAPI，业务组件不拼 URL；适配器是协议扩展，不手改生成输出。类型化 Action 保留重试 key/version/body，缓存和草稿机制继续由原 Query/Hook 负责。

原 26/22/9 用例全部保留，本机均已通过；另有 4 项迁移风险集成测试通过。最终提交 CI 和完整审查结论见工程验收与书外交付报告。旧教材不重新归因于模板，本轮只登记后续修订范围。

模板性能 behavior 已适配为提交后无身份数据库查询，避免遥测错误遮蔽成功提交；第五项新增集成回归专门验证此风险。
