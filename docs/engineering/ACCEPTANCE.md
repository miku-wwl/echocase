# 应用仓库重构验收

基线：63c587277541b4e700258aad82de9b2ad0ba32f8，保留原Phase2A分支和main；新review分支codex/application-only-restructure-20261111。2026-11-11所有者范围变更见ADR0009，当前不以环境交付验收。

## 已执行结果

| 检查 | 状态 | 实际结果 |
|---|---|---|
| 应用编译 | VERIFIED | EchoCase.slnx仅构建四个src项目，0警告/错误 |
| 独立单元 | VERIFIED | 清除测试数据库环境变量后单独运行，26通过，无跳过 |
| 独立集成 | VERIFIED | 新项目真实PostgreSQL/API/迁移，22通过，无跳过 |
| 独立E2E | VERIFIED | 独立npm包9项通过、失败/跳过/flaky均0；覆盖五模块与Phase2A应用改进 |
| API与前端 | VERIFIED | 生成类型无漂移；TypeScript/Vite构建通过 |
| 实际依赖边界 | VERIFIED | 项目/求值引用、Compile项、解析包及源码import均通过 |
| 实际生产输出 | VERIFIED | publish DLL/deps.json与前端bundle source map来源检查通过，没有测试程序集/源码混入 |
| 边界反例 | VERIFIED | 临时副本中生产引用测试、生产NUnit包、C#测试import、前端fixture import均拒绝；恢复后通过 |
| 实际应用查询工具 | VERIFIED | 迁入测试区的QueryProbe执行成功；真实Store取50调查，临时库已清理。不作性能SLA |
| 业务/数据兼容 | VERIFIED | src与frontend/src相对基线无差异，包括三条EF迁移；旧数据/回执、版本/幂等/授权和草稿仍受原有检查保护 |
| 历史保留 | VERIFIED（本地对象） | 原分支指向63c5872，旧交付脚本与PDF对象存在；最终再核对远程引用 |
| 最终提交应用CI | NOT_RUN（提交前快照） | 本地验证已完成；必须观察最终推送SHA的application-ci，交接补充实际运行引用，不用早期运行替代 |

这些数量描述保留下来的检查，没有增加业务测试总量。E2E只经过公共接口；Unit与Integration没有彼此引用。可选QueryProbe不在默认CI运行。云/运维或PDF工具不参与构建。

## 责任审计与范围

生产四层、前端源码、应用迁移/身份/事务保留。运维和出版流水线、历史PDF/证据从新树退役，完整路径清单见RETIRED-FILES；当前分类见REPOSITORY-RESPONSIBILITY。普通测试结果留在忽略的TestResults/test-results或CI短期附件，不维护证据发行平台。

前端只移除Playwright开发依赖，现有其余锁定版本与integrity保持，锁地址统一官方registry；E2E有自己的包/锁文件。没有重写业务、执行旧基础设施实验、改动现有业务库或创建替代部署仓库。

## PARTIAL / BLOCKED / NOT_RUN

PARTIAL：教材源已收窄并重绑路径，深入讲解/插图/最终编辑仍是后续2B；账户恢复/MFA/会话治理、回执容量/清理、分页等既有应用限制仍存在，不宣称生产完备。

BLOCKED：当前没有需要所有者处理的阻断。

NOT_RUN：未重新生成PDF，未执行历史环境/运维实验，未执行上游模板全套测试；这些均不是当前DoD。最终提交CI在观察成功前不标VERIFIED。

[开发](DEVELOPMENT.md)、[独立测试与产物检查](TESTING.md)、[当前实验](EXPERIMENTS.md)、[2B清单](PUBLICATION-INVENTORY.md)给出复现与继续学习入口。最终交接应同时给出源SHA、匹配CI和当前工作区状态。
