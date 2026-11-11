# 本地交付与 Azure 设计

## 开发

PowerShell 7、.NET SDK 10.0.300、Node 22.22.2+、Podman 或 Docker。开发使用 Podman 脚本，数据库仅映射 127.0.0.1:55432，采用明确的公开实验密码，禁止复用到生产。

```powershell
./scripts/dev-db.ps1
dotnet restore --locked-mode
./scripts/dev.ps1 migrate
./scripts/dev.ps1 api
# 另一个终端
cd frontend
npm ci
npm run dev
```

访问 127.0.0.1:5173 并自行注册。API 5080。关闭启动终端中的进程即可停止开发服务；`./scripts/dev-db.ps1 stop` 保留数据卷。

## 容器

`python experiments/container.py` 构建真实镜像，在独立桥接网络和独立 PostgreSQL 容器迁移、启动、创建数据并重建应用。成功后 127.0.0.1:6080 保留供审阅。容器名 echocase-app、echocase-container-db，持久卷 echocase-container-pgdata、echocase-keys。该实例与开发库分离。

```powershell
podman stop echocase-app echocase-container-db
# 恢复，保留原数据
podman start echocase-container-db echocase-app
```

Docker Compose 替代描述：设置 ECHOCASE_DB_PASSWORD 后 `docker compose up --build -d`。该 Compose provider 路径尚未在本机执行，直接 Podman 路径已验证。不要同时占用6080。`docker compose down` 保留卷；不要随意加 -v。

## Azure：NOT_RUN

建议单个 App Service 容器 + PostgreSQL Flexible Server，不引入 Kubernetes。需要所有者先审批实际资源与费用，之后再创建。当前没有云资源、云部署或云费用。

部署设计需补齐：HTTPS 与代理配置、AllowedHosts 真实域名、生产 Secure Cookie、Data Protection 密钥保护与持久化、数据库 TLS、运行与迁移权限分离、托管身份、网络访问、日志告警、备份与异机恢复、会话撤销与账户恢复。不能直接把本地 Development 容器暴露到公网。

参考：[App Service 容器配置](https://learn.microsoft.com/en-us/azure/app-service/configure-custom-container)、[数据库托管身份](https://learn.microsoft.com/en-us/azure/app-service/tutorial-connect-msi-azure-database)。这是基于官方机制的设计，具体 Azure 行为未经本项目运行验证。
