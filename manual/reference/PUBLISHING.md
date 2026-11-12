# 教材维护说明（不进入正文）

正文范围只由 `manual/book.json` 决定。工具不扫描目录后自动装订参考报告。源码摘录使用当前路径和固定应用提交；UI 使用未改动历史 PNG；机制图由原创几何源生成 SVG。PDF 使用嵌入的本机 Microsoft YaHei / Consolas 字体，不将字体文件提交到仓库。

Windows 维护环境需要 Python、`tools/requirements.txt` 中的包和 Poppler。从仓库根目录的最少构建路径为：

```powershell
python manual/tools/prepare_assets.py
python manual/tools/draw_figures.py
python manual/tools/build_book.py
python manual/tools/verify_book.py
```

首次素材准备从保留的 Git 历史提取选定 PNG，并验证相关应用源码未漂移。完整原始观察只写入忽略的 `manual/build/`，不装订正文、不提交大 JSON。素材来源清单保留每张原始图片的哈希和历史位置。

出版器只折行源码，不修改其字符；准确行范围、摘要、图号与内容统计写入 `manual/build/publication-stats.json`。主输出固定在 `manual/dist/Enterprise-Full-Stack-Engineering.pdf`。审校用页面、联系图和数值检查也写 `manual/build/`，最终编辑结论保存在参考目录。

修改正文或几何之后需要重新生成 PDF 和页面，检查最新页的可读性、裁切、行号、标题、链接与书签。不能用旧渲染图证明新 PDF 没有版式缺陷。实际应用 CI 保持原有职责，不加入沉重出版流水线。
