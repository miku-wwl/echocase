# Phase 2A 复现与证据导航

工作分支 `codex/phase2a-engineering-20261111`，起点 f7e0cad。前置为 .NET SDK 10.0.300、Node 22.22.2（本机26.5也实测）、Python3.13、Podman5.8.3 或 CI 的 Docker、PostgreSQL17.7。浏览器本机 Edge，CI Chromium。所有实验账号/口令为隔离本地教学用途。

## 独立开发库与后端

在仓库根 PowerShell 执行。若名称/端口已存在，先核对其归属，不覆盖已有库；本次工作已创建 echocase-p2a-dev/55433 供复核。不要同时跑后端测试与停库实验，不要在 Windows API 使用程序集时重新构建同一输出目录。

```powershell
podman run -d --name echocase-p2a-dev -p 127.0.0.1:55433:5432 `
  -e POSTGRES_USER=echocase -e POSTGRES_PASSWORD=echocase-p2a-local -e POSTGRES_DB=echocase `
  -v echocase-p2a-dev-data:/var/lib/postgresql/data postgres:17.7-alpine
$env:ConnectionStrings__EchoCase='Host=127.0.0.1;Port=55433;Database=echocase;Username=echocase;Password=echocase-p2a-local'
$env:ECHOCASE_TEST_CONNECTION=$env:ConnectionStrings__EchoCase
# 使用绝对路径：NUnit 进程工作目录不一定是仓库根
$env:ECHOCASE_PHASE2_EVIDENCE=Join-Path (Get-Location) 'evidence/phase2a/reproduced/database'
dotnet restore --locked-mode
dotnet test --no-restore --logger 'trx;LogFileName=backend.trx' --results-directory evidence/phase2a/reproduced/backend
dotnet restore experiments/phase2a/DbProbe --locked-mode
dotnet run --project experiments/phase2a/DbProbe --no-restore -- evidence/phase2a/reproduced/database
dotnet tool restore
dotnet ef database update --project src/EchoCase.Infrastructure --startup-project src/EchoCase.Api --no-build
$env:ASPNETCORE_ENVIRONMENT='Development'
dotnet run --project src/EchoCase.Api --no-build --no-launch-profile --urls http://127.0.0.1:5080
```

测试只创建随机 `echocase_test_*` 数据库并在 finally 精确删除；DbProbe 使用 `echocase_probe_*`。旧演示实例6080及其数据不在这些流程中。开发库55433不是用户旧库，不调用 Phase 1 的数据库脚本来复现本轮。

## 前端与实际浏览器

另一个终端启动 Vite 后，再在第三个终端运行合同与浏览器检查。保持后端5080与前端5173就绪。

```powershell
cd frontend
npm ci
npm run dev
```

```powershell
cd frontend
npm run contract
git diff --exit-code -- src/api/schema.d.ts
npm run build
$env:ECHOCASE_BROWSER_EVIDENCE='../evidence/phase2a/reproduced/browser'
node node_modules/@playwright/test/cli.js test
```

浏览器注册随机账户；四项新场景共用一个独立测试账户，原四项流程各用随机账户，避免把认证限流误当用例失败。不关闭限流以跑测试。需要 Chromium 时先 `npx playwright install chromium` 并按 CI 配置设置 CI=true；Windows 默认使用已安装 Edge。

## 真实 OCI 升级、故障与应用回退

此脚本自己创建隔离数据库，**不依赖开发库55433**，可以在没有 API/Vite 的干净检出中运行。旧提交必须存在于 Git 对象库，浅克隆需要先获取它。6081 需空闲。

```powershell
python experiments/phase2a/delivery.py --engine podman --output evidence/phase2a/reproduced/delivery --port 6081
# Linux/CI 将 --engine 改为 docker
python tools/verify_phase2a.py --evidence-root evidence/phase2a/reproduced
```

脚本从旧源和当前源构建，生成随机名称的本次网络/卷/容器，实际停本次数据库，并在 finally 恢复/清理，只保留构建镜像与证据目录。若失败，latest.json 指向 FAILED 目录，原错误和清理退出码必须检查，不能改状态冒充通过。旧/新应用回退在同一向前模式上执行；不会执行会删除新字段的 Down。

## 门禁、原始证据与远程 CI

```powershell
python tools/verify.py
python tools/verify_phase2a.py
python tools/test_phase2a_gate.py --output work/phase2a-gate-selftest.json
```

第一个工具继续检查冻结的 Phase 1 结构/证据/教材源引用；第二个核对本轮实际结果，不以总测试数量或性能比值充当质量门槛；第三个只在 work 临时副本中改变重试键、SQL 条件、有限数值和回退阶段，预期均拒绝，然后检查恢复副本可通过。不要运行旧 catalog 或原 test_gate 来重写冻结的旧证据。

| 位置 | 可以查明什么 |
|---|---|
| `evidence/phase2a/before/` | 两个基线浏览器失败、原现场文字、截图、trace；时间精度失败与错误追踪不一致 |
| `evidence/phase2a/backend/backend.trx` | 本轮领域、真实 PostgreSQL/API/迁移/架构检查的具体断言结果 |
| `evidence/phase2a/database/` | SQL 与跟踪、保证同时加载的竞争、微秒一致性、真实 Store 三种索引执行计划 |
| `evidence/phase2a/browser/` | 原五模块/503/双窗口/移动端回归，以及四个新真实时序场景；JSON 与截图 |
| `evidence/phase2a/delivery/latest.json` | 当前本地成功运行目录；同级保留第一次追踪编号检查失败的记录 |
| `evidence/phase2a/upstream-source.json` | 固定模板提交、实际阅读文件与摘要；不代表上游执行结果 |
| `evidence/phase2a/qa/` | 新门禁反例检查 |
| `.github/workflows/phase2a.yml` | 每次推送真实重新执行后端、合同、浏览器、Docker交付；新产物写 fresh 目录，合并下载后语义验证 |

CI integrity 先核对已提交的本地证据；full-stack 与 delivery 再分别产生本次真实运行结果；fresh-evidence 验证本次 OCI 源为当前 clean 提交。artifact 名 `phase2a-full-stack`、`phase2a-delivery`；失败时还有调试日志/trace。Azure 不执行。
