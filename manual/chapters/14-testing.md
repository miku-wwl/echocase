# 独立测试：用失败定位应用边界

测试分层不是把同一程序集分成几个目录。纯领域/用例测试应无需数据库；EF/HTTP/Identity组合必须在真实PostgreSQL上检查；浏览器再覆盖Cookie、DOM、状态时序与公共API的组合。

UnitTests只引用Domain/Application，具有自己的NUnit依赖。IntegrationTests引用API/Infrastructure，所有夹具、账号生成、随机测试库和SQL记录器都在该项目。应用solution不列入测试项目；两种测试可以各自dotnet test，不需要先打包运行环境。

每次集成夹具创建受控echocase_test_随机库，finally只删除这个库。缺测试连接就失败，不把缺环境伪装为跳过。调用WebApplicationFactory时替代的是HTTP宿主，不是数据库：原值Version谓词、真实外键/唯一键和事务回滚仍由PostgreSQL执行。

E2E是test/e2e中的独立npm包，frontend不依赖Playwright。测试经过UI或公共API，不引入应用内部fixture。关键用例保留五模块闭环、关联修订、草稿/后台刷新/双窗口、提交后丢响应与不可读成功正文。没有因重构提高测试总量，也不通过增加重试隐藏失败。

等待条件应表达业务完成。保存说明可能已渲染，而异步表单还没关闭；宽泛文字定位器会同时匹配输入框与已保存段落。应等待表单关闭，再定位确认区并读取真实服务器状态。测试同步问题也要保留失败原因。

架构检查同时看项目引用、MSBuild求值Compile项、实际NuGet库和publish DLL/deps.json；前端检查imports及生产bundle的source map来源。文件夹名称正确只是一项条件，不能代替真实构建图。data-testid属性不是测试源码，也不意味着测试框架已打进bundle。

复现入口见[独立测试指南](../../backend/docs/engineering/TESTING.md)。产物在忽略的TestResults/test-results目录及CI测试附件，普通CI不维护历史证据或出版流水线。

## 练习

**14-A：** 删除测试连接再只运行UnitTests，应发生什么？参考答案：单元项目应正常运行，因为它不引用数据库/API或集成夹具；IntegrationTests必须明确失败，不能静默改用内存库。

**14-B：** 如果API.csproj通过Compile包含了tests里的helper，仅检查ProjectReference够吗？参考答案：不够；实际编译项也要检查。生产包图和publish输出还需检查测试程序集/SDK是否混入。

**14-C：** 为什么Playwright独立包比前端devDependency更清晰？参考答案：开发依赖虽然通常不会打进bundle，但分离后安装、锁文件、配置和责任都独立；仍需检查生产imports/bundle，不能只靠包的位置宣称隔离。
