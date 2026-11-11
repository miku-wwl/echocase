namespace EchoCase.Domain;

public sealed class DomainRule(string code, string message) : Exception(message)
{
    public string Code { get; } = code;
}

public enum InvestigationStatus { Active, Reviewing, Submitted }
public enum LinkKind { Corroborates, Contradicts }

public sealed class Investigation
{
    private readonly List<Discovery> _discoveries = [];
    private readonly List<EvidenceLink> _links = [];
    private Investigation() { }
    public Guid Id { get; private set; }
    public string OwnerId { get; private set; } = "";
    public string CaseId { get; private set; } = "";
    public InvestigationStatus Status { get; private set; }
    public int Version { get; private set; }
    public string Notes { get; private set; } = "";
    public string? Suspect { get; private set; }
    public string? Reasoning { get; private set; }
    public string? SupportingEvidence { get; private set; }
    public int? Score { get; private set; }
    public DateTimeOffset CreatedAt { get; private set; }
    public DateTimeOffset UpdatedAt { get; private set; }
    public IReadOnlyCollection<Discovery> Discoveries => _discoveries.AsReadOnly();
    public IReadOnlyCollection<EvidenceLink> Links => _links.AsReadOnly();

    public static Investigation Start(string ownerId, string caseId, DateTimeOffset now)
    {
        Require(!string.IsNullOrWhiteSpace(ownerId), "owner_required", "调查必须有所有者。");
        CaseCatalog.Get(caseId);
        return new() { Id = Guid.NewGuid(), OwnerId = ownerId, CaseId = caseId, Version = 1, CreatedAt = now, UpdatedAt = now };
    }

    public bool IsVisible(EvidenceDefinition e) => e.Requires is null || _discoveries.Any(x => x.EvidenceId == e.Requires);

    public void Examine(string evidenceId, DateTimeOffset now)
    {
        Editable();
        var e = CaseCatalog.Evidence(evidenceId);
        Require(IsVisible(e), "evidence_locked", "请先调查前置证据。");
        Require(!_discoveries.Any(x => x.EvidenceId == evidenceId), "already_examined", "该证据已调查。");
        _discoveries.Add(new(Id, evidenceId, now));
        Advance(now);
    }

    public void Link(string source, string target, LinkKind kind, DateTimeOffset now)
    {
        Editable();
        Require(Enum.IsDefined(kind), "invalid_relation", "关联类型无效。");
        Require(source != target, "self_link", "证据不能关联自身。");
        Require(new[] { source, target }.All(id => _discoveries.Any(x => x.EvidenceId == id)), "unexamined_link", "只能关联已调查的证据。");
        if (string.CompareOrdinal(source, target) > 0) (source, target) = (target, source);
        Require(!_links.Any(x => x.SourceId == source && x.TargetId == target), "duplicate_link", "此对证据已有关联。");
        _links.Add(new(Id, source, target, kind));
        Advance(now);
    }

    public void RemoveLink(Guid id, DateTimeOffset now)
    {
        Editable();
        var link = _links.SingleOrDefault(x => x.Id == id);
        Require(link is not null, "link_not_found", "关联不存在。");
        _links.Remove(link!);
        Advance(now);
    }

    public void SaveNotes(string notes, DateTimeOffset now)
    {
        Editable();
        Require(notes.Length <= 4000, "notes_too_long", "笔记最多 4000 字符。");
        Notes = notes.Trim();
        Advance(now);
    }

    public void Review(DateTimeOffset now)
    {
        Require(Status == InvestigationStatus.Active, "invalid_transition", "只有调查中的档案可以进入复核。");
        Require(_discoveries.Count >= 3 && _links.Count >= 2, "insufficient_evidence", "复核需要至少三条已调查证据和两条关联。");
        Status = InvestigationStatus.Reviewing;
        Advance(now);
    }

    public void Resume(DateTimeOffset now)
    {
        Require(Status == InvestigationStatus.Reviewing, "invalid_transition", "只有复核中的档案可以返回调查。");
        Status = InvestigationStatus.Active;
        Advance(now);
    }

    public void Submit(string suspect, string reasoning, IReadOnlyCollection<string> support, DateTimeOffset now)
    {
        Require(Status == InvestigationStatus.Reviewing, "invalid_transition", "先完成调查并进入复核。");
        Require(CaseCatalog.Harbor.Suspects.Contains(suspect), "unknown_suspect", "请选择案件中的相关人员。");
        Require(reasoning.Trim().Length is >= 20 and <= 4000, "reasoning_length", "结论说明需要 20 至 4000 字符。");
        Require(support.Distinct().Count() >= 3 && support.All(id => _discoveries.Any(x => x.EvidenceId == id)), "invalid_support", "结论需要至少三条不同的已调查证据。");
        Suspect = suspect; Reasoning = reasoning.Trim(); SupportingEvidence = string.Join(',', support.Distinct().Order());
        Score = CaseCatalog.Evaluate(suspect, support);
        Status = InvestigationStatus.Submitted;
        Advance(now);
    }

    private void Editable() => Require(Status == InvestigationStatus.Active, "investigation_readonly", "只有调查中可以修改；复核中请先返回调查，提交后只读。");
    private void Advance(DateTimeOffset now) { Version++; UpdatedAt = now; }
    private static void Require(bool condition, string code, string message) { if (!condition) throw new DomainRule(code, message); }
}

public sealed class Discovery
{
    private Discovery() { }
    internal Discovery(Guid investigationId, string evidenceId, DateTimeOffset now) { InvestigationId = investigationId; EvidenceId = evidenceId; ExaminedAt = now; }
    public Guid InvestigationId { get; private set; }
    public string EvidenceId { get; private set; } = "";
    public DateTimeOffset ExaminedAt { get; private set; }
}

public sealed class EvidenceLink
{
    private EvidenceLink() { }
    internal EvidenceLink(Guid investigationId, string sourceId, string targetId, LinkKind kind) { Id = Guid.NewGuid(); InvestigationId = investigationId; SourceId = sourceId; TargetId = targetId; Kind = kind; }
    public Guid Id { get; private set; }
    public Guid InvestigationId { get; private set; }
    public string SourceId { get; private set; } = "";
    public string TargetId { get; private set; } = "";
    public LinkKind Kind { get; private set; }
}
