# 模板基础整改工程验收

开始日期：2026-11-12；终审补充：2026-11-13。范围：`codex/template-migration-20261112` 的应用迁移；不合并 main，不改历史分支，不重写教材。

| 验收项 | 结果与依据 |
|---|---|
| 官方生成基线独立存在 | 171个真实ca-sln生成文件逐字节校验，独立bootstrap分支/提交和生成参数保留 |
| 实际模板机制接入 | 四层Add*Services、端点发现/命名、ISender、扫描注册的handlers、授权/验证等behaviors、CurrentUser/IdentityService参与业务请求 |
| 单一生产架构 | 仅四个backend项目、一个React前端；无Todo API、第二DbContext或平行旧端点；Application不直接引用EF/API |
| PostgreSQL数据兼容 | 领域、协调服务、Store、DbContext映射和三条迁移保持原实现；原旧数据升级/并发测试通过；新增HasPendingModelChanges为false |
| 合同与生成客户端 | 实际OpenAPI 3.0，稳定operationId；固定NSwag14.8.0；TS端点方法与应用协议适配器；重复生成摘要一致 |
| 一致性与安全 | 原所有权、Cookie/CSRF、If-Match、幂等、同键并发、原子审计/回执场景保留并通过；新增旧所有者回放拦截通过 |
| 构建 | 本机后端零警告/错误；前端TS与生产构建通过；活动还原保持正常安全审计 |
| 独立回归 | 原26单元、22集成、9浏览器全部通过；新增5集成通过，共26单元/27集成/9浏览器，均无跳过 |
| 精确提交CI | 最终提交的远端应用CI在书外交付报告记录；不以其他SHA或本机结果冒充 |
| 四目录与依赖隔离 | 本机MSBuild求值、解析包图、实际publish DLL/deps.json及前端source map来源检查全部通过；跟踪结构符合四目录加.github |

## 保留的已知边界

官方未修改模板默认还原被当前NuGet审计警告升级为错误阻止。隔离bootstrap构建保留警告，仅在命令行将NU1902/NU1903降为警告；此设置没有进入活动应用。独立bootstrap CI的14项单元、19项功能、5项浏览器通过，1项示例登录等待Log out超时，整条bootstrap运行未通过。没有伪造“官方模板全绿”，也未改变其断言。活动EchoCase不保留该示例UI；自己的9项原浏览器场景通过。

本机验证使用临时PostgreSQL 17.7容器的专用库及随机测试库。没有接触生产数据库或外部账户，没有创建Azure资源或执行模板的部署工作流。性能探针只编译，不重新进行性能基准。

Phase 2B PDF与章图源按原提交保留，摘要未变。新源码不自动使旧书重新对齐；只提供[后续修订影响表](../../../manual/reference/TEMPLATE-MIGRATION-IMPACT.md)。本工程实现等待所有者独立接受，未启动教材重写。
