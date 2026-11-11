# 独立测试与边界验证

## 单元：tests/unit/EchoCase.UnitTests

只引用Domain/Application，NUnit与TestSDK仅在测试项目中。领域、状态、关联修订、投影与程序集边界测试无需数据库。移走的是原有用例，不按数量增加新测试。

```powershell
dotnet restore tests/EchoCase.Tests.slnx --locked-mode
dotnet test tests/unit/EchoCase.UnitTests --no-restore --logger 'trx;LogFileName=unit.trx' --results-directory tests/unit/TestResults
```

## 集成：tests/integration/EchoCase.IntegrationTests

真实PostgreSQL验证迁移/数据保留、关系约束、Cookie/CSRF/资源授权、并发、回执和原子性。WebApplicationFactory替代HTTP宿主，不替代数据库。夹具和SQL记录器只在该项目。

```powershell
$env:ECHOCASE_TEST_CONNECTION='Host=127.0.0.1;Port=5432;Database=postgres;Username=YOUR_TEST_ADMIN;Password=YOUR_TEST_PASSWORD'
dotnet test tests/integration/EchoCase.IntegrationTests --no-restore --logger 'trx;LogFileName=integration.trx' --results-directory tests/integration/TestResults
```

连接必须允许创建/删除临时测试库，不能使用生产业务库。测试只创建随机echocase_test_库并在finally精确删除；缺环境变量会失败，不静默跳过。独立运行不会依赖单元测试夹具。可选设置ECHOCASE_TEST_ARTIFACTS为绝对路径，记录真实SQL/跟踪观察；默认不写证据。

可选QueryProbe位于tests/integration/EchoCase.QueryProbe，只调用实际Store列表查询并比较三种索引访问计划，使用临时echocase_probe_库。它不在默认CI运行，不测基础设施容量，也不作为性能SLA：

```powershell
dotnet run --project tests/integration/EchoCase.QueryProbe -- tests/integration/TestResults/query-probe
```

## E2E：tests/e2e

该npm包独立锁定Playwright，frontend包不安装测试运行器。通过UI/API检查五模块、关联修订、503下草稿保留、晚到响应、后台刷新、双窗口、原键确认与不可读成功响应。不导入生产内部模块，不添加通用QA平台。API/Vite需已启动。

```powershell
cd tests/e2e
npm ci
npm test
```

本机默认已安装Edge；CI使用Chromium并运行npx playwright install --with-deps chromium。若本机使用Chromium，可安装后设置CI=true。结果/截图/失败trace写test-results，不提交进源码。ECHOCASE_E2E_ARTIFACTS可覆盖应用场景附件目录。

## 实际依赖与产物检查

```powershell
python scripts/check_boundaries.py
dotnet publish src/EchoCase.Api --no-restore -c Release -o work/application-publish
# 在frontend执行 npm run build:verify，再回根目录
python scripts/check_boundaries.py --publish-dir work/application-publish --frontend-dist frontend/dist
```

检查器验证源码引用、MSBuild求值后的引用/Compile项、NuGet解析库、独立测试引用方向、前端imports、实际publish DLL/deps.json和bundle source map来源。默认要求已restore，--structure-only仅供快速静态检查，不能替代完整验收。数据-testid等可测属性不等于打包了测试源码。

当前CI是一条应用工作流：构建、单元、PostgreSQL集成、TS/前端构建、API合同、E2E及产物隔离。只上传普通测试结果，七天保留；不运行历史环境演练或出版门禁。
