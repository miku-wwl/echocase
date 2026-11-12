# 第 13 章 React 渲染快照与状态所有者

后端已经有明确的状态机，前端仍可能丢数据。原因是浏览器同时处理服务器事实、网络中的操作、用户输入和局部交互。把它们都叫 state，只解决了语法命名，没有解决谁能覆盖谁。React 的渲染模型为这些变化提供执行基础，业务仍要定义各类状态的含义。

## 13.1 事件回调看到哪一次渲染

React 调用组件函数，依据当前 props 和 state 计算 JSX，再把必要变化提交到 DOM。事件回调与局部变量属于那次渲染的快照。调用 setter 会安排下一次计算，不会把已经执行中的闭包变量改造成未来值。[渲染与提交](https://react.dev/learn/render-and-commit)、[状态快照](https://react.dev/learn/state-as-a-snapshot)

{{figure react-render}}

若保存按钮回调捕获文本 A，发出请求后用户输入 A+B，晚到回调仍然对应发送 A 的那次操作。它不应因为组件此时显示 A+B，就把 A+B 当成已经提交的正文。反过来，也不该把输入框强行恢复成响应中的 A。网络操作需要保存明确的意图快照，不能依赖“执行回调时随便读取哪个变量”。

函数式 setDraft(d => ...) 接收更新队列中的前一个状态，适合在异步确认时比较当前代次。它解决的是读取最新本地前值的问题，不自动知道这份前值是否对应原操作。操作中仍需携带 draftRevision，业务比较才能成立。[更新队列](https://react.dev/learn/queueing-a-series-of-state-updates)

## 13.2 Render 与 Effect 的职责边界

渲染应该计算界面，不在组件函数体中直接发起写入。用户按下保存属于事件；浏览器地址变化监听与服务器快照到本地状态的同步属于 Effect 的使用范围。把请求藏进“某字段变了就保存”的 Effect，容易让初始化、重渲染或后台刷新意外产生新命令。[Effect 同步](https://react.dev/learn/synchronizing-with-effects)

EchoCase 在事件中构造 Operation，交给 mutation；草稿钩子的 Effect 只处理快照到达与已知成功确认。两个 Effect 的前提不同：服务器新快照能更新干净草稿，却不能覆盖脏草稿；保存确认还需检查对应代次。Effect 并不天然比事件更“响应式”，关键是变化由哪个原因触发。

{{code react-root}}

QueryClient 在组件外创建，避免每次渲染都新建缓存容器。应用启用 StrictMode，开发时会增加渲染与 Effect 检查，帮助暴露不纯计算和缺少清理的问题；它不表示生产环境每次用户点击都必然执行两次写入。[StrictMode](https://react.dev/reference/react/StrictMode)

## 13.3 状态按所有权分开

{{figure state-owners}}

Query 缓存只保存服务器确认的 Session。Operation 保存本次发送的 route、method、body、version、key 和可选草稿代次。useNotesDraft 保存 text、baseline、version、revision、dirty 与 saved。tab、selected、图节点坐标则只表达当前交互。它们可以出现在同一屏，但更新权限不同。

例如 pending 的保存内容可作为“正在保存此快照”提示，却不进入确认缓存。用户继续输入会改变 draft.text，不会改变 operation.body。后台 refetch 更新 Query，若草稿已脏，不能因此改写 baseline。把这些值分开后，一句“保存成功”才能精确指向其中一个操作，而不是含混地宣布整个页面都已同步。

这种分离也让错误恢复更简单。服务器错误不要求“回滚所有 React state”，因为确认缓存从未写入未经确认的文本；只需保留草稿并展示错误。局部乐观呈现仍然存在，但它明确标注为 pending，不冒充持久事实。

## 13.4 组件身份决定状态保留多久

{{figure component-boundaries}}

{{code react-workspace}}

App 用调查 Id 作为 Workspace 的 key。切换调查时，React 将它视为不同组件身份，本地草稿和图坐标不会串到另一份档案。相同调查内部切换页签，NotesEditor 保持挂载，只使用 hidden 改变可见性，草稿因此继续存在。[状态保留与重置](https://react.dev/learn/preserving-and-resetting-state)

这是有范围的保留：返回总览使工作台卸载，刷新页面也会重建本地状态。当前实现没有浏览器持久草稿或离开确认。不能把“切换页签不丢输入”扩大成“任何导航与重启都能恢复”。状态生命周期应与产品提示一致。

App 负责身份和导航，Workspace 负责本次调查装配，钩子负责请求与草稿，编辑器负责字段交互。拆分的收益在于不同变化原因被放到不同所有者中，而不是让所有文件行数一样。前端曾把请求、草稿、图谱和页面结构混在一个大组件里；需要修复的正是这些状态之间隐含的覆盖关系。

## 13.5 TypeScript 辅助哪些判断

Session 和 ReviseLinkRequest 来自生成合同，Operation 则是前端自己拥有的意图类型。两者分开，使 API 字段变化和本地操作生命周期可以分别检查。可选 draftRevision 说明并非所有命令都与笔记代次有关；成功处理必须先判断 route，不能把任意业务成功当成笔记已保存。

unknown 出现在网络和泛型缓存边界，具体使用处再缩小为 Session。当前实现主要依赖生成合同和服务端行为，没有完整运行时 schema 验证。因此类型系统能约束前端源码，却不能对任意失真的成功 JSON 提供证明。第十一章的正文不可读保护只覆盖解析失败，合法 JSON 但字段错误还需要其他策略。

## 13.6 组件库不是业务状态机

{{code button-contract}}

Button 组合 Base UI 行为、变体样式和原始 props，让 disabled、可访问属性与事件继续由使用者传入。它没有决定“何时允许修订”。NotesEditor 和 LinkEditor 依据业务状态、冲突、长度与 blocked 计算 disabled，再把结果交给控件。

统一视觉样式可以降低重复，也可能掩盖实际组件后端。本实现使用 Base UI 版本的按钮原语，不能因为目录叫 shadcn/ui 就假定内部一定是另一套组件库。阅读真实依赖和组件封装，才能解释焦点、禁用和属性透传如何发生。

React 19 提供许多可选机制，本应用没有为展示版本号而引入所有新 API。这里的核心难点是异步事实与用户意图的分离，基础 Hook 配合明确协议已能表达。下面把组件身份与更新队列接回实际代码，再进入 Query 生命周期。

## 13.7 状态属于树中的位置，不属于函数局部变量

组件每次调用都会创建新的局部变量，React 仍能保留输入，是因为它将 Hook 状态关联到组件在树中的身份和 Hook 调用顺序。函数不是一个一直挂在栈上的窗口对象；下一次渲染会重新执行函数，再取回相应状态。

这解释了两个实际选择。useNotesDraft 总在 NotesEditor 的固定调用位置运行，不能按某个临时 tab 条件决定是否调用 Hook；Workspace 的 key 随调查 Id 改变，表示应该建立另一组状态。把 key 随每次服务器 version 改变则会把每次刷新变成卸载重建，草稿也会随之丢失。

渲染过程中不应该修改已有 state 对象。setDraft 返回新对象，让 React 和使用方能够把变化识别为新状态；旧操作快照也不会因为共享可变引用被悄悄改写。当前 Operation 的 body 在构造时来自文本值，后续输入不会变动这个字符串快照。

## 13.8 为什么函数式更新仍需业务条件

setDraft(d => ...) 只保证更新函数获得队列中的适当前值。它不会推断 current Session 属于哪个请求，也不会自动知道某个 success 是否已被处理。代码因此同时使用操作 key、draftRevision 和 result.version，分别检查重复确认、输入代次和服务器先后。

若只使用函数式更新却无条件 dirty=false，晚到响应仍会丢掉新编辑状态；若只比较版本却不比较代次，同一次保存等待期间的新输入仍可能被误确认。React 提供正确组合状态更新的机制，领域化的客户端模型提供判断条件。

开发检查增加 Effect 执行机会，也推动我们让确认逻辑具有明确身份。acknowledged ref 不是为了掩盖所有重复 Effect，而是记录“这个成功键已经用于确认”，让后续重渲染不重复产生可见状态变化。其他 Effect 仍需按自身资源正确清理，例如地址监听的移除。
