# EchoCase · Enterprise .NET Full-Stack Application Engineering

一个专注业务应用的 .NET 10 + React 19 工程项目：用虚构调查案例学习需求、DDD、Clean Architecture、CQRS、EF Core/PostgreSQL、API 安全与一致性，以及复杂前端状态。

五模块为案件、证据、证据关联、调查进度、结论提交。保留关联修订、旧数据兼容、版本条件写入、持久幂等回执、资源所有权、草稿保护和显式冲突恢复。

本仓库拥有应用代码、数据库模型/迁移、独立测试和轻量应用 CI。云资源、环境发布、镜像发行、SRE 运维和灾备不是当前目标。`EchoCase.Infrastructure` 是应用持久化/身份层，继续保留。

## 源码与独立测试

```text
backend/EchoCase.Domain/          聚合、规则、状态机
backend/EchoCase.Application/     用例、查询、DTO、持久化端口
backend/EchoCase.Infrastructure/  EF、PostgreSQL、Identity、迁移
backend/EchoCase.Api/             HTTP 合同与依赖组装
backend/docs/               应用需求、架构、API与开发文档
frontend/src/                React、查询缓存、草稿、图谱
test/unit/                 独立 NUnit 单元测试
test/integration/          独立 PostgreSQL/API 集成测试；可选 QueryProbe
test/e2e/                  独立 Playwright 包与公共接口测试
test/tools/                边界检查与测试启动工具
manual/                    教材章节与reference材料
```

`EchoCase.slnx` 只包含四个应用项目。`test/EchoCase.Tests.slnx` 是独立测试入口。依赖方向始终是 Tests → Application；单元测试不引用 API、数据库实现或集成夹具。前端应用不安装 Playwright。

Git跟踪结构只保留backend/frontend/test/manual四个主目录，另有.github。当前布局与验证见[整理报告](backend/docs/engineering/CONSOLIDATION.md)。

## 本地开发

前置：.NET SDK 10.0.300、Node 22.22.2+、可访问的 PostgreSQL 17、Python 3（边界检查）。PostgreSQL 可来自自己的本地安装；仓库不管理其生命周期。以下连接中的账号/口令需自行替换。

```powershell
$env:ConnectionStrings__EchoCase='Host=127.0.0.1;Port=5432;Database=echocase;Username=YOUR_USER;Password=YOUR_PASSWORD'
$env:ASPNETCORE_ENVIRONMENT='Development'
dotnet restore EchoCase.slnx --locked-mode
dotnet build EchoCase.slnx --no-restore
dotnet tool restore
dotnet ef database update --project backend/EchoCase.Infrastructure --startup-project backend/EchoCase.Api --no-build
dotnet run --project backend/EchoCase.Api --no-build --no-launch-profile --urls http://127.0.0.1:5080
```

另一个终端：

```powershell
cd frontend
npm ci
npm run dev
```

打开 [本地工作台](http://127.0.0.1:5173)，创建本地账户。Windows 下重新编译 API 前先停止使用同一输出目录的进程。详细命令见 [开发指南](backend/docs/engineering/DEVELOPMENT.md)。

## 验证

```powershell
dotnet restore test/EchoCase.Tests.slnx --locked-mode
dotnet test test/unit/EchoCase.UnitTests --no-restore
# 使用可创建临时测试库的本地测试账号；不要使用业务生产数据库
$env:ECHOCASE_TEST_CONNECTION='Host=127.0.0.1;Port=5432;Database=postgres;Username=YOUR_TEST_ADMIN;Password=YOUR_TEST_PASSWORD'
dotnet test test/integration/EchoCase.IntegrationTests --no-restore
python test/tools/check_boundaries.py
```

API 与 Vite 已运行时，单独执行 E2E：

```powershell
cd test/e2e
npm ci
# 本机默认 Edge；CI 安装 Chromium
npm test
```

[测试与依赖隔离](backend/docs/engineering/TESTING.md)说明实际项目图、运行依赖、publish 输出和前端 bundle 的检查方法。应用 CI 只有 [application-ci.yml](.github/workflows/application-ci.yml)，执行构建、独立测试、合同与边界检查；不发布或部署应用。

## 文档与学习

- [需求](backend/docs/requirements/PRD.md)、[领域](backend/docs/domain/DOMAIN-MODEL.md)、[架构](backend/docs/architecture/ARCHITECTURE.md)、[API](backend/docs/api/API-DESIGN.md)
- [当前路线与 DoD](backend/docs/PLAN.md)、[应用实验索引](manual/reference/EXPERIMENTS.md)、[模板机制比较](manual/reference/TEMPLATE-COMPARISON.md)
- [重构验收](backend/docs/engineering/APPLICATION-ONLY-ACCEPTANCE.md)、[仓库责任与退役清单](backend/docs/engineering/REPOSITORY-RESPONSIBILITY.md)
- [教材源](manual/README.md)、[后续 Phase 2B 内容清单](manual/reference/PUBLICATION-INVENTORY.md)

## 范围变更与历史

2026-11-11 所有者明确收窄为应用工程，本次要求替代原计划中的云与交付目标。原 E10 部署实验不再是当前 DoD；没有将历史重新命名成从来不存在。

历史 Phase 2A 分支 `codex/phase2a-engineering-20261111` 保留在 `63c587277541b4e700258aad82de9b2ad0ba32f8`。历史实验、原证据和两份旧 PDF 可从 [该提交](https://github.com/miku-wwl/echocase/tree/63c587277541b4e700258aad82de9b2ad0ba32f8)恢复；它们不是当前交付物。本次不生成 PDF，不修改 main，也不改变现有业务数据。
