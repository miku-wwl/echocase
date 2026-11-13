# 第 19 章 沿一条关联修订贯通整个系统

“允许改变关联类型，并解释为什么改变”是一项小需求，却能检验整个系统是否一致。这里的工程目标是修订同一条关系，保护别人的修改，保留失败草稿，并让重复尝试只确认同一意图。本章按这些承诺连接真实文件，而不是按目录逐个介绍技术。

## 19.1 先把变化写成可判断的句子

Active 调查中，用户选择已有关系，修改 Kind 并输入二十至五百个 Unicode 标量值的解释。关系 Id、InvestigationId 和两端保持，Rationale 与 RevisedAt 成对变化，根 Version 只前进一次。完全相同的类型和解释拒绝，不消耗新版本。Submitted 没有重新编辑路径。

{{figure evolution}}

图中每条连线对应一项必须传递的语义。它并不表示这些文件在一次迁移中都被重写：领域、Store、映射来自原有实现，命令与生成客户端接入当前模板基础。需求演进强调最终协作，而模板迁移历史另有明确来源。

删除再创建会破坏关系身份；直接更新 Links 会绕过根版本；仅改前端会失去服务器规则；只加列会遗漏旧回执。四种快捷方案都能“让页面看起来可编辑”，却没有履行同一承诺。

## 19.2 领域根先决定，再修改

{{code domain-revise}}

按行看，Editable 检查状态，合法枚举与成员查找定位真正对象，Trim 后的 EnumerateRunes 定义长度单位，类型和文本比较拒绝无意义修订。所有可预知校验都在赋值前完成，因此业务拒绝不会留下半改的 CLR 对象。

{{code link-mutate}}

内部 Revise 只改 Kind、Rationale、RevisedAt，无法替换 Guid 或端点；根随后 Advance。private setter 与 internal 方法把入口约束落到类型边界，真正不变量仍由根方法保证。纯 .NET 领域无需理解 IRequest、Cookie 或 EF，这使规则可以在无 I/O 的反例中独立推演。

## 19.3 命令带决定，处理器带身份

{{code revise-command}}

{{code revise-handler}}

ReviseLinkCommand 带 Id、Key、Version、LinkId、Body，没有 owner。Authorize 属性让直接 Send 也要求身份，Validator 验证 Key。处理器通过 IUser 取当前人，再交给协调服务。路由目标属于客户端声明，owner 属于可信上下文，两者在这里才组合为一次受保护用例。

{{code app-revise}}

操作名 revise-link 和 linkId 进入指纹对象，body 也随原版本一起参与散列；回调只描述如何修改已加载聚合。若相同 Key 被用来修订另一个 linkId，指纹就不同，不能复用回执。若为重试偷偷换最新 Version，也是在改变原意图。

这里还有一个真实兼容决定：修订要求精确枚举名称，已有创建关联入口保留原接受范围。新增需求没有顺便重写所有旧接口。若希望统一，必须单独判断旧客户端，而不是把兼容变化隐藏在内部清理中。

## 19.4 一次 Store 写入承接所有持久保证

{{code store-receipt}}

这个片段运行前，事务已开启、owner/key 锁已取得、目标已按 owner 加载。相同回执在版本比较之前重放，支持响应丢失后的原样恢复；资源过滤却更早，防止前所有者绕过当前权限。若没有回执且 expectedVersion 不等于加载值，则尚未执行领域回调就返回 412。

{{code store-save}}

apply 在此执行根行为，随后投影成功结果，将审计和序列化回执纳入同一上下文。SaveChanges 写根、子、审计和回执，Commit 才完成整体持久承诺。不存在“子对象成功、根失败也算修订”的中间合同。

如果两个不同 Key 都在版本 4 上作出决定，两个 CLR 根都可变成 5；真正仲裁依靠 SQL WHERE OriginalVersion 与审计版本唯一键。失败者的子修改、审计和回执随事务回滚。不能根据两个处理器都走完领域方法，就认为产生了两次有效修订。

## 19.5 映射与迁移保护过去的数据

{{code migration-columns}}

Rationale 和 RevisedAt 使用可空列，让旧关系保持“未记录修订”的真实意义。配对 CHECK 保护新持久形状，原 Guid、端点与类型不被迁移伪造。迁移时间不是历史修订时间，不能为了避免 null 给全部旧行补一个没有发生过的事实。

{{code app-linkview}}

LinkView 的可选默认 null 还保护旧 JSON 回执。数据库行能升级，不表示存储响应会自动出现新字段。旧回执重放仍描述当年的成功，不应补成最新调查；正常 GET 才提供当前已确认快照。表行、请求合同、响应消费者与持久 JSON，是四项需要分别考虑的兼容对象。

{{code model-root}}

Version 显式配置为并发令牌，推进数值仍由领域负责。这个配置把前面的意图前提连接到 SQL 原值条件，新增解释列没有绕过它。

EF 将原关系识别为已有实体，只修改 Kind、Rationale、RevisedAt；根修改 Version、UpdatedAt。第七章的真实历史 SQL 与跟踪观察来自相同的未变更映射和 Store，不是本次出版新造数据。它说明为什么新增解释仍在原有根并发边界之内。

## 19.6 端点将 HTTP 合同转成应用请求

{{code api-route}}

方法名 ReviseLink 经模板命名辅助方法成为 OpenAPI operationId；路由中的 id 与 linkId 约束为 Guid，body 使用 ReviseLinkRequest。端点解析 Key、If-Match，Send 完成后才设置 ETag 和 Ok。它不接收新端点、不在 HTTP 中重写领域规则，也不直接保存 DbContext。

{{code nswag-revise-signature}}

生成方法把这个 operationId 变成 reviseLink，参数区分目标与正文。OpenAPI 3.0 经过 NSwag 14.8.0 产生当前 TypeScript SDK。这个构建过程连接语言边界，运行时仍需应用适配器添加 Cookie、CSRF、Key 和 If-Match。生成器没有推导“同一次重试”的业务含义。

## 19.7 编辑器冻结的是读过的版本

{{code link-baseline}}

LinkEditor 打开时将 kind、rationale 和 version 放进 draft。后台新 GET 更新 props.version，却不自动改 draft.version。两者不同即 conflict，保存按钮禁用，用户可以复制解释、取消并核对当前关系。若自动换基线，服务器将无法知道用户从未看过中间变化。

{{code workspace-revise}}

Workspace 把冻结版本、正文、linkId 和新 Key 接入 mutation。这个回调是界面意图进入协议的连接点，而不是组件自己调用裸 fetch。新 Key 在新决定时生成，未知结果重试则使用 mutation.variables 中已经冻结的旧 Operation。

{{code adapter-dispatch}}

executeOperation 的 revise-link 分支只选择生成方法，Operation 同时送入 apiCall 的上下文，供 transport 添加原 Key 与 Version。NSwag 知道 URL，适配器知道头，Query 知道等待和确认，编辑器知道草稿基线。每一层无需重复其他层全部知识。

{{figure version-propagation}}

同一个版本沿途承担不同工作：draft.version 表示用户看过的快照，Operation.version 固定一次意图，If-Match 是协议前提，Command.Version 是应用输入，Change.ExpectedVersion 保护业务进入，EF OriginalValues 才最终进入 SQL 条件。领域 Current Version = 5 是目标值，不能替代原值 4。

## 19.8 成功响应还不能随意关闭草稿

{{code link-save}}

onSave 返回 Promise，编辑器 await 完成后才清 draft；异常被捕获并保留解释，错误由 Workspace 呈现。useInvestigation 的 onSettled 还 await 查询失效刷新，避免过早解除 pending。笔记编辑器允许等待时继续输入下一代内容，关系编辑器采用更简单的冻结表单策略；两种交互不必强行统一。

新确认数据只按不倒退版本进入 Query 缓存。旧回执能确认过去成功，却不能覆盖更高版本。网络或成功正文解析失败归为本地 status 0 时，界面保留原操作并阻止不同写入。这里仍受第六章的解析范围限制，不承诺所有错误形状 JSON 都被验证。

## 19.9 评审沿用户承诺逆向追踪

{{figure review-model}}

“修订同一条关系”对应稳定 Guid 与端点；“不会覆盖他人决定”对应根版本、原始值与事务；“失败不丢解释”对应 draft 生命周期；“网络未知可恢复”对应同键同指纹回执。每项承诺都有源码落点，也有可能推翻它的反例。

领域验证身份、标量值边界和拒绝后不变；数据库验证旧数据、真实约束、竞争和回滚；浏览器验证延迟响应、确认缓存与保留草稿。验证不是为每个文件配一个镜像测试，而是给跨层承诺建立独立观察出口。

这条路径能复用，是因为新行为仍只改变一个本地聚合。若以后要求完整修订历史、多人权限或可靠外部通知，就必须扩大模型；当前最新解释、私人 owner 和操作审计不能假装满足这些新承诺。维护性的终点是当前变化能够清楚推理，未来改变条件明确，而不是把所有相似表单抽成一套充满开关的框架。
