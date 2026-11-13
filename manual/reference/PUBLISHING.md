# 历史出版维护说明

此文件原先描述 2026-11-12 的单版本出版过程。2026-11-13 起，维护入口已改为[双版本出版说明](../editions/template-first/reference/PUBLISHING.md)。默认构建新版；历史重建必须显式传入 `--manifest manual/book.json`。

原 manifest、chapters、figures 和已发行 PDF 保持不变。历史正文固定 908811b，重建输出位于忽略的 manual/build/historical/，不再允许写回原 dist/Enterprise-Full-Stack-Engineering.pdf。其原发行 SHA-256 始终校验为 dd00cbfb1cfeb58cea6f28e13c6ea0dd6d72df68bc4668ba6016f1c8edf66166。

不要在迁移后的工程上运行旧 prepare_assets.py 或 draw_figures.py 来准备新版。新版有独立准备、图源、选择器与统计，旧源码直接从不可变 Git 对象验证；历史工作区不必也不可能等于当前应用。当前出版器排版更新后的历史重建件，不宣称与旧发行 PDF 字节相同。
