# 本地应用开发

从仓库根按README配置ConnectionStrings__EchoCase，使用自己的本地PostgreSQL。应用账号需要目标库读写，EF迁移需要相应DDL权限。工具不替你创建环境或停止数据库。

```powershell
dotnet restore EchoCase.slnx --locked-mode
dotnet build EchoCase.slnx --no-restore
dotnet tool restore
dotnet ef database update --project backend/EchoCase.Infrastructure --startup-project backend/EchoCase.Api --no-build
$env:ASPNETCORE_ENVIRONMENT='Development'
dotnet run --project backend/EchoCase.Api --no-build --no-launch-profile --urls http://127.0.0.1:5080
```

第二终端在frontend执行npm ci和npm run dev；打开5173。Vite代理/api到5080，浏览器同源处理Cookie/CSRF。API不自动执行迁移；源模型和迁移放Infrastructure。修改映射后审查生成迁移，再用独立集成测试验证旧数据。

API在Development暴露/openapi/v1.json。保持API运行，在frontend执行：

```powershell
npm run contract
git diff --exit-code -- backend/api/schema.d.ts
npm run build
```

需要新增合同的任务应审阅生成文件差异并提交；验证已有合同则要求无差异。不要手改生成声明替代API合同。

Windows运行API时程序集会被锁定，重新build/test/publish前停止该开发进程。若使用其他端口，调整Vite代理/ECHOCASE_BASE_URL；默认命令保持5080/5173。

编译产物验证可运行dotnet publish到test/TestResults/publish目录，前端build:verify生成source map供边界检查。这些是应用构建检查，不发行镜像或运行环境发布。
