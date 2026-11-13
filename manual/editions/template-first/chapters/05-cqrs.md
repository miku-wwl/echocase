# 第 5 章 MediatR、逻辑 CQRS 与提交之后的风险

CQRS 先区分语义，再选择分派方式。查询表示“想知道什么”，命令表示“准备作出什么决定”。EchoCase 通过不同请求和处理器表达它们，但仍共用一个 PostgreSQL 数据库，查询和成功命令都可返回 SessionView。这里没有独立投影，也没有从事件重建状态；MediatR 更不是消息队列。

## 5.1 三个接口把一次调用接起来

IRequest<TResponse> 声明请求的返回合同，IRequestHandler<TRequest,TResponse> 实现处理，ISender.Send 将两者在进程内连接。GetInvestigationQuery 描述读取，SaveNotesCommand 描述带版本与幂等身份的写入。命令采用 record 便于清楚表达值，但并不自动保证请求正文深度不可变，也不自动持久化。

{{code query-handler}}

查询处理器从 IUser 取得 owner，再调用 service.Get；查询同样需要身份与资源过滤。命令处理器也使用相同身份端口，只是调用另一个用例。与直接调用服务相比，Send 增加了一层可共享的授权、校验与诊断路径，也增加扫描、泛型注册和跨文件导航的理解成本。它适合稳定横切规则，不应被当成无需推理的魔法入口。

处理器由启动时的程序集扫描注册。请求对象的类型决定解析哪一个 IRequestHandler，而不是由字符串方法名决定。漏掉扫描程序集、请求与返回类型不匹配，都会使分派无法形成预期路径；这些错误不会由“采用了 Clean Architecture”自动避免。

## 5.2 行为列表真正形成嵌套调用

{{figure mediator-onion}}

图中向内是 next，向外是 await 后续代码。MediatR 14.3.0 将行为反向聚合为委托，最先注册的行为位于外侧。Logging 的注册形式不同：它是 IRequestPreProcessor，由框架的 RequestPreProcessorBehavior 先运行，再进入显式行为。因此不能把 LoggingBehaviour 的文件名误读为同一列表中的普通 IPipelineBehavior。[实际包装实现](https://github.com/LuckyPennySoftware/MediatR/blob/v14.3.0/src/MediatR/Wrappers/RequestHandlerWrapper.cs)

{{code logging-name}}

用户名解析发生在处理器之前，可能读取 Identity 数据。若这里失败，内侧 UnhandledException 尚未进入；HTTP 外围边界仍能处理异常。UnhandledException 本身记录并重抛，不会把任何错误自动变成成功 DTO，也不负责生成 ProblemDetails。

Authorization 随后检查请求类型的 Authorize 属性。当前查询和命令都要求身份；角色和策略分支是可用机制，当前业务没有声明具体角色或策略。资源是否属于当前人仍然未知，必须等 Store 按 Id 和 OwnerId 加载。

{{code authorization-identity}}

“能够调用这个用例”与“能够修改这一份调查”是两个判断。若以后新增入口直接调用 ISender，第一项检查仍存在；若直接绕过 Send 调用服务，它不再经过行为链。架构保证总有具体入口范围，不能从一种调用路径推断所有可能调用都被拦截。

## 5.3 FluentValidation 应验证什么

{{code write-validator}}

八个具体写命令校验器继承共同 Key 规则。ValidationBehaviour 收集 IValidator<TRequest>，调用 ValidateAsync，汇总失败后抛出应用 ValidationException。当前规则不查询数据库，也不推进聚合版本。它把直接 Send 的语法边界补齐，HTTP 层随后可将 Key 错误映射为稳定 400。

{{figure validation}}

版本头形状属于端点，Key 形状属于命令合同，Active 才能修改属于领域，唯一性和并发竞争属于数据库。领域规则不能仅搬到 Validator：校验发生时尚未拥有事务内加载的当前聚合，先查一次再保存仍可能过期。客户端提前提示也只是交互帮助。

模板行为用 Task.WhenAll 执行多个校验器。当前纯语法规则没有共享上下文问题；未来若把同一 scoped DbContext 注入多个异步校验器，就不能据此假设可以并行查询。通用行为的实现方式会限制扩展方式。准确了解扫描与执行，比笼统说“加一个 Validator 就行”更重要。

## 5.4 处理器与协调服务分工

{{figure usecase}}

{{code app-revise}}

ReviseLinkHandler 负责取得可信 owner 并调用这里的用例。服务将操作名、linkId 与正文纳入指纹，构造领域回调；Store 完成加载、回执和版本检查后，在已经开启的事务内执行回调。应用端口接收的是行为，不是已经修改好的脱离对象。

这里的枚举转换还保留一项合同差异：修订 PUT 要求精确枚举名称，防止 Enum.TryParse 接受数值字符串；历史建联 POST 仍保留较宽的旧接受范围。维护中的一致风格不能凌驾于已公开兼容。若要统一，应把收紧旧合同作为明确变化。

{{code app-fingerprint}}

指纹由 id、version、operation、body 的应用序列化结果计算 SHA-256，不是任意 HTTP 原始字节的散列。空格与头顺序不直接决定它，但原版本和目标关系会。Key 保留收到的字符串形式，没有统一 UUID 大小写。原样重试保持同一表示；不能声称所有文字形式的同一 UUID 都自动折叠。

## 5.5 时间、返回视图与事务所有权

服务通过 TimeProvider 取得 UTC 时间，并裁到 PostgreSQL 可保存的微秒精度。它把同一 now 传给领域，Store 再让业务、审计与回执共同提交。当前没有外部副作用，因此这一事务边界能够覆盖承诺；未来若增加可靠通知，需要另行设计交付，不能悄悄塞进领域回调。

成功命令返回完整 SessionView，让前端立即得到新版本、证据与关系，再按版本单调规则合并。返回视图不意味着查询与写入采用同一职责。它只是当前小聚合的便利选择，规模增长后可重新评估投影成本。CQRS 不要求为了名称对称而建立两套数据库。

## 5.6 为什么提交之后仍可能表现为失败

{{figure performance-after-commit}}

官方生成的原 PerformanceBehaviour 在 next 返回后，若耗时超过阈值，会通过 IdentityService 再查询用户名。假设处理器已提交业务，第二次身份查询却失败，异常仍能沿调用栈返回端点，使调用者看到失败。数据库已保存与 HTTP 失败同时成立，用户若换新键再试，就可能执行第二次意图。

{{code bootstrap-performance}}

这是对历史模板源码的失败路径分析，并非本书重新运行原实现得到的负例记录。它揭示一个普遍判断：事务提交后增加辅助 I/O，会扩大“业务成功、交付失败”的窗口。诊断逻辑也属于业务结果返回路径，不能只因名叫日志便视为无风险。

{{code performance-return}}

当前适配移除提交后的身份查询，慢请求日志只使用已在作用域内的 UserId。计时围绕处理器，超过 500 ms 才进入该分支；它不含外侧 Logging、授权、校验及最终 JSON 序列化。修正减少了一项可避免失败，不保证所有日志提供者绝不抛错，也没有消除网络响应丢失。

{{code slow-store-test}}

这个测试包装器先 await 真实 Store，待事务提交后再延迟 600 ms，使 Performance 必然进入慢路径。另一个身份替身允许第一次用户名查询，第二次直接抛错；第一次由预处理 Logging 使用。测试以真实 API 创建调查，断言成功、身份调用只有一次，数据库回执与审计各一项。

这项回归说明修正后的路径不会为了慢日志再访问身份库。它没有证明任意部署中的全部辅助组件都不会失败。工程教训是把成功承诺与可选诊断成本分开，并继续用幂等回执恢复不可消除的交付不确定性。

## 5.7 抽象何时值得保留

通用行为集中稳定规则，领域根集中业务不变量，协调服务复用意图协议，Store 集中本地原子提交。它们减少的是相同承诺的重复。若一个新用例需要跨聚合、跨资源或外部交付，原有 Write 并不能凭签名相似就胜任。

评审时可以沿失败倒推：谁先拒绝，拒绝前做过哪些 I/O，谁拥有提交权，提交之后还有什么能抛错。能回答这些问题，MediatR 才是在帮助理解；若只会说“请求经过几个 Behavior”，分派层反而隐藏了系统最重要的时序。
