# 企业级 .NET 全栈软件工程

[阅读模板修订版 PDF](dist/Enterprise-Full-Stack-Engineering-Template-First.pdf)

**Template-First Revised Edition · 2026-11-13**。新版源码固定于接受工程提交 `9f68721e18f15ae603e6502fa46b8fa78f9df55c`，以真正生成的 Jason Taylor CleanArchitecture v10.8.0 为基础，解释请求管道、MediatR、NSwag、原有事务与浏览器草稿。它不随 main 后续出版提交漂移，也没有为配合教材改动应用。

[历史 107 页 PDF](dist/Enterprise-Full-Stack-Engineering.pdf) 独立保留。其来源仍为 `908811b95fb40cf14fa79b8eddf41796aa02cc04`，出版记录为 `bf9de37b9bd4d5cc2c227af2c857360e048b15d1`；PDF SHA-256 为 `dd00cbfb1cfeb58cea6f28e13c6ea0dd6d72df68bc4668ba6016f1c8edf66166`。旧版正文、清单、图源和 PDF 均未被新版覆盖。

## 阅读与来源

新版包含序言、20 个主要章节和概念附录。前六章连接需求、真实模板基础、领域、两层请求管道与生成客户端；中段解释 EF、兼容演进、MVCC、版本与回执；随后进入安全、React 确认缓存、草稿和图谱；最后讨论计划、反例、跨层需求与设计推理。

| 版本 | 正文清单 | 编辑源 | 输出 |
|---|---|---|---|
| 模板修订版 | [独立 manifest](editions/template-first/book.json) | [章节](editions/template-first/chapters/)、[新版图源](editions/template-first/figures/)、共用历史素材 | 独立 Template-First PDF |
| 历史版 | [原 book.json](book.json) | 原 chapters/、figures/ | 原 PDF 只读；重建写入忽略目录 |

源码框直接从不可变 Git 对象提取，保留准确路径、行号、摘要和链接。九组真实界面来自 2026-11-11 的历史运行 `63c5872`，没有冒称新截图；当前领域、协调服务、映射和 Store 与其一致，客户端和请求链则用新版源码解释。单机查询数据不是生产指标。

正文只由各版 manifest 的章节组成。reference/、工具、QA 清单、原始运行数据和出版脚本不进入读者正文。`{{code ...}}` 与 `{{figure ...}}` 在出版时解析。

## 出版维护与审校

- [新版出版说明](editions/template-first/reference/PUBLISHING.md)：版本选择、保护机制和最少构建路径。
- [源码对齐报告](editions/template-first/reference/SOURCE-ALIGNMENT.md)：全部章节、57 处旧摘录、44 张旧机制图及素材来源。
- [编辑与视觉验收](editions/template-first/reference/EDITORIAL-VISUAL-QA.md)：最终统计、逐页审查、修正与 A–H 验收。
- [编辑方法](editions/template-first/EDITORIAL-METHOD.md)：读者目标、机制图问题和源码教学映射。

本版只处理应用工程知识；没有新增云、部署或运维内容。运行应用与测试仍以 backend/docs/engineering/ 中的指南为准。
