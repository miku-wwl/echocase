# 附录 术语、阅读导航与一手参考

本附录帮助定位概念，不作为环境安装或操作清单。源码以书前固定的应用提交为准；在线文档可能继续更新，应核对所读版本与项目锁定依赖。机制结论来自本书对实际实现和明确范围内观察的解释。

## A.1 易混概念对照

| 术语 | 在本书中的准确含义 |
|---|---|
| 案件定义 | 固定材料目录，不保存某位用户的调查进度 |
| 调查实例 | 某 owner 的独立聚合，拥有稳定 Guid 和版本 |
| 聚合根 | 统一表达调查成员约束和状态变化的业务对象 |
| ISender / Handler | 进程内分派请求及其处理器，不是消息队列 |
| MediatR Behavior | 包装已构造请求的应用执行链，区别于 HTTP 中间件 |
| CurrentUser / IUser | HTTP 身份到应用当前用户端口的适配 |
| OpenAPI | 路径、operationId 与数据形状的机器合同 |
| NSwag SDK | 从合同生成的 DTO 与可调用 Fetch 方法 |
| 逻辑 CQRS | 读写意图与方法分离，当前共用数据库和视图 |
| 工作单元 | 一次有限加载、决定和保存中的上下文生命周期 |
| 身份解析 | 同一跟踪上下文中，同一实体键对应同一实例 |
| 原始值 | EF 跟踪时保存的前值，用于差异与并发条件 |
| 当前值 | 此刻 CLR 对象中的值，尚不代表已经提交 |
| DetectChanges | 把属性与关系差异识别成跟踪状态的阶段 |
| MVCC 行版本 | 数据库为并发快照管理的物理可见性机制 |
| 应用 Version | 由调查根推进、公开给客户端的业务版本 |
| If-Match | 客户端本次新决定基于的已确认资源前提 |
| 幂等键 | 在 owner 范围内标识同一次意图，不是资源版本 |
| 指纹 | 当前应用对目标、版本、操作与正文建立的摘要 |
| 回执 | 某次成功操作当时的历史 SessionView |
| 原子性 | 相关持久修改一起成立或一起不成立 |
| 结果未知 | 浏览器尚无法判断原写入是否成功的本地状态 |
| 确认缓存 | 只包含服务器确认快照的 Query 数据 |
| pending 投影 | 对正在发送操作的暂时呈现，不冒充已保存 |
| baseline | 草稿开始编辑时依赖的已确认内容和版本 |
| revision | 本地编辑代次，区别于服务器资源版本 |
| dirty | 尚需用户或保存结果处理的本地编辑意图 |
| rebase | 把草稿前提换到新事实；当前不静默执行 |
| 图布局 | 节点坐标和视口等呈现状态，当前不持久化 |

## A.2 按问题回到机制

源码框已经提供固定提交、符号上下文和可定位链接，不必在正文再维护一份逐文件索引。需要复读时，先确定问题属于哪种事实，再回到相应机制。

| 当前疑问 | 阅读路径 |
|---|---|
| 请求究竟在哪里停止 | [两层请求管道](04-request-pipeline.md)与[行为嵌套](05-cqrs.md) |
| 对象改了，数据库是否成功 | [EF 跟踪](07-persistence.md)与[根版本竞争](10-concurrency.md) |
| 同一事务为何能读到不同版本 | [MVCC 与语句快照](09-mvcc.md) |
| 不知道保存结果，能否换键再试 | [生成客户端与适配器](06-api.md)、[历史回执](11-idempotency.md) |
| 成功为何不能清空新输入 | [单调确认缓存](14-server-state.md)与[草稿代次](15-drafts.md) |
| 一项需求怎样跨层保持同一含义 | [关联修订完整路径](19-evolution.md) |

详细源码对齐清单随教材编辑源保存在 reference/，不要求读者按文件清单复现实验。读者真正需要带走的是来源、时间、所有权和仲裁之间的联系。

## A.3 框架与协议的一手资料

- [ASP.NET Core 中间件](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/?view=aspnetcore-10.0)：阅读委托嵌套、顺序与短路。
- [ASP.NET Core 防伪](https://learn.microsoft.com/en-us/aspnet/core/security/anti-request-forgery?view=aspnetcore-10.0)：理解 Cookie 应用的请求令牌边界。
- [默认 ProblemDetails writer 固定源码](https://github.com/dotnet/aspnetcore/blob/v10.0.9/src/Http/Http.Extensions/src/DefaultProblemDetailsWriter.cs)：核对默认扩展与定制钩子的先后。
- [EF Core 跟踪](https://learn.microsoft.com/en-us/ef/core/change-tracking/)、[变更检测](https://learn.microsoft.com/en-us/ef/core/change-tracking/change-detection)、[身份解析](https://learn.microsoft.com/en-us/ef/core/change-tracking/identity-resolution)：分别理解状态、差异与实例身份。
- [EF Core 并发](https://learn.microsoft.com/en-us/ef/core/saving/concurrency)、[事务](https://learn.microsoft.com/en-us/ef/core/saving/transactions)、[生成值](https://learn.microsoft.com/en-us/ef/core/modeling/generated-properties)：核对 WHERE 原值、提交边界与键生成。
- [EF 单查询与拆分](https://learn.microsoft.com/en-us/ef/core/querying/single-split-queries)：理解同级集合放大与读取一致性的取舍。
- [PostgreSQL 17 MVCC](https://www.postgresql.org/docs/17/mvcc-intro.html)、[隔离级别](https://www.postgresql.org/docs/17/transaction-iso.html)、[显式锁](https://www.postgresql.org/docs/17/explicit-locking.html)：区分快照、写竞争与事务级 advisory lock。
- [PostgreSQL 时间类型](https://www.postgresql.org/docs/17/datatype-datetime.html)、[EXPLAIN](https://www.postgresql.org/docs/17/using-explain.html)、[多列索引](https://www.postgresql.org/docs/17/indexes-multicolumn.html)、[排序索引](https://www.postgresql.org/docs/17/indexes-ordering.html)：核对精度与真实访问路径。
- [React 渲染与提交](https://react.dev/learn/render-and-commit)、[状态快照](https://react.dev/learn/state-as-a-snapshot)、[更新队列](https://react.dev/learn/queueing-a-series-of-state-updates)：理解闭包与函数式更新。
- [React Effect](https://react.dev/learn/synchronizing-with-effects)、[状态保留](https://react.dev/learn/preserving-and-resetting-state)、[StrictMode](https://react.dev/reference/react/StrictMode)：理解组件身份与开发检查。
- [TanStack Query 查询键](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys)、[取消](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)、[写后失效](https://tanstack.com/query/latest/docs/framework/react/guides/invalidations-from-mutations)：核对使用中 v5 的行为。
- [React Flow 交互](https://reactflow.dev/learn/concepts/adding-interactivity)：研究受控节点与变化应用。
- [Playwright 网络](https://playwright.dev/docs/network)、[断言](https://playwright.dev/docs/test-assertions)：理解如何控制交付与等待事实。
- [CleanArchitecture v10.8.0 固定上游](https://github.com/jasontaylordev/CleanArchitecture/tree/e5c08ecead8a52f6cf519477bf6c57668248c035)：真实生成来源；生成基线与当前业务接受分开解释。
- [MediatR 14.3.0 包装实现](https://github.com/LuckyPennySoftware/MediatR/blob/v14.3.0/src/MediatR/Wrappers/RequestHandlerWrapper.cs)：核对行为反向聚合与 next。
- [NSwag TypeScript 生成器](https://github.com/RicoSuter/NSwag/wiki/TypeScriptClientGenerator)：核对 Fetch 模板与生成职责。

## A.4 关于真实性与适用范围

UI 图片来自 2026 年 11 月 11 日、历史工程 63c5872 的真实 EchoCase 浏览器捕获，未改称本版新运行，书页只裁切相关区域并叠加独立编号。机制图为本书原创矢量图；示意版本、事务与时间轴不伪装成采集数据。查询时间来自单机、合成应用数据、暖缓存的有限观察，不能当作生产容量结论。
