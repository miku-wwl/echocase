# 调查领域模型

Investigation 是聚合根，持有 Discovery 和 EvidenceLink。OwnerId、CaseId、创建时间不通过业务修改。Version 初始 1，每次成功领域变化递增。关联类型 Corroborates/Contradicts 均无向，按 ordinal ID 顺序规范化，图上不画方向箭头。

状态：Active → Reviewing → Submitted；Reviewing → Active 可返回。Active 允许发现、关联、删除关联与笔记；Reviewing 冻结编辑，提交要求三条不同已发现支持证据；Submitted 永久只读。

证据链：access-log 解锁 badge-ledger，后者解锁 dispatch。camera、maintenance、witness 初始可调查。Body 仅在已发现时投影。当前锁定标题可见，这是产品选择。提交固定评分为教学规则，不代表现实判断。

领域不变量由 NUnit 验证；数据库额外保护版本、状态、关联外键与唯一性。两者互补。SQL 实验中的 on_call 表仅演示跨行写偏斜，不是新增业务模块。
