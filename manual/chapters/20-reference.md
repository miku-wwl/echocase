# 附录 B 参考来源与工程词汇 {#references}

## 一手技术来源

以下来源用于核对框架机制，项目实验则是这些机制在当前配置下的执行证据。在线文档会更新，复现时应同时参考锁文件与本地代码。

| 主题 | 官方或上游来源 | 阅读目的 |
|---|---|---|
| Clean Architecture | [Jason Taylor 源码](https://github.com/jasontaylordev/CleanArchitecture) | DI、请求行为、Identity、事件时机 |
| Cookie API 行为 | [ASP.NET Core 10 API 认证](https://learn.microsoft.com/en-us/aspnet/core/security/authentication/api-endpoint-auth?view=aspnetcore-10.0) | 401/403 与重定向的边界 |
| CSRF | [ASP.NET 防伪文档](https://learn.microsoft.com/en-us/aspnet/core/security/anti-request-forgery?view=aspnetcore-10.0) | Cookie 请求的独立保护 |
| 乐观并发 | [EF Core 并发](https://learn.microsoft.com/en-us/ef/core/saving/concurrency) | 原值条件、影响行数与异常 |
| 值生成 | [EF Core 值生成](https://learn.microsoft.com/en-us/ef/core/modeling/generated-properties) | 手动 Guid 与生成约定 |
| PostgreSQL 主键 | [Npgsql 值生成](https://www.npgsql.org/efcore/modeling/generated-properties.html) | Provider 的默认行为 |
| 事务隔离 | [PostgreSQL 17 文档](https://www.postgresql.org/docs/17/transaction-iso.html) | 语句快照、事务快照与序列化失败 |
| 乐观界面 | [TanStack Query 乐观更新](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates) | 取消、快照、回滚与重新读取 |
| Mutation | [TanStack Mutation](https://tanstack.com/query/latest/docs/framework/react/guides/mutations) | 写入生命周期与重试 |
| 图谱性能 | [React Flow 性能](https://reactflow.dev/learn/advanced-use/performance) | 节点规模增长时的测量与优化 |
| 组件来源 | [shadcn/ui](https://github.com/shadcn-ui/ui) | 可拥有的组件与 MIT 许可证 |


## 关键术语

| 术语 | 在 EchoCase 中的精确定义 |
|---|---|
| Aggregate Root | 调查的一致性入口，控制发现、关联、笔记与结论 |
| Invariant | 每次合法业务动作完成后必须仍成立的约束 |
| CQRS | 命令与查询职责分离；本项目共用单库 |
| Optimistic Concurrency | 用原版本作为数据库更新条件，拒绝过期意图 |
| Idempotency Key | 标识一次可重试的用户意图，作用域为账户 |
| Receipt | 与业务同事务保存的原操作响应快照 |
| MVCC Snapshot | 数据库语句或事务所观察的一致可见版本 |
| Write Skew | 各自更新不同行仍破坏跨行约束的并发异常 |
| Server State | 由服务端权威保存、客户端缓存的调查状态 |
| Dirty Draft | 用户已编辑但尚未成功提交的本地内容 |
| Readiness | 当前依赖条件下是否可处理需要数据库的工作 |
| Reproducibility | 按公开条件执行并获得可比较结果，不承诺字节相同 |
| Evidence Integrity | 文件、结构化结果与有限测量来源的一致性检查 |

## 复现结果不一致时

先记录版本、命令、退出码与原始输出，再确认输入数据、环境变量、数据库迁移、Cookie 身份与端口。性能差异先检查负载和暖机条件，业务差异先检查预期版本与案件规则。不要为了得到书中数字而改写原始样本，也不要把不同环境的一次失败直接归类为代码问题或环境问题。

实验的价值在于解释变化。若复现揭示新的失败，应新增证据、降低相关状态、修正实现或文字，再重复相同检查。教材与应用共同演化，才能保持技术解释和运行事实一致。
