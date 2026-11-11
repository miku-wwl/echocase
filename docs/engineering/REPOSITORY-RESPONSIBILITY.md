# 当前仓库责任审计

按实际用途分类，而非按infrastructure、logging、Docker等单词计数。src/EchoCase.Infrastructure保留应用EF/Identity；CI的PostgreSQL服务仅供应用集成测试，不是环境发布。范围变更见ADR0009。

| 分类 | 当前内容 |
|---|---|
| 业务应用 | src四层、frontend应用/构建配置、模型/迁移/身份/一致性；生产源码保持基线行为 |
| 应用测试 | unit、integration、独立e2e；可选真实Store QueryProbe也只在测试区 |
| 应用文档 | 需求/领域/架构/API、开发/测试/应用实验与验收 |
| 全栈教材 | 应用Markdown源与新2B索引，没有活动PDF或旧出版器 |
| 轻量CI | 仅application-ci；编译、测试、合同、依赖/产物检查 |
| 历史引用 | HISTORY、ADR历史说明及指向63c5872的源/证据链接；不执行旧脚本 |
| 不需要的运维内容 | 当前Git树为0；旧脚本/工作流/证据/出版物已退役 |

详细[退役/迁移路径](RETIRED-FILES.md)按Git差异生成。Git忽略的work、bin/obj、node_modules与测试产物不属于活动源；没有为清理源码而破坏原业务数据库或用户文件。

边界检查不是仅看目录：实际MSBuild编译/引用项、解析NuGet库、前端imports、publish DLL/deps.json和bundle来源均执行检查。受控负例也确认了拒绝路径。应用请求日志/TraceId保留用于调试，没有集中监控或故障演练职责。
