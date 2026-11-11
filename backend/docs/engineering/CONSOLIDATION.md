# 四目录布局整理

基线：应用化分支3d192a3859e25d48f20b58d7cc08c1fdda20d71d。新review分支codex/four-directory-consolidation-20261111；不改变基线分支或main。本次只有路径、引用与工具位置整理。

```text
backend/   四个.NET项目；docs/应用文档
frontend/  原React/TypeScript应用
test/     unit/、integration/、e2e/、tools/
manual/    原教材章节；reference/学习材料与2B清单
.github/   application-ci.yml
```

| 原位置 | 新位置 |
|---|---|
| src/** | backend/** |
| tests/** | test/** |
| docs/requirements、domain、api、architecture、PLAN | backend/docs/对应位置 |
| docs/engineering开发、测试、责任及历史记录 | backend/docs/engineering；旧验收记录标明3d192a3历史布局 |
| 模板比较、应用案例、实验导航、2B清单 | manual/reference/ |
| scripts/check_boundaries.py、wait_http.py | test/tools/ |

全部原文档内容保留并重绑相对链接，固定历史提交链接不改义。后端业务源码/迁移与frontend/src相对基线内容未变；测试行为保留，只更新项目引用、工具根定位和结果路径。Frontend的src是其内部目录，不是被禁止的顶层src。

## 验证快照

- VERIFIED：Git跟踪主目录为backend/frontend/test/manual，另有.github；根配置文件保留。
- VERIFIED：两套solution锁定restore成功；四个backend项目构建0错误/警告；26项独立单元测试通过。
- VERIFIED：前端TypeScript/Vite构建通过；实际MSBuild/包图、publish DLL/deps.json和bundle来源隔离检查通过。
- VERIFIED：迁移后EF工具运行，模型与现有迁移无差异；保留文档链接检查通过。
- 本机PostgreSQL不可连接，原Podman连接/机器没有配置。没有为整理任务修复或新建环境；该次集成运行失败原因是连接拒绝，不能记为代码检查通过。22集成、9E2E、实际EF迁移和合同由本轮CI的独立PostgreSQL服务验收，最终推送SHA必须有自己的成功运行。

## 本地文件与限制

四目录限制针对Git跟踪结构。已单独检查本机忽略项：原work/含历史构建/学习/测试资料，保持原位；不以视觉目录数删除它。原docs/scripts的空目录或生成缓存可逆保存在test/TestResults/consolidation，未丢弃数据。node_modules、bin/obj及测试结果仍忽略，不计入活动源。

本轮没有重做运维/历史清理，没有改变本地业务库，没有恢复出版器或生成PDF。manual保留Markdown教材源，Phase2B编写/出版仍NOT_RUN。最终交接另附匹配源码SHA的CI结果；没有以历史运行代替新路径验证。
