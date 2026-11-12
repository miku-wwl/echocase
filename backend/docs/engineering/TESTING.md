# 独立测试与边界验证

## 单元：test/unit/EchoCase.UnitTests

只引用Domain/Application，NUnit与TestSDK仅在测试项目中。领域、状态、关联修订、投影与程序集边界测试无需数据库。移走的是原有用例，不按数量增加新测试。

```powershell
dotnet restore test/EchoCase.Tests.slnx --locked-mode
dotnet test test/unit/EchoCase.UnitTests --no-restore --logger 'trx;LogFileName=unit.trx' --results-directory test/unit/TestResults
```

## 集成：test/integration/EchoCase.IntegrationTests

真实PostgreSQL验证迁移/数据保留、关系约束、Cookie/CSRF/资源授权、并发、回执和原子性。WebApplicationFactory替代HTTP宿主，不替代数据库。夹具和SQL记录器只在该项目。

```powershell
$env:ECHOCASE_TEST_CONNECTION='Host=127.0.0.1;Port=5432;Database=postgres;Username=YOUR_TEST_ADMIN;Password=YOUR_TEST_PASSWORD'
dotnet test test/integration/EchoCase.IntegrationTests --no-restore --logger 'trx;LogFileName=integration.trx' --results-directory test/integration/TestResults
```

连接必须允许创建/删除临时测试库，不能使用生产业务库。测试只创建随机echocase_test_库并在finally精确删除；缺环境变量会失败，不静默跳过。独立运行不会依赖单元测试夹具。可选设置ECHOCASE_TEST_ARTIFACTS为绝对路径，记录真实SQL/跟踪观察；默认不写证据。

可选QueryProbe位于test/integration/EchoCase.QueryProbe，只调用实际Store列表查询并比较三种索引访问计划，使用临时echocase_probe_库。它不在默认CI运行，不测基础设施容量，也不作为性能SLA：

```powershell
dotnet run --project test/integration/EchoCase.QueryProbe -- test/integration/TestResults/query-probe
```

## E2E：test/e2e

该npm包独立锁定Playwright，frontend包不安装测试运行器。通过UI/API检查五模块、关联修订、503下草稿保留、晚到响应、后台刷新、双窗口、原键确认与不可读成功响应。不导入生产内部模块，不添加通用QA平台。API/Vite需已启动。

```powershell
cd test/e2e
npm ci
npm test
```

本机默认已安装Edge；CI使用Chromium并运行npx playwright install --with-deps chromium。若本机使用Chromium，可安装后设置CI=true。结果/截图/失败trace写test-results，不提交进源码。ECHOCASE_E2E_ARTIFACTS可覆盖应用场景附件目录。

## 实际依赖与产物检查

```powershell
python test/tools/check_boundaries.py
dotnet publish backend/EchoCase.Api --no-restore -c Release -o test/TestResults/publish
# 在frontend执行 npm run build:verify，再回根目录
python test/tools/check_boundaries.py --publish-dir test/TestResults/publish --frontend-dist frontend/dist
```

检查器验证源码引用、MSBuild求值后的引用/Compile项、NuGet解析库、独立测试引用方向、前端imports、实际publish DLL/deps.json和bundle source map来源。默认要求已restore，--structure-only仅供快速静态检查，不能替代完整验收。数据-testid等可测属性不等于打包了测试源码。

当前CI是一条应用工作流：构建、单元、PostgreSQL集成、TS/前端构建、API合同、E2E及产物隔离。只上传普通测试结果，七天保留；不运行历史环境演练或出版门禁。

模板迁移保留原26项单元、22项PostgreSQL/API集成和9项E2E断言。新增`PostgresApiTests.Template.cs`的5项集成检查使用官方模板的作用域ISender测试模式，验证匿名直接分派、验证器实际执行且无落库、所有权改变后不能回放旧所有者回执、模型及三条旧迁移不漂移。因此当前集成总数为27；没有用新增数量代替原场景。

NSwag轻量检查先用已提交schema重生成客户端并要求无差异，再从运行的真实API更新schema/客户端并要求无差异。其开发依赖不会成为前端运行时依赖或引入测试包。原模板完整测试仅在独立bootstrap分支，真实结果及一个示例登录浏览器超时见模板来源文档；活动CI没有忽略自己的回归失败。

第五项迁移回归使真实 Store 提交后延迟超过 500ms，并让额外身份查询抛错，确认性能日志不把已提交操作转为失败，且审计/回执仍各一次。
