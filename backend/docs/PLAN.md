# 当前开发路线与Definition of Done

2026-11-11所有者批准将EchoCase收窄为Enterprise .NET Full-Stack Application Engineering。新边界取代原README中的云与广义CI/CD目标；原E10作为历史，不是当前完成条件。见ADR0009与历史引用。

## 学习目标

- T1：Clean Architecture & DDD，依赖倒置、聚合、不变量、用例与取舍。
- T2：EF Core & PostgreSQL，跟踪、SQL、迁移、事务、索引和并发。
- T3：Advanced React Engineering，组件、类型、服务器状态/草稿、查询同步与恢复。
- T4：API Security & Data Consistency，身份、资源所有权、CSRF、合同、条件写与幂等。
- T5：Application Testing, Maintainability & Software Quality，独立测试、架构边界、重构与轻量CI。

## 当前路线

1. 理解四层与模板机制，建立普通本地.NET/React/PostgreSQL开发入口。
2. 用根聚合表达五模块的规则与状态，并以纯单元测试验证。
3. 用真实数据库验证映射、迁移、旧数据、并发、授权和回执事务。
4. 用生成合同集成前端，验证草稿、冲突和完整用户流程。
5. 基于真实需求作小范围演进；保持测试独立和应用CI，记录机制与取舍。

## 当前DoD

- 五模块可工作；按开发文档能恢复依赖、迁移、启动后端和Vite。
- 领域规则正确；EF持久化/迁移保留业务数据；API授权与一致性已验证。
- 前端状态和关键用户流程正确；单元、独立集成、关键E2E通过。
- 生产→测试引用/import为零，测试包不进入生产依赖和产物。
- 轻量application-ci在最终推送提交通过。
- 架构决策、应用实验和全栈学习材料可追溯。

环境交付/运维不属于当前DoD；教材的后续深写与视觉出版另行进行。本轮只重构责任、目录与依赖，不增加业务模块或重写工作逻辑。
