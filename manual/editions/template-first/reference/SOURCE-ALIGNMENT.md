# Template-First 修订版源码对齐报告

日期：2026-11-13。本文件及 JSON 索引不进入 PDF。

## 固定来源

- 当前工程：`9f68721e18f15ae603e6502fa46b8fa78f9df55c`。出版提交推进 main，不改变此引用。
- 官方模板：`Clean.Architecture.Solution.Template@10.8.0`；[上游 e5c08ec](https://github.com/jasontaylordev/CleanArchitecture/tree/e5c08ecead8a52f6cf519477bf6c57668248c035)。
- 实际生成：`f1df1a3c3b95bae184600a0ccef629eccaa18080`；171 个原始生成文件有独立来源记录，活动应用保留明确转换。
- 历史教材工程：`908811b95fb40cf14fa79b8eddf41796aa02cc04`；历史发行：`bf9de37b9bd4d5cc2c227af2c857360e048b15d1`。
- 历史真实界面/数据库运行：`63c587277541b4e700258aad82de9b2ad0ba32f8`，2026-11-11。

原应用先自行实现，随后纠偏并真实生成模板、独立验证、迁移业务和适配。原生成样例曾有登录等待超时及审计告警限制，不描述成全部上游样例通过；当前业务接受的 26/27/9 是另一范围。[工程基线 main CI](https://github.com/miku-wwl/echocase/actions/runs/43338869463)与[独立 bootstrap 运行](https://github.com/miku-wwl/echocase/actions/runs/43181797531)分别保留。

## 逐章决定

| 编辑源 | 处理与核验结论 | 摘录出现次数 |
|---|---|---|
| 00-preface.md | 重写来源、读者前提、真实纠偏与历史素材边界。 | 0 |
| 01-requirements.md | 保留固定案件、任务闭环、投影、失败后果与有限范围；当前源码逐项核验。 | 2 |
| 02-clean-architecture.md | 重写真实生成历史、直接项目引用、运行端口回调、保留/适配/移除、扫描与作用域。 | 3 |
| 03-domain.md | 保留已成立的 Guid 身份、聚合、状态转移、标量值与原子赋值推理。 | 4 |
| 04-request-pipeline.md | 重写 SaveNotes 全链路；拆开 HTTP、绑定、Logging 预处理、四行为、处理器与 Store 事务。 | 8 |
| 05-cqrs.md | 重写 IRequest/Handler/ISender、扫描、逻辑 CQRS、校验和提交后诊断风险；展示历史与当前真实片段。 | 9 |
| 06-api.md | 重写 OpenAPI 3.0、命名 operationId、NSwag 14.8.0、真实生成方法、适配器和未知结果范围。 | 10 |
| 07-persistence.md | 保留跟踪深度，补 AutoDetectChanges 夹具前提、历史日期、AcceptAllChanges/Commit 分界及审计适配。 | 4 |
| 08-schema-evolution.md | 核验可空迁移、旧 JSON 回执与真实时间精度，标明历史观察。 | 3 |
| 09-mvcc.md | 核验每语句快照、并发写条件和对象缓存；图中事务与快照均明确示意，历史探针单独注明。 | 1 |
| 10-concurrency.md | 核验 CAS、指定 Audit 约束和事务回滚；历史竞争结果没有冒称新执行。 | 2 |
| 11-idempotency.md | 更新类型化 kind/目标参数、SDK/适配器分类；保留回执次序与原意图恢复，补解析范围限制。 | 4 |
| 12-security.md | 重写 Cookie、IUser、IdentityService、两层入口授权、事务 owner 过滤及前所有者重放反例。 | 7 |
| 13-react.md | 保留快照与组件生命周期；把 route 判断改为当前 kind，更新意图所有权。 | 3 |
| 14-server-state.md | 更新 Query → executeOperation → 生成 SDK → apiCall 的真实接线与取消；保留缓存单调。 | 5 |
| 15-drafts.md | 保留基线、代次与三方比较；核验 notes 判别分支，重新裁切真实 UI，未编造新版截图。 | 5 |
| 16-graph.md | 核验无向关系、稳定身份、本地布局；补 revise-link 到生成方法的执行路径。 | 4 |
| 17-performance.md | 核验三种历史计划、所有数值与工作负载；明确没有本轮新基准或生产指标。 | 2 |
| 18-testing.md | 保留反例推理，补直接 Send、无效 Key、前所有者、模型漂移、慢写诊断五项保护。 | 6 |
| 19-evolution.md | 实质扩写为 16 处真实跨层摘录，连接根、命令、处理器、协调、事务、映射迁移、端点、SDK、UI 与验证。 | 16 |
| 20-reasoning.md | 保留原有题目，新增直接 Send、运行时 JSON 验证与 SaveChanges/Commit 三道推理题。 | 0 |
| 21-reference.md | 更新术语与官方版本；正文改为章节导航，详细文件/摘录索引移到外部对齐资料。 | 0 |

## 57 处旧摘录与当前选择

原 57 处出现位置逐项从 908811b 解析，再按当前等价职责定位到 9f68721；46 处文本不变，11 处已变化。变化包含端点移动、DI/Cookie 所属位置、当前用户端口和网络适配。并非只替换 SHA。[完整逐项对照](historical-57-excerpt-audit.json)。

新版当前使用 98 处摘录、84 个不同选择器、808 行原始源码。96 处是当前工程，2 处明确标为历史官方生成比较（注册与性能行为）。选择器总量 98 包含少量审计用途而未装订的候选；没有把未使用代码装订以增加页数。每次提取记录 commit、Git blob、路径、行范围、片段 SHA-256；软折行保留原字符，不产生虚构行号。[选择器与校验元数据](source-selector-audit.json)、[可编辑选择定义](../source-selections.json)。

源码始终先读取 Git 固定对象；当前工程还比较完整工作文件，不以工作区内容代替固定来源。工程清单覆盖 backend/frontend/test/.github 全部 128 个跟踪文件。历史重建直接验证旧 Git 对象，在迁移后的工作树不要求旧实现仍存在；这不是关闭固定来源检查。[工程字节清单](engineering-source-inventory.json)。

## 容易误读的机制及修正

- 直接 ProjectReference 是 API → Infrastructure → Application → Domain；运行调用图另外绘制。临时 Handler 在当前作用域取得 scoped DbContext。
- Logging 是最外侧预处理；内侧才是 UnhandledException → Authorization → Validation → Performance。Logging 身份读取可早于校验，也不被内层异常行为包住。
- 对带 SessionId 的既有调查修改，Store 先开事务、锁、按 owner 加载、查回执、比版本，才执行领域回调；Start 没有目标加载分支，不能将前所有者笔记夹具结论推广成任意未来权限变化保证。资源检查在回执之前，回执在版本拒绝之前。
- Performance 只计量处理器，不含外侧授权/校验与 JSON 写出；当前慢日志没有提交后的用户名数据库查询。原失败路径属于源码推演，实际回归验证修正后只有一次查名。
- FluentValidation 当前检查 Key 语法，不查询当前聚合；领域与关系约束保持原职责。无效 Key 在业务事务写入前失败，不宣称零 SQL。
- NSwag 生成 URL、method、DTO 和正文解析；应用适配器保留 Cookie、CSRF、If-Match、Key 与错误规范化。不是仅生成 .d.ts，也不生成草稿/回执状态机。
- DTO 接口不验证任意运行 JSON。畸形成功 JSON 可变成 response_unreadable；空成功正文可能被接受为 null，合法错误形状没有完整验证。
- CurrentUser 从 claims 取身份，通用 Authorization 不替代具体调查 owner 过滤。当前无团队/管理员业务授权或数据库 RLS；所有权转移仅出现在夹具 SQL。
- 跟踪快照的接受与显式 Commit 分开，EF Unchanged 不证明最终提交。历史夹具为分离时刻关闭自动检测。
- PostgreSQL MVCC 与应用 Version、查询到达顺序与资源版本、本地 revision 与服务器 Version 都分别解释。

## 图与真实素材

44 张历史机制 SVG 全部审阅：31 RETAIN、1 REVISE、12 REPLACE、0 REMOVE；另 ADD NEW 7 张。[逐项决定及原因](figure-decisions.json)。主要替换图展示实际引用、请求时序、职责、校验、作用域、端点生命周期、安全、Query 与跨层演进；新增图展示来源交汇、行为嵌套、提交后风险、生成/运行双时间、owner/回执、跟踪/提交和版本传播。

九组 PNG 保持原像素和摘要。各图标题注明历史日期；笔记三图改为同一真实界面的局部条带，省去空白输入区，标明两个裁切片属于同一界面。没有合成应用内容或新执行声明。[素材出处](asset-provenance.json)。

领域 Investigation、协调服务 Investigations、EF EchoDbContext、PostgresInvestigationStore 与历史运行源逐字节一致；请求分派和前端 transport 已改变，因此不宣称整个应用都等于历史运行。真实 SQL、200/412、精度与计划从固定 63c5872 读取；概念 xmin/xmax、事务号、时间轴和跨行业务反例明确为示意。

## 断言类别与限制

| 类别 | 本版使用方式 |
|---|---|
| VERIFIED | Git 文件/摘录/哈希、真实历史像素与观察、已有基线 CI；本次构建/渲染/结构检查另有 QA |
| SOURCE-ANALYSED | 当前注册与源码解释、框架包装顺序、原性能行为的反事实风险 |
| ILLUSTRATIVE | 机制图中的 T1、快照编号、任意示例版本和用于推理的值班反例 |
| NOT_RUN | 本轮没有重新执行原性能负例、新捕获应用 UI 或重新跑历史 SQL 性能基准 |

仍保留实现限制：回执无自动清理、草稿无页面重启恢复、一般 5xx 未统一持久恢复、生成客户端无完整成功正文 schema 验证、图位置仅本地、列表最多五十项且无游标。没有为教材修改这些应用行为。

正文没有环境命令、原始 JSON、CI 历史或测试清单；再现与审查文件独立于章节 manifest。出版源码和图可编辑，原 book.json、章节、SVG、PNG 与历史 PDF 保持不变。
