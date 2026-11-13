# 第 4 章 一次写入穿过两层请求管道

一条 SaveNotes 端点几乎可以写在一行上，但保存远不止这一行。HTTP 中间件处理浏览器协议，端点绑定构造参数，MediatR 包装应用请求，处理器协调业务，Store 才拥有事务。必须辨认每一层包住什么，才能预测失败发生后哪些代码不会再执行。

## 4.1 先看完整执行，再拆开边界

{{figure request-pipeline}}

图中纵向箭头给出执行次序，右括线标出 Store 事务；提交成功后才沿调用栈回返。事务并不包住整个 HTTP 请求，也不包住所有 MediatR 行为。它在 Store 内开始，早于领域回调；提交完成之后还要穿过 Performance、端点结果和 JSON 写出。把“调用领域方法”画在事务开启之前，会误导读者理解回执、回滚和并发窗口。

同一请求至少有三个成功时刻：数据库提交，服务端构造成功结果，浏览器解析并接纳结果。它们有因果先后，却没有跨数据库与浏览器的共同事务。后两阶段失败时，已经提交的业务事实可能仍然存在。

## 4.2 HTTP 中间件是宿主层的委托嵌套

外围中间件先设置安全头、TraceId 与 API no-store，再 try/await next，最后记录 HTTP 状态及耗时。异常沿异步调用栈回返；尚未开始响应时，它将已知异常映射成公开 ProblemDetails。外层包装并不表示它总能重写已经发送的字节。[ASP.NET Core 中间件](https://learn.microsoft.com/en-us/aspnet/core/fundamentals/middleware/?view=aspnetcore-10.0)

{{code api-pipeline}}

UseRouting 先选出端点与元数据。Authentication 恢复 Cookie 身份，RateLimiter 随后才能按用户 Id 分区，Authorization 再检查端点要求。业务端点组统一 RequireAuthorization；没有有效会话时，请求可在这里结束，MediatR 尚未接到请求。

自定义 CSRF 中间件位于授权之后，检查 /api 下除 GET、HEAD、OPTIONS 外的请求。登录和注册虽然允许匿名，也必须通过防伪令牌对。它处理的是浏览器写入来源，不知道命令是否符合领域状态机。有效 Cookie、有效 CSRF 与可修改某份调查，必须分别判断。

静态文件和默认文件处理随后执行。开发或测试环境映射 OpenAPI；API 未匹配路径返回 API 404，而其他路径可回退 SPA。中间件注册顺序定义请求进入条件，端点注册则声明可执行目标，两者不能按源码行号混读为“启动时逐条处理请求”。

## 4.3 绑定器、端点与当前用户各有来源

{{figure binding-sources}}

{{code api-save}}

Guid id 来自路由，NotesRequest 来自 JSON，ISender 来自 DI，HttpContext 和 CancellationToken 来自宿主。绑定成功以后，端点执行 Key 与 Version，构造 SaveNotesCommand，再 await Send。这里不再把 ClaimsPrincipal 和 InvestigationService 作为端点参数；当前用户在处理器侧通过 IUser 取得。

{{code save-command}}

命令有 Id、Key、Version、Body，却没有 Owner。Id 与正文是客户端声明，IUser 是服务端建立的身份上下文，不能因为都最终成为 C# 值就把信任等级混同。Version 方法解析的是显式请求头，也不是 FluentValidation 自动绑定出来的字段。

{{code api-version}}

当前解析器接受带双引号的正整数；缺失或不合形状返回 428。它没有实现弱标签、标签列表或星号。这个有限合同与完整 HTTP 实体标签语法不能画等号。Key 则先按字符串取得，随后由命令校验器检查标准 UUID 形式。

## 4.4 严格 JSON 只证明请求形状

{{code api-json}}

必需构造参数、可空注解、严格数字与拒绝未知成员共同收紧绑定。拼错字段不能悄悄消失，null 也不能随意流入非空参数。但字符串“形式存在”不等于业务内容合法；笔记长度、调查状态和证据是否已解锁仍属于后面的规则。

Kestrel 的正文限制为 16 KiB，计量单位是字节；领域内容限制按 Unicode 标量值等业务单位计算。满足字符数不保证满足传输字节数。严格未知字段也有兼容代价：新客户端对旧服务添加字段可能被拒绝，不能把所有加字段都称为无条件兼容。

## 4.5 Send 内部还有另一条嵌套链

Logging 预处理器先执行，然后进入 UnhandledException、Authorization、Validation、Performance，最后才到 SaveNotesHandler。它们是 MediatR 请求行为，不是 ASP.NET Core 中间件。它们接收已构造的请求对象，既不重新绑定 JSON，也不负责匹配 URL。

Logging 会通过 IdentityService 读取用户名，因此校验失败之前可能已经发生身份读取。准确结论是“无效 Key 在业务事务写入之前被拒绝”，不是“所有校验都发生在任何 SQL 之前”。其预处理包装器还在 UnhandledException 外侧，日志预处理自身的失败不会被内层行为捕获，但仍可沿调用栈到达 HTTP 外围错误边界。

Authorization 检查 IRequest 类型的 Authorize 属性及当前身份；Validation 调用注册的校验器；Performance 计量其内层处理器时间。当前请求只有登录要求，没有实际声明角色或策略。各层的顺序让拒绝能够短路：Authorization 拒绝后，Validator、处理器和 Store 都不会运行。

{{code save-handler}}

处理器从 IUser 取得 owner，调用原协调服务。服务建立操作指纹和领域回调；Store 开启事务，验证 owner、回执与版本，才执行回调。领域根改变 CLR 对象，EF 比较变化并产生 SQL。只有 SaveChanges 与 Commit 成功，Store 才向上返回视图。

## 4.6 按停止点推演一条失败

假设浏览器带着版本 4 保存，但数据库已是 5。若 Cookie 无效，HTTP Authorization 先给出拒绝；若会话有效但 CSRF 缺失，防伪层先停止；若 JSON 无法绑定，命令不会构造；若 If-Match 缺失，端点抛出 428；若 Key 非 UUID，Validation 拒绝；前面全部通过，Store 才可能以 412 拒绝过期版本。

若同一 Key 的有效历史回执已经存在，则 Store 在版本比较之前返回旧结果，但资源所有权检查仍在回执之前。这种次序支持结果未知后的重试，同时防止旧回执成为访问旁路。错误并非每层各自投票，公开结果取决于实际先到达的边界。

{{code api-faults}}

已知应用错误保留稳定 code，领域拒绝映射为 422；未知异常与数据库问题只公开通用说明。UnhandledException 行为主要记录并重抛，并未代替这里的 HTTP 映射。直接调用 ISender 的测试接到的是异常，经过 HTTP 的调用者才接到状态与 ProblemDetails。

## 4.7 启动登记与每次执行是两个时刻

{{figure endpoint-lifecycle}}

{{code endpoint-discovery}}

启动时扫描实现 IEndpointGroup 的公开类型，读取静态 RoutePrefix 并调用 Map，形成 /api 端点组。命名 MapPut 辅助方法为委托加上方法名，SaveNotes 因而有稳定 operationId。请求到达时再匹配、绑定、解析 scoped 依赖并执行。反射发现不是每次请求重扫程序集，也不是绕过框架路由。

路由 guid 约束、JSON 绑定、端点内头解析与 Validator 是不同停止点。定位一个“400/404”时，应先确认是否匹配端点、是否进入委托、是否调用 Send；只在领域入口观察，会把大量未到达领域的失败误判为业务规则问题。

## 4.8 返回对象之后，响应仍在形成

{{figure problem-writer}}

历史运行曾发现响应头使用纯 TraceId，而 ProblemDetails 正文被默认 writer 写成完整 W3C 标识。当前 CustomizeProblemDetails 在最终 writer 路径统一字段。这是结果构造与结果执行分离的实例，不是数据库事务问题；本版沿用这一真实历史案例，没有再次生成同一次追踪记录。

成功路径同样如此：Respond 设置 ETag 并返回 Ok，随后 JSON 才写入网络。HTTP 外围耗时包含更广的宿主处理，Performance 行为却只围绕处理器，不包含外侧认证、校验与响应序列化。两个数字即使不同，也可能都准确。

await 把逻辑结果沿调用链传回，CancellationToken 则提出协作停止请求。取消并不撤销已经提交的事务；同一 scoped DbContext 也不能为了提速并行查询。请求管道建立进入条件，事务决定持久事实，客户端确认交付结果。只有把这三种边界分开，才能理解一次写入何时仍然未知。
