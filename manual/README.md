# 出版

Markdown 在 chapters/，代码片段与测量在构建时从真实文件展开；Mermaid 本地渲染，不使用 CDN。字体优先 Microsoft YaHei，Linux 使用 Noto Sans CJK SC。字体和浏览器版本会改变分页，复现保证可构建与可检查，不保证 PDF 字节完全相同。

```powershell
uv venv work/venv --python 3.13
uv pip install --python work/venv/Scripts/python.exe -r manual/requirements.txt
cd manual
npm ci
cd ..
python tools/catalog.py
python tools/verify.py
node manual/tools/build.mjs
node manual/tools/build.mjs --report
work/venv/Scripts/python.exe manual/tools/pdfqa.py layout manual/dist/Enterprise-Full-Stack-Engineering.pdf evidence/qa/book-layout.json
work/venv/Scripts/python.exe manual/tools/pdfqa.py render manual/dist/Enterprise-Full-Stack-Engineering.pdf work/book-pages
```

Node publisher 从 frontend 的 Playwright 包加载，先安装 frontend 依赖。本机使用 Edge；CI 环境使用 Chromium，需要安装对应浏览器。Pandoc 必须在 PATH。可用 ECHOCASE_PYTHON 指定 Python，否则默认 work/venv。

两遍打印：第一次从 outline 顺序匹配所有章/节标题，填入目录；第二次重查页数与标题目的页，任何不匹配非零退出。插图加载和 Mermaid 渲染失败直接中止。layout 几何检查不能替代人工逐页视觉检查；人工记录保存在 evidence/qa/visual-review.json。
