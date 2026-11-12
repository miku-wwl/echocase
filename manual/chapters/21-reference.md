# 附录 术语、源码地图与一手参考

本附录帮助定位概念，不作为环境安装或操作清单。源码以书前固定的应用提交为准；在线文档可能继续更新，应核对所读版本与项目锁定依赖。机制结论来自本书对实际实现和明确范围内观察的解释。

## A.1 易混概念对照

| 术语 | 在本书中的准确含义 |
|---|---|
| 案件定义 | 固定材料目录，不保存某位用户的调查进度 |
| 调查实例 | 某 owner 的独立聚合，拥有稳定 Guid 和版本 |
| 聚合根 | 统一表达调查成员约束和状态变化的业务对象 |
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

## A.2 按问题进入源码

| 想理解的问题 | 主要符号与当前路径 |
|---|---|
| 状态与成员规则 | Investigation；backend/EchoCase.Domain/Investigation.cs |
| 用例与读模型 | InvestigationService、SessionPresenter；backend/EchoCase.Application/Investigations.cs |
| 原子写协议 | WriteAsync；backend/EchoCase.Infrastructure/PostgresInvestigationStore.cs |
| 映射与关系约束 | OnModelCreating；backend/EchoCase.Infrastructure/EchoDbContext.cs |
| 请求和身份边界 | Program；backend/EchoCase.Api/Program.cs |
| 网络分类 | request；frontend/src/api/client.ts |
| 确认缓存生命周期 | useInvestigation；frontend/src/workspace/useInvestigation.ts |
| 草稿确认与冲突 | useNotesDraft；frontend/src/workspace/useNotesDraft.ts |
| 字段交互 | NotesEditor、LinkEditor；frontend/src/workspace/ |
| 业务图与局部布局 | EvidenceGraph；frontend/src/EvidenceGraph.tsx |
| 规则反例 | LinkRevisionTests；test/unit/EchoCase.UnitTests/ |
| 持久边界反例 | PostgresApiTests、MigrationTests；test/integration/EchoCase.IntegrationTests/ |
| 浏览器时间反例 | consistency.spec.ts；test/e2e/specs/ |

以上是研究入口，不要求按表逐项执行。章节中的源码框提供固定提交、准确行号和链接，可沿调用进入完整上下文。

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
- [CleanArchitecture 固定上游](https://github.com/jasontaylordev/CleanArchitecture/tree/e1ab4cc4d5d7b4e25e57bd8b0514b766573b8c04)：用于第二章的机制比较，不表示已运行上游完整测试。

## A.4 关于真实性与适用范围

UI 图片来自真实 EchoCase 浏览器捕获，书页只裁切相关区域并叠加独立编号。机制图为本书原创矢量图；示意版本、事务与时间轴不伪装成采集数据。查询时间来自单机、合成应用数据、暖缓存的有限观察，不能当作生产容量结论。
