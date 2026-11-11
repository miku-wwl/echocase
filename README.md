# EchoCase · Enterprise Full-Stack Engineering

一个可运行、可复现、可审阅的调查工作台与中文工程教材。技术：C# / ASP.NET Core 10、DDD / CQRS、PostgreSQL / EF Core、React 19 / TypeScript、TanStack Query、React Flow、官方 shadcn 组件。

## 交付物

- [中文教材 PDF](manual/dist/Enterprise-Full-Stack-Engineering.pdf)：18 章、26 项实验记录、练习与参考答案、真实截图、源码片段与可点击目录。
- [独立成册验收报告](docs/ACCEPTANCE-REPORT.md) / [PDF](manual/dist/EchoCase-Acceptance-Report.pdf)：明确 VERIFIED / PARTIAL / BLOCKED / NOT_RUN，披露目标差异与生产限制。
- [工程路线与参考审计](docs/PLAN.md)、[架构](docs/architecture/ARCHITECTURE.md)、[API](docs/api/API-DESIGN.md)、[测试](docs/testing/TEST-STRATEGY.md)、[部署](docs/deployment/DEPLOYMENT.md)、[实验索引](manual/chapters/19-labs.md)。

本项目为教学与作品集 review edition，不宣称生产就绪。Azure 未部署，不创建付费资源。所有案件与人物虚构。

## 快速运行（Windows / PowerShell 7）

前置：.NET SDK 10.0.300、Node 22.22.2+、已启动的 Podman 机器。不要在 API 正运行时重新编译同一输出目录；Windows 会锁定正在执行的程序集。

```powershell
./scripts/dev-db.ps1
# 数据库只绑定 127.0.0.1:55432，公开本地实验密码禁止用于生产

dotnet restore --locked-mode
./scripts/dev.ps1 migrate
./scripts/dev.ps1 api
```

另开终端：

```powershell
cd frontend
npm ci
npm run dev
```

访问 http://127.0.0.1:5173，创建本地账户。API 为5080。五模块：案件、证据、关联、调查进度、结论提交。六条证据形成一个完整案件。关联无向，发现与提交受状态机约束；终态只读。

## 运行与验证

```powershell
# 停止开发 API 后运行后端全集；会创建并精确删除随机测试数据库
./scripts/dev.ps1 test
# 重启 API 与 Vite 后
cd frontend
node node_modules/@playwright/test/cli.js test
```

后端结果是 evidence/backend/backend.trx，浏览器结果是 evidence/browser/results.json；首次失败与修正前证据也保留。当前数量与远程 CI 状态以验收报告为准。

实验与出版使用独立 Python 环境，见 [测试说明](docs/testing/TEST-STRATEGY.md)。完整实验配置好连接后运行：

```powershell
uv venv work/venv --python 3.13
uv pip install --python work/venv/Scripts/python.exe -r manual/requirements.txt
$env:ECHOCASE_PG_DSN='postgresql://echocase:echocase-local-only@127.0.0.1:55432/echocase'
work/venv/Scripts/python.exe experiments/database.py
work/venv/Scripts/python.exe experiments/backup.py
# 以下会短暂停止且在 finally 恢复本项目开发数据库；不要与其他测试并行
work/venv/Scripts/python.exe experiments/reliability.py
work/venv/Scripts/python.exe experiments/container.py
```

容器实验从独立 PostgreSQL 模式启动，验证应用删除重建后原调查与认证仍可用；成功后保留 http://127.0.0.1:6080 供审阅。开发库与容器验收库独立。Compose 文件可供另一路径使用，但 provider 路径没有在本机运行。

## 证据与出版门禁

```powershell
work/venv/Scripts/python.exe tools/catalog.py
work/venv/Scripts/python.exe tools/verify.py
work/venv/Scripts/python.exe tools/test_gate.py
work/venv/Scripts/python.exe tools/catalog.py
```

检查器验证结构化结果、摘要、来源数字、引用与有限依赖规则；不能证明所有自然语言结论。自测先验证正常副本，再以七类损坏证明非零退出。26份实验记录含假设、机制、设计、执行、观测、解释、限制、清理。

[出版命令](manual/README.md)使用本地 Pandoc、Mermaid、Playwright，两遍目录映射、PDF负向自测、版面几何检查和逐页视觉复核。字体与浏览器会影响分页，不承诺字节相同。

## 范围与限制

- 四层模块化单体、单数据库事务，没有微服务/Kubernetes/多租户/AI。
- Version / If-Match 防过期写；UUID 幂等键和持久回执防相同意图重复提交。
- Identity 哈希、Cookie、CSRF、资源所有权、限流和合同负测试；MFA、账户恢复、安全戳吊销等生产身份能力未实现。
- 案件目录在代码固定，列表最近50条，没有分页、协作、动态案件版本或回执自动清理。
- 可观测性为日志、trace上下文与仪表点，没有完整监控告警平台；性能结果仅为本机测量。
- pg_dump实验只恢复三条合成记录，不冒充完整应用灾难恢复或PITR。
- 教材实际规模与原300–400页编辑目标的差异、第三方独立审阅缺项均在验收报告披露。

## 停止与保留数据

关闭开发服务终端；`./scripts/dev-db.ps1 stop` 停开发数据库。容器实例：`podman stop echocase-app echocase-container-db`。这些操作保留数据。删除卷会丢失调查和密钥，不属于默认清理。

[第三方来源与许可证](THIRD-PARTY-NOTICES.md)。原仓库 Apache-2.0；官方 shadcn 组件与复制样式保留其 MIT 许可证。
