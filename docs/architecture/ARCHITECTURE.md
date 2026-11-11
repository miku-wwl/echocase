# 应用架构与责任边界

Domain只依赖.NET基础库；Application引用Domain，定义用例、DTO与IInvestigationStore；Infrastructure引用Application，实现EF/PostgreSQL/Identity；API引用Infrastructure并组装Scoped依赖。React通过生成OpenAPI类型访问公共API。

运行路径为HTTP→身份/CSRF/端点→InvestigationService→IInvestigationStore→根聚合与EF→PostgreSQL。编译依赖向内；运行调用进入基础设施。DbContext、Store、用例服务为Scoped，TimeProvider为Singleton。Infrastructure是应用层次，不是环境部署目录。

## 一致性

Store开启数据库事务，以owner/key获取事务级advisory lock；先按owner/id加载资源，再检查回执/指纹。历史同键返回原业务快照，改意图409，新键旧版本412。根方法维护规则并推进Version；根UPDATE包含原Version。子记录、审计、回执同事务；特定版本审计唯一冲突也映射412。没有外部消息副作用。

整数版本是整个调查的一致性令牌。关联修订只改既有实体，保留身份与端点；解释和修订时间成对为空/存在。可空列迁移、旧回执默认字段以及真实数据迁移测试保留。业务时间在应用边界统一到微秒。

读路径使用单语句Include取得语句级快照；每案最多6条发现、15条关联，列表限制50。OwnerId/UpdatedAt组合索引与可选实际Store查询探针属于应用数据访问；大规模分页/投影需另行需求，不以当前查询推断容量。

## 前端

App负责身份/导航；Workspace组合业务视图；useInvestigation持有已确认快照和命令；useNotesDraft持有原内容/版本/编辑代次；NotesEditor和LinkEditor管理交互。pending呈现与确认缓存分离，历史回执不倒退版本，明确冲突后才生成新意图。查询消费AbortSignal，成功响应体无法读取也保留未知写入意图。React Flow坐标是本地呈现。

## 测试依赖

应用solution只含src四项目。UnitTests仅引用Domain/Application；IntegrationTests引用应用API/持久化；QueryProbe是测试区域的可选查询分析工具。E2E是独立npm包，只经过UI/API，不导入应用内部模块。生产构建不需要任何测试项目。

check_boundaries.py既查源码和引用，也读取MSBuild求值Compile/ProjectReference、NuGet运行依赖、publish DLL/deps.json与前端source map来源。具体命令和边界见测试指南。它不是通用恶意构建脚本沙箱。

当前没有发布编排或集中遥测平台。请求日志、TraceId、少量业务冲突/回执计数和健康诊断保留为应用调试能力。旧环境实验见历史提交；当前CI只验应用代码。
