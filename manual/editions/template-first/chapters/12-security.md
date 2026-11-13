# 第 12 章 登录、用例授权与资源所有权

“已登录”只说明当前请求有身份，并不说明他可以读取某份私人调查，更不说明可以重放曾经属于自己的旧回执。模板增加了一层用例授权，但原有数据库资源过滤仍不可少。本章沿着同一身份进入 HTTP、MediatR 与事务的过程，解释各项保护为什么必须同时成立。

## 12.1 Identity 保存账户，Cookie 恢复会话

Identity 的 UserManager 处理账户、密码和失败次数；登录端点检查后，手工构造 NameIdentifier 与 Name，并用 EchoCase scheme 签入。后续请求用 Cookie 恢复 principal，不需要再传密码。邮箱用于展示，稳定用户 Id 用于资源隔离。

{{code api-login}}

{{code api-cookie}}

HttpOnly 限制脚本直接读会话 Cookie，SameSite Strict 收紧跨站携带，非开发与非测试环境要求 Secure。两小时有效期不滑动延长。API 将未登录与无权限重定向分别变成 401、403，避免生成客户端收到一个 HTML 登录页却当成 JSON。

AddIdentityCore、AddRoles、EF stores 与 SignInManager 是注册能力，不意味着每项默认身份流程都已经使用。当前手工 principal 不自动获得完整安全戳持续验证、全设备撤销、MFA、确认邮箱或密码重置。样例管理员 seed 没有进入活动应用。不能因为存在 IdentityService 类型就把这些可选能力写成产品功能。

## 12.2 IUser 让处理器取得可信上下文

{{code current-user}}

CurrentUser 读取当前 HttpContext 的 NameIdentifier，Application 只依赖 IUser。它不从 JSON 或路由读取 Owner，也不会因为客户端发送了一个同名字段就信任它。没有当前身份时 Required 抛出异常；后台调用者也必须面对这项前提。

{{code api-owner}}

这里的保护有两层：AuthorizationBehaviour 在进入受保护用例前要求 IUser.Id，处理器在取 owner 时仍要求非空。外层 HTTP RequireAuthorization 保护 HTTP 入口，内层行为保护 Send 入口。直接 ISender 的匿名测试因此会失败，即使没有经过路由和 Cookie 中间件。

## 12.3 通用授权没有调查 Id 的业务答案

{{figure security-boundaries}}

当前 Authorize 属性没有角色或策略内容，仅要求身份。模板保留 Roles 和 Policy 分支，IdentityService 也能用 UserManager、claims factory 和 IAuthorizationService 检查策略；当前业务却没有管理员或团队调查。能力存在与授权规则已被调用，需要分别描述。

{{code identity-policy}}

即使未来某角色可以使用“修订”用例，也还需要判断目标调查属于谁。Store 的 Graph 同时筛选 Id 与 OwnerId，Get、List、Write 都遵循身份范围。404 合并不存在与不可见，避免轻易披露资源是否存在。Guid 难猜、按钮隐藏和先前页面检查都不能代替这次查询。

## 12.4 回执必须留在当前资源边界之后

{{figure owner-replay}}

{{code store-lock}}

对已有调查的修改，事务开始后先取得 owner/key 的事务锁，再按当前 owner 加载目标。若找不到，立即 404，尚未查历史回执。随后才比较回执指纹并考虑重放。这意味着回执回答的是一个仍有权访问资源的调用者提出的问题，不能单凭“过去做过这件事”开放旧响应。

实际回归构造了一个反例：Alice 成功保存并持有 Key，测试夹具用 SQL 将资源归到 Bob，Alice 再用原 Key 与正文重放。她仍是有效登录用户，回执也仍存在，但响应必须为 404；Bob 能读到成功笔记，版本只前进一次。**转移仅是测试夹具操作，应用没有生产所有权转移 API。**

{{code former-owner-test}}

若把回执查询挪到所有权检查之前，通用 Authorization 仍会通过，却会把旧 SessionView 交回 Alice。这是横切行为无法替代资源授权的具体原因。测试只证明当前检查次序，没有证明对任意未来并发转移协议都安全；将来实现共享或转移，仍需定义权限变更与在途事务怎样仲裁。

PostgreSQL 的 WHERE 过滤发生在 Store 事务中，但当前没有数据库 RLS。使用高权限直接 SQL 仍可绕过应用路径，不能把“事务内资源过滤”误称为数据库对任意访问者的独立行级授权。所有业务入口必须遵守同一存储协议。

## 12.5 Cookie 自动携带，所以还要 CSRF

有效 Cookie 只能证明浏览器拥有会话，不能证明用户在本应用中发起这次写入。适配器先获取 CSRF 请求令牌，写入时用 X-CSRF-TOKEN 与对应防伪 Cookie 配对。登录、注册也经过校验，登出后的客户端重新取令牌，身份切换不沿用旧交互上下文。[ASP.NET Core 防伪机制](https://learn.microsoft.com/en-us/aspnet/core/security/anti-request-forgery?view=aspnetcore-10.0)

SameSite 与 CSRF 缩小不同攻击面，不能相互替代。若攻击者能在同源运行任意脚本，往往能取得请求令牌并利用现有会话；HttpOnly 也不阻止恶意脚本代用户发请求。XSS 因而还需要输出、内容与脚本来源边界。

## 12.6 不发送的数据，不依赖浏览器保密

{{figure ui-evidence}}

SessionPresenter 只在证据已调查后发送 Body，锁定证据摘要也被替换。真实历史界面中的锁只是解释，真正保护发生在服务器投影。把全部正文先发给页面再用 CSS 隐藏，没有同等意义。

React 把普通笔记与解释作为文本输出，没有任意 HTML 注入。若将来支持富文本，必须重新定义允许标记、清理和渲染。no-store 约束 HTTP 缓存；Query 缓存按 owner/id 分区，登录和登出清理非 me 查询。服务端隔离与浏览器账户切换清理分别防守资源和呈现边界。

## 12.7 安全配置只在其实际范围内成立

CSP 限制文档脚本、连接和嵌入；style-src 仍允许 unsafe-inline 以兼容样式和图谱，不能称作禁止全部内联内容。生产静态页面由 API 宿主提供时才受该页面 CSP 约束；开发 Vite 页面不会因某个 JSON 响应带 CSP 而自动拥有同样策略。

认证限流按远端 IP 每分钟十五次，写入按用户 Id 每分钟一百二十次。它们是进程内固定窗口，不能保证多实例全局平滑配额。代理后的真实客户端地址也取决于可信转发配置。密码失败锁定、限流与稳定错误文案分别约束成本、速度与信息暴露，不能用一句“已接安全组件”概括。
