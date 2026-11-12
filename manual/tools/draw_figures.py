"""Original vector illustrations. Geometry is independent from application UI pixels."""
from pathlib import Path
from html import escape
import json, statistics, re

M = Path(__file__).resolve().parents[1]
OUT = M/'figures'/'mechanisms'
CAT = {}
INK='#173c44'; TEAL='#24766e'; GOLD='#a6732d'; RED='#af543c'; MUTED='#627477'
PALE='#edf4f2'; WARM='#f8f2e7'; LINE='#c8d7d3'

def units(s): return sum(1 if ord(c)>255 else .55 for c in s)
def wrap(s,n):
    lines=[]; line=''
    for c in re.findall(r'[A-Za-z0-9_.:-]+|[^A-Za-z0-9_.:-]',s):
        if c=='\n' or units(line+c)>n:
            if line.strip():lines.append(line.rstrip())
            line='' if c=='\n' else c.lstrip()
        else: line+=c
    if line: lines.append(line)
    return lines

class SVG:
    def __init__(self,h=430):
        self.h=h; self.p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{h}" viewBox="0 0 960 {h}">',
          '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#627477"/></marker></defs>',
          f'<rect width="960" height="{h}" rx="14" fill="#f8faf9"/>']
    def text(self,x,y,s,size=22,color=INK,bold=False,anchor='start'):
        self.p.append(f'<text x="{x}" y="{y}" font-family="BookBold" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(s)}</text>' if bold else
                      f'<text x="{x}" y="{y}" font-family="Book" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(s)}</text>')
    def rect(self,x,y,w,h,fill=PALE,stroke=LINE):
        self.p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}"/>')
    def line(self,x1,y1,x2,y2,color=MUTED,arrow=False,dash=False):
        self.p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2"'+(' marker-end="url(#arrow)"' if arrow else '')+(' stroke-dasharray="7 6"' if dash else '')+'/>')
    def box(self,x,y,w,h,title,body,fill=PALE):
        self.rect(x,y,w,h,fill); self.text(x+18,y+35,title,23,bold=True)
        lines=[line for item in body for line in wrap(item,(w-36)/20)]
        leading=min(30,(h-66)/max(len(lines)-1,1))
        size=min(20,leading*.83)
        if size<17: raise ValueError(f'Box overflow: {title}: {len(lines)} lines in {h}')
        yy=y+64
        for line in lines:
            self.text(x+18,yy,line,size); yy+=leading
    def save(self,id,caption):
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/f'{id}.svg').write_text('\n'.join(self.p+['</svg>']),encoding='utf-8')
        CAT[id]=dict(type='svg',file=f'figures/mechanisms/{id}.svg',caption=caption)

def columns(id,title,items,caption,h=400):
    n=len(items); w=(904-(n-1)*20)/n
    lineCount=max(sum(len(wrap(item,(w-36)/20)) for item in body) for _,body in items)
    boxHeight=min(h-100,max(150,84+(lineCount-1)*30));h=boxHeight+100
    s=SVG(h); s.text(28,42,title,26,bold=True)
    for i,(head,body) in enumerate(items): s.box(28+i*(w+20),70,w,boxHeight,head,body,WARM if i==n-1 else PALE)
    s.save(id,caption)

def flow(id,title,nodes,caption,notes=None,connect=True):
    s=SVG(340 if notes else 270);s.text(28,42,title,26,bold=True)
    n=len(nodes);gap=30;w=(904-(n-1)*gap)/n
    for i,(head,body) in enumerate(nodes):
        x=28+i*(w+gap);s.box(x,78,w,150,head,body)
        if connect and i<n-1:s.line(x+w+2,153,x+w+gap-5,153,arrow=True)
    if notes:s.text(30,287,notes,21,color=MUTED)
    s.save(id,caption)

def lanes(id,title,actors,events,caption,foot='时间向右；编号表示发生顺序，不表示耗时比例。'):
    h=118+len(actors)*118+60;s=SVG(h);s.text(28,40,title,26,bold=True)
    for i,a in enumerate(actors):
        y=90+i*118;s.text(25,y+36,a,21,bold=True);s.line(165,y+50,928,y+50,color=LINE)
    for lane,col,label,tone in events:
        x=180+col*185;y=78+lane*118
        s.rect(x,y,172,90,WARM if tone else PALE)
        for k,line in enumerate(wrap(label,7.5)):
            s.text(x+12,y+26+k*25,line,19,color=RED if tone else INK)
    s.line(174,h-50,924,h-50,arrow=True);s.text(28,h-15,foot,18,color=MUTED);s.save(id,caption)

def tracking():
    s=SVG(520);s.text(28,42,'同一对象，三个观察时刻',26,bold=True)
    heads=['观察点','根 Investigation','子 EvidenceLink'];xs=[28,230,580];ws=[190,338,350]
    rows=[('刚加载','Unchanged\nOriginal Version = 4','Unchanged\nOriginal Kind = Corroborates'),
          ('领域方法返回','CLR Version = 5\n状态尚未扫描','CLR Kind = Contradicts\n解释、时间已赋值'),
          ('DetectChanges 后','Modified\nUpdatedAt、Version','Modified\nKind、Rationale、RevisedAt')]
    for j,h in enumerate(heads):s.text(xs[j]+12,90,h,21,bold=True)
    for i,row in enumerate(rows):
        y=112+i*112
        for j,v in enumerate(row):
            s.rect(xs[j],y,ws[j],100,WARM if i==2 else PALE)
            for k,t in enumerate(v.split('\n')):s.text(xs[j]+12,y+35+k*29,t,19)
    s.text(30,490,'真实记录：保存后 Version = 5；旧版本对子实体的修改随失败事务回滚。',20,color=MUTED)
    s.save('ef-tracking','变更检测把 CLR 属性差异转为 EF 状态；实际记录保留了扫描前后的区别。')

def tuple_versions():
    s=SVG(495);s.text(28,42,'MVCC 可见性与应用版本属于不同层次',26,bold=True)
    s.box(28,80,410,154,'旧物理行版本',['业务 Version = 4','xmin = T0；xmax = T1（示意）'])
    s.box(518,80,410,154,'新物理行版本',['业务 Version = 5','xmin = T1；T1 提交后可见'],WARM)
    s.line(442,158,510,158,arrow=True);s.text(480,129,'更新',19,anchor='middle')
    s.box(28,277,410,162,'快照 S0：T1 尚未提交',['读取旧版本 4','看不到 T1 的未提交版本'])
    s.box(518,277,410,162,'快照 S1：T1 已提交',['新的 Read Committed 语句读到 5','旧快照的规则不会被改写'],WARM)
    s.line(232,238,232,267,arrow=True);s.line(720,238,720,267,arrow=True)
    s.text(30,478,'T0 / T1 是概念事务标识；本图没有声称采集到这些 xmin / xmax 值。',19,color=MUTED)
    s.save('mvcc-tuples','行版本解释“读到哪个事实”；应用 Version 解释“此次写入基于哪个事实”。')

def aggregate():
    s=SVG(510);s.text(28,42,'聚合边界：一次业务修改只有一个版本',26,bold=True)
    s.rect(30,66,900,385,fill='#ffffff')
    s.box(270,85,420,125,'Investigation · 聚合根',['Owner / Status / Version / Notes'])
    s.box(60,275,385,133,'Discovery · 已调查证据',['复合身份：调查 + 证据','只由根的 Examine 增加'])
    s.box(515,275,385,133,'EvidenceLink · 证据关系',['稳定 Guid；规范化端点','只能由根建立、删除、修订'])
    s.line(385,212,252,270,arrow=True);s.line(575,212,706,270,arrow=True)
    s.text(480,483,'修改子对象 → 根推进 Version → 同一数据库事务',22,anchor='middle',color=TEAL)
    s.save('aggregate','聚合不是数据库表的别名；根负责把跨成员规则组织成一次业务决定。')

def states():
    s=SVG(370);s.text(28,42,'调查状态及允许的决定',26,bold=True)
    for x,title,body in [(30,'Active',['调查、笔记、关联','可修改']), (345,'Reviewing',['复核证据和结论','暂停编辑']), (660,'Submitted',['结论与评分封存','终态，只读'])]:s.box(x,105,270,170,title,body)
    s.line(302,155,338,155,arrow=True);s.line(617,155,653,155,arrow=True)
    s.text(329,91,'Review',18,anchor='middle');s.text(646,91,'Submit',18,anchor='middle')
    s.line(479,290,167,290,arrow=True);s.text(318,321,'Resume：返回调查',21,anchor='middle')
    s.save('domain-states','复核需要至少三条已调查证据和两条关联；提交还必须满足支持证据与说明规则。')

def architecture():
    s=SVG(430);s.text(28,42,'编译依赖与运行调用，分别阅读',26,bold=True)
    s.box(28,82,260,120,'API',['解析协议、身份','组装具体实现'])
    s.box(350,82,260,120,'Application',['用例、DTO','IInvestigationStore'])
    s.box(672,82,260,120,'Domain',['Investigation','不依赖框架'])
    s.line(294,145,342,145,arrow=True);s.line(616,145,664,145,arrow=True)
    s.box(350,270,360,117,'Infrastructure',['Postgres Store + EF','Identity / migrations'])
    s.line(482,265,482,211,arrow=True);s.line(712,320,800,210,arrow=True)
    s.line(156,206,156,329);s.line(156,329,340,329,arrow=True)
    s.text(35,370,'组合根引用并注册实现',17,color=MUTED)
    s.text(30,411,'图中选择关键项目引用；运行时 Application 通过端口调用具体 Store。',19,color=MUTED)
    s.save('architecture','依赖倒置让应用层拥有端口；数据库实现依赖端口定义，而非反过来。')

def request_pipeline():
    s=SVG(620);s.text(28,42,'PUT 修订关联如何穿过请求管道',26,bold=True)
    names=[('① 外围中间件','安全头、TraceId、计时；包住后续异常'),('② Routing','选中端点，获得授权与限流元数据'),('③ Authentication','Cookie → ClaimsPrincipal'),('④ RateLimiter / Authorization','先有可信身份，再按身份分区；检查授权'),('⑤ 防伪校验','写 API 必须有 Cookie / Header 令牌对'),('⑥ 端点绑定与调用','严格 JSON → If-Match / Key → Application')]
    for i,(head,sub) in enumerate(names):
        y=70+i*79;s.rect(28,y,822,67,PALE if i%2==0 else '#ffffff');s.text(44,y+27,head,21,bold=True);s.text(44,y+53,sub,19)
        if i<5:s.line(874,y+25,874,y+92,arrow=True)
    s.text(30,590,'响应、异常沿调用栈返回外围；响应已经开始后，不能重新写完整错误正文。',20,color=RED)
    s.save('request-pipeline','此图按 Program.cs 的真实顺序绘制；授权短路时端点不会被执行。')

def plan_chart(data):
    s=SVG(430);s.text(28,42,'相同业务查询，索引改变取得前 50 个根的成本',26,bold=True)
    labels=[('无 owner 索引','withoutComposite'),('只有 OwnerId','ownerOnly'),('OwnerId + UpdatedAt DESC','withComposite')]
    for i,(label,key) in enumerate(labels):
        vals=data['plans'][key]['executionMs'];med=statistics.median(vals);y=94+i*91
        s.text(30,y+22,label,20);x=360;w=med/5.5*480
        s.rect(x,y,w,32,TEAL if i==2 else '#9eafaa',stroke='none');s.text(x+w+13,y+23,f'{med:.3f} ms',21,bold=True)
        s.text(x,y+61,'7 次暖缓存观测的中位数',18,color=MUTED)
    s.text(30,405,'30,000 根 / 100 所有者；单机固定顺序；这是数据库执行时间，不是 API 延迟。',19,color=MUTED)
    s.save('query-cost','实际 Store.ListAsync 的参数化 SQL；复合索引减少根选择工作，连接仍有自己的成本。')

def plans():
    columns('query-plans','只画与决策有关的计划分支',[
      ('无索引',['Seq Scan：30,000 行','筛掉 29,700 行','top-N Sort：取 50 根']),
      ('OwnerId 索引',['Bitmap Heap Scan','命中该 owner 的 300 根','仍需按 UpdatedAt 排序']),
      ('复合索引',['Index Scan 按时间有序','Limit 提前停止：50 根','随后连接子表、组装对象'])],
      '代表性真实计划的简化结构；根选择分支消除排序，不意味着整个查询再无排序。',h=430)

def keys():
    s=SVG(435);s.text(28,42,'两个坐标决定一次写入的身份',26,bold=True)
    s.box(28,82,425,228,'Version：事实的坐标',['“我看过哪个资源版本？”','不同意图可能基于同一个版本。','过期 → 412，交给用户重新决定。'])
    s.box(507,82,425,228,'Idempotency-Key：意图的坐标',['“这是不是同一次尝试？”','网络重试必须保留原键和请求。','同键异指纹 → 409，拒绝改写意图。'],WARM)
    s.text(30,361,'旧回执确认过去的提交；当前 GET 描述现在的资源。',24,color=TEAL,bold=True)
    s.text(30,405,'重试：原 Key + 原 Version + 原 Body；新决定：新 Key + 重新确认的 Version。',20,color=MUTED)
    s.save('intent-coordinates','条件写入和幂等分别解决丢失更新与不确定重试；它们不能互相替代。')

def state_owners():
    columns('state-owners','同一屏幕上的四种状态，不应混成一个对象',[
      ('确认事实',['Query cache','服务器返回的 Session','只接受不倒退的版本']),
      ('用户意图',['draft + baseline','输入代次 revision','保留未保存内容']),
      ('交互与呈现',['tab / selected / nodes','pending 操作快照','节点位置不写入数据库'])],
      'React 负责重绘，Query 负责服务器状态生命周期，草稿钩子负责输入语义。',h=420)

def graph():
    s=SVG(405);s.text(28,42,'业务关系是无向的，控件连接手势带有方向',26,bold=True)
    s.box(35,92,300,115,'access-log',['证据节点 · id 稳定'])
    s.box(625,92,300,115,'badge-ledger',['证据节点 · id 稳定'])
    s.line(338,151,622,151,color=RED);s.text(480,128,'Contradicts',21,color=RED,anchor='middle')
    s.box(120,270,720,90,'同一条 EvidenceLink',['Guid 不变；端点不变；修订 Kind / Rationale / RevisedAt'],WARM)
    s.text(30,392,'拖动只修改 Node.position；修订类型必须穿过命令、根版本与事务。',20,color=MUTED)
    s.save('graph-semantics','source / target 是技术字段；领域按 ordinal 规范端点，避免 A-B 与 B-A 重复。')

def main():
    data=json.loads((M/'build/selected-observations.json').read_text(encoding='utf-8'))
    flow('business-loop','五个模块围绕同一调查闭环',[
      ('案件',['选择固定案件','建立个人调查']),('证据',['解锁与调查','获取正文']),('关联',['连接事实','修订解释']),('进度',['笔记、复核','返回调查']),('结论',['支持证据','提交并封存'])],
      '模块划分说明用户任务；一致性边界仍是调查聚合。')
    architecture();aggregate();states();request_pipeline();tracking();tuple_versions();keys();state_owners();graph();plans();plan_chart(data)
    columns('requirements','把一句功能要求拆成可判断的边界',[
      ('意图',['调查员希望修订关系','保留端点和稳定身份','写明判断改变的理由']),
      ('前提',['当前用户拥有调查','状态为 Active','基于已读取的版本']),
      ('结果',['根版本只前进一次','关系、审计、回执同提交','旧窗口得到可解释的拒绝'])],
      '验收条件应描述事实与后果，按钮存在本身不能证明需求成立。',h=430)
    columns('template-tradeoffs','固定模板比较：机制与当前需要',[
      ('上游请求管道',['MediatR + 多种 Behavior','ApplicationDbContext 端口','SavingChanges 拦截器']),
      ('EchoCase 显式路径',['Service 方法 → Write 端口','领域根表达业务规则','Store 组织本地事务']),
      ('改变选择的条件',['用例数量与横切逻辑增长','跨聚合流程或外部通知','需可靠交付时再设计 outbox'])],
      '比较固定提交中的机制；不从目录数量推导架构质量。',h=440)
    flow('usecase','一个命令有四种不同职责',[
      ('API',['身份、合同','版本与键']),('Service',['意图命名','指纹、时间']),('Aggregate',['业务允许吗','决定新状态']),('Store',['加载、提交','并发、回执'])],
      '逻辑 CQRS 分离读写意图，读写仍然使用同一 PostgreSQL 数据库。')
    columns('validation','校验规则为什么分布在多个边界',[
      ('语法与合同',['API：必填 / null / 未知字段','枚举字符串与版本头','尚未发生业务状态变更']),
      ('业务语义',['Domain：Active 才能修改','解释 20-500 个标量值','不得修订为完全相同的值']),
      ('持久事实',['DB：外键 / 唯一 / CHECK','根版本条件与事务','不自动理解完整业务状态机'])],
      '各层守住自己的假设；界面校验改善反馈，不能替代服务端规则。',h=450)
    columns('http-outcomes','错误是协议中的决定',[
      ('尚未接受意图',['400：格式或防伪失败','401：需要认证','404：不可见的资源']),
      ('需要重新决定',['409：同键不同请求','412：资源版本已变化','422：业务规则拒绝']),
      ('不能直接下结论',['响应丢失 / 200 正文不可读','浏览器没有可靠结果','保留原意图，原样重试'])],
      '状态码与客户端的“结果未知”属于不同观察层次。',h=440)
    columns('di-scope','请求作用域是一条资源所有权链',[
      ('Singleton',['TimeProvider','无每次请求的跟踪状态','可作为可替换时间依赖']),
      ('Scoped',['Service → Store → DbContext','本次请求共享上下文','不同请求拥有独立跟踪器']),
      ('异步边界',['await 保持调用顺序','CancellationToken 向下传','不并行使用同一 DbContext'])],
      '依赖注入只组装对象；数据库事务仍由 Store 显式开启和提交。',h=420)
    columns('binding-sources','端点参数的来源不同，信任级别也不同',[
      ('传入数据',['路由：id / linkId','JSON：Kind / Rationale','Headers：Version / Key']),
      ('可信上下文',['认证：ClaimsPrincipal','DI：InvestigationService','宿主：HttpContext / ct']),
      ('用例输入',['Owner 只来自 claims','版本解析后传给 Service','不让请求正文指定 owner'])],
      '参数绑定组装调用；合法形状不等于业务合法，也不等于资源可见。',h=430)
    flow('problem-writer','一个错误对象在写出前还会经历加工',[
      ('异常映射',['选择 status','code / detail']),('Results.Problem',['构造结果','尚未发字节']),('默认 Writer',['补默认字段','写 Activity.Id']),('定制钩子',['统一 TraceId','最后序列化'])],
      'ASP.NET Core v10.0.9 的真实顺序；最终值的所有权决定修复应放在哪一阶段。')
    columns('endpoint-lifecycle','端点登记与端点执行处在两个时刻',[
      ('应用构建',['MapPut 登记路由与委托','授权 / 限流元数据','处理器的参数契约']),
      ('请求执行',['路由匹配 → 绑定参数','解析 DI 与可信身份','调用 Service → 执行 IResult']),
      ('可能的停止点',['路由不匹配','认证、防伪或绑定失败','端点内规则或数据库拒绝'])],
      '处理器尚未进入，错误也可能已经形成；返回结果之后，字节仍需写出并被解析。',h=450)
    flow('ef-materialization','关系行如何成为可修改的对象图',[
      ('SQL 行',['JOIN 带来','重复根列']),('身份解析',['按实体主键','复用跟踪实例']),('关系修复',['FK 关联根','填充私有集合']),('快照',['OriginalValues','供差异与条件用'])],
      '写路径加载带跟踪图；只读 Get/List 使用 AsNoTracking。')
    columns('ef-identity','预先分配 Guid 与状态判断必须一致',[
      ('领域意图',['new EvidenceLink','构造器分配 Guid','加入已跟踪根的集合']),
      ('映射约定',['ValueGeneratedNever()','声明键由应用负责','避免把非默认键误当已有行']),
      ('需要观察的事实',['Added → INSERT','不是 Modified → UPDATE','异常名不足以证明真实竞争'])],
      '生成策略影响新成员发现；看实体状态和实际 SQL，才能区分映射错误与并发。',h=440)
    flow('ef-states','跟踪状态描述持久化意图，不是业务状态',[
      ('Detached',['不由本上下文','管理']),('Unchanged',['已跟踪','没有待写差异']),('Added',['准备新增','INSERT']),('Modified',['准备改值','UPDATE']),('Deleted',['准备移除','DELETE'])],
      '状态可按操作进入或转换；本图按语义并列展示，不表示固定的状态转换链。',connect=False)
    columns('ef-values','同一个 Version，三个不同来源的值',[
      ('Original = 4',['B 加载时记录','没有因 A 提交而改变','进入 WHERE 的预期值']),
      ('Current = 5',['B 自己的领域决定','只是待写入的值','进入 SET 的新值']),
      ('Database = 5',['A 已提交的结果','数值与 B 想写的一样','来源不同，B 仍应冲突'])],
      '示意推演：Current 等于数据库数值，不能证明本次操作已经成功。',h=440)
    columns('schema-contract','一次加列，存在三个时间维度的合同',[
      ('旧数据库行',['无解释与修订时间','迁移后两列均为 null','不编造历史修订事实']),
      ('新业务操作',['解释经 Trim 后校验','解释与时间成对写入','不改变原关联身份']),
      ('旧 JSON 回执',['可能缺少新增字段','LinkView 可选默认 null','重放仍描述过去的结果'])],
      '迁移成功只覆盖表结构；对象反序列化与领域语义还需独立兼容。',h=440)
    flow('time-precision','把可公开时间统一到持久层能保存的精度',[
      ('TimeProvider',['100 ns ticks','UTC 时刻']),('Now()',['去掉不足','1 µs 的尾数']),('领域与回执',['同一个 now','即时响应']),('PostgreSQL',['微秒精度','重读同一时刻'])],
      '实际修复后两个 ticks 都为 639299753895425590；不把显示格式当作时刻一致。')
    lanes('mvcc-statements','Read Committed：一个事务内也可能看到两个版本',
      ['事务 A','事务 B'],[(0,0,'① SELECT 见 v4',False),(1,1,'② 更新并提交 v5',True),(0,2,'③ 新 SELECT 见 v5',False)],
      '语句级快照允许不重复读；事务包裹并不自动意味着整个事务只有一个读取快照。')
    lanes('mvcc-visibility','快照记住当时的可见世界',
      ['事务 T1','旧快照 S0','新快照 S1'],[(0,0,'① 更新，未提交',False),(1,1,'② T1 仍活跃',False),(0,2,'③ T1 提交',False),(1,3,'④ 仍读旧版本',True),(2,3,'⑤ 可读新版本',False)],
      '示意可见性：后来的提交不会把旧快照改写成新快照；实际规则还结合事务状态。')
    columns('write-skew','两行不冲突，业务决定仍可能冲突',[
      ('共同前提',['至少一人保持值班','A 与 B 都读取两人值班','两条读相互依赖']),
      ('各改一行',['A 把自己设为离岗','B 也把自己设为离岗','每行版本比较都可能通过']),
      ('设计含义',['单行 CAS 不覆盖跨根约束','需锁定共同仲裁点或更强隔离','序列化失败要重试整个决定'])],
      '概念反例：展示根版本策略的边界，不声称 EchoCase 已实现值班业务。',h=440)
    lanes('cas-race','不同 Key，仍然竞争同一个根版本',
      ['请求 A','请求 B','数据库'],[(0,0,'① 读到 Version 4',False),(1,0,'① 读到 Version 4',False),(0,1,'② 准备 Version 5',False),(1,1,'② 准备 Version 5',False),(2,2,'③ 一个提交成功',False),(1,3,'④ 412；整体回滚',True)],
      '真实双 Store 竞争结果为 200 / 412；最终版本 5，修订审计和回执各保留一条。')
    columns('transaction-set','原子提交的单位不是单条 UPDATE',[
      ('根与子',['Investigations：Version / 时间','Links：类型 / 解释 / 时间','同一次业务决定']),
      ('可观察承诺',['Audit：此版本发生何种操作','Receipt：该意图得到何结果','响应仅在提交成功后返回']),
      ('任一失败',['版本条件影响 0 行','或版本审计唯一键冲突','整个事务回滚，避免半条事实'])],
      'EF 批次中 Audit 可能先写；只有整体事务结果可以作为成功依据。',h=440)
    lanes('receipt-lock','相同 Key：后来的重试读取已提交回执',
      ['第一次请求','重试请求','数据库'],[(0,0,'① 获得 owner/key 锁',False),(1,1,'② 等待同一把锁',True),(2,2,'③ 业务 + 回执提交',False),(1,3,'④ 获锁后读取回执',False)],
      '事务级 advisory lock 在提交或回滚后释放；锁名哈希碰撞只会增加无谓等待。')
    columns('security-boundaries','身份、资源、防伪分别回答不同问题',[
      ('认证',['Cookie 验证当前身份','Owner 来自可信 claims','不接受请求体指定 owner']),
      ('资源授权',['WHERE Id AND OwnerId','不可见与不存在同为 404','回执重放之前检查资源']),
      ('防伪与内容',['写入校验 CSRF 令牌对','未调查证据不发正文','CSP / no-store 缩小暴露面'])],
      '这些边界共同保护会话应用；Identity 的存在不等于完整账户安全生命周期。',h=450)
    flow('react-render','事件之后，React 重新计算界面',[
      ('事件',['回调读取','本次快照']),('排队更新',['函数式 set','基于最新前值']),('Render',['纯计算 JSX','不提交请求']),('Commit',['更新 DOM','再执行 Effect'])],
      '事件闭包不会自动变成下一次渲染的变量；网络回调必须明确携带原操作快照。')
    columns('component-boundaries','按状态的变化原因拆分组件',[
      ('App / Workspace',['身份、导航与调查装配','Workspace 的 key = id','不同调查重置本地状态']),
      ('业务钩子',['useInvestigation：请求协议','useNotesDraft：草稿语义','函数式更新读取队列前值']),
      ('编辑与呈现',['NotesEditor 保持挂载','LinkEditor 保存打开时版本','Graph 局部节点坐标'])],
      '切换页签隐藏笔记面板，不卸载草稿；切换调查则使用新组件身份。',h=440)
    flow('query-cycle','一次 mutation 的完成包含后续确认读取',[
      ('onMutate',['取消旧 GET','消费 signal']),('mutationFn',['原版本与键','发送请求']),('onSuccess',['单调合并','确认缓存']),('onSettled',['await 失效刷新','再解除 pending'])],
      '等待失效刷新让编辑器在看到确认状态后关闭；它仍不提供跨浏览器原子性。')
    lanes('late-get','请求完成顺序不等于资源版本顺序',
      ['旧 GET','写入响应','确认缓存'],[(0,0,'① 查询基于 v4',False),(1,1,'② 写入确认 v5',False),(2,2,'③ 缓存已经是 v5',False),(0,3,'④ v4 晚到被拒绝',True)],
      '取消减少过期读取；latest 的版本比较还保护无法取消的晚到结果和旧回执。')
    lanes('draft-generation','保存发出后，用户可以继续写下一代输入',
      ['输入框','操作快照','成功处理'],[(0,0,'① revision 1：A',False),(1,1,'② 保存 A / r1',False),(0,2,'③ revision 2：A+B',False),(2,3,'④ 确认 r1，保留 r2',True)],
      '成功只确认被发送的代次；输入框当前文本不等于该次保存的请求正文。')
    columns('three-way','冲突比较保留三个事实',[
      ('baseline',['开始编辑前的内容','草稿基于哪个版本','作为用户判断的参照']),
      ('server current',['后台获取的最新已保存内容','版本可能高于 baseline','不能静默当成草稿新基线']),
      ('local draft',['本窗口尚未保存的输入','可由用户保留或放弃','显式确认后才形成新意图'])],
      '三方展示支持判断，没有实现自动文本合并；新确认也仍可能再次遇到并发。',h=430)
    columns('uncertain','HTTP 成功与浏览器确认之间仍有缺口',[
      ('服务器可能已提交',['数据库事务提交完成','回执已持久化','响应字节却未到达浏览器']),
      ('浏览器状态 0',['fetch 失败','或成功正文无法解析','保留 mutation.variables']),
      ('恢复含义',['同一次操作原样重试','得到历史回执','若资源更新，草稿继续待确认'])],
      '当前实现覆盖特定未知结果；没有声明通用断线持久队列或 exactly-once 网络传输。',h=450)
    columns('test-reasoning','按失败机制选择验证边界',[
      ('Domain / Unit',['非法状态与边界字符串','固定时间与无 I/O 的规则','断言业务事实而非实现细节']),
      ('PostgreSQL / API',['真实约束、事务、迁移','并发屏障使两方都读旧版','检查持久结果与回滚']),
      ('Browser / E2E',['响应延迟与正文丢失','等待确认状态而非睡眠','比较草稿、当前值与版本'])],
      '测试层次说明能观察什么；目录或测试总数都不能替代反例的解释。',h=440)
    flow('evolution','关联修订沿一条语义链演进',[
      ('规则',['保持身份','解释长度']),('持久化',['可空演进','根子同事务']),('协议',['新增 PUT','旧回执兼容']),('界面',['冻结基线','失败留草稿'])],
      '变化穿过必要边界；共享 Write 路径承担幂等、版本、审计，不再复制另一套。')
    columns('review-model','评审一个改动时，沿承诺逆向追问',[
      ('用户承诺',['保存指的是哪一代输入？','失败后还保留什么？','用户能否看见并发变化？']),
      ('协议与事务',['重试是否保持原意图？','根和子是否同提交？','读取快照支持何种结论？']),
      ('维护与边界',['规则由哪个对象拥有？','新增复杂度解决何种反例？','哪项假设变化会推翻选择？'])],
      '综合推理把需求、源码和运行含义连起来，而非用术语数量给架构评分。',h=440)
    # Crop coordinates reference original pixels. PDF draws separate numbered badges.
    ui={
      'ui-dashboard':('02-dashboard',[230,150,1170,730],[(.16,.32,'1'),(.55,.83,'2')],
          '案件总览：①案件定义入口；②个人调查列表。固定案件与每位用户的调查实例是不同对象。', ['①固定案件不是共享调查进度。','②个人档案由 owner 隔离；列表统计来自已取得的调查快照。']),
      'ui-evidence':('03-evidence',[250,260,1150,780],[(.21,.28,'1'),(.84,.47,'2')],
          '真实证据工作台：①卡片显示已调查状态；②详情正文由调查结果提供。', ['①可见、已调查、可编辑属于不同条件。','②正文没有在未调查时预先发送给浏览器。']),
      'ui-verdict':('05-verdict',[265,435,920,700],[(.5,.25,'1'),(.72,.48,'2')],
          '真实封存界面：结论、支持证据与固定规则评分一起展示。', ['①提交后的读模型已经包含 Verdict。','②100 分属于固定教学案件规则，并非现实调查结论的可信度。']),
      'ui-dirty':('dirty-refetch',[295,640,860,655],[(.9,.14,'1'),(.9,.67,'2'),(.86,.93,'3')],
          '真实脏草稿冲突：版本 1 的草稿保留，服务器已经是版本 2。', ['①输入框保留“本窗口的待核实推断”。','②比较区同时展示空基线、另一窗口的事实与本地草稿。','③采用服务器内容或显式确认草稿，是两种新的用户决定。']),
      'ui-inflight':('inflight-draft',[295,580,860,450],[(.91,.28,'1'),(.85,.91,'2')],
          '真实晚到保存结果之后的界面：服务器确认旧快照，输入框仍保留后来输入。', ['①文本包含“等待时继续记录的新线索”。','②有未保存修改；成功响应没有把新一代输入错误标为已保存。']),
      'ui-graph':('04-graph',[260,530,1140,650],[(.55,.33,'1'),(.24,.8,'2')],
          '真实图谱：节点布局是本地呈现，证据关系另有稳定身份。', ['①连线表达关系类型，没有业务方向箭头。','②下面的关系列表提供可访问的修订与删除入口。']),
      'ui-revision':('link-revision',[270,610,1120,580],[(.55,.33,'1'),(.43,.85,'2')],
          '真实修订完成后的图谱：同一关联改为矛盾关系，解释显示在列表中。', ['①关系的端点未更换，类型改变后边的视觉编码同步改变。','②解释随服务器确认快照显示；修订时间保存在返回数据中。']),
      'ui-unreadable':('unreadable-body',[295,590,860,440],[(.91,.3,'1'),(.85,.91,'2')],
          '成功正文不可读后，以原意图重试并恢复确认的真实界面。', ['①截图记录恢复后的文本，不把它伪称为错误发生瞬间。','②恢复确认依赖历史回执，而不是重新执行一次新的保存。']),
      'ui-mobile':('08-mobile',None,[(.88,.08,'1'),(.74,.46,'2')],
          '真实窄屏图谱：工具栏换行，节点区域可缩放与拖动。', ['①导航与内容适应窄视口。','②图形手势之外仍需保留表单式建联入口。'])
    }
    for id,(name,crop,marks,caption,legend) in ui.items():
        CAT[id]=dict(type='ui',file=f'figures/ui/{name}.png',crop=crop,marks=marks,caption=caption,legend=legend,
                     maxHeight=360 if id=='ui-mobile' else 370)
    CAT['ui-revision']['panels']=[
      dict(crop=[480,710,720,230],marks=[(.96,.42,'1')],label='同一真实界面的画布局部'),
      dict(crop=[280,1090,720,90],marks=[(.96,.65,'2')],label='同一界面的关系列表解释')]
    CAT['ui-mobile']['layout']='side'
    CAT['ui-mobile']['panels']=[
      dict(crop=[0,0,390,550],marks=[(.90,.13,'1')],label='原窄屏界面：上半部'),
      dict(crop=[0,550,390,646],marks=[(.86,.45,'2')],label='原窄屏界面：下半部')]
    (M/'figures'/'catalog.json').write_text(json.dumps(CAT,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'{len(CAT)} teaching figures ({len(ui)} annotated UI views).')

if __name__=='__main__': main()
