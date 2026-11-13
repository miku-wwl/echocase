"""Edition-specific mechanism drawings; never overwrites historical SVG/PNG."""
from pathlib import Path
import hashlib,json
from draw_figures import SVG as Base,INK,TEAL,GOLD,RED,MUTED,PALE,WARM,LINE,wrap
from editions import MANUAL as M,protected_history

E=M/'editions/template-first';OUT=E/'figures/mechanisms'
CAT=json.loads((E/'figures/catalog.json').read_text(encoding='utf-8'))
OLD=json.loads((M/'figures/catalog.json').read_text(encoding='utf-8'))
DECISIONS={}

class SVG(Base):
    def __init__(self,h,title):
        super().__init__(h);self.text(28,42,title,26,bold=True)
    def save(self,id,caption,status='REPLACE',reason=''):
        OUT.mkdir(parents=True,exist_ok=True)
        path=OUT/f'{id}.svg';path.write_text('\n'.join(self.p+['</svg>'])+'\n',encoding='utf-8')
        CAT[id]=dict(type='svg',file=str(path.relative_to(M)).replace('\\','/'),caption=caption)
        DECISIONS[id]=dict(id=id,status=status,reason=reason or caption,revisedFile=CAT[id]['file'])
    def label(self,x,y,text,width=35,size=21,color=INK,leading=29):
        for i,t in enumerate(wrap(text,width)):self.text(x,y+i*leading,t,size,color)
    def row(self,y,left,right,tone=PALE):
        self.rect(28,y,904,79,tone);self.text(45,y+32,left,23,bold=True);self.text(330,y+32,right,21)
    def tag(self,x,y,text,color=TEAL):
        self.rect(x,y,36,32,color,color);self.text(x+18,y+24,text,19,'#ffffff',bold=True,anchor='middle')

def lineage():
    s=SVG(510,'模板来源与业务迁移，是两条相交的历史')
    s.text(30,91,'业务线',21,bold=True);s.text(30,260,'官方线',21,bold=True)
    s.line(340,337,510,337,arrow=True)
    s.box(170,94,285,118,'早期自行实现',['908811b：原业务已实现','未采用要求的模板基础'])
    s.box(520,260,390,128,'实际生成 v10.8.0',['上游 e5c08ec → 生成 f1df1a3','独立验证，保留样例局限'],WARM)
    s.line(715,255,715,211,arrow=True)
    s.box(520,80,390,132,'迁移并接受 9f68721',['真实引入分派、行为、身份、端点','保留原聚合、数据与写入协议'])
    s.text(170,306,'CleanArchitecture',23,bold=True);s.text(170,337,'真实模板输入',21)
    s.line(455,153,505,153,arrow=True)
    s.text(32,438,'纠偏发生在实际生成之后；没有把早期实现追溯改称为模板项目。',21,color=TEAL)
    s.text(32,476,'图中仅标关键提交；完整不可变来源保存在教材参考资料。',19,color=MUTED)
    s.save('template-lineage','真实生成与业务迁移相交，既不否认原业务实现，也不抹去模板要求的纠偏。','ADD NEW')

def architecture():
    s=SVG(650,'上：直接项目引用　下：一次写入的真实调用')
    names=[('API','HTTP / 组合根'),('Infrastructure','EF / Identity / Store'),('Application','请求 / 端口 / 协调'),('Domain','纯 .NET 聚合')]
    for n,(name,sub) in enumerate(names):
        x=28+n*230;s.rect(x,90,214,116);s.text(x+13,125,name,22,bold=True);s.text(x+13,164,sub,18)
        if n<3:s.line(x+215,148,x+228,148,arrow=True)
    s.text(30,242,'实线为 .csproj 的直接引用；API 使用 Application 类型依靠传递引用。',20,color=MUTED)
    s.line(30,270,930,270,color=LINE)
    labels=[('端点 / ISender',40),('Behavior / Handler',275),('InvestigationService',565)]
    for title,x in labels:s.text(x,320,title,22,bold=True)
    s.line(210,313,262,313,arrow=True);s.line(505,313,551,313,arrow=True)
    s.rect(570,355,350,85,WARM);s.text(588,389,'Application 拥有端口',22,bold=True);s.text(588,419,'IInvestigationStore',21)
    s.line(750,327,750,350,arrow=True)
    s.rect(45,470,455,112);s.text(63,506,'Infrastructure 实现：Postgres Store',22,bold=True);s.text(63,543,'Begin → owner / 回执 / 版本 → apply',20)
    s.line(570,400,275,400);s.line(275,400,275,465,arrow=True)
    s.rect(570,470,350,112,WARM);s.text(588,506,'Domain：ReviseLink',22,bold=True);s.text(588,543,'回调内改变根与子对象',21)
    s.line(503,526,565,526,arrow=True)
    s.text(30,624,'运行能走向数据库；内层代码仍不编译依赖具体数据库实现。',21,color=TEAL)
    s.save('architecture','直接引用与运行调用分开编码；端口定义向内，事务与领域回调在运行时合作。')

def tradeoffs():
    s=SVG(550,'同一生成基础，不同机制有不同迁移决定')
    cols=[30,225,580];s.text(cols[0],92,'决定',22,bold=True);s.text(cols[1],92,'来自模板的机制',22,bold=True);s.text(cols[2],92,'当前 EchoCase 的落点',22,bold=True)
    rows=[('保留','MediatR / Validation / DI','请求行为与程序集扫描'),('保留','端点组 / IUser / Identity','发现、命名与当前用户端口'),('适配','应用 DbContext / 样例实体','Guid 聚合 + IInvestigationStore'),('适配','保存审计与事件示例','原有 Audit / Receipt 同事务'),('移除','Aspire / Todo / Weather','不进入活动业务与仓库范围'),('移除','样例删库初始化 / seed','既有迁移链；不重建业务数据')]
    for n,(a,b,c) in enumerate(rows):
        y=112+n*60;s.rect(28,y,904,54,WARM if a=='适配' else PALE);s.text(44,y+35,a,22,bold=True);s.text(225,y+35,b,20);s.text(580,y+35,c,20)
    s.text(30,518,'保留的是执行机制；选择性适配不是“从未真正初始化模板”。',21,color=TEAL)
    s.save('template-tradeoffs','迁移决策按机制分类；没有将可选样例抽象机械替换为业务承诺。')

def scopes():
    s=SVG(460,'处理器临时创建，工作单元仍由请求作用域拥有')
    for x,name in [(28,'请求 A'),(500,'请求 B')]:
        s.rect(x,82,432,300,'#ffffff');s.text(x+18,118,name,24,bold=True)
        s.text(x+18,166,'Transient Handler',23);s.line(x+215,175,x+215,198,arrow=True)
        s.rect(x+18,205,396,145);s.text(x+33,239,'同一 scoped 服务链',22,bold=True);s.text(x+33,278,'IUser → Service → Store',22);s.text(x+33,317,'唯一 DbContext / 跟踪快照',22)
    s.text(30,421,'A 与 B 不共享跟踪对象；TimeProvider 可单例，共享时钟不共享实体。',21,color=TEAL)
    s.save('di-scope','Transient 处理器在当前作用域内取得 scoped 依赖，不等于每解析一次就新建上下文。')

def pipeline():
    s=SVG(960,'SaveNotes：进入、短路、事务与成功回返')
    s.line(69,83,69,850,color=LINE)
    stages=[('1','HTTP 外围边界','安全头 / TraceId / 异常映射；响应未开始才可重写',PALE),
      ('2','Routing → Authentication','端点元数据；Cookie 建立可信 principal',PALE),
      ('3','RateLimiter → Authorization → CSRF','限频 / 登录要求 / 写请求令牌；可在端点前停止',PALE),
      ('4','绑定 → 命名端点 SaveNotes','route + body + ISender；解析 Key / Version；Send',PALE),
      ('5','Logging 预处理器','可能读取用户名；位于内层异常行为之外',WARM),
      ('6','MediatR 四层行为','UnhandledException → Authorization → Validation → Performance',PALE),
      ('7','Handler → InvestigationService','IUser 提供 owner；构造指纹与领域回调',PALE),
      ('8','Store 开始事务，取得同键锁','加载 owner/id → 查回执 → 比较预期版本',WARM),
      ('9','apply → 领域根 → EF 保存','根与子变化；加入 Audit / Receipt；SaveChanges',WARM),
      ('10','Commit 成功 → 调用栈回返','Performance 日志 → SessionView → ETag / Ok → JSON',PALE)]
    for i,(n,title,body,tone) in enumerate(stages):
        y=78+i*78;s.tag(48,y+12,n);s.rect(110,y,808,66,tone);s.text(128,y+28,title,23,bold=True);s.text(128,y+55,body,19)
        if i<9:s.line(75,y+50,75,y+80,arrow=True)
    # A bracket marks transaction extent, not a shortcut around apply.
    s.line(928,624,943,624);s.line(943,624,943,812);s.line(943,812,928,812)
    s.text(30,895,'事务只覆盖 8–10 中提交前的 Store 工作；不是整个 HTTP 或 MediatR 链。',20,color=TEAL)
    s.text(30,935,'成功提交不保证浏览器收到正文；任一短路都会使内层尚未执行的阶段停下。',20,color=MUTED)
    s.save('request-pipeline','无历史回执的新写成功路径。右括线标 Store 事务，到 Commit 为止；领域操作在事务内，提交后仍有结果交付。')

def binding():
    s=SVG(480,'客户端声明、宿主依赖与可信身份在不同位置进入')
    s.box(28,85,400,164,'端点绑定',['路由 id；JSON NotesRequest','DI：ISender；宿主：ctx / ct','端点显式解析 Key / If-Match'])
    s.box(530,85,400,164,'命令对象',['Id / Key / Version / Body','SaveNotesCommand','没有 Owner 字段'],WARM)
    s.line(435,167,522,167,arrow=True)
    s.rect(28,295,400,125);s.text(47,331,'Cookie → Claims → CurrentUser',22,bold=True);s.text(47,374,'IUser.Id 不来自请求正文',22)
    s.rect(530,295,400,125,WARM);s.text(550,331,'Handler 取得 owner',22,bold=True);s.text(550,374,'service.Notes(id, owner, …)',22)
    s.line(435,360,522,360,arrow=True);s.line(730,253,730,289,arrow=True)
    s.save('binding-sources','参数最终都是值，来源与信任仍不同；身份在处理器侧通过 IUser 进入协调服务。')

def lifecycle():
    s=SVG(510,'反射发现发生在启动；请求时只执行已构造的路由')
    s.text(30,90,'启动时',23,bold=True)
    items=[('程序集导出类型',35),('IEndpointGroup',340),('RoutePrefix / Map',645)]
    for t,x in items:s.rect(x,110,278,75);s.text(x+13,154,t,22)
    s.line(318,150,335,150,arrow=True);s.line(623,150,640,150,arrow=True)
    s.rect(35,215,888,76,WARM);s.text(54,247,'MapPut(SaveNotes, pattern) → WithName("SaveNotes")',22,bold=True);s.text(54,276,'路由 / 授权 / 限流元数据 → OpenAPI operationId',20)
    s.line(780,188,780,209,arrow=True)
    s.line(30,322,930,322,color=LINE);s.text(30,362,'每次请求',23,bold=True)
    s.text(35,413,'匹配路由 → 绑定值 / scoped 依赖 → 命名委托 → Send → 执行 IResult',22)
    s.text(35,466,'启动未执行领域；请求不重扫程序集；改方法名可能改变生成客户端名称。',20,color=TEAL)
    s.save('endpoint-lifecycle','端点发现、命名合同和每次请求执行分处不同时间，避免把反射与业务运行混为一谈。')

def mediator():
    s=SVG(675,'Send 的嵌套：进入顺序与返回顺序相反')
    layers=[('RequestPreProcessorBehavior：先 Logging',PALE),('UnhandledException：记录并重抛',WARM),('Authorization：当前身份 / 可选角色策略',PALE),('Validation：请求形状规则',PALE),('Performance：计时只包内层 Handler',WARM),('Handler → Service → Store',PALE)]
    for i,(label,tone) in enumerate(layers):
        x=30+i*28;y=78+i*75;w=900-i*56
        s.rect(x,y,w,545-i*84,tone);s.text(x+16,y+34,label,22,bold=True)
    s.text(210,552,'Store 才拥有事务；通用行为不自动开事务',21,color=TEAL)
    s.text(30,656,'Logging 的失败不在内侧 UnhandledException 包围内；HTTP 外围仍可捕获。',18,color=MUTED)
    s.save('mediator-onion','按 MediatR 注册与包装实现绘制；next 向内调用，await 返回后向外继续。','ADD NEW')

def usecase():
    s=SVG(465,'一次命令的职责，不等于一层一句透传')
    roles=[('Endpoint','绑定协议 → Command'),('Pipeline','身份 / Key 校验 / 诊断'),('Handler','IUser → 当前 owner'),('Service','操作名 / 时间 / 指纹 / 回调'),('Store','事务 / owner / 回执 / 版本'),('Domain','在回调内决定规则与新状态')]
    for i,(a,b) in enumerate(roles):
        y=82+i*55;s.text(35,y+29,a,23,bold=True);s.text(274,y+29,b,22);s.line(30,y+43,930,y+43,color=LINE)
    s.text(35,442,'Store 在领域回调前已开启事务；同一事务保存根、子、Audit、Receipt。',20,color=TEAL)
    s.save('usecase','处理器接入模板横切能力，协调服务复用原意图协议，领域与 Store 分别决定合法性和持久成败。')

def validation():
    s=SVG(570,'每项校验需要它能够可靠观察的事实')
    rows=[('HTTP 绑定 / 端点','JSON 形状、Guid、If-Match 形式','尚未形成完整用例'),('MediatR Validator','Key 是 D 格式 UUID','业务事务尚未写入'),('Domain 聚合','Active、成员、解释、实际变化','事务内已加载的对象图'),('PostgreSQL','FK / CHECK / 唯一 / CAS','持久关系与并发仲裁')]
    for i,(a,b,c) in enumerate(rows):
        y=80+i*105;s.rect(30,y,900,92,WARM if i==3 else PALE);s.text(47,y+32,a,23,bold=True);s.text(380,y+32,b,21);s.text(380,y+66,c,20,color=MUTED)
        if i<3:s.line(210,y+94,210,y+104,arrow=True)
    s.text(32,538,'不是零 SQL 才叫“先校验”：外侧 Logging 可能已读取身份，但没有业务写入。',20,color=TEAL)
    s.save('validation','校验范围由事实来源决定；通用 Validator 不替代事务内领域判断和数据库竞争。')

def telemetry():
    s=SVG(590,'同样已经提交，辅助查询决定了交付是否又失败')
    s.text(30,88,'历史模板的风险路径（源码推演）',23,bold=True)
    for x,a,b in [(30,'next 返回','事务已提交'),(340,'慢分支查用户名','额外数据库 I/O'),(650,'查询抛错','成功被表现为错误')]:
        s.rect(x,115,278,120,WARM);s.text(x+14,153,a,22,bold=True);s.text(x+14,195,b,21,color=RED)
    s.line(312,172,335,172,arrow=True);s.line(622,172,645,172,arrow=True)
    s.text(30,292,'当前路径与实际回归',23,bold=True)
    s.line(38,394,920,394,color=LINE,arrow=True)
    events=[(40,'预处理查名','调用次数 1'),(274,'真实 Store','提交已完成'),(508,'夹具延迟 600 ms','进入慢分支'),(742,'只记录 UserId','返回成功')]
    for x,a,b in events:s.text(x,349,a,21,bold=True);s.text(x,378,b,20)
    s.text(30,460,'身份替身：第一次允许，第二次必抛错；修正后的行为没有第二次调用。',21)
    s.text(30,506,'数据库观察：一项操作审计、一份回执；不是运行旧实现的失败复现。',21)
    s.text(30,554,'移除可避免的提交后 I/O，仍保留网络交付未知时的原意图重试。',20,color=TEAL)
    s.save('performance-after-commit','上半部是历史源码风险分析，下半部是当前实际回归构造；两者不混为同一次观测。','ADD NEW')

def sdk():
    s=SVG(665,'构建阶段生成合同；运行阶段传递意图')
    s.text(30,92,'构建与合同更新',23,bold=True)
    cells=[(30,'命名端点','operationId'),(270,'OpenAPI 3.0','frontend/\nopenapi.json'),(510,'NSwag 14.8.0','Fetch\nDTO Interface'),(750,'generated.ts','可调用客户端')]
    for x,a,b in cells:
        s.rect(x,115,180,127);s.text(x+12,151,a,21,bold=True);s.label(x+12,188,b,13,18)
        if x<750:s.line(x+184,177,x+234,177,arrow=True)
    s.line(30,281,930,281,color=LINE);s.text(30,322,'浏览器运行（没有即时生成）',23,bold=True)
    chain=[('React 组件 / Query','草稿、缓存、等待、原操作身份'),('executeOperation → 生成 SDK','kind 选择方法；SDK 编码路径与正文'),('注入 fetch：apiCall 适配器','Cookie / CSRF / Key / If-Match / signal'),('ASP.NET Core → Store','授权、业务、回执与原子提交')]
    for i,(a,b) in enumerate(chain):
        y=344+i*66;s.rect(30,y,900,57,WARM if i==2 else PALE);s.text(45,y+35,a,21,bold=True);s.text(455,y+35,b,20)
        if i<3:s.line(240,y+59,240,y+66,arrow=True)
    s.text(30,642,'返回：Response → SDK 解析 → ApiError / Session → Query → React 确认。',20,color=TEAL)
    s.save('nswag-two-times','生成和调用采用分开的时间区域；业务并发与恢复由应用层次合作完成。','ADD NEW')

def security():
    s=SVG(535,'三道边界回答不同问题，不能相互代替')
    stages=[('HTTP','Cookie / RequireAuthorization / CSRF','浏览器是谁，写入上下文是否有效'),('MediatR','Authorize 属性 + IUser','是否允许进入受保护用例'),('Store 事务','WHERE Id AND OwnerId → 回执','现在是否仍可访问这一份调查')]
    for i,(a,b,c) in enumerate(stages):
        y=85+i*128;s.rect(30,y,900,111,WARM if i==2 else PALE);s.text(48,y+35,a,24,bold=True);s.text(250,y+35,b,22);s.text(250,y+77,c,21)
        if i<2:s.line(130,y+113,130,y+128,arrow=True)
    s.text(30,508,'当前没有团队/管理员业务授权，也没有数据库 RLS；资源过滤依赖统一 Store。',20,color=TEAL)
    s.save('security-boundaries','通用登录要求保护用例入口，事务内资源过滤保护具体对象；CSRF 仍是独立边界。')

def owner():
    s=SVG(550,'持有旧回执，不代表现在仍拥有资源')
    s.text(30,92,'历史提交',22,bold=True);s.text(255,92,'Alice + Key K → 笔记成功 → Receipt K 留存',22)
    s.line(30,116,930,116,color=LINE)
    s.rect(30,145,900,80,WARM);s.text(48,180,'测试夹具 SQL 将 OwnerId 改为 Bob',23,bold=True);s.text(48,208,'用于构造反例；没有生产转移 API',20,color=MUTED)
    s.text(30,270,'Alice 原样重放',22,bold=True);s.line(220,263,305,263,arrow=True)
    s.rect(315,242,600,98);s.text(335,277,'先查当前 Id + Alice → 不可见 → 404',23,bold=True);s.text(335,312,'到此停止；不读取旧 Session 回执',21)
    s.line(640,344,640,382,color=RED,dash=True)
    s.rect(315,390,600,79,WARM);s.text(335,423,'若先重放 Receipt K，就会泄露旧资源',22,color=RED);s.text(335,451,'Authorize 只能确认她仍已登录，阻止不了此旁路',19)
    s.text(30,518,'实际回归同时确认：Bob 可见成功笔记，原回执仍只一份。',21,color=TEAL)
    s.save('owner-replay','把所有权检查放在回执之前，避免历史成功成为当前资源权限的通行证。','ADD NEW')

def savecommit():
    s=SVG(475,'跟踪器接受变化，早于显式事务最终提交')
    s.text(30,98,'对象 / EF',22,bold=True);s.text(30,253,'数据库事务',22,bold=True)
    points=[(230,'修改 / 检测','Modified'),(485,'SaveChanges 返回','Unchanged / Original = 5'),(758,'Commit 成功','可向上确认')]
    for x,a,b in points:s.text(x,97,a,21,bold=True);s.label(x,139,b,17,20)
    s.line(220,195,918,195,arrow=True)
    s.rect(225,229,510,107,WARM);s.text(242,268,'事务已开；SQL 成功但未最终提交',22,bold=True);s.text(242,310,'此时失败仍不能把跟踪状态当作持久证明',20)
    s.line(741,284,810,284,arrow=True);s.text(817,284,'提交',23,bold=True)
    s.text(30,391,'SaveChanges 默认 AcceptAllChanges：接受对象快照，不是替外部事务作承诺。',20)
    s.text(30,436,'Store 只在 CommitAsync 成功后返回；失败上下文不继续服务下一次业务。',20,color=TEAL)
    s.save('ef-savecommit','拆开 CLR 变化、EF 状态、SQL 保存和显式提交四个时刻，避免把 Unchanged 误读为已提交。','ADD NEW')

def query():
    s=SVG(475,'Query 负责生命周期，SDK 和适配器负责不同传输部分')
    points=[('onMutate',30,'取消旧 GET / 消费 signal'),('mutationFn',350,'executeOperation\n→ SDK'),('onSuccess',670,'单调合并 Session')]
    for a,x,b in points:s.rect(x,95,260,140);s.text(x+14,136,a,23,bold=True);s.label(x+14,179,b,17,20)
    s.line(295,160,344,160,arrow=True);s.line(615,160,664,160,arrow=True)
    s.rect(350,285,580,98,WARM);s.text(367,321,'onSettled：await 两类失效刷新',23,bold=True);s.text(367,357,'刷新完成前 pending 仍未结束',21)
    s.line(800,240,800,279,arrow=True)
    s.text(30,429,'SDK：URL / method / DTO / 解析；适配器：Cookie / CSRF / Key / If-Match。',20,color=TEAL)
    s.save('query-cycle','mutation 成功与整个确认周期完成分开；Query 不再自行组织 HTTP 路径。')

def uncertain():
    s=SVG(525,'结果未知：沿原意图再次询问，而不是发明新决定')
    s.text(30,95,'服务器',23,bold=True);s.text(345,95,'浏览器传输与解析',23,bold=True);s.text(690,95,'本地意图',23,bold=True)
    s.rect(30,126,260,122);s.text(45,163,'Commit + Receipt',23,bold=True);s.text(45,209,'业务已经成立',22)
    s.rect(345,126,290,122,WARM);s.text(362,163,'断线 / 成功正文解析失败',21,bold=True);s.text(362,209,'ApiError status = 0',22,color=RED)
    s.rect(690,126,240,122);s.text(705,163,'保留 Operation',23,bold=True);s.text(705,209,'禁止不同写入',22)
    s.line(295,182,339,182,arrow=True);s.line(640,182,684,182,arrow=True)
    s.line(808,254,808,315);s.line(808,315,155,315);s.line(155,315,155,254,arrow=True)
    s.text(250,351,'同 Key + 同 Version + 同目标 + 同 Body',23,bold=True)
    s.text(30,410,'旧回执确认过去；Query 仍拒绝低版本倒退，草稿按代次与基线确认。',21)
    s.text(30,466,'范围：不验证所有合法 JSON 形状；一般 5xx 与页面重启未统一持久恢复。',20,color=MUTED)
    s.save('uncertain','SDK 解析与适配器错误规范化协作；恢复保留原意图，当前资源和历史回执仍分开。')

def evolution():
    s=SVG(670,'同一项承诺沿真实文件传递，而不是只沿目录传递')
    data=[('稳定关系身份','Investigation.ReviseLink','不重建 Guid / 不换端点'),('受保护的意图','Requests.cs：Command / Handler','IUser + Key + Version + Body'),('事务协议','Investigations.cs → Postgres Store','指纹 / owner / 回执 / CAS'),('兼容数据','EchoDbContext + LinkRevisionExplanation','可空列 / 原迁移链 / 旧 JSON'),('跨语言合同','Endpoints → openapi.json → generated.ts','ReviseLink → reviseLink'),('用户确认','LinkEditor → Workspace → Query','冻结基线 / SDK / 保留失败草稿')]
    for i,(a,b,c) in enumerate(data):
        y=80+i*86;s.rect(30,y,900,74,WARM if i%2 else PALE);s.text(45,y+30,a,22,bold=True);s.text(300,y+29,b,20);s.text(300,y+57,c,19,color=MUTED)
        if i<5:s.line(155,y+77,155,y+86,arrow=True)
    s.text(30,640,'每条边连接一项用户承诺；验证沿身份、原子性、兼容和确认分别观察。',20,color=TEAL)
    s.save('evolution','跨层影响图标明具体方法与文件，让必要改动及其复用保证可被逐一解释。')

def versions():
    s=SVG(600,'从用户看过的版本，到 SQL 必须匹配的原值')
    rows=[('LinkEditor draft.version = 4','用户打开编辑时看过的事实'),('Operation.version = 4 / Key K','本次意图冻结，重试保持不变'),('If-Match: "4" → Command.Version','HTTP 前提进入已类型化请求'),('Change.ExpectedVersion = 4','Store 前置比较，不关闭后续竞争'),('EF Original = 4；Current = 5','WHERE 用原值，SET 用领域目标值'),('Commit → Session.version = 5','回执确认过去；缓存仍按版本单调合并')]
    for i,(a,b) in enumerate(rows):
        y=80+i*75;s.rect(30,y,900,65,WARM if i==4 else PALE);s.text(45,y+28,a,22,bold=True);s.text(45,y+53,b,19,color=MUTED)
        if i<5:s.line(890,y+67,890,y+75,arrow=True)
    s.text(30,568,'数据库已有别人的 5，不等于本次 Current = 5 已经成功。',21,color=TEAL)
    s.save('version-propagation','一个数字沿层次改变职责；类型化合同传值，领域与数据库分别决定目标和仲裁。','ADD NEW')

RETAIN={
'business-loop':'固定案件的五模块任务闭环未改变，仍解释业务而非框架。',
'aggregate':'Guid 根与普通子实体、版本边界和成员写入口未变。',
'domain-states':'Active/Reviewing/Submitted 转移和复核条件未变。',
'mvcc-tuples':'概念事务明确标示，区分物理行版本与业务 Version。',
'intent-coordinates':'资源版本与意图键的双坐标仍是当前协议。',
'state-owners':'确认缓存、草稿和局部图位置的状态所有权未变。',
'graph-semantics':'无向业务关系与有方向的控件手势区别未变。',
'query-plans':'历史 30,000 根三种计划有效，正文新增历史适用界限。',
'query-cost':'数值与原始历史观察一致，明确单机暖缓存限制。',
'requirements':'修订需求的身份、前提和原子结果未变。',
'http-outcomes':'列示的是代表性结果而非完整状态清单，未知结果的区别仍成立。',
'problem-writer':'原有最终 writer 的 TraceId 修正仍在当前 Program，正文明确为历史案例。',
'ef-materialization':'单语句图、身份解析、字段导航与原值快照未变。',
'ef-identity':'应用预分配 Guid 与 ValueGeneratedNever 保持一致。',
'ef-states':'五种状态与业务状态的区别仍准确。',
'ef-values':'Original/Current/Database 三值的竞争解释未变。',
'schema-contract':'可空列和旧回执默认值的三份时间合同未变。',
'time-precision':'业务微秒截断机制及历史精度数据可核对。',
'mvcc-statements':'READ COMMITTED 每语句快照仍是当前 Store 默认隔离。',
'mvcc-visibility':'概念可见性图不冒充实际 xmin/xmax 记录。',
'write-skew':'跨根反例明确为教学示意，不冒充应用功能。',
'cas-race':'不同 Key 竞争同根版本的历史观察仍由未变 Store 支持。',
'transaction-set':'根、子、Audit、Receipt 同事务保证未变。',
'receipt-lock':'同 owner/key 的事务锁与重放次序未变。',
'react-render':'事件快照与函数式更新的框架机制不受客户端迁移影响。',
'component-boundaries':'组件状态所有者未变，Query 仍协调请求生命周期；协议细节由新增图展开。',
'late-get':'取消及缓存单调合并机制未变。',
'draft-generation':'输入代次与在途保存的对应规则未变。',
'three-way':'baseline/current/draft 三方比较规则未变。',
'test-reasoning':'按失败机制区分验证边界仍有效，正文新增模板特有反例。',
'review-model':'从用户承诺逆向追问仍覆盖当前完整路径。',
}

def tracking():
    # Keep the original clear state table; revise only the historical caption and
    # a crucial fixture condition that generic snapshot explanations can hide.
    original=(M/OLD['ef-tracking']['file']).read_text(encoding='utf-8')
    original=original.replace('同一对象，三个观察时刻','历史夹具：关闭自动检测后，显式观察三个时刻')
    original=original.replace('真实记录：保存后 Version = 5；旧版本对子实体的修改随失败事务回滚。','2026-11-11：原值 4 → 当前 5；显式 DetectChanges 才观察到 Modified。')
    OUT.mkdir(parents=True,exist_ok=True);p=OUT/'ef-tracking.svg';p.write_text(original,encoding='utf-8')
    CAT['ef-tracking']=dict(type='svg',file=str(p.relative_to(M)).replace('\\','/'),caption='历史真实跟踪观察。夹具关闭自动检测以分离观察时刻；调试工具本身若触发检测，显示可能不同。')
    DECISIONS['ef-tracking']=dict(id='ef-tracking',status='REVISE',reason='补足 AutoDetectChanges 夹具条件与历史日期，避免把 Unchanged 误当普遍即时状态。',revisedFile=CAT['ef-tracking']['file'])

def main():
    protected_history()
    for fn in [lineage,architecture,tradeoffs,scopes,pipeline,binding,lifecycle,mediator,usecase,validation,telemetry,sdk,security,owner,savecommit,query,uncertain,evolution,versions,tracking]:fn()
    # Crop the unchanged real pixels into labelled strips, removing uninformative
    # textarea whitespace without pretending the strips are another UI state.
    for id in ['ui-inflight','ui-unreadable']:
        CAT[id]['panels']=[dict(crop=[295,620,850,105],marks=[[.57,.62,'1']],label='同一历史界面：输入框局部'),
                           dict(crop=[295,955,850,90],marks=[[.82,.33,'2']],label='同一界面：保存状态；省去中间空白')]
    CAT['ui-dirty']['panels']=[dict(crop=[295,620,850,105],marks=[[.4,.62,'1']],label='同一历史界面：保留中的输入'),
                             dict(crop=[295,1010,850,285],marks=[[.9,.55,'2'],[.9,.88,'3']],label='同一界面：三方比较与显式选择')]
    audit=[]
    for id,item in OLD.items():
        if item['type']!='svg':continue
        row=DECISIONS.get(id)
        if row is None:
            if id not in RETAIN:raise ValueError('Unreviewed historical figure '+id)
            row=dict(id=id,status='RETAIN',reason=RETAIN[id],revisedFile=item['file'])
        row.update(historicalFile=item['file'],historicalSHA256=hashlib.sha256((M/item['file']).read_bytes()).hexdigest())
        audit.append(row)
    if len(audit)!=44:raise ValueError('Historical figure count')
    audit.extend(v for k,v in DECISIONS.items() if k not in OLD)
    (E/'reference/figure-decisions.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (E/'figures/catalog.json').write_text(json.dumps(CAT,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(historicalReviewed=44,decisions={s:sum(x['status']==s for x in audit) for s in ['RETAIN','REVISE','REPLACE','REMOVE','ADD NEW']},catalog=len(CAT))))

if __name__=='__main__':main()
