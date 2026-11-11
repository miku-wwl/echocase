using EchoCase.Domain;
using NUnit.Framework;

namespace EchoCase.Tests;

[TestFixture, Category("Unit")]
public sealed class DomainTests
{
    private static readonly DateTimeOffset Now = new(2026,11,11,0,0,0,TimeSpan.Zero);
    private static Investigation New() => Investigation.Start("owner", CaseCatalog.CaseId, Now);
    private static Investigation Ready()
    {
        var i = New(); foreach (var id in new[] { "access-log", "badge-ledger", "dispatch" }) i.Examine(id, Now);
        i.Link("access-log", "badge-ledger", LinkKind.Corroborates, Now); i.Link("badge-ledger", "dispatch", LinkKind.Corroborates, Now); return i;
    }
    [Test] public void StartRequiresOwner() => Assert.Throws<DomainRule>(() => Investigation.Start("", CaseCatalog.CaseId, Now));
    [Test] public void UnknownCaseIsRejected() => Assert.Throws<DomainRule>(() => Investigation.Start("u", "unknown", Now));
    [Test] public void HiddenEvidenceCannotBeExamined() { var i = New(); Assert.Throws<DomainRule>(() => i.Examine("dispatch", Now)); Assert.That(i.Version, Is.EqualTo(1)); }
    [Test] public void ExaminingUnlocksOnlyItsSuccessor() { var i = New(); i.Examine("access-log", Now); Assert.That(i.IsVisible(CaseCatalog.Evidence("badge-ledger")), Is.True); Assert.That(i.IsVisible(CaseCatalog.Evidence("dispatch")), Is.False); }
    [Test] public void DuplicateExaminationDoesNotAdvanceVersion() { var i = New(); i.Examine("camera", Now); Assert.Throws<DomainRule>(() => i.Examine("camera", Now)); Assert.That(i.Version, Is.EqualTo(2)); }
    [Test] public void SelfLinkIsRejected() { var i = Ready(); Assert.Throws<DomainRule>(() => i.Link("camera", "camera", LinkKind.Corroborates, Now)); }
    [Test] public void LinkRequiresBothDiscoveredEndpoints() => Assert.Throws<DomainRule>(() => New().Link("camera", "maintenance", LinkKind.Corroborates, Now));
    [Test] public void ReversedPairIsDuplicateEvenWithOtherKind() { var i = Ready(); Assert.Throws<DomainRule>(() => i.Link("badge-ledger", "access-log", LinkKind.Contradicts, Now)); }
    [Test] public void UndefinedEnumIsRejected() { var i = Ready(); Assert.Throws<DomainRule>(() => i.Link("access-log", "dispatch", (LinkKind)99, Now)); }
    [Test] public void ReviewHasMinimumEvidenceGate() => Assert.Throws<DomainRule>(() => New().Review(Now));
    [Test] public void ReviewFreezesWritesUntilResume() { var i = Ready(); i.Review(Now); Assert.Throws<DomainRule>(() => i.SaveNotes("no", Now)); i.Resume(Now); i.SaveNotes("yes", Now); Assert.That(i.Notes, Is.EqualTo("yes")); }
    [Test] public void InvalidTransitionCannotSkipReview() { var i = Ready(); Assert.Throws<DomainRule>(() => i.Submit("林澈", new string('x', 30), ["access-log","badge-ledger","dispatch"], Now)); }
    [Test] public void DuplicateSupportCannotSatisfyMinimum() { var i = Ready(); i.Review(Now); Assert.Throws<DomainRule>(() => i.Submit("林澈", new string('x', 30), ["access-log","access-log","access-log"], Now)); }
    [Test] public void UnexaminedSupportIsRejected() { var i = Ready(); i.Review(Now); Assert.Throws<DomainRule>(() => i.Submit("林澈", new string('x', 30), ["access-log","badge-ledger","camera"], Now)); }
    [Test] public void VerdictIsDeterministicAndSubmittedIsTerminal() { var i = Ready(); i.Review(Now); i.Submit("林澈", new string('x', 30), ["access-log","badge-ledger","dispatch"], Now); Assert.That(i.Score, Is.EqualTo(100)); Assert.Throws<DomainRule>(() => i.Resume(Now)); Assert.Throws<DomainRule>(() => i.Examine("camera", Now)); }
    [Test] public void AlternativeVerdictIsPersistedWithLowerEvaluation() { var i = Ready(); i.Review(Now); i.Submit("许舟", new string('x', 30), ["access-log","badge-ledger","dispatch"], Now); Assert.That(i.Score, Is.EqualTo(40)); }
    [Test] public void NotesLengthIsDomainInvariant() => Assert.Throws<DomainRule>(() => New().SaveNotes(new string('x',4001), Now));
    [Test] public void RemoveLinkChangesVersionAndReadiness() { var i = Ready(); var version = i.Version; i.RemoveLink(i.Links.First().Id, Now); Assert.That(i.Version, Is.EqualTo(version+1)); Assert.Throws<DomainRule>(() => i.Review(Now)); }
    [Test] public void CoreHasNoFrameworkOrOutwardDependencies() { var names = typeof(Investigation).Assembly.GetReferencedAssemblies().Select(a => a.Name!); Assert.That(names.All(x => x.StartsWith("System") || x == "netstandard"), Is.True); var app = typeof(Application.InvestigationService).Assembly.GetReferencedAssemblies().Select(a => a.Name!); Assert.That(app.Any(x => x.Contains("Infrastructure") || x.Contains("EntityFramework") || x.Contains("AspNetCore")), Is.False); }
    [Test] public void UnexaminedBodiesAreAbsentFromProjection() { var view = Application.SessionPresenter.Map(New()); Assert.That(view.Evidence.All(x => x.Body is null), Is.True); }
}
