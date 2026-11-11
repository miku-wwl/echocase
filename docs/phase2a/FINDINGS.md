# Phase 2A 工程场景：机制、观测与判断

这是 A–E 的工程记录，不是日志转录。原始数据在 `evidence/phase2a/`。实现与旧 PDF 属于不同版本；出版素材索引见 PUBLICATION-INVENTORY。

## A：真正修改既有规则，而不增加模块

**问题与假设。** 更正关联判断如果只能删除再建，会丢掉关联身份。“原关联修订类型并解释”应只扩展已有根聚合行为，保留旧调查、端点和请求合同，沿用原安全与一致性门禁。

**实现路径。** PRD → ADR 0007 → Investigation.ReviseLink → InvestigationService.ReviseLink → PUT links/{linkId} → 可空列迁移 → 生成 LinkView/ReviseLinkRequest 类型 → 图谱列表中的 LinkEditor → 实际浏览器修订与 OCI 新旧版本验证。API 不自行改 EF 实体属性，子关联的 Revise 为 internal，根操作推进 Version。新请求包含 linkId 参与指纹，不能把另一个关联的同键请求当同一意图。

**观测。** `browser/link-revision.json` 保存真实前后快照，ID、sourceId、targetId 不变，类型与解释改变，版本只加一；重新加载仍可见。领域测试验证 Review 状态拒绝、未知关联拒绝、无变化拒绝，以及 19/20/500/501 个 emoji 的边界。API 的 500 个 emoji 与 PostgreSQL 存储同样通过，避免 UTF-16 长度与 char_length 不同。

**取舍。** 字符指 Unicode scalar，不是字素簇；组合字符/家庭 emoji 可以占多个 scalar，UI 和服务端采用同一计数口径。仅保留最新解释，不实现完整关联历史。旧 POST 创建仍可没有解释，因此不能声称全部关联都有完整理由。这种局部演进比强制给旧记录补默认说明更诚实。

## B：EF 跟踪、真实 SQL、迁移与原子性

**模式演进。** 测试先只应用旧的两条迁移，在真实旧列集上保存用户、调查、发现与关联，再应用第三条迁移。旧关联 ID/笔记不变，两个新字段均为 null；直接 SQL 只填解释、不填时间会被 ck_link_revision 拒绝。实际固定旧镜像还生成了缺新字段的回执，新镜像原键重放成功。前者覆盖模式/映射，后者覆盖真实旧应用的序列化合同。

**跟踪观测。** `database/migration-tracking.json` 在 AutoDetectChangesEnabled=false 时记录根和关联均为 Unchanged；调用根修订再 DetectChanges 后，根的 UpdatedAt/Version 与关联的 Kind/Rationale/RevisedAt 标记为 Modified。没有删除/插入关联。拦截器保存实际执行的 SQL，不记录参数值。根 UPDATE 的 WHERE 包含 Id 和原 Version，子 UPDATE 只按自身 ID；跨实体一致性依靠同一次事务与根令牌，不能只看子 UPDATE 就认定存在独立保护。[EF Core change tracking](https://learn.microsoft.com/en-us/ef/core/change-tracking/)、[乐观并发](https://learn.microsoft.com/en-us/ef/core/saving/concurrency)描述了相关机制。

**两种失败。** 一个测试用两个跟踪上下文提交不同解释，后者抛 DbUpdateConcurrencyException，重新读取只剩胜者解释。另一个测试实际调用生产 Store，barrier 让不同幂等键的两次读取都完成后再放行领域回调；记录隔离级别为 READ COMMITTED。结果为 200/412，只剩一条新回执和一条修订审计。EF 批处理可能先写审计，特定版本唯一约束冲突也被映射为 412；外层事务同时回滚子关联和回执。执行 SQL 与 surviving counts 见 `database/store-race.json`，不靠一次“碰巧并发”的请求证明路径。

**隔离替代。** 不把所有请求改为 SERIALIZABLE：当前单聚合的根令牌足以拒绝旧版本，序列化隔离会增加重试与全事务失败面。同键 advisory lock 只串行化相同 owner/key，不阻止不同键竞争；64 位锁名哈希碰撞最多导致额外串行等待，不是不同请求共用回执。单语句 Include 取得语句级快照；拆多条读取需要重新评估一致性。旧 E18/E19 演示隔离现象的独立表实验仍有教学价值，但不是当前业务实际执行路径。

**时间精度的实际失败。** 首轮 API 响应 RevisedAt 为 `639299746962572167` tick，数据库重读为 `639299746962572160`。7 个 tick 的差异使记录比较失败。应用在把时间传入领域前截到微秒后，两者相等；旧回执不修改。证据 `before/timestamp.trx`、前后 `timestamp-precision.json` 保留了发现与修正，避免把精度差误诊为并发覆盖。

**真实列表查询。** DbProbe 调用生产 `PostgresInvestigationStore.ListAsync` 并拦截 DbCommand，随后对同一 SQL/参数执行 EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)。实际表含 30,000 个调查、100 个所有者、60,000 个发现、30,000 条关联；目标所有者 300 个调查中取最近 50 个，联接后 100 行。没有使用与应用相似的另建 timeline 表。

本机七次热缓存观测的中位数为：无所有者索引 4.037ms、初始 OwnerId 单列索引 1.808ms、现有 OwnerId/UpdatedAt DESC 组合索引 0.929ms。组合索引让取前 50 的顺序读取更便宜，不能消除最终联接/排序成本；保留索引也增加存储与写维护成本。`application-query-plan.json` 包含全部样本、预热、完整代表计划与实际 SQL。固定顺序、单机、合成分布、只有每调查两条发现/一条关联、无并发负载；没有推断生产容量或宣称本阶段新增了这个早已存在的索引。

**回退选择。** 应用回退保留扩展模式。Down 明确删除新列；本阶段故意不执行会丢数据的 Down。不能把迁移文件可逆生成误读为数据无损可逆。[EF 迁移应用说明](https://learn.microsoft.com/en-us/ef/core/managing-schemas/migrations/applying?tabs=dotnet-core-cli)也强调审查目标状态与数据影响。

## C：重复、旧版本与未知网络结果

**协议。** 每次写入需要原意图的键；已有调查另带强格式单值 If-Match。指纹包括调查、版本、操作与正文。先按 owner/id 加载资源，再检查回执；同键同指纹返回原快照，同键改正文 409，新键旧版本 412，领域不允许 422。失败不缓存回执。链接属于另一个本人调查时不能修改，跨账户目标统一 404。

**保证。** 对遵守协议、走同一 PostgreSQL 端口的业务写入，同一 owner/key 的本地数据库效果至多提交一次，并可以重放同一响应。不是网络 exactly-once、永久可用保证或外部通知可靠交付。回执目前不自动过期/清理，也没有容量治理；不得在任意时间删除回执后仍承诺无限期去重。键按原字符串重试，客户端不重新生成键或变更大小写。

**未知结果。** 浏览器 route.fetch 将笔记实际送达 ASP.NET/PostgreSQL，等待提交响应后 route.abort 丢掉返回。直接 GET 证明原内容已提交；另一个真实请求再保存新内容。点击“重试同一次操作”重用原键/版本/正文，拿到原回执，服务器版本不再增加。MutationObserver 检查页面没有观察到版本倒退，原草稿保留等待显式决策。`browser/lost-response.json` 保存两次实际请求、已提交/较晚/最终快照。这与 `workflow.spec.ts` 单纯返回假 503 的注入点不同。

## D：草稿、缓存与呈现的所有权

**先失败。** `before/results.json` 两个故意运行在基线前端的检查失败：晚到保存响应把“等待时继续记录的新线索”覆盖成先提交内容；dirty 草稿刷新后仍可直接保存，原代码会读取最新 s.version，绕过用户确认。截图、现场 JSON 与失败 trace 保留，不能把“输入框还在”当成状态正确。

**状态模型。** useInvestigation 持有已确认服务器快照、命令和失效；Query key 包含用户与调查。结构共享策略按版本单调接受 GET/回执，pending 文本仅单独呈现。useNotesDraft 保存原笔记、原版本和编辑代次；输入即标 dirty，避免“改回原文”在等待请求期间被误认为可覆盖的 clean 状态。成功只清除同代提交；有后续输入则推进自己已确认基线但保留文本。已知新版本展示三份内容并要求显式确认；未知结果禁止其他新写，允许继续输入，原键重试。

**请求取消。** Query 的 AbortSignal 真正传给 fetch。取消不等于网络写入未知，故不包装成 ApiError network_error。TanStack 的取消机制只有信号被查询消费才会真正终止对应请求；参见[官方取消说明](https://github.com/TanStack/query/blob/main/docs/framework/react/guides/query-cancellation.md)。

**维护性。** App 从 1018 行拆为 475 行，Workspace 保留工作台呈现，笔记和关联编辑器独立；协议与草稿规则各有 hook。收益由晚到响应、后台刷新、双窗口、未知结果和完整五模块的实际回归证明，行数本身不作为完成指标。没有新全局 store、协作框架或大规模视觉重做。

**限制。** 页面关闭/切换调查后不恢复未保存草稿，没有自动合并。所有状态在单调查版本下冲突，修改其他字段也可能要求再确认，较细粒度令牌可以降低冲突但会改变当前聚合一致性边界。React Flow 节点坐标仍是本地呈现，不假装持久布局。

## E：交付、诊断、恢复与回退

`experiments/phase2a/delivery.py` 从 git archive 固定旧提交构建旧镜像，从当前源构建新镜像；记录源提交、源内容摘要、脏工作区标志、镜像 ID、非 root UID。每次创建独立网络、数据库/密钥卷及随机命名容器。不是复用正在运行的旧演示实例来冒充干净部署。

路径为旧迁移/旧应用写入三发现两关联与笔记 → 新迁移且旧应用继续读写 → 新应用重放旧关联回执并修订 → 真停数据库 → live=200/ready=503/business=503 → finally 恢复数据库 → 旧镜像回退并写笔记 → SQL 直接确认新解释未丢 → 新镜像前滚并结案100分。Cookie 通过持久 DataProtection 卷跨重建使用；临时卷初始化为 UID1654，不以 root 运行应用。

第一次停库链发现错误正文 traceId 是完整 W3C Activity.Id，而响应头是 Activity.TraceId。默认 ProblemDetails writer 在调用 CustomizeProblemDetails 之前设置该字段，覆盖了调用端提供的扩展；由源码与本地 422 复现共同定位，见[ASP.NET Core v10.0.9 源码](https://github.com/dotnet/aspnetcore/blob/v10.0.9/src/Http/Http.Extensions/src/DefaultProblemDetailsWriter.cs)。统一定制后，第二次真实演练的 503 正文、头与日志编号一致。第一次失败与其成功清理结果也保留。

成功记录入口 `delivery/latest.json`；每次运行目录含两份构建、旧/新/重复迁移、故障与最终日志、逐阶段事实、最终调查和清理退出码。只删除本次成功创建的资源；旧6080实例及其他容器未动。GitHub Actions 使用 Docker 重新执行同一脚本，并把新运行证据上传，再用语义门禁核对，不能靠仓库里旧绿灯代替。

边界：本地与 CI 都是单机 loopback HTTP 的 Development 策略，没有 TLS、真实反向代理、多副本、HA、负载或完整业务灾备证据。Azure 为设计，未创建资源；完整目标与批准条件见 AZURE-DESIGN。
