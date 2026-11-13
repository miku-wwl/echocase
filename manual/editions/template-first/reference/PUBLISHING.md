# 双版本出版维护说明

本文件是维护资料，不进入教材。所有命令从仓库根目录执行，当前工作分支必须为 main。只在 manual/ 内维护出版资产；应用基线始终是 9f68721e18f15ae603e6502fa46b8fa78f9df55c。

## 依赖

Python 与 manual/tools/requirements.txt；Windows Microsoft YaHei（含粗体）、Consolas、Segoe UI Symbol；Poppler 的 pdftoppm。字体来自本机授权安装，仓库不重新分发字体文件。没有付费服务或云构建依赖。

```powershell
python -m pip install -r manual/tools/requirements.txt
python manual/tools/prepare_template_first.py
python manual/tools/draw_template_first.py
python manual/tools/build_book.py
python manual/tools/verify_book.py
python manual/tools/render_review.py
```

默认 manifest 是 manual/editions/template-first/book.json。prepare 校验工程文件和历史像素，补齐缺失源文件但不覆盖已编辑的新章节；draw 仅改新版图源及分类清单。更改章节和图源后重新构建、渲染并审查，不能用旧渲染图证明新 PDF。

## 固定来源与不可覆盖的历史

source_excerpts.extract 总是先 git show manifest 指定的不可变提交，不从移动 main 读取源内容。新版额外比较对应工作文件的完整内容，98 个选择器记录 blob、行范围和片段散列；最终只装订章节实际引用的选择。历史比较须在选择器中显式声明 commit 和标签，不能悄悄混入当前源码。

历史 book.json、chapters/ 和 figures/ 保持原样。需要重建历史正文时显式选择原清单：

```powershell
python manual/tools/build_book.py --manifest manual/book.json
python manual/tools/verify_book.py --manifest manual/book.json
```

它读取原固定 908811b 源码，写 manual/build/historical/Enterprise-Full-Stack-Engineering-Rebuilt.pdf。当前工作树已经迁移，不能要求它等于旧应用；这不关闭来源验证，所引片段仍直接从旧 Git 对象解析并逐项复核。出版器的排版改进可能改变重建布局，重建件不宣称字节等于历史发行件。

两个 manifest 的输出与 build 目录隔离。任何试图将重建输出指向原 manual/dist/Enterprise-Full-Stack-Engineering.pdf 的调用都会被拒绝；全部出版入口都验证其既定 SHA-256。原发行 PDF 才是不可变历史版，不重新生成它。

## 复现与检查

新版 PDF 使用 invariant 模式，在相同工具、字体和固定输入下验证重复构建 SHA 一致。跨平台字体或库差异不承诺字节级一致。来源与结构验证检查摘录、全部图中文字、图片摘要、目录、书签、内部目标、页码和文本安全区。工程 inventory 覆盖 backend/frontend/test/.github 的全部 128 个跟踪文件。

render_review 将每页转为 110 dpi PNG，并以每六页一张生成带页码联系图。页面、统计和原始观察只写入忽略的 manual/build/。联系图负责全书覆盖，重要图和疑似缺陷页还应打开完整页面。自动几何检查不能代替中文可读性与教学因果审查。

报告与图分类位于本 reference/，不会被自动装订。最终 GitHub 应用 CI 仍运行已有 26/27/9 测试与合同、构建、依赖隔离检查，未为教材增加或修改 CI。
