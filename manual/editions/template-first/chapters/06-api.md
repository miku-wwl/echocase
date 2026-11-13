# 第 6 章 从 OpenAPI 到 NSwag，再到用户的一次意图

生成客户端可以消除手写路径和 DTO 的漂移，却不能替用户决定“重试还是重新确认”。本章把五项职责拆开：OpenAPI 描述形状，生成 DTO 提供静态类型，生成方法组织 HTTP 调用，适配器补上 EchoCase 协议，Query 与组件管理用户意图和确认状态。

## 6.1 两种生成方案并不等价

历史版本使用 openapi-typescript 生成 schema.d.ts 类型声明，路径、HTTP 方法和 request<T> 由应用手写。类型声明不会发请求。当前版本使用 NSwag 14.8.0 从 OpenAPI 3.0 生成 Fetch 客户端 EchoCaseApiClient，同时生成 DTO 接口和可调用方法。旧方案在这里用于比较历史，不能继续作为当前运行路径。

{{figure nswag-two-times}}

图的上半部发生在构建与合同更新阶段：后端端点生成 OpenAPI，NSwag 将文档变成 TypeScript 源码，编译器检查调用者。下半部才是浏览器运行：React → Query → executeOperation → 生成方法 → 注入的 fetch 适配器 → 网络。NSwag 不在每个点击时重新生成代码，也不会生成当前草稿或幂等恢复状态机。

## 6.2 稳定 operationId 是跨语言名称合同

{{code endpoint-naming}}

模板辅助 MapPut 要求命名方法，并以 handler.Method.Name 设置端点名称。SaveNotes、ReviseLink 和 SubmitVerdict 由此获得稳定 operationId。HTTP URL 即使没变，随意改处理方法名也可能改变生成的 SDK 名称；反过来，只改前端方法也会在再生成时丢失。这是一项需要评审的公开合同。

frontend/nswag.json 使用 SingleClientFromOperationId、Fetch 模板、DTO Interface、日期时间 String 和 useAbortSignal。生成结果没有把 ISO 时间变成 Date 实例，也没有替业务解释时区。markOptionalProperties 为 false 与字段值可空又是不同维度：字段是否出现与字段可否为 null，不能仅看一个问号判断。[NSwag 官方生成器说明](https://github.com/RicoSuter/NSwag/wiki/TypeScriptClientGenerator)

{{code nswag-revise-signature}}

{{code nswag-verdict-signature}}

这两个签名明确区分路径目标与正文类型。编译器可以阻止把 NotesRequest 当作 VerdictRequest，却不能证明调查处于 Active，也不能证明 Version 仍然有效。生成合同把结构错误提前暴露，时间与权限仍需运行判断。

## 6.3 一条生成方法实际做什么

{{code nswag-save-method}}

按行阅读可看到路径参数编码、JSON.stringify、PUT、Accept/Content-Type、AbortSignal、this.http.fetch，以及成功处理函数。URL 和方法属于生成代码，应用没有在功能组件再拼一套相同地址。this.http 可注入 transport，正是 EchoCase 接入特殊协议的位置。

{{code nswag-save-process}}

成功处理器先读取 text，再 JSON.parse 并作 TypeScript 类型断言。类型断言在运行时不验证对象形状；空 200 正文还可能被转换为 null。它能因读取失败或畸形 JSON 抛错，却不能保证所有合法 JSON 都符合 SessionView。当前没有运行时 schema 验证器，不能把“生成客户端”写成对任意成功正文的完整验证。

这也说明生成文件应由生成器维护。手工补一项领域检查，下一次生成可能覆盖它；若要增强运行验证，应在应用拥有的明确边界设计，并同步合同和失败语义。本次教材只解释现有实现，没有改变应用。

## 6.4 适配器拥有会话与条件写入

{{code adapter-headers}}

apiCall 为每次调用建立客户端，并注入 fetch。它从生成的 method 判断是否写入，必要时取得 CSRF 令牌，添加 X-CSRF-TOKEN、Idempotency-Key 与带引号的 If-Match，携带 same-origin Cookie，并传递取消信号。生成器负责路径与正文，适配器负责应用特有的上下文。

{{code client-fetch}}

成功 Response 原样返回给生成解析器，不会在适配器中提前消费正文。非成功结果则读取 ProblemDetails，规范为 ApiError；状态、稳定 code、面向人的 detail 与 traceId 各有用途。若两个层次都 response.json，第二次读取就可能失败，形成自己制造的“正文不可读”。

生成方法不显式接收 Key 或 Version，因此 NSwag 文档本身不能代替这份时间协议。executeOperation 把 Operation 同时当作适配上下文传入，避免调用 SDK 时遗漏原意图。将来新增写方法时，必须保持这条接线，类型正确不自动意味着协议完整。

## 6.5 两个坐标，保护两种事实

{{figure intent-coordinates}}

Version 回答“我看过哪个资源版本”，Key 回答“这是哪一次尝试”。同键同指纹返回历史结果，同键异指纹为 409，新意图基于旧版本为 412。重试必须保留 Key、Version、目标与正文；改用最新版本并沿用旧键，不是恢复，而是在同一身份里改写决定。

当前 SaveNotes 会推进版本，不能因为用了 PUT 就假设重复调用天然没有副作用。服务在响应中返回 ETag，但没有实现 If-None-Match 和 304 的完整读取缓存协议，也不接受完整 If-Match 语法。标签主要用于当前聚合的条件写入，不能跨调查比较大小。

## 6.6 类型化操作连接 Query 与 SDK

{{code adapter-intent}}

Action 的 kind 区分 notes、revise-link、verdict 等语义，Operation 再附加 version、key 和可选 draftRevision。它不再让组件携带随意路径与 method。判别联合使 switch 分支与正文类型对应，但引用对象仍须被调用者当作已冻结意图使用；语言类型不代替状态所有权。

{{code adapter-dispatch}}

useInvestigation 的 mutationFn 调 executeOperation，生成方法再通过适配器发出请求。读取则将 Query 提供的 signal 送入生成的 getInvestigation。取消旧 GET 与拒绝低版本响应共同防止晚到数据覆盖新确认结果；仅调用 AbortController 并不足以证明所有旧响应都已经消失。[TanStack Query 取消机制](https://tanstack.com/query/latest/docs/framework/react/guides/query-cancellation)

## 6.7 成功状态与成功确认之间的缺口

{{figure uncertain}}

{{code client-body}}

successfulResponse 在收到成功状态后置真，随后生成解析器才读取正文。若读取或解析失败，适配器产生浏览器本地 status 0 / response_unreadable；没有成功响应的网络错误也规范为 status 0。它不是服务器返回的 HTTP 0。Query 取消会保留原错误，不当作未知写入。

未知写入时，mutation.variables 仍持有原 Operation，界面阻止新写入并允许原样重试。服务器若已提交，可返回旧回执；若资源又前进，旧回执只确认过去，不能让确认缓存倒退。当前保护针对这些本地网络与解析错误，不能推导所有 5xx 或合法但错误形状 JSON 都有同样恢复。空正文限制也必须与生成解析器的实际行为一起理解。

## 6.8 读写合同最终服务于判断

单个调查按 Id 与 owner 过滤，列表最多五十项，查询使用单语句对象图与 AsNoTracking。no-store 约束 HTTP 缓存，TanStack Query 仍管理按身份分区的应用缓存。列表没有完整游标分页，时间戳相同也没有额外 Id 次序，不能把有限总览描述成任意历史遍历。

{{figure http-outcomes}}
