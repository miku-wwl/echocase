# 验证策略

运行前启动 PostgreSQL，设置 ECHOCASE_TEST_CONNECTION。`./scripts/dev.ps1 test` 使用公开本地实验连接。测试创建随机 echocase_test_ 数据库并精确清理；缺连接不跳过测试。

领域与架构测试无需数据库：`dotnet test --filter Category=Unit`。全集包含真实 PostgreSQL 的 Identity、事务、外键、并发、幂等、迁移与安全。两个 DbContext 和两个 API 请求分别验证并发不同层次。

开发 API/Vite 启动后，在 frontend 执行 `node node_modules/@playwright/test/cli.js test`。本机使用已安装 Edge；CI 使用安装的 Chromium。四组工作流验证五模块、注入503恢复、真实双窗口冲突和390px布局。失败trace不提交，结构化结果与稳定截图保留。

实验脚本需 Python 依赖：`uv venv work/venv --python 3.13`，`uv pip install --python work/venv/Scripts/python.exe -r manual/requirements.txt`。设置 `ECHOCASE_PG_DSN=postgresql://echocase:echocase-local-only@127.0.0.1:55432/echocase` 后运行 database.py 与 backup.py；reliability.py 需要 API；container.py 使用 Podman。

`tools/catalog.py` 生成实验记录、摘要与 manifest；`tools/verify.py` 核对有限结构化证据与来源；`tools/test_gate.py` 先证明正常临时副本通过，再注入七类损坏检查非零退出。重新运行自测会更新证据，应再次运行 catalog 更新摘要。文本摘要统一 CRLF→LF，二进制摘要不变。

PDF 负向自测 `manual/tools/test_pdfqa.py` 生成临时空白/越界/目录缺失输入。真实 PDF 再运行 layout、TOC 与逐页渲染。自动几何检查不能替代图意和教学审阅。

未执行：覆盖率统计、长期并发负载、全面渗透、全浏览器和完整辅助技术审计、外部独立人员验收。
