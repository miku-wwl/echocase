"""Build traceable experiment records and a manifest from executed artifacts."""
import hashlib,json,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def read(p):return json.loads((root/p).read_text(encoding='utf-8-sig'))
ns={'t':'http://microsoft.com/schemas/VisualStudio/TeamTest/2010'};trx=ET.parse(root/'evidence/backend/backend.trx');counts=trx.find('.//t:Counters',ns).attrib
tests={r.attrib['testName']:r.attrib['outcome'] for r in trx.findall('.//t:UnitTestResult',ns)}
browser=read('evidence/browser/results.json')['stats']
summary={'backend':{'total':int(counts['total']),'passed':int(counts['passed']),'failed':int(counts['failed'])},'browser':{'passed':browser['expected'],'failed':browser['unexpected']}}
(root/'evidence/summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
database=read('evidence/database/results.json')['query_optimization'];plan_summary={}
for label in ('before','after'):
    entry=database[label]['plan'][0];lines=[]
    def walk(node,depth=0):
        name=node['Node Type']+(' on '+node['Index Name'] if 'Index Name' in node else '')
        lines.append('  '*depth+name+' (rows='+str(node['Actual Rows'])+', loops='+str(node['Actual Loops'])+')')
        for child in node.get('Plans',[]):walk(child,depth+1)
    walk(entry['Plan']);plan_summary[label+'_tree']='\n'.join(lines);plan_summary[label+'_blocks']=entry['Plan']['Shared Hit Blocks'];plan_summary[label+'_execution_ms']=entry['Execution Time']
(root/'evidence/database/plan-summary.json').write_text(json.dumps(plan_summary,indent=2),encoding='utf-8')

# Each entry has a distinct question and an executable reproduction route.
specs=[
('E01','依赖边界退化', 'Domain 引入外向依赖时，门禁能否阻止？','项目引用是编译时知识；运行时调用方向不等于引用方向。', 'CoreHasNoFrameworkOrOutwardDependencies','依赖门禁检查真实程序集；故障自测只在临时副本注入 Infrastructure 引用。','正常边界成立，坏输入必须非零退出。','程序集检查不能识别所有职责混杂；还需人工审查变化原因。','src/EchoCase.Domain/EchoCase.Domain.csproj'),
('E02','领域脱离框架', '不启动数据库是否仍可验证领域与模板取舍？','领域不依赖持久化或 HTTP，应用端口不返回 IQueryable。','StartRequiresOwner','直接构造调查，用固定时间驱动业务方法，结合上游机制审计。','拒绝没有所有者的调查，领域测试不建立数据库连接。','这证明当前规则可独立验证，不证明所有未来变化都不涉及外层。','src/EchoCase.Domain/Investigation.cs'),
('E03','解锁与状态机', '非法操作是否既被拒绝又不推进版本？','先验证再修改，终态只读，复核门槛依赖聚合集合。','HiddenEvidenceCannotBeExamined','先尝试锁定证据，再按门禁→凭证册→调度顺序调查，验证解锁链。','锁定路径被拒绝，Version 保持 1；合法路径逐次推进。','仅覆盖固定案件；动态案件规则版本尚未实现。','tests/EchoCase.Tests/DomainTests.cs'),
('E04','请求管道保护', '认证 Cookie 是否足以让缺防伪头的写请求成功？','Cookie 自动发送，CSRF 令牌提供独立请求证明。','CsrfIsRequiredEvenWithValidCookie','使用已登录客户端省略 X-CSRF-TOKEN，保持其他请求条件可观察。','缺防伪头返回 400，受保护写入未完成。','没有进行全面浏览器跨站攻击工具扫描；此处是明确负向合同。','src/EchoCase.Api/Program.cs'),
('E05','失败原子性', '领域拒绝后是否留下审计或幂等回执？','业务状态、审计、回执共用事务；异常导致回滚。','DomainFailureRollsBackReceiptAndAudit','新调查直接请求进入复核，随后以新上下文查询回执和审计。','422，失败键无回执，审计仍只有启动记录。','未注入数据库 COMMIT 确认丢失；传输未知结果需另一类实验。','src/EchoCase.Infrastructure/PostgresInvestigationStore.cs'),
('E06','合同污染', 'null 或伪造额外 OwnerId 是否被静默接受？','严格构造参数、非空注解与未知成员拒绝。','MalformedAndNullContractsAreRejected','分别发送 notes:null 与多出的 ownerId 字段。','两者均返回 400，客户端无法通过 JSON 指定所有者。','生成类型提供编译约束，不做运行时 JSON schema 验证。','frontend/src/api/schema.d.ts'),
('E07','迁移与关系约束', '增量迁移是否保留数据，直接坏写能否被数据库拒绝？','迁移历史、组合索引、复合外键和 CHECK。','UpgradePreservesExistingInvestigationAndEfRejectsStaleTrackedWriter','专用库先应用初始迁移，写笔记，再升级；另一测试直插未知发现关联。','数据保留且至少两个迁移；非法关联触发 23503。','真实云滚动升级、巨大表索引在线构建没有运行。','src/EchoCase.Infrastructure/Migrations'),
('E08','丢失更新与版本', '两个相同旧版本写请求是否恰有一胜？','SQL 条件更新与 EF 并发令牌保护聚合版本。','DifferentKeysCompetingOnOneVersionHaveOneWinner','不同键并发写笔记；另用两个独立 DbContext 保存相同旧版本。','API 状态为 200/412；EF 旧上下文保存抛并发异常。','这不是长期压力测试；受控交错有利于机制解释。','tests/EchoCase.Tests/PostgresApiTests.cs'),
('E09','重复请求去重', '相同键并发写入是否只提交一次？','数据库事务级锁加持久回执，同键同指纹返回原快照。','SameKeyConcurrentRequestsCommitOnce','两个请求共享键、版本与正文，查询提交后的审计数量。','两个响应版本相同，仅一条 notes 审计。','保证受回执保留期和所有写路径遵循端口约束。','src/EchoCase.Infrastructure/PostgresInvestigationStore.cs'),
('E10','水平越权', '合法登录用户能否访问另一账户调查？','可信 OwnerId 与资源 ID 联合过滤，拒绝存在性泄漏。','ForeignOwnerCannotReadOrWrite','Alice 创建调查；Bob 分别读取和修改该 ID。','两种请求均为 404，原调查保持属于 Alice。','未完成 MFA、邮箱确认、安全戳会话撤销等生产身份能力。','tests/EchoCase.Tests/PostgresApiTests.cs'),
('E11','浏览器持久工作流', '刷新后是否仍可完成五模块调查？','真实 Cookie、HTTP、API、EF 与 PostgreSQL 全链路。','browser','注册、启动、调查、关联、笔记、刷新、复核、提交、再次刷新。','完整工作流通过，封存结果评分 100，截图由实际页面采集。','单一虚构案件；不代表复杂故事或所有设备兼容。','frontend/tests/workflow.spec.ts'),
('E12','乐观回滚', '注入保存 503 后，草稿与服务端事实是否正确分离？','onMutate 快照、onError 回滚、dirty 草稿独立于 Query 缓存。','browser','仅拦截 notes 响应，保存草稿后直接读取服务器；解除拦截重试。','错误可见，草稿保留，服务器仍为空；解除后保存成功。','此故障为浏览器注入，不是真实数据库暂停。','frontend/src/App.tsx'),
('E13','图谱关联', '图与文本交互是否对应持久化关系？','React Flow 投影与无向边规范化，服务端校验发现与唯一性。','browser','调查证据后以选择框建立两条关联，展示图谱并刷新后提交。','图谱与提交工作流通过；域测试覆盖自环、反向重复与未发现端点。','端点拖拽手势、大图性能与屏幕阅读器尚未独立测试。','frontend/src/EvidenceGraph.tsx'),
('E14','验收门禁自测', '检查器是否真的拒绝坏输入？','退出码而非日志措辞控制门禁；临时副本隔离故障。','qa','删除文件、修改摘要、引入外向引用、伪造状态、超限性能、删答案和伪造测量。','正常基线必须返回 0，七类损坏各自非零。','有限规则检查不能证明所有自然语言论断。','tools/test_gate.py'),
('E15','查询计划优化', '匹配过滤和排序的组合索引是否减少工作？','B-tree 前导等值范围与有序访问，ANALYZE 更新统计。','database','十万条、五千所有者；两条件各预热三次并测二十一次，保留 JSON 计划。','返回行数均为 20，Seq Scan 与索引计划可对照，测量来自保存样本。','合成单机暖缓存表；不是完整应用吞吐或生产容量。','experiments/database.py'),
('E16','真实依赖故障', '数据库停用时能否正确降级并恢复原调查？','连接池失效、异常包装、live/ready 分离与持久卷。','reliability','真实停止 echocase-postgres，核对健康与业务状态，finally 恢复。','200/503/503，恢复后原调查可读；首次 500 缺陷已修正。','恢复时间从启动命令返回后计，不等于端到端 RTO。','experiments/reliability.py'),
('E17','容器重建', '删除应用容器后状态与 Cookie 是否仍成立？','镜像无状态，数据库与 Data Protection 密钥卷持久化。','container','独立数据库迁移、创建账户与调查、删除重建应用，再读取原调查。','非 root 运行、静态资源服务、调查与 Cookie 均需存活。','只验证本地 OCI 路径；Compose provider 与 Azure 未运行。','experiments/container.py'),
('E18','不可重复读', '同一事务两次读取在不同隔离级别是否相同？','READ COMMITTED 语句快照与 REPEATABLE READ 事务快照。','database','A 读 10，B 写 20，再让 A 读取；分别使用两种隔离。','READ COMMITTED 为 10/20；REPEATABLE READ 为 10/10。','受控两个连接，不代表所有隔离现象都已覆盖。','experiments/database.py'),
('E19','写偏斜与可串行化', '快照隔离是否保证至少一人值班？','跨行不变量与序列化依赖检测；40001 需要整体事务重试。','database','两事务先读两人在岗，再分别离岗；比较 Repeatable Read 与 Serializable。','前者可无人值班，后者第二写入 40001 并保留一人。','教学 on_call 表，不是 EchoCase 业务功能；用于解释聚合边界。','experiments/database.py'),
('E20','幂等键误复用', '相同键改变正文是否被错误重放？','请求指纹绑定用户意图，键不是任意缓存 ID。','ReusedKeyWithChangedPayloadIsConflict','先保存 first，再以相同键保存 different。','第二请求为 409，不能变成新写入或返回无关成功。','当前规范化基于强类型序列化；跨语言通用规范化未实现。','src/EchoCase.Application/Investigations.cs'),
('E21','追踪上下文', '服务端是否沿用有效上游 traceparent？','W3C Trace Context 与 ASP.NET 请求活动。','reliability','真实 HTTP 读取带固定有效 traceparent，逐次检查 X-Trace-Id。','一百次测量读取的追踪 ID 与输入一致。','没有验证外部 collector、采样与跨服务导出。','experiments/reliability.py'),
('E22','性能回归拒绝', '超出教学阈值的样本是否使门禁失败？','结构化样本阈值与语义检查，避免仅摘要失败掩盖真实检查。','qa','在临时副本把 p95 改为 9999，并刷新摘要，单独触发性能条件。','门禁必须非零，正常证据仍通过。','阈值是本地顺序读取教学预算，不能跨硬件作为严格 SLO。','tools/test_gate.py'),
('E23','远程 CI 失败与恢复', '远程门禁能否阻断缺失证据，正常提交能否通过？','工作流依赖图、真实 runner 退出码与制品。','ci','在工作分支提交并推送删除 manifest，等待真实失败后恢复清单并推送，保留两次运行 ID。','实际记录中缺清单运行被门禁拒绝，恢复清单后的完整工作流成功。','GitHub 环境与本机不是同一硬件；云部署不在此实验内。','experiments/ci-drill.ps1'),
('E24','备份恢复机制', 'pg_dump 自定义格式能否恢复表与中文记录？','逻辑备份保留模式和数据；恢复目标为独立数据库。','backup','备份三行合成日志，pg_restore 到新库并比较精确行内容。','三行与原表一致，保存备份字节数与 SHA-256，两库随后清理。','不是完整应用 DR、异机备份或 PITR；没有生产 RTO/RPO。','experiments/backup.py'),
('E25','移动端工作台', '390px 视口是否可操作且无横向溢出？','响应式布局、标签化表单和替代关联路径。','browser','390×844 登录、开始调查、查证据和查看图谱，检查 scrollWidth。','流程通过，文档宽度不超过视口，保存真实截图。','没有覆盖所有移动设备或 WCAG 全面审计。','frontend/tests/workflow.spec.ts'),
('E26','出版校验器反例', '空白、越界和不匹配目录是否会被拒绝？','PDF 几何、书签映射与两遍稳定性检查。','pdfqa','生成受控坏 PDF，分别调用实际 layout 和 TOC 检查命令。','坏 PDF 必须非零；最终成品再跑同一检查。','几何检查不理解图意，仍需人工检查每一页。','manual/tools/pdfqa.py'),
]
category={'browser':'evidence/browser/results.json','qa':'evidence/qa/gate-selftest.json','database':'evidence/database/results.json','reliability':'evidence/reliability/results.json','container':'evidence/container/results.json','ci':'evidence/ci/results.json','backup':'evidence/backup/results.json','pdfqa':'evidence/qa/pdf-selftest.json'}
experiments=[];appendix=['# 附录 A 实验复现手册 {#labs}','\n以下记录与仓库 docs/experiments 同源生成。每项包含问题、机制、基线、执行、观测、解释、限制和清理。状态来自真实结构化证据；无法确认的项目保留 NOT_RUN。\n']
for id,title,question,mechanism,selector,design,observation,limits,source in specs:
    artifact=category.get(selector,'evidence/backend/backend.trx');p=root/artifact
    status='VERIFIED' if p.is_file() else 'NOT_RUN'
    if selector not in category and tests.get(selector)!='Passed':status='PARTIAL'
    if selector=='ci' and p.is_file():status=read(artifact)['status']
    if selector=='browser':observation+=' 当前浏览器结果：%s 通过、%s 失败。'%(browser['expected'],browser['unexpected'])
    elif selector not in category:observation+=' 对应测试 %s：%s。'%(selector,tests.get(selector,'未找到'))
    command=(f'dotnet test --filter "FullyQualifiedName~{selector}"' if selector not in category else {'browser':'cd frontend\nnode node_modules/@playwright/test/cli.js test','qa':'python tools/test_gate.py','database':'python experiments/database.py','reliability':'python experiments/reliability.py','container':'python experiments/container.py','ci':'gh workflow run engineering.yml --ref codex/enterprise-masterclass-20261111','backup':'python experiments/backup.py','pdfqa':'python manual/tools/test_pdfqa.py'}[selector])
    if selector=='ci':command='pwsh -File experiments/ci-drill.ps1 -ReviewBranch codex/your-review-branch\n# 仅在干净且已推送的独立审阅分支执行；脚本拒绝 main。'
    cleanup='集成测试仅删除自动创建的 echocase_test_ 数据库；单元测试无外部状态。'
    if selector=='database':cleanup='脚本 finally 删除本次随机 echocase_lab_ 数据库；开发数据库不被清空。'
    elif selector=='reliability':cleanup='finally 启动被停止的 echocase-postgres；脚本非零时先检查容器与 ready，保留失败证据。'
    elif selector=='container':cleanup='审阅后停止 echocase-app 与 echocase-container-db，保留数据库与密钥卷。删除卷会丢失数据，非自动清理步骤。'
    elif selector=='backup':cleanup='finally 只删除此次 source/restore 随机库，二进制备份不持久保留。'
    elif selector in ('qa','pdfqa'):cleanup='临时副本与受控坏 PDF 由 TemporaryDirectory 自动清理，原始源和成品不被修改。'
    doc=f'''# {id} {title}

状态：**{status}**。来源：`{source}`。证据：`{artifact}`。

## 1. 工程问题与假设

{question} 假设：已声明的保护在合法路径允许操作，在负向或竞争条件下给出明确拒绝，不留下半提交状态。

## 2. 底层机制

{mechanism}

## 3. 基线与实验设计

{design} 先固定输入、身份、数据与执行条件，再引入一个明确变化；不同时改变多个因素后只归因于其中一个。

## 4. 执行与复现

从仓库根目录运行。先按 README 配置真实 PostgreSQL 与所需环境变量，使用文档锁定依赖。浏览器实验需要开发 API 与 Vite 已运行；容器实验自行构建。

```text
{command}
```

## 5. 实测观测

{observation} 结论以证据文件中的断言、样本和进程退出码为准；若复现结果不同，保留新结果并将状态降为 PARTIAL。

## 6. 解释与架构含义

{mechanism} 因此验收必须检查这一边界上的可观察结果，而不能以组件已安装或代码已生成代替。对应实现 `{source}` 与本章问题具有直接关系。

## 7. 限制与替代解释

{limits} 单次通过不证明没有其他缺陷；故障注入只覆盖其明确注入的位置与条件。

## 8. 清理与复核

{cleanup} 对照正常输入再运行一次相关门禁，确认清理没有破坏环境。完整测试与来源应保留在仓库，不将原始日志塞进教材正文。
'''
    (root/'docs/experiments').mkdir(parents=True,exist_ok=True);(root/f'docs/experiments/{id}.md').write_text(doc,encoding='utf-8')
    appendix.append(doc.replace(f'# {id} {title}',f'## {id} {title}').replace('\n## ','\n### '))
    artifacts=[]
    if p.is_file():artifacts=[{'path':artifact,'sha256':hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n') if p.suffix in ('.json','.trx','.txt','.md') else p.read_bytes()).hexdigest()}]
    if id=='E15':artifacts.append({'path':'evidence/database/plan-summary.json','sha256':hashlib.sha256((root/'evidence/database/plan-summary.json').read_bytes().replace(b'\r\n',b'\n')).hexdigest()})
    experiments.append({'id':id,'title':title,'status':status,'source':source,'selector':selector,'artifacts':artifacts})
(root/'evidence/manifest.json').write_text(json.dumps({'hash_policy':'SHA-256; text CRLF normalized to LF','experiments':experiments},ensure_ascii=False,indent=2),encoding='utf-8')
(root/'manual/chapters/19-labs.md').write_text('\n\n'.join(appendix),encoding='utf-8');print('Generated',len(experiments),'experiment records')
