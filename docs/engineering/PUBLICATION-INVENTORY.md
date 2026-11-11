# Phase 2B · Enterprise .NET Full-Stack Software Engineering

所有者已批准教材收窄为企业.NET全栈应用工程。旧PDF仅为历史，保留于63c5872，不作为当前交付物。本次只整理源和编写入口，不重新出版、不追页数。

## 当前内容资产

| 主线 | 可用源/教材 | 2B深化工作 |
|---|---|---|
| 需求与五模块 | PRD、DOMAIN-MODEL、manual ch01 | 把规则、状态、授权、成功/失败条件写成可审查用例 |
| Clean/DDD/CQRS/DI | 四层源码、TEMPLATE-COMPARISON、ch02–05、ADRs | 并排追踪固定模板与实际用例，解释端口、生命周期、校验和领域行为 |
| ASP.NET/API合同 | Program、生成schema、ch04/06/10 | 注释请求处理、严格JSON、Cookie/CSRF/资源所有权、ProblemDetails编号 |
| EF内部机制 | EchoDbContext/Store、迁移、集成SQL记录器、ch07/08 | 跟踪状态→子UPDATE/根原值条件→事务失败的真实因果图 |
| 数据一致性/兼容 | 旧列集迁移、旧JSON回执、微秒精度、APP03–05 | 解释为什么可空演进/时间精度/失败回滚是合同的一部分；不写环境发布教材 |
| React/TypeScript | App/Workspace/hooks/editors、ch11/12 | 解释确认缓存、pending呈现、基线/代次、取消、未知响应、显式冲突 |
| React Flow | EvidenceGraph/LinkEditor、ch13、五模块E2E | 业务关联与本地坐标分离，标注同一关联修订的身份保持 |
| 查询性能 | 实际Store、索引、QueryProbe、ch15 | 注释真实SQL、三种计划与测量条件；不扩为负载/可用性框架 |
| 独立测试 | tests/unit、integration、e2e；TESTING；ch14 | 源码图/运行包/publish/bundle的隔离证据；失败同步条件，避免测试数量叙事 |
| 维护性与需求演进 | CASE-STUDIES、ADR0007/0008/0009、APP09 | 需求→影响→领域/用例/合同/迁移/React→回归的连贯案例；解释为何小而明确的拆分有效 |

## 继续保留的真实教训

- 晚到响应清dirty会丢新输入，后台refetch不能静默换写入版本。
- 已提交但响应丢失、200正文不可读，均需保护原意图；旧回执不能倒退确认缓存。
- 子实体更新与根Version、审计、回执要同事务；实际SQL比接口名称更能说明机制。
- .NET tick与PostgreSQL微秒精度差异，以及默认ProblemDetails writer覆盖编号，都是应用框架案例。
- 等待表单真正完成、定位确认内容，而非任何相同文字，是有因果的E2E同步。
- 测试放目录里不够，必须验证求值引用、真实包图和生产产物。

基线的原始截图/失败记录可从[历史证据](https://github.com/miku-wwl/echocase/tree/63c587277541b4e700258aad82de9b2ad0ba32f8/evidence)选用并标明版本；当前运行截图在独立E2E结果或CI附件，不自动装订为教材。源码已移动，2B须以本轮最终提交重新绑定引用和注释。

## 明确删除的课程职责

不设置Azure、云身份/资源配置、容器发行、环境部署、Kubernetes/Terraform、监控平台、SRE事件或灾备章节。历史发生环境可以一笔交代，重点仍是应用错误/框架机制，不把旧运维课程改名后保留。

## 后续编写与出版工作

围绕上述主线重新组织课程、深入源码讲解、制作应用架构/数据/请求/React时序图、重拍并注释真实UI、完善练习与答案、核对引用和技术结论，最后再做版式/目录/链接/逐页QA。旧PDF的QA不能移作尚未生成新教材的证明。当前资料是源资产与索引，最终插图/教材仍为NOT_RUN。
