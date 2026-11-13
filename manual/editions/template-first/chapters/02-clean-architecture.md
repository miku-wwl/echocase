# 第 2 章 官方模板如何成为应用的真实基础

四个项目名称不能证明 Clean Architecture，更不能证明项目来自某个模板。前者需要检查依赖方向和职责，后者需要生成来源及实际迁移。EchoCase 的新版同时回答这两个问题：模板负责建立可复用的请求与集成骨架，业务代码保留自己的身份、事务和失败语义。

## 2.1 从自行实现到真实模板迁移

{{figure template-lineage}}

历史应用先实现了调查聚合、存储端口、Cookie、EF 和 React。随后发现它偏离“基于 Jason Taylor 官方模板”的要求。补救过程实际生成了 v10.8.0 解决方案，保存 171 个生成文件的来源与散列，形成独立 bootstrap 提交，再把既有业务迁入该基础。它不是给旧目录换名字，也不是读了上游代码后声称受到启发。

官方上游固定为 `e5c08ecead8a52f6cf519477bf6c57668248c035`，生成提交为 `f1df1a3c3b95bae184600a0ccef629eccaa18080`。独立样例验证暴露过登录界面等待超时；样例依赖审计也曾要求显式区分告警与错误。这些局限没有被写成“所有原始样例均通过”，也没有通过削弱当前应用断言来掩盖。最终业务接受基线是 `9f68721`，两项验证回答的是不同问题。[固定官方来源](https://github.com/jasontaylordev/CleanArchitecture/tree/e5c08ecead8a52f6cf519477bf6c57668248c035)

生成阶段是历史事实；最终运行图才是当前设计。官方 `src/Domain`、`Application`、`Infrastructure`、`Web` 的职责被迁入 `backend/EchoCase.*`，独立 React 位于 `frontend/`，各级验证位于 `test/`，教材位于 `manual/`。这满足仓库布局约束，却不改变内部依赖原则。

## 2.2 编译箭头与运行箭头要分别读

{{figure architecture}}

实际项目引用是 API → Infrastructure → Application → Domain。API 因传递引用能够使用 Application 类型；不能把运行调用画成额外的直接 ProjectReference。Domain 不引用 EF、HTTP 或 MediatR，Application 引用 Domain 并拥有存储与身份端口，Infrastructure 实现它们。API 作为组合根选择实现，同时负责协议。

运行时则是端点 → ISender → 行为与处理器 → InvestigationService → IInvestigationStore。Store 开启事务、加载聚合，再调用应用提供的领域回调。运行调用走向数据库，编译依赖却不要求 Application 引用具体 Store。依赖倒置改变接口由谁拥有，不会把所有实际执行箭头倒过来。

{{code app-port}}

端口没有泄露 DbSet 或 IQueryable，因此 Application 不能随意改变 Include、隔离或跟踪策略。代价是新增复杂查询可能要扩展端口，回调也只适合当前进程内的工作单元。接口不是“数据库可以随意替换”的证明：替代实现仍须履行所有权、回执、根版本和原子提交的同一承诺。

## 2.3 保留、适配与移除分别意味着什么

{{figure template-tradeoffs}}

保留的模板机制包括扩展式 DI 注册、MediatR 程序集扫描、请求预处理与行为链、FluentValidation、IUser/CurrentUser/IdentityService，以及端点组发现。它们都进入当前执行路径，不是留作示范的空文件。生成的命名端点辅助方法还成为稳定 OpenAPI operationId 的来源。

适配首先发生在业务持久化端口。模板样例通过应用 DbContext 接口操作 Todo；EchoCase 继续让 IInvestigationStore 承担一次调查的本地事务。原有 Guid 聚合、私有集合、三条迁移和 owner/key 回执协议已经有共同语义。机械替换为样例 BaseEntity、整型标识或通用保存拦截器，会改变这些语义，却未必带来收益。

审计也保留在原事务内：一次根版本对应一项操作审计，并与结果回执一同保存。没有采用模板样例的通用创建者/修改者拦截器和领域事件调度。两者不能仅凭名称视为同一种审计。模板事件钩子还不等于可靠外部交付；保存之前发出邮件，后续回滚不能收回邮件。当前应用没有外部通知，不需要把本地一致性扩展成消息架构。

移除的可选内容包括 Aspire 编排、Todo/Weather 样例、样例 UI 和部署脚手架。它们不属于当前应用范围。官方生成样例中的开发初始化器也没有进入活动应用：它可删除并重建样例数据库，不能拿来管理需要保留的调查历史。实际初始化使用既有迁移链。移除可选样例与否认真实模板生成，是完全不同的历史陈述。

## 2.4 注册如何变成一次真实分派

先看生成基线中的注册片段。它固定于 f1df1a3，属于历史模板比较；下一段才是当前应用。行为类型和扫描骨架保留，命名空间、业务服务与部分行为实现已经适配，不能从注册形状相同推导内部行为完全未变。

{{code bootstrap-registration}}

{{code app-registration}}

RegisterServicesFromAssembly 扫描 Application 程序集中的 IRequestHandler 实现，AddValidatorsFromAssembly 找到具体校验器；后续 Send 根据请求与返回类型解析处理器。注册是启动配置，处理器执行是请求时行为。一个 record 实现 IRequest 并不会自动执行，更不自动建立事务。

Logging 注册为 request preprocessor，其余四项按 UnhandledException、Authorization、Validation、Performance 加入开放泛型行为。MediatR 的预处理包装器位于这些行为外侧，不能只看列表就把 Logging 当作最内层日志。第五章会把这条嵌套调用展开。[MediatR 14.3.0 注册实现](https://github.com/LuckyPennySoftware/MediatR/blob/v14.3.0/src/MediatR/Registration/ServiceRegistrar.cs)

{{figure di-scope}}

处理器由 MediatR 默认按 transient 解析，InvestigationService、IUser、Store 与 DbContext 则显式 scoped。临时处理器依赖 scoped 服务完全可以：它们在同一请求作用域中取得同一组资源。Transient 不意味着每次都会创建新的 DbContext；真正决定上下文身份的是 DbContext 注册与解析作用域。

TimeProvider 是单例，因为它不保存某次请求的跟踪实体。DbContext 不能因此也改成单例：两个请求将可能共享实体身份与原始值，而且同一上下文不支持并行数据库操作。await 保持逻辑调用顺序，不会自动提供线程安全或业务原子性。

## 2.5 当前用户是一项端口能力

IUser 由 Application 定义，CurrentUser 在 API 中用 IHttpContextAccessor 读取 NameIdentifier，IdentityService 在 Infrastructure 中使用 UserManager 和授权服务。应用因此可以要求“需要当前用户”，而不直接引用 HttpContext。新请求没有 OwnerId 正文字段，处理器从本次作用域取得身份。

身份端口并不凭空创造后台用户。直接从根容器启动一个 Send，若没有有效当前身份，受保护请求仍会失败。将来增加后台作业，需要显式设计身份来源和权限，不能伪造一个 HttpContext 便假装沿用了相同信任边界。

## 2.6 为什么保留应用协调服务

模板处理器与原 InvestigationService 并存，并非两套互相竞争的分派器。前者命名请求、接入通用行为和取得用户；后者建立时间、操作指纹与领域回调。存储仍只由一个 Store 负责。这样能把迁移限制在必要边界，避免同时重写已经接受的并发与幂等语义。

这种安排有维护成本：读一条请求要跨处理器与服务，简单处理器看起来像转发。若日后各个用例显著分化，可以重新评估把协调移入处理器；若只是为了消除一行转发而复制八套指纹与事务前提，系统反而更难理解。判断依据应是共同变化的职责，而不是每一层必须写多少代码。

## 2.7 测试约定也需要适配范围

官方模板提供分层测试组织和请求处理习惯，EchoCase 将自己的领域、PostgreSQL/API 与浏览器验证保留在独立 test。生产解决方案不引用测试项目，测试可以引用生产。包的传递图与实际产物还须独立检查，文件夹名字本身不会阻止测试依赖泄漏。

架构是否有效，最后看需求能否沿已有保证演进。关联修订增加真实命令、根行为、可空列、生成客户端方法和编辑器，却没有使 Domain 理解 Cookie，也没有使 Application 编译依赖 EF。这些可解释的变化，是模板成为应用基础之后仍然需要作出的工程判断。
