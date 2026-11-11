# 模块化单体架构

## 编译与运行边界

Domain 仅依赖 .NET 基础程序集；Application 引用 Domain，定义用例、DTO 和 IInvestigationStore；Infrastructure 引用 Application，实现 EF/PostgreSQL/Identity；API 引用 Infrastructure 并组装依赖。React 使用生成 OpenAPI 类型，同源访问 API。

运行路径：HTTP → 认证/授权/CSRF → 端点 → InvestigationService → IInvestigationStore → 领域回调与 EF → PostgreSQL。依赖图与调用方向不同。身份来自票据，不接受 JSON OwnerId。DbContext/Store/Service 为 Scoped，TimeProvider 为 Singleton。

## 写入原子性

Store 开始事务，按 OwnerId+Key 获取事务级 advisory lock，按 OwnerId+InvestigationId 加载资源，再检查原回执。命中且指纹一致时返回原快照；不一致 409。新请求比较版本，执行领域动作，保存聚合、回执和审计后提交。版本令牌参与数据库 UPDATE；审计同版本唯一冲突的特定错误也映射为 412。

没有外部副作用、outbox 或消息系统。持久化端口的回调不能发送邮件或调用外部服务，否则数据库回滚不再覆盖全部效果。

## 读取与容量边界

单案件聚合最多六条发现与十五条无向关联，采用单 SQL Include 保持语句级快照；列表限制 50。大规模数据需要投影和分页，不应直接扩大当前全部加载策略。组合索引匹配 OwnerId/UpdatedAt。合成性能实验独立于应用表，禁止将其结果描述为应用生产容量。

Phase 2A 增加了针对真实 `PostgresInvestigationStore.ListAsync` SQL 的三组执行计划对照：无所有者索引、初始的 OwnerId 单列索引、现有组合索引。数据是实际应用表中的合成数据，仍不能代表生产容量；SQL、参数、完整计划和测量限制保存在 `evidence/phase2a/database/application-query-plan.json`。

## 演化与限制

案件目录在代码中固定，目前没有不可变案件版本实体。回执没有自动清理，审计不是防篡改存储。身份采用成熟哈希与 Cookie，但账户全生命周期未完成。应用为可审阅教学实现，不能据此宣称生产就绪。

关联解释使用向后兼容的可空列扩展；旧应用回退保留向前模式。前端的请求/确认快照、草稿基线和编辑代次分别由 `useInvestigation`、`useNotesDraft` 和 `NotesEditor` 管理；历史回执不允许倒退缓存。具体权衡见 ADR 0007/0008 与 Phase 2A 场景记录。
