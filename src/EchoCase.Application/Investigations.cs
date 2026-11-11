using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using EchoCase.Domain;

namespace EchoCase.Application;

public sealed record CaseSummary(string Id, string Title, string Subtitle, string Synopsis, string[] Suspects, int EvidenceCount);
public sealed record EvidenceView(string Id, string Title, string Kind, string Summary, string? Body, bool Locked, bool Examined);
public sealed record LinkView(Guid Id, string SourceId, string TargetId, string Kind);
public sealed record VerdictView(string Suspect, string Reasoning, string[] SupportingEvidence, int Score);
public sealed record SessionView(Guid Id, string CaseId, string Title, string Status, int Version, string Notes, DateTimeOffset CreatedAt, DateTimeOffset UpdatedAt, IReadOnlyList<EvidenceView> Evidence, IReadOnlyList<LinkView> Links, VerdictView? Verdict);
public sealed record StartRequest(string CaseId);
public sealed record LinkRequest(string SourceId, string TargetId, string Kind);
public sealed record NotesRequest(string Notes);
public sealed record VerdictRequest(string Suspect, string Reasoning, string[] SupportingEvidence);
public sealed record Change(string OwnerId, string Key, string Fingerprint, Guid? SessionId, int? ExpectedVersion, string Operation);

public sealed class ApplicationFault(int status, string code, string message) : Exception(message)
{
    public int Status { get; } = status;
    public string Code { get; } = code;
}

public interface IInvestigationStore
{
    Task<IReadOnlyList<SessionView>> ListAsync(string ownerId, CancellationToken ct);
    Task<SessionView> GetAsync(Guid id, string ownerId, CancellationToken ct);
    Task<SessionView> WriteAsync(Change change, Func<Investigation?, Investigation> apply, CancellationToken ct);
}

public static class SessionPresenter
{
    public static SessionView Map(Investigation i) => new(i.Id, i.CaseId, CaseCatalog.Get(i.CaseId).Title, i.Status.ToString(), i.Version, i.Notes, i.CreatedAt, i.UpdatedAt,
        CaseCatalog.Get(i.CaseId).Evidence.Select(e => new EvidenceView(e.Id, e.Title, e.Kind,
            i.IsVisible(e) ? e.Summary : "完成前置调查后解锁。", i.Discoveries.Any(d => d.EvidenceId == e.Id) ? e.Body : null,
            !i.IsVisible(e), i.Discoveries.Any(d => d.EvidenceId == e.Id))).ToArray(),
        i.Links.OrderBy(l => l.SourceId).ThenBy(l => l.TargetId).Select(l => new LinkView(l.Id, l.SourceId, l.TargetId, l.Kind.ToString())).ToArray(),
        i.Score is null ? null : new(i.Suspect!, i.Reasoning!, i.SupportingEvidence!.Split(','), i.Score.Value));
}

public sealed class InvestigationService(IInvestigationStore store, TimeProvider clock)
{
    public static CaseSummary[] Cases() => [new(CaseCatalog.Harbor.Id, CaseCatalog.Harbor.Title, CaseCatalog.Harbor.Subtitle, CaseCatalog.Harbor.Synopsis, CaseCatalog.Harbor.Suspects, CaseCatalog.Harbor.Evidence.Count)];
    public Task<IReadOnlyList<SessionView>> List(string owner, CancellationToken ct) => store.ListAsync(owner, ct);
    public Task<SessionView> Get(Guid id, string owner, CancellationToken ct) => store.GetAsync(id, owner, ct);

    public Task<SessionView> Start(string owner, string key, StartRequest body, CancellationToken ct) =>
        Write(owner, key, null, null, "start", body, _ => Investigation.Start(owner, body.CaseId, clock.GetUtcNow()), ct);
    public Task<SessionView> Examine(Guid id, string owner, string key, int version, string evidenceId, CancellationToken ct) =>
        Write(owner, key, id, version, "examine", new { evidenceId }, i => { i!.Examine(evidenceId, clock.GetUtcNow()); return i; }, ct);
    public Task<SessionView> Link(Guid id, string owner, string key, int version, LinkRequest body, CancellationToken ct) =>
        Write(owner, key, id, version, "link", body, i =>
        {
            if (!Enum.TryParse<LinkKind>(body.Kind, false, out var kind) || !Enum.IsDefined(kind)) throw new DomainRule("invalid_relation", "关联类型无效。");
            i!.Link(body.SourceId, body.TargetId, kind, clock.GetUtcNow()); return i;
        }, ct);
    public Task<SessionView> RemoveLink(Guid id, string owner, string key, int version, Guid linkId, CancellationToken ct) =>
        Write(owner, key, id, version, "unlink", new { linkId }, i => { i!.RemoveLink(linkId, clock.GetUtcNow()); return i; }, ct);
    public Task<SessionView> Notes(Guid id, string owner, string key, int version, NotesRequest body, CancellationToken ct) =>
        Write(owner, key, id, version, "notes", body, i => { i!.SaveNotes(body.Notes, clock.GetUtcNow()); return i; }, ct);
    public Task<SessionView> Transition(Guid id, string owner, string key, int version, string action, CancellationToken ct) =>
        Write(owner, key, id, version, action, new { action }, i =>
        {
            if (action == "review") i!.Review(clock.GetUtcNow());
            else if (action == "resume") i!.Resume(clock.GetUtcNow());
            else throw new ApplicationFault(404, "action_not_found", "操作不存在。");
            return i;
        }, ct);
    public Task<SessionView> Verdict(Guid id, string owner, string key, int version, VerdictRequest body, CancellationToken ct) =>
        Write(owner, key, id, version, "verdict", body, i => { i!.Submit(body.Suspect, body.Reasoning, body.SupportingEvidence, clock.GetUtcNow()); return i; }, ct);

    private Task<SessionView> Write<T>(string owner, string key, Guid? id, int? version, string operation, T body, Func<Investigation?, Investigation> apply, CancellationToken ct)
    {
        if (!Guid.TryParseExact(key, "D", out _)) throw new ApplicationFault(400, "idempotency_key_required", "写操作需要 UUID 格式的 Idempotency-Key。");
        var canonical = JsonSerializer.Serialize(new { id, version, operation, body });
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(canonical)));
        return store.WriteAsync(new(owner, key, hash, id, version, operation), apply, ct);
    }
}
