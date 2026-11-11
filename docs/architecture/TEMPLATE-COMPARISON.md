# Jason Taylor CleanArchitecture 与 EchoCase：固定源码的取舍审查

审查对象为上游提交 [`e1ab4cc4d5d7b4e25e57bd8b0514b766573b8c04`](https://github.com/jasontaylordev/CleanArchitecture/tree/e1ab4cc4d5d7b4e25e57bd8b0514b766573b8c04)。本地逐文件阅读路径为 `work/upstream-cleanarchitecture`；其源文件摘要见[历史审查记录](https://github.com/miku-wwl/echocase/blob/63c587277541b4e700258aad82de9b2ad0ba32f8/evidence/phase2a/upstream-source.json)。这是源码机制比较，没有运行上游模板测试，也没有将其 Todo 业务复制进 EchoCase。

## 一次修改请求经过什么

上游 `src/Application/TodoItems/Commands/UpdateTodoItem/UpdateTodoItem.cs` 的请求记录由 MediatR 分派到处理器。处理器通过 `IApplicationDbContext.TodoItems.FindAsync` 取得实体，设置 Title/Done，再调用 SaveChangesAsync。Application 的 DI 注册日志预处理器，随后注册异常、授权、校验、性能行为。Infrastructure 把 IApplicationDbContext 解析为当前作用域的 ApplicationDbContext；两个 SavingChanges 拦截器分别补审计字段、分派领域事件，最后由关系提供者保存。

EchoCase 的对应操作是 PUT 修订关联。API 解析 Cookie 身份、防伪令牌、If-Match 与幂等键，调用 InvestigationService.ReviseLink；Store 开启事务并锁定 owner/key，先按 owner/id 加载聚合，检查回执，再比较版本。应用回调调用根聚合方法，EF 将子实体修改、根版本、审计与回执写入同一事务。没有通用调度器，也没有外部副作用。

两条路径的区别发生在明确边界：上游应用可直接表达 EF 查询；EchoCase 端口把加载、回执、并发与事务策略收在基础设施。前者减少针对每个用例的仓储方法，后者避免业务应用层依赖 EF 查询语义，但当前带委托的写端口只能在进程内使用。

## 机制与选择

| 上游固定文件/机制 | EchoCase 选择 | 理由、代价与重新评估条件 |
|---|---|---|
| `Application/DependencyInjection.cs`：程序集扫描、请求处理器与开放泛型行为 | **采用依赖方向，简化分派**。显式 Scoped 服务和方法 | 当前九类调查命令可直接追踪。新增横切行为时需要审查每个入口；若多个模块形成大量独立处理器，再评估管道，不能仅复制接口名 |
| `Application/Common/Interfaces/IApplicationDbContext.cs`：暴露 DbSet、SaveChangesAsync | **未采用这个 EF 端口**。IInvestigationStore 显式 List/Get/Write | 编译边界测试证明 Application 不引用 EF。代价是映射、有限读方法和特定写回调；不是可以无成本替换所有数据库的保证 |
| `ValidationBehaviour.cs`：并行运行 FluentValidation validators，汇集失败 | **简化并按边界分工**。JSON 必填/null/多余字段由 API，业务约束在领域，关系约束在 DB | 没有重复引入校验库。端口外调用仍受领域保护；数据库特有约束不能只靠前端。若未来 validators 共用一个 DbContext，必须评估并行访问问题，不能直接照搬 Task.WhenAll |
| `AuthorizationBehaviour.cs`：请求特性、身份、角色或策略 | **采用可信身份，增加实际资源过滤**。owner 来自 Cookie，SQL 同时按 id/owner 查询 | 上游通用角色行为不自动表达某调查的所有权。EchoCase 不需要角色体系；404 统一不可见与不存在，且检查资源发生在回执重放之前 |
| `Infrastructure/DependencyInjection.cs`：DbContext/拦截器 Scoped、TimeProvider Singleton | **采用生命周期原则**，API 为 composition root | 同一请求使用同一上下文；不把 DbContext 当线程安全单例。TimeProvider 可替换，应用将对外时间精度约定为微秒 |
| `AuditableEntityInterceptor.cs`：SavingChanges 更新创建/修改者、Owned 实体变更判断 | **未采用通用审计基类**。根聚合显式 Advance，Store 写操作审计 | 子实体并不是 EF Owned 对象；仅依赖 Owned 检查不会自动推进根版本。每个根操作必须推进 Version，版本唯一审计与实际并发测试补足约束。审计没有全量前后值、防篡改能力 |
| `DispatchDomainEventsInterceptor.cs`：SavingChanges 时取事件、清集合、mediator.Publish | **未采用事件分派**。本地业务与审计同一事务 | SavingChanges 发生在数据库提交之前。外部邮件/消息无法由后续 SQL 回滚。当前没有这类副作用需求，故不添加 outbox；将来需要可靠外部交付时必须设计提交后交付与重试 |
| `UpdateTodoItem`：按 ID 加载、修改属性、SaveChanges | **采用用例清晰性，增加聚合与协议保护** | Investigation 不开放任意 setter。子关联只能由根修订，根版本参与 UPDATE 条件；同键锁、唯一回执和审计处理不同竞争来源。这是 EchoCase 需求，并非对上游样例安全性的全面结论 |
| `Web/Program.cs`：初始化器、HTTPS/HSTS、OpenAPI、可选客户端、服务默认值 | **选择适用部分**。显式 `--migrate`、同源静态前端、健康端点与结构化日志 | 不在普通应用启动时迁移，不复制 Todo/Aspire/跨域默认策略。迁移任务拥有数据库变更权限的边界仍需真实云配置；当前本地账号没有实现最小数据库权限分离 |
| `AppHost` / `ServiceDefaults` / 数据库提供者条件模板 | **未采用运行编排**。固定 PostgreSQL、普通ASP.NET与Vite开发命令 | 不复制模板可选运行器，保持应用源码责任与明确依赖 |

## CQRS 与 DDD 的实际边界

EchoCase 的查询与命令方法、请求合同分离，但读写共用 PostgreSQL 和 SessionView，属于逻辑 CQRS。没有单独投影数据库、异步读模型或完整 Event Sourcing。引入 MediatR 不会自动改变这些事实。

根聚合约束 Active/Reviewing/Submitted、发现前置、规范无向端点、重复关联和结论支持。关联修订只增加一项根行为；没有为解释字符串引入无独立语义的通用 ValueObject 层次。基础设施映射负责外键、唯一键、成对可空解释和 Version 条件。直接 SQL 可以绕过部分领域规则，故日常业务写入只能走同一端口；没有声称数据库独立复刻了所有状态机约束。

当前 InvestigationService 约百行，所有用例共享同一 Write 路径。Phase 2A 真正需要拆分的是前端千行 App 中互相影响的请求、草稿、工作台职责。新结构把 App、Workspace、useInvestigation、useNotesDraft、NotesEditor、LinkEditor 分开，修复有失败重现的状态错误。没有为了与模板目录对齐而制造命令文件或通用框架。

## 可以推翻这些选择的信号

新增跨聚合事务、大量可组合用例行为、复杂查询分页、可靠外部通知或独立模块团队，都会改变当前端口/分派选择。反之，同一案件的六条证据、十五条关联上限没有提供服务化或消息系统的理由。比较结论是本范围内的适配判断；上游完整模板执行与所有模板选项仍为 **NOT_RUN**。


当前责任边界由ADR0009定义，模板比较保留应用机制；历史环境交付选型不作为当前任务。测试路径已迁到tests/unit、tests/integration和tests/e2e。
