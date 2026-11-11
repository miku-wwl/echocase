# EchoCase 工程与出版路线图

日期：2026-11-11。工作分支 `codex/enterprise-masterclass-20261111`。保留 main，不合并，不创建付费云资源。

## 现状与参考审计

原仓库只有 README 与 Apache-2.0 LICENSE，无可运行代码或历史实验。README 的五模块是验收边界。

参考仓库 `miku-wwl/devops-delivery`：

| 分支 | 核对提交 | 采用的方法 |
|---|---|---|
| p12/manual | 84fb320bc336bf6e116f27ac809235b0328d1138 | Markdown 教学结构、图表、Playwright 打印、两遍目录 |
| release/v1.0 | b062e7841026db4c17ee3c73ac3cf6ce233ac68a | 证据与版面失败必须非零退出、故意损坏输入验证门禁 |
| v2/enterprise | 7a41a899cb9b0fbb853f9d087a5b804e24e24229 | 区分真实/注入/模拟、单机测量边界、独立验收 |

实际阅读 `manual/tools/build.py`、`verify_evidence.py`、`docs/ACCEPTANCE_REPORT.md`、`docs/RELEASE_v1.0.md`、`v2/docs/PLAN.md`。参考仓库不被修改；没有复制其集群或平台架构。

Jason Taylor CleanArchitecture 核对提交 `e1ab4cc4d5d7b4e25e57bd8b0514b766573b8c04`。阅读 Application DI、Authorization/Validation behaviours、DbContext、SavingChanges 域事件拦截器与 Infrastructure DI。借鉴向内依赖和请求管道，不整体生成 Aspire/Todo 应用。采用显式用例而非引入 Mediator/Mapper。模板的角色权限不能替代资源所有权检查，SavingChanges 事件不等于已提交事件。本项目没有继承其业务源代码，详见 THIRD-PARTY-NOTICES.md。

## 阶段门禁

| 阶段 | 产出 | 验收依据 |
|---|---|---|
| S0 基础 | 版本锁、架构/课程/实验设计、测试与出版入口 | 干净还原、构建与门禁故障自测 |
| S1 领域 | 调查聚合、状态机、证据访问、关联、结论 | 纯领域 NUnit + 依赖约束 |
| S2 服务 | 身份、PostgreSQL、迁移、命令查询、事务 | 真实 PostgreSQL 集成/并发/幂等/越权测试 |
| S3 全栈 | React、TanStack Query、React Flow、生成契约 | Playwright 五模块工作流、回滚和冲突 |
| S4 实验 | 至少 20 个实验、优化、恢复、CI/容器 | 实际退出码、原始证据、可复现脚本 |
| S5 出版 | 18 章中文教材、答案、插图、独立报告 | 每页渲染、目录/链接/证据/版面核验 |

每阶段遵循设计→实现→测试→实验→证据→教学→审查。状态只用 VERIFIED / PARTIAL / BLOCKED / NOT_RUN；代码存在不算运行成功。教材页数目标 300–400，最终按内容质量评估，不以放大字号或重复材料凑数。

## 课程

1 需求与边界；2 Clean Architecture；3 DDD 与状态机；4 ASP.NET 请求管道；5 CQRS 编排；6 API 契约；7 关系模型与迁移；8 并发与隔离；9 幂等与重试；10 身份与威胁建模；11 React 架构；12 服务端状态；13 证据图；14 分层测试；15 SQL 与性能；16 可观测性与恢复；17 容器/CI/Azure；18 综合考核。

## 决策

单一调查聚合使用显式整数 Version，方便 HTTP If-Match 与课堂分析。子记录使用关系表，关联外键指向已发现证据。身份使用 ASP.NET Identity 密码哈希和 Cookie；所有写操作校验防伪令牌。以 PostgreSQL 事务级 advisory lock 串行化同用户同幂等键；提交聚合与幂等回执同事务，错误不缓存。只保留一个虚构案件，案件规则版本固定于代码。Azure 仅提供部署设计，不实测付费资源。
