"""Exact source selections. Anchors are exclusive at the end; no invented code."""
from pathlib import Path
import hashlib, subprocess

ROOT=Path(__file__).resolve().parents[2]
B='backend/'; F='frontend/src/'; T='test/'
D=B+'EchoCase.Domain/Investigation.cs'; A=B+'EchoCase.Application/Investigations.cs'
P=B+'EchoCase.Api/Program.cs'; S=B+'EchoCase.Infrastructure/PostgresInvestigationStore.cs'
E=B+'EchoCase.Infrastructure/EchoDbContext.cs'
Q=F+'workspace/useInvestigation.ts'; N=F+'workspace/useNotesDraft.ts'
SPECS={
 'domain-start':(D,'    public static Investigation Start','    public bool IsVisible'),
 'domain-examine':(D,'    public void Examine','    public void Link'),
 'domain-link':(D,'    public void Link','    public void RemoveLink'),
 'domain-revise':(D,'    public void ReviseLink','    public void SaveNotes'),
 'domain-transitions':(D,'    public void Review','    public void Submit'),
 'domain-submit':(D,'    public void Submit','    private void Editable'),
 'domain-advance':(D,'    private void Editable','}\n\npublic sealed class Discovery'),
 'app-port':(A,'public interface IInvestigationStore','public static class SessionPresenter'),
 'app-presenter':(A,'public static class SessionPresenter','public sealed class InvestigationService'),
 'app-revise':(A,'    public Task<SessionView> ReviseLink','    public Task<SessionView> Notes'),
 'app-time':(A,'    private DateTimeOffset Now','    private Task<SessionView> Write'),
 'app-fingerprint':(A,'    private Task<SessionView> Write',None),
 'app-linkview':(A,'public sealed record LinkView','public sealed record VerdictView'),
 'api-di':(P,'builder.Services.AddSingleton','builder.Services.AddOpenApi'),
 'api-cookie':(P,'builder.Services.AddAuthentication','builder.Services.AddAuthorization'),
 'api-json':(P,'builder.Services.ConfigureHttpJsonOptions','builder.Services.AddSingleton'),
 'api-trace':(P,'builder.Services.AddProblemDetails','var app = builder.Build'),
 'api-pipeline':(P,'app.UseRouting();','app.UseDefaultFiles();'),
 'api-faults':(P,'        var (status, code, detail) = e switch','        if (status >= 500)'),
 'api-version':(P,'static int Version','public sealed record Credentials'),
 'api-route':(P,'api.MapPut("/investigations/{id:guid}/links/','api.MapDelete'),
 'api-owner':(P,'static string Owner','static int Version'),
 'api-login':(P,'    var principal = new ClaimsPrincipal','}).RequireRateLimiting("auth");'),
 'store-read':(S,'    private IQueryable<Investigation> Graph','    public async Task<SessionView> WriteAsync'),
 'store-lock':(S,'        await using var tx','        var previous ='),
 'store-receipt':(S,'        var previous =','        var result = apply'),
 'store-save':(S,'        var result = apply','        catch (DbUpdateConcurrencyException)'),
 'store-conflicts':(S,'        catch (DbUpdateConcurrencyException)','        return response;'),
 'model-root':(E,'        i.Property(x => x.Version)','        i.HasMany(x => x.Discoveries)'),
 'model-index':(E,'        i.HasIndex(x => new { x.OwnerId, x.UpdatedAt })','        i.HasMany(x => x.Discoveries)'),
 'store-list':(S,'    public async Task<IReadOnlyList<SessionView>> ListAsync','    public async Task<SessionView> GetAsync'),
 'model-collections':(E,'        i.HasMany(x => x.Discoveries)','        var d = b.Entity'),
 'model-links':(E,'        l.HasKey(x => x.Id)','        var r = b.Entity'),
 'model-receipt':(E,'        var r = b.Entity','    }\n}'),
 'migration-columns':(B+'EchoCase.Infrastructure/Migrations/20261111060117_LinkRevisionExplanation.cs','            migrationBuilder.AddColumn<string>','            migrationBuilder.AddCheckConstraint'),
 'react-root':(F+'main.tsx','const queryClient =',None),
 'react-identity':(F+'App.tsx','        onLogin={(u) =>','        error={'),
 'react-workspace':(F+'App.tsx','          <Workspace','        ) : ('),
 'button-contract':(F+'components/ui/button.tsx','function Button(', 'export { Button'),
 'query-latest':(Q,'function latest','export function useInvestigation'),
 'query-get':(Q,'  const queryKey =','  const mutation ='),
 'query-mutation':(Q,'    onMutate:','  const uncertain ='),
 'query-uncertain':(Q,'  const uncertain =','  const act ='),
 'draft-initial':(N,'  const [draft, setDraft]','  const acknowledged ='),
 'draft-refresh':(N,'  useEffect(() => {','  useEffect(() => {',1),
 'draft-ack':(N,'    const { result, operation }','  }, [success, current.version]);'),
 'draft-edit':(N,'    conflict:','    discard:'),
 'draft-operation':(N,'    operation:',None),
 'notes-pending':(F+'workspace/NotesEditor.tsx','  const optimistic =','  return ('),
 'client-fetch':(F+'api/client.ts','    response = await fetch','  if (!response.ok)'),
 'client-body':(F+'api/client.ts','  if (response.status === 204)',None),
 'graph-position':(F+'EvidenceGraph.tsx','        position:','        data:'),
 'graph-edges':(F+'EvidenceGraph.tsx','  const edges:','  const connect ='),
 'link-baseline':(F+'workspace/LinkEditor.tsx','        onClick={() =>','  return (',1),
 'link-save':(F+'workspace/LinkEditor.tsx','        onClick={async () =>','      >\n        保存关联修订'),
 'unit-revision':(T+'unit/EchoCase.UnitTests/LinkRevisionTests.cs','    public void RevisionKeepsIdentity','    [TestCase'),
 'unit-unicode':(T+'unit/EchoCase.UnitTests/LinkRevisionTests.cs','    [TestCase','    [Test]\n    public void UnknownLink'),
 'e2e-delay':(T+'e2e/specs/consistency.spec.ts','  await page.route("**/api/investigations/*/notes", async (route) => {','  await input.fill'),
 'integration-race':(T+'integration/EchoCase.IntegrationTests/PostgresApiTests.LinkRevision.cs','                var result = await new PostgresInvestigationStore','                return (result, null);'),
}

def extract(id,commit,specs=None,verify_worktree=True):
    spec=(specs or SPECS)[id]
    label='应用源码'
    if isinstance(spec,dict):
        path,start,end=spec['path'],spec['start'],spec.get('end')
        rest=[1] if spec.get('nextOccurrence') else []
        commit=spec.get('commit',commit)
        label=spec.get('label',label)
    else:path,start,end,*rest=spec
    # Always resolve the immutable source FIRST. A worktree is an additional
    # invariant for the accepted engineering edition, not an alternate source.
    text=subprocess.check_output(['git','show',f'{commit}:{path}'],cwd=ROOT).decode('utf-8-sig').replace('\r\n','\n')
    if verify_worktree and commit=='9f68721e18f15ae603e6502fa46b8fa78f9df55c':
        current=(ROOT/path).read_text(encoding='utf-8-sig').replace('\r\n','\n')
        if current!=text:raise ValueError(f'Source changed after pinned commit: {path}')
    elif verify_worktree and specs is None:
        current=(ROOT/path).read_text(encoding='utf-8-sig').replace('\r\n','\n')
        if current!=text:raise ValueError(f'Source changed after pinned commit: {path}')
    a=text.index(start)
    if end is None:b=len(text)
    else:
        b=text.index(end,a+len(start)) if (rest and rest[0]==1) else text.index(end,a+1)
    snippet=text[a:b].rstrip()
    if not snippet:raise ValueError(id)
    line=text[:a].count('\n')+1
    blob=subprocess.check_output(['git','rev-parse',f'{commit}:{path}'],cwd=ROOT,text=True).strip()
    return dict(id=id,path=path,start=line,end=line+snippet.count('\n'),text=snippet,
                sha256=hashlib.sha256(snippet.encode()).hexdigest(),commit=commit,blob=blob,label=label)
