# Phase 2B 出版内容资产清单

这是可供后续编写的材料清单，**不是已经完成的教材出版**。2A没有扩写/重排PDF。冻结教材97页、旧验收PDF6页继续保留；300–400页是否合理由真实教学内容决定，不为页数制造新模块或基础设施。

## 可直接进入深写的工程故事

| 叙事与读者应学会的判断 | 已有源/材料 | 可用执行素材 | 2B编写动作 |
|---|---|---|---|
| 一个关联修订如何跨越边界；小需求为什么仍需要合同、数据和发布审查 | PRD、ADR0007、RELEASE-NOTES、Domain/Application/API/迁移/LinkEditor | `browser/link-revision.json/.png`；后端修订测试；OCI前后关联身份 | 按需求→影响→规则→合同→迁移→交互→交付写连贯案例；做变化影响图和前后合同注释 |
| 从模板理解机制而不是照搬目录 | TEMPLATE-COMPARISON；固定上游9份文件与摘要 | `upstream-source.json`；本项目依赖边界测试 | 并排追踪 UpdateTodoItem 与 ReviseLink；标清DI作用域、行为顺序、EF端口与事件发生时点；不写成上游全集执行报告 |
| EF跟踪如何变成多个UPDATE，为什么子表没有Version也不能局部提交 | SqlObservation、迁移测试、Store竞争测试 | `database/migration-tracking.json`、`store-race.json` 的真实SQL/状态/结果 | 从 Unchanged→DetectChanges→Modified→条件UPDATE→回滚讲解，标注身份映射与事务边界；日志放附录/仓库 |
| 模式可以回退，数据未必可回退 | ADR0007、第三迁移、delivery.py | 旧镜像真实数据→扩展模式→旧应用写入→新解释仍在 | 画 expand/应用切换/回退/前滚时间线；解释为什么不执行有损Down，并明确没有灾备/PITR结论 |
| 时间精度导致的合同不一致 | Application.Now；新API一致性断言 | `before/timestamp.trx`，前后 timestamp-precision JSON | 用7 tick真实差异拆解.NET/数据库精度与回执稳定性；设计跨存储类型的练习 |
| 幂等不是拿到成功响应，更不是网络exactly-once | Application.Write、PostgresStore、useInvestigation | `browser/lost-response.json/.png`，同键并发/误用/旧版本测试 | 画提交点/丢响应/后续写/旧回执时间线；解释有限保留、精确原请求重试及所有权检查顺序 |
| React正确性取决于时间与状态所有权 | ADR0008、useNotesDraft、NotesEditor、useInvestigation | `before/`两项失败；`browser/inflight-draft`、dirty-refetch、lost-response | 用失败时序与修复后时序对照，逐步解释编辑代次、基线、确认缓存/pending呈现、显式冲突；避免只列hook API |
| 真实查询、索引和测量限制 | DbProbe、Store.ListAsync、索引迁移 | `application-query-plan.json`三组完整计划、样本、SQL与参数 | 重绘可读的计划路径和样本分布；解释取前50与联接排序、写成本/基数、预热与固定顺序偏差；不转述为生产SLA |
| 故障发现必须能回到对应日志 | API ProblemDetails定制；框架固定源码说明 | `before/problem-trace.json`、第一次OCI失败、第二次200/503/503与统一TraceId | 以“看起来都有编号但对不上”开篇，解释框架写入顺序；匿名化/裁切日志，不把异常堆栈堆成正文 |
| 应用交付要能执行旧版，而不是只build一个镜像 | delivery.py、phase2a.yml、AZURE-DESIGN | 本地各阶段事实/镜像ID/迁移/日志/清理；CI fresh artifacts | 展示干净源→部署→验证→诊断→回退→前滚；画本地/CI/云设计三种证据范围；明确Azure未运行 |

## 现有18章的使用建议

保留现有课程骨架。ch01补实际变更影响；ch02/05深化模板与端口；ch03/06/07沿关联修订规则讲合同与模式；ch08/09用真实竞争与丢响应贯穿；ch10区分已验证保护与生产缺口；ch11/12拆解状态时序；ch13注释原图谱的新修订入口；ch14解释为什么选这些断言而不是追数量；ch15使用真实应用SQL；ch16/17改为完整应用交付故事；ch18做综合判断练习。ch19实验索引使用 TRACEABILITY 的两个编号空间，不能把现 E09 误写成原维护性E09。

旧PDF的源摘录和截图代表Phase1；Markdown ch12已作必要准确性修正，尚未出版。2B必须绑定一个明确工程提交，重新提取源码片段，不能仅更新行号后假设解释仍对应同一逻辑。

## 可用视觉资产与待制作清单

- 现有五模块、图谱、结论、390px屏幕截图可保留作基线；本轮 `browser/link-revision.png`、`inflight-draft.png`、`dirty-refetch.png`、`lost-response.png` 是实际浏览器场景，不是设计稿。
- 基线失败截图/trace与修复后截图适合成对注释；需裁掉大段空白、标注提交前/后、查询/草稿版本和注入点。单张截图不能证明版本、事务或因果，旁边应配真实JSON/测试断言的解释。
- 2B待制作：两套请求链比较图、聚合/表/令牌映射图、三种前端时序图、同键/异键竞争图、旧/新应用切换图、实际SQL计划图。尚未制作这些出版级插图，不把本清单标为已交图。
- 截图中的随机账户、调查ID、traceId为实验数据；出版时统一标明合成/本地身份，避免读者误以为线上真实案例。

## 2B必须保留的证据语义

“VERIFIED”只覆盖具体运行与环境。旧E18/E19是独立SQL示例，旧E24不是完整业务灾备，原PDF目标仍PARTIAL；Azure/生产HA/TLS/负载/PITR为NOT_RUN。不能因2A工程通过而把这些状态改绿。完整源日志放仓库，正文以问题、机制、推理、取舍和失败教训为主。

复现脚本、原始证据和本目录已具备编写入口。后续出版还需章节深写、视觉设计、交叉引用/源码重绑、练习答案深化、真实截图注释、技术审校、两遍目录/链接/书签检查和逐页视觉QA。没有把旧PDF已做的QA当成尚未生成的新教材QA。
