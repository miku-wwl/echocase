# 模板整改对历史教材的后续修订影响

本轮只登记影响，不重写正文、不重画图、不重建PDF。待工程基线独立接受后，另行开展教材修订。

历史出版提交：`bf9de37b9bd4d5cc2c227af2c857360e048b15d1`；书内源码基线：`908811b95fb40cf14fa79b8eddf41796aa02cc04`。PDF SHA-256：`dd00cbfb1cfeb58cea6f28e13c6ea0dd6d72df68bc4668ba6016f1c8edf66166`，与原提交逐字节一致。

旧书描述的是当时的自行实现，不能改写成“始终从模板开始”。新书必须区分历史和新生成基线；所有57处摘录及附录索引都应在新工程接受后重新对齐。

| 章节源 | 后续处理 | 具体插图ID（均保留原图，本轮未修订） |
|---|---|---|
| `02-clean-architecture.md` | 实质修订：真实模板来源、MediatR管线、Identity端口、DI和偏离依据，删除当前实现未用模板的结论。 | `architecture`、`template-tradeoffs`、`di-scope` |
| `04-request-pipeline.md` | 实质修订：命名端点发现、ISender调用、授权/验证behaviors、错误映射与生命周期；区分HTTP中间件和MediatR管线。 | `request-pipeline`、`binding-sources`、`problem-writer`、`endpoint-lifecycle` |
| `05-cqrs.md` | 实质修订：真实command/query/handler、验证器、IUser身份来源及原协调服务在handler内的角色。 | `usecase`、`validation` |
| `06-api.md` | 实质修订：NSwag固定版本、OpenAPI3.0和operationId、生成方法/DTO与传输适配器分工。 | `intent-coordinates`、`http-outcomes` |
| `07-persistence.md` | 复核源码上下文：映射和跟踪机制未变；解释为何不继承样例拦截器或替换现有DbContext。 | `ef-materialization`、`ef-tracking`、`ef-identity`、`ef-states`、`ef-values` |
| `08-schema-evolution.md` | 复核：旧三条迁移和回执兼容保持；补充模板初始化必须移除的原因及无模型漂移验证。 | `schema-contract`、`time-precision` |
| `10-concurrency.md` | 复核：根/子/audit/receipt事务未变；在竞态图外标明前置模板管线不拥有事务。 | `cas-race`、`transaction-set` |
| `11-idempotency.md` | 修订客户端代码与调用图：生成方法经适配器传递原key/version；所有权仍早于回执查询。 | `receipt-lock`、`uncertain`、`ui-unreadable` |
| `12-security.md` | 修订来源与DI：CurrentUser、IdentityService、授权behavior；保留Cookie/CSRF与资源事务授权的两级区别。 | `security-boundaries`、`ui-evidence` |
| `14-server-state.md` | 更新NSwag/apiCall和类型化意图的源码；缓存单调性与取消时序需要按新提交重新核验。 | `late-get`、`query-cycle` |
| `15-drafts.md` | 更新Operation.kind和生成客户端的摘录；原草稿代次/三方比较保留，UI与时序需新基线复核。 | `draft-generation`、`ui-inflight`、`three-way`、`ui-dirty` |
| `18-testing.md` | 补充管线直接分派、回放前所有权和模型漂移的反例意义；不把测试运行库存入正文。 | `test-reasoning` |
| `19-evolution.md` | 修订跨层演进路径，新增handler/validator/operationId/NSwag生成影响，保留领域规则。 | `evolution`、`review-model` |
| `21-reference.md` | 重建真实源码索引、版本引用、模板来源和依赖说明；原锚点不可自动视作当前实现。 | 无独立图；修订索引 |

第1/3章的业务需求和领域规则、第9章MVCC、第13章React渲染、第16章图谱、第17章历史查询观察、第20章推理题无需因模板名称而整体改写；但源码引用、历史界面日期、测量适用范围及连接到新请求路径的段落仍需复核。序言应说明新来源和版本。

重点重画候选：`architecture`、`template-tradeoffs`、`di-scope`、`request-pipeline`、`endpoint-lifecycle`、`usecase`、`validation`。`intent-coordinates`、`receipt-lock`、`uncertain`、`query-cycle`、`security-boundaries`、`evolution`需结合实际新调用路径修订标注；EF/MVCC/事务/草稿图先按不变机制复核，不能只替换图题就宣称技术更新。

真实截图与运行观察继续保留其原始出处。未来接受的新版本若重新采集，必须单独记录；本轮9项浏览器回归通过不意味着旧PNG已更新。发布脚本的固定源码漂移检查应继续拒绝直接用新工作区重建旧版本教材。
