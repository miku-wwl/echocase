# 当前应用实验导航

当前应用实验使用APP编号，完整机制/源码/独立测试入口见[EXPERIMENTS](../reference/EXPERIMENTS.md)。编号是当前范围的新索引，不是把历史26项或原E01–E10重命名。

原E01–E09中的依赖、领域、迁移、并发、幂等、授权、React、SQL与维护性继续有效。原E10交付属于历史Phase2A，不再是当前完成条件。历史原始记录可从[基线](https://github.com/miku-wwl/echocase/tree/63c587277541b4e700258aad82de9b2ad0ba32f8/docs/experiments)恢复。

复现时先读测试指南，明确单元无需数据库、集成需要临时测试库权限、E2E需要运行的API/Vite。所有步骤观察实际返回值、版本、持久内容与失败边界，不以总测试数作为学习成绩。
