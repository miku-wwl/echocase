> 历史记录：本文件对应已验证应用化基线3d192a3，文中旧路径记录当时布局；当前布局见根README。

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
| 历史保留 | VERIFIED | 本地与远程原分支均为63c5872，旧脚本/PDF对象存在；远程main仍为3395678 |
| 应用CI工程检查点 | VERIFIED | [42986911612](https://github.com/miku-wwl/echocase/actions/runs/42986911612)在ba2f1dd完整通过；26单元/22集成/9浏览器、合同与实际产物隔离均通过。验收材料提交后再核对最终分支头CI |

这些数量描述保留下来的检查，没有增加业务测试总量。E2E只经过公共接口；Unit与Integration没有彼此引用。可选QueryProbe不在默认CI运行。云/运维或PDF工具不参与构建。

## 责任审计与范围

生产四层、前端源码、应用迁移/身份/事务保留。运维和出版流水线、历史PDF/证据从新树退役，完整路径清单见RETIRED-FILES；当前分类见REPOSITORY-RESPONSIBILITY。普通测试结果留在忽略的TestResults/test-results或CI短期附件，不维护证据发行平台。

前端只移除Playwright开发依赖，现有其余锁定版本与integrity保持，锁地址统一官方registry；E2E有自己的包/锁文件。没有重写业务、执行旧基础设施实验、改动现有业务库或创建替代部署仓库。

## PARTIAL / BLOCKED / NOT_RUN

PARTIAL：教材源已收窄并重绑路径，深入讲解/插图/最终编辑仍是后续2B；账户恢复/MFA/会话治理、回执容量/清理、分页等既有应用限制仍存在，不宣称生产完备。

BLOCKED：当前没有需要所有者处理的阻断。

NOT_RUN：未重新生成PDF，未执行历史环境/运维实验，未执行上游模板全套测试；这些均不是当前DoD。最终分支头CI仍须按匹配SHA单独核验。

[开发](DEVELOPMENT.md)、[独立测试与产物检查](TESTING.md)、[当前实验](../../../manual/reference/EXPERIMENTS.md)、[2B清单](../../../manual/reference/PUBLICATION-INVENTORY.md)给出复现与继续学习入口。最终交接应同时给出源SHA、匹配CI和当前工作区状态。


## 交接检查点

工程源检查点为ba2f1dd68ff7afdd94a2a4ec6064a2d50bf0983f；对应application-ci已通过，下载实际TRX和浏览器JSON再次核对。当前只保留这一条工作流，所有旧部署/出版步骤已退役。最终交接另列验收材料提交的完整SHA与匹配绿灯，不用此检查点代替最终提交结果。

旧的忽略构建缓存已可逆移到work/application-restructure/retired-generated，避免源码根目录残留旧experiments/tools和混合测试目录；没有删除用户业务数据。
