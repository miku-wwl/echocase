# Azure 部署设计与未执行边界

状态 **NOT_RUN**。Phase 2A 没有登录创建 Azure 资源、执行 az deployment、开启计费或发布应用。本地/CI 容器运行不等于 Azure 执行证据。此设计服务于同一个模块化单体，不引入 AKS、消息服务或微服务。

## 最小目标拓扑

一个 Linux App Service 承载非 root OCI 应用和静态 React，同源 HTTPS；Azure Database for PostgreSQL Flexible Server 为业务数据库；ACR 保存经 CI 验证的镜像 digest。Web 应用通过 VNet integration/private DNS 连接受限数据库，公网不开放 PostgreSQL。Key Vault 管理连接秘密，应用托管身份只读必要秘密。App Service plan、网络能力、数据库和镜像存储都有实际资源/费用影响，规格及预算需所有者先批准。

## 本地配置不能直接照搬的地方

| 事项 | 目标设计 | 当前差距 |
|---|---|---|
| HTTPS/Cookie | 边缘强制 HTTPS，应用生产 Cookie Secure=Always；校验可信代理/转发头与 HSTS | 本地/CI 是 loopback HTTP Development，未验证反向代理和真实 TLS |
| 数据库身份 | 应用账号仅业务 DML；独立迁移身份拥有 DDL；秘密轮换/连接池更新 | 演练使用可创建临时库的实验账号，未部署最小权限分离或托管身份 DB 认证 |
| DataProtection | 所有实例/slot 使用受控持久密钥存储，并用 Key Vault 加密；固定应用隔离名 | 当前只是 Docker/Podman 命名卷；Azure Blob/Key Vault provider 的配置和依赖尚未实现，不能直接扩多实例 |
| 迁移 | 独立、串行、可审查的迁移执行任务，预先校验目标模式与备份；应用启动不自动迁移 | 已有 --migrate 与可空列扩展，本地演练未证明真实云权限、锁等待或大表 DDL 耗时 |
| 健康/遥测 | 进程 live 与依赖 ready 分开，平台按 ready 决定接流量；日志/指标接收并保留 TraceId | 当前有结构化请求日志、ActivitySource/Meter 和健康端点；没有验证云日志采集、告警或分布式追踪后端 |
| 账户与安全 | 按实际使用人群补邮箱确认、恢复、会话撤销等；完成威胁评估 | 不以现有资源越权/CSRF 测试代替完整生产账户治理 |
| 备份/恢复 | Flexible Server 备份/PITR 策略，经真实业务数据恢复演练验收 RPO/RTO | 旧 E24 是小型独立数据演示；本轮应用回退不是完整灾备或 PITR |

## 获得资源与预算批准之后的执行顺序

1. 锁定已绿 CI 的源提交、镜像 digest、迁移清单和批准的预算/区域/网络/保留策略。
2. 用 GitHub Environment 限定发布身份和人工批准；OIDC 联合身份只授予必要 Azure 操作。当前工作流只有 contents:read，不存在已启用的云部署权限。
3. 验证备份可恢复，检查旧应用与扩展模式兼容；独立身份执行迁移，保存真实目标状态与日志。
4. 在获批 plan 支持的 staging slot 验证 HTTPS、代理、Cookie/CSRF、密钥持久性、资源越权、旧数据、修订与五模块，然后再决定切流量。slot 能力与费用需要选型核对，未在本机假设已具备。
5. 监测错误率、ready、连接池、锁等待和版本冲突；异常时退回旧镜像/slot，保留向前模式并验证新数据。数据库模式不兼容时另做恢复方案，不执行有损 Down 来冒充回退。
6. 实际验证后分别报告部署、故障恢复和生产差距；设计通过不把任一执行项改为 VERIFIED。

没有提供可误执行的资源创建脚本；所列服务只是本项目可行的有限设计，最终云实施属于需要另行授权的工作。
