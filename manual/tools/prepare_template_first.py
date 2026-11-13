"""Prepare edition sources and audit immutable implementation/asset authorities.

This is book maintenance, not a reader-facing experiment script. Existing
revised chapters are never overwritten. Historical PNG/PDF bytes are read-only.
"""
from pathlib import Path
import hashlib,json,re,subprocess
from collections import Counter
from source_excerpts import SPECS,extract
from editions import MANUAL as M,ROOT,protected_history

E=M/'editions/template-first';BASE='9f68721e18f15ae603e6502fa46b8fa78f9df55c'
OLD='908811b95fb40cf14fa79b8eddf41796aa02cc04'
BOOT='f1df1a3c3b95bae184600a0ccef629eccaa18080'
HISTORY='63c587277541b4e700258aad82de9b2ad0ba32f8'
A='backend/EchoCase.Application/';P='backend/EchoCase.Api/';I='backend/EchoCase.Infrastructure/'
F='frontend/src/';R=A+'Investigations/Requests.cs';B=A+'Common/Behaviours/'
EP=P+'Endpoints/Investigations.cs';C=F+'api/client.ts';G=F+'api/generated.ts';Q=F+'workspace/useInvestigation.ts'
T='test/integration/EchoCase.IntegrationTests/PostgresApiTests.Template.cs'

def git(path,commit=BASE):return subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT)
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
    protected_history()
    if subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()!='main':raise RuntimeError('Publication is main-only')
    subprocess.run(['git','diff','--exit-code',BASE,'--','backend','frontend','test','.github','Directory.Build.props','Directory.Packages.props','global.json','EchoCase.slnx','dotnet-tools.json'],cwd=ROOT,check=True)
    config=json.loads((E/'book.json').read_text(encoding='utf-8'))
    (E/'chapters').mkdir(parents=True,exist_ok=True)
    for name in config['chapters']:
        target=E/'chapters'/name
        if not target.exists():target.write_bytes((M/'chapters'/name).read_bytes())
    specs={k:dict(path=v[0],start=v[1],end=v[2],**({'nextOccurrence':True} if len(v)>3 else {})) for k,v in SPECS.items()}
    def add(key,path,start,end=None,**options):specs[key]=dict(path=path,start=start,end=end,**options)
    add('api-di',P+'Program.cs','builder.AddApplicationServices();','builder.WebHost.ConfigureKestrel')
    add('api-cookie',I+'DependencyInjection.cs','        builder.Services.AddAuthentication','        builder.Services.AddAuthorization')
    add('api-json',P+'Program.cs','builder.Services.ConfigureHttpJsonOptions','builder.Services.AddProblemDetails')
    add('api-version',EP,'    private static int Version','    private static IResult Respond')
    add('api-route',EP,'    public static async Task<IResult> ReviseLink','    public static async Task<IResult> RemoveLink')
    add('api-owner',R,'internal static class RequestOwner','public sealed class GetCasesHandler')
    add('api-login',P+'Program.cs','    var principal = new ClaimsPrincipal','}).WithName("Login")')
    add('client-fetch',C,'      const headers =','      if (!response.ok)')
    add('client-body',C,'  try {\n    return await perform(client);','export async function refreshCsrf')
    add('app-registration',A+'DependencyInjection.cs','        builder.Services.AddValidatorsFromAssembly','        builder.Services.AddScoped<InvestigationService>')
    add('infra-scope',I+'DependencyInjection.cs','        builder.Services.AddSingleton(TimeProvider.System);','    }\n}')
    add('web-openapi',P+'DependencyInjection.cs','        builder.Services.AddScoped<IUser','    }\n}')
    add('endpoint-discovery',P+'Infrastructure/WebApplicationExtensions.cs','        var endpointGroupTypes','        return app;')
    add('endpoint-naming',P+'Infrastructure/EndpointRouteBuilderExtensions.cs','    public static RouteHandlerBuilder MapPut','    /// <inheritdoc',nextOccurrence=True)
    add('api-save',EP,'    public static async Task<IResult> SaveNotes','    public static async Task<IResult> TransitionInvestigation')
    add('api-save-route',EP,'        group.MapPut(SaveNotes','        group.MapPost(TransitionInvestigation')
    add('save-command',R,'[Authorize] public sealed record SaveNotesCommand','[Authorize] public sealed record TransitionInvestigationCommand')
    add('revise-command',R,'[Authorize] public sealed record ReviseLinkCommand','[Authorize] public sealed record RemoveLinkCommand')
    add('save-handler',R,'public sealed class SaveNotesHandler','public sealed class TransitionInvestigationHandler')
    add('revise-handler',R,'public sealed class ReviseLinkHandler','public sealed class RemoveLinkHandler')
    add('query-handler',R,'public sealed class GetInvestigationHandler','public sealed class StartInvestigationHandler')
    add('write-validator',R,'public abstract class WriteCommandValidator','public sealed class StartInvestigationValidator')
    add('authorization-identity',B+'AuthorizationBehaviour.cs','        var authorizeAttributes =','            // Role-based authorization')
    add('validation-dispatch',B+'ValidationBehaviour.cs','        if (_validators.Any())','        return await next();')
    add('logging-name',B+'LoggingBehaviour.cs','        var requestName =','    }\n}')
    add('performance-return',B+'PerformanceBehaviour.cs','        var response = await next();','        return response;')
    add('current-user',P+'Services/CurrentUser.cs','    public string? Id','\n\n}')
    add('identity-policy',I+'Identity/IdentityService.cs','    public async Task<bool> AuthorizeAsync','    public async Task<Result> DeleteUserAsync')
    add('nswag-save-path',G,'    saveNotes(id: string, body: NotesRequest, signal?: AbortSignal): Promise<SessionView> {','        const content_')
    add('nswag-save-method',G,'    saveNotes(id: string, body: NotesRequest, signal?: AbortSignal): Promise<SessionView> {','    protected processSaveNotes')
    add('nswag-save-process',G,'    protected processSaveNotes','    /**',nextOccurrence=True)
    add('nswag-revise-signature',G,'    reviseLink(id: string, linkId: string, body: ReviseLinkRequest, signal?: AbortSignal): Promise<SessionView> {','        let url_')
    add('nswag-verdict-signature',G,'    submitVerdict(id: string, body: VerdictRequest, signal?: AbortSignal): Promise<SessionView> {','        let url_')
    add('adapter-headers',C,'      if (write) headers.set','      const response =')
    add('adapter-intent',C,'export type Action =','export function executeOperation')
    add('adapter-dispatch',C,'      case "revise-link":','      case "unlink":')
    add('query-dispatch',Q,'    mutationFn:','    onMutate:')
    add('workspace-revise',F+'Workspace.tsx','            onRevise={(linkId, body, version) =>','          />')
    add('link-mutate','backend/EchoCase.Domain/Investigation.cs','    internal void Revise(LinkKind','\n}')
    add('slow-store-test',T,'        public async Task<SessionView> WriteAsync','    [Test]')
    add('slow-result-test',T,'        var result = await Success(await Send(client, token, HttpMethod.Post, "/api/investigations"','    [Test]')
    add('direct-sender-test',T,'    public async Task TemplateAuthorizationProtectsDirectSenderWithoutHttpEndpoint','    [Test]')
    add('validation-test',T,'            var sender = scope.ServiceProvider.GetRequiredService<ISender>();','        finally')
    add('former-owner-test',T,'        // Fixture-only transfer:','        var visibleToBob')
    add('model-drift-test',T,'    public async Task TemplateIntegrationIntroducesNoDatabaseModelOrMigrationDrift','\n}')
    add('bootstrap-registration','src/Application/DependencyInjection.cs','        builder.Services.AddMediatR','    }\n}',commit=BOOT,label='官方生成比较（历史）')
    add('bootstrap-initializer','src/Infrastructure/Data/ApplicationDbContextInitialiser.cs','            await _context.Database.EnsureDeletedAsync();','        }',commit=BOOT,label='官方样例（已移除）')
    add('bootstrap-performance','src/Application/Common/Behaviours/PerformanceBehaviour.cs','            if (!string.IsNullOrEmpty(userId))','            _logger.LogWarning',commit=BOOT,label='官方原性能行为（历史）')
    # Resolve every selector now, including those retained from the earlier book.
    verified=[]
    for key in specs:
        entry=extract(key,BASE,specs,True)
        verified.append({k:v for k,v in entry.items() if k!='text'})
    dump(E/'source-selections.json',specs)
    dump(E/'reference/source-selector-audit.json',verified)
    audit=[]
    oldconfig=json.loads((M/'book.json').read_text(encoding='utf-8'))
    for name in oldconfig['chapters']:
        for key in re.findall(r'\{\{code ([\w-]+)\}\}',(M/'chapters'/name).read_text(encoding='utf-8')):
            old=extract(key,OLD,verify_worktree=False)
            new=extract(key,BASE,specs,True)
            audit.append(dict(chapter=name,id=key,historicalCommit=OLD,historicalPath=old['path'],historicalSHA256=old['sha256'],
                              revisedPath=new['path'],revisedSHA256=new['sha256'],textUnchanged=old['text']==new['text']))
    if len(audit)!=57:raise ValueError(f'Historical excerpt inventory changed: {len(audit)}')
    dump(E/'reference/historical-57-excerpt-audit.json',audit)
    # Historical pixels remain byte-for-byte unchanged, with current relevance
    # argued by selected unchanged sources rather than a false whole-app match.
    provenance=json.loads((M/'reference/asset-provenance.json').read_text(encoding='utf-8'))
    for item in provenance['screenshots']:
        if hashlib.sha256((M/item['file']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Historical screenshot changed')
    provenance['historicalEquivalenceAudit']={k:provenance.pop(k) for k in ['identicalApplicationFiles'] if k in provenance}
    unchanged=[]
    for path in ['backend/EchoCase.Domain/Investigation.cs','backend/EchoCase.Application/Investigations.cs','backend/EchoCase.Infrastructure/EchoDbContext.cs','backend/EchoCase.Infrastructure/PostgresInvestigationStore.cs']:
        historical_path=path.replace('backend/','src/',1)
        if git(path)!=git(historical_path,HISTORY):raise ValueError('Historical mechanism changed: '+path)
        unchanged.append(path)
    provenance.update(revisedSourceCommit=BASE,unchangedMechanismPaths=unchanged,note='Nine genuine captures from 2026-11-11, historical commit 63c5872. Not newly captured from the migrated application. Current UI business behavior is representative; API dispatch/transport changed. Only the listed core mechanisms are byte-equivalent to the historical run.')
    dump(E/'reference/asset-provenance.json',provenance)
    build=M/'build/template-first';build.mkdir(parents=True,exist_ok=True)
    # Reuse original observation selection from its immutable Git source if the
    # prior local intermediate is unavailable. No measurement is fabricated.
    plan=json.loads(git('evidence/phase2a/database/application-query-plan.json',HISTORY))
    selected=dict(commit=HISTORY,query={k:v for k,v in plan.items() if k not in ['withoutComposite','ownerOnly','withComposite']},
                      plans={k:plan[k] for k in ['withoutComposite','ownerOnly','withComposite']},
                      race=json.loads(git('evidence/phase2a/database/store-race.json',HISTORY)),
                      tracking=json.loads(git('evidence/phase2a/database/migration-tracking.json',HISTORY)),
                      precision=json.loads(git('evidence/phase2a/database/timestamp-precision.json',HISTORY)))
    dump(build/'selected-observations.json',selected)
    catalog=json.loads((M/'figures/catalog.json').read_text(encoding='utf-8'))
    for item in catalog.values():
        if item['type']=='ui':item['caption']='历史真实界面（2026-11-11）。'+item['caption']
    if not (E/'figures/catalog.json').exists():dump(E/'figures/catalog.json',catalog)
    files=subprocess.check_output(['git','ls-files','backend','frontend','test','.github'],cwd=ROOT,text=True).splitlines()
    inventory=[]
    for file in files:
        pinned=git(file)
        if (ROOT/file).read_bytes().replace(b'\r\n',b'\n')!=pinned.replace(b'\r\n',b'\n'):raise ValueError('Engineering worktree drift: '+file)
        inventory.append(dict(path=file,sha256=hashlib.sha256(pinned).hexdigest()))
    dump(E/'reference/engineering-source-inventory.json',dict(commit=BASE,files=inventory))
    print(json.dumps(dict(chapters=len(config['chapters']),selectors=len(specs),historicalSelectionsAudited=len(audit),changedSelections=sum(not x['textUnchanged'] for x in audit),engineeringFiles=len(inventory),historicalPdf=protected_history()),ensure_ascii=False))

if __name__=='__main__':main()
