# 调查领域模型

Investigation是聚合根，持有Discovery和EvidenceLink。OwnerId、CaseId、创建时间不通过业务修改。Version初始1，每次成功领域变化加一。无向关联按ordinal端点ID规范化，不自环、不反向重复、两端必须已发现。

状态：Active→Reviewing→Submitted；Reviewing→Active可返回。只有Active允许发现、关联、修订、删除关联和笔记。复核门槛为三条发现/两条关联；提交需要三条不同已发现支持证据；Submitted只读。

关联修订保留Id/InvestigationId/SourceId/TargetId，改变Kind、Trim后的20–500 Unicode scalar解释与修订时间；无变化拒绝。旧数据的解释与时间均可为空，CHECK保护成对存在。只保留最新解释，不是完整历史事件存储。

access-log解锁badge-ledger，后者解锁dispatch。camera、maintenance、witness初始可调查。锁定标题可见，Body只有发现后投影。固定评分是教学规则，不自动判断解释真伪。

单元测试覆盖纯领域规则与状态；独立集成测试覆盖实际映射、关系约束、事务、并发、旧数据/回执兼容。领域规则与数据库约束互补，不能互相替代。
