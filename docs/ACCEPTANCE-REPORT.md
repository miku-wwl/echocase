# EchoCase 工程与出版验收报告 {#acceptance}

日期：2026-11-11（Pacific/Auckland）。分支：codex/enterprise-masterclass-20261111。结论：**PARTIAL，已形成可运行、可审阅的全栈工程版本，尚未满足原任务全部旗舰教材目标。**

这是一份独立于教材的验收材料，由同一执行者建立并运行自动检查；没有第三方审计员或外部读者独立复现，不把作者自测声称为第三方认证。main 未合并，Azure 未创建资源或产生费用。

## 已实现的应用

五模块均在真实浏览器、ASP.NET Core 和 PostgreSQL 上走通：案件浏览/启动/恢复；证据查看/调查/前置解锁；无向证据关联与 React Flow 图谱；笔记/状态/并发/幂等进度；有证据支持的结论与只读封存。案件为原创虚构单案，六条证据，评分是固定教学规则。

架构是 Domain → 基础类型、Application → Domain、Infrastructure → Application、API 组装依赖的模块化单体。没有引入微服务、Kubernetes、多租户、AI 或事件溯源。借鉴 Jason Taylor 模板的边界和请求行为机制，没有复制其 Todo/Aspire/Identity 业务源代码。官方 shadcn 组件和必要 CSS 保留 MIT 许可证。

## 自动化与实验结果

| 检查 | 结果 | 范围与证据 |
|---|---|---|
| 后端 NUnit | VERIFIED：{{claim:backend_passed}} / {{claim:backend_total}} | evidence/backend/backend.trx；无跳过 |
| 真实 PostgreSQL | VERIFIED | 外键、增量迁移保留、双 DbContext、原子回滚 |
| Playwright | VERIFIED：{{claim:browser_passed}} 组 | evidence/browser/results.json；完整工作流、注入503、双窗口、390px |
| 架构边界 | VERIFIED | 程序集引用 + 临时副本外向引用故障 |
| 幂等与版本 | VERIFIED | 同键提交一次、异键竞争一胜一412、改正文409 |
| 身份与资源授权 | VERIFIED，范围有限 | 未登录401、异主404、CSRF400、登录速率429、正文不提前返回 |
| 可靠性 | VERIFIED，单机注入 | live200 / ready503 / 业务503，恢复后原调查可读 |
| 容器 | VERIFIED，直接Podman路径 | 多阶段构建、UID1654、独立DB、应用重建、数据与Cookie保留 |
| pg_dump/restore | VERIFIED，合成小库 | 三条中文记录精确恢复；非完整应用DR或PITR |
| QA 自测 | VERIFIED | 七类证据损坏、三类坏PDF均非零退出 |
| NuGet/npm扫描 | VERIFIED，当时数据库范围 | evidence/backend/dependency-audit.json 与两份npm报告无已知告警 |
| 远程 GitHub Actions | 以 evidence/ci/results.json 为准 | 必须记录真实失败演练与正常运行，配置文件不算运行证据 |

性能：十万条、五千所有者的合成时间线，组合索引前后中位数分别 {{claim:sql_before}} / {{claim:sql_after}} ms，返回行数相同且计划由 Seq Scan 转索引。真实 API 暖机后顺序100次读取 p95 为 {{claim:api_p95}} ms。它们不是生产容量、最大吞吐或长期稳定性结论。

恢复计时 {{claim:recovery_ms}} ms 从容器启动命令返回后开始，不包含完整启动命令与故障检测时间，因此不是端到端 RTO。没有给出生产 RPO。

26份实验记录在 docs/experiments/E01–E26.md；每项包含问题、机制、基线、执行、观测、解释、限制与清理。manifest 绑定文本规范化后的 SHA-256，检查有限的结构化结果、代码片段、来源数字、引用与答案。它不能证明所有自然语言推论无误。

## 真实缺陷与修正证据

| 发现 | 修正 | 再验证 |
|---|---|---|
| 初始迁移缺工具引用 | API加入 EF Design | 真实数据库全集通过 |
| 手动Guid新关联被EF误判为更新 | ValueGeneratedNever | 完整调查不再产生假并发冲突 |
| 审计唯一约束竞争返回503 | 特定版本约束映射412 | 一胜一拒绝与回滚断言 |
| 登录200但页面不切换 | 保留me查询观察器，仅清其他缓存 | 浏览器完整流程 |
| OpenAPI版本号变number|string | 严格JSON数字策略 | 再生成合同并构建 |
| 停库后EF包装异常返回500 | 映射已知Npgsql包装 | 真实停库/恢复重跑 |
| 开发pasta网络不支持接桥接 | 容器验收用独立数据库网络 | 从独立模式迁移并重建 |
| 门禁损坏副本缺前端片段 | 先验证正常夹具，再单一注入 | 七项均出现预期诊断 |

首次失败的TRX、浏览器JSON和错误映射前日志保留；不是用最终成功覆盖所有工程历史。

## 出版验收与目标差异

教材含18章、前言、实验手册、参考来源，54道章末练习与参考答案，架构/状态/序列/关系图、真实应用截图和当前源码片段。目录采用两遍打印并核对目的页，测量由来源JSON展开。构建、版面和视觉记录分别在 manual/tools 与 evidence/qa。

**编辑目标仍为 PARTIAL：当前属于约百页的精炼审阅版，明显少于原约300–400页目标，章节深度尚需继续扩展。** 没有通过增加空白、放大字号或重复原始日志凑页数。不能把这一版本称为已完成原任务所要求的完整旗舰教材。

逐页视觉状态与实际页数以 evidence/qa/visual-review.json 和 book-layout.json 为准。任何仍存在的越界、缺图或极小文字都是阻断问题；普通章末留白须在审阅记录中说明。目录、图意与源码一致性和实际PDF再生成需要分别确认。

## 最终条件逐项评估

| 原条件 | 状态 | 说明 |
|---|---|---|
| 干净环境可运行 | VERIFIED，限定范围 | 独立容器数据库和镜像构建；远程runner另记 |
| 五模块端到端 | VERIFIED | 完整浏览器与数据库流程 |
| 架构/领域 | VERIFIED | 测试与边界门禁 |
| 数据一致性/并发 | VERIFIED | SQL、EF与HTTP三层证据 |
| 认证授权边界 | VERIFIED，限定范围 | 生产身份治理未完成 |
| React/API集成 | VERIFIED | Cookie、生成合同、浏览器 |
| 分层测试 | VERIFIED | 单元、集成、架构、E2E |
| 性能/可靠性 | VERIFIED，单机范围 | 暖缓存合成数据与有界故障 |
| CI/CD与部署 | PARTIAL | 本地OCI验证，远程CI实际状态另记，Azure NOT_RUN |
| 教材实质深度与视觉 | PARTIAL | 精炼审阅版，未达到原旗舰规模与完整编辑目标 |
| 每页视觉检查 | 以视觉记录为准 | 未观察的页不得勾选 |
| 产物一致性 | PARTIAL至门禁完成 | 来源数字/源码/证据可机器核对，语义仍需审阅 |
| 限制披露 | VERIFIED | 本报告与各实验均列范围 |
| 分支提交可审阅 | 以最终Git记录为准 | 不合并main、不修改保护规则 |

## 剩余风险与所有者动作

仍需扩写教材机制、案例、练习层次与独立读者反馈；安排未参与实现者按干净环境复现并审阅。生产前补齐账户恢复、邮箱确认或外部身份、MFA适用策略、安全戳/会话撤销、密钥保护、持久日志告警、完整应用异机备份恢复、回执保留与数据治理。

当前只展示最近50份调查，无分页/多人协作/动态案件版本；图谱布局不持久化；Workspace组件较大；图谱未懒加载；未完成大图性能、全浏览器、全面无障碍、长期负载、完整渗透、镜像漏洞扫描/签名/SBOM或生产运行验证。不要把单机结果外推。

Azure部署需所有者先审阅具体资源与费用，再授权创建。main 合并与最终内容验收由所有者进行；工作分支和本地运行实例用于审阅，不代表生产发布。
