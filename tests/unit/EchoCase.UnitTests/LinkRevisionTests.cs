using EchoCase.Domain;
using NUnit.Framework;

namespace EchoCase.UnitTests;

[TestFixture, Category("Unit")]
public sealed class LinkRevisionTests
{
    private static readonly DateTimeOffset Now = DateTimeOffset.Parse("2026-11-11T06:00:00Z");
    private static Investigation Ready()
    {
        var i = Investigation.Start("owner", "harbor-01", Now);
        foreach (var e in new[] { "access-log", "badge-ledger", "dispatch" }) i.Examine(e, Now);
        i.Link("access-log", "badge-ledger", LinkKind.Corroborates, Now);
        i.Link("badge-ledger", "dispatch", LinkKind.Corroborates, Now);
        return i;
    }
    [Test]
    public void RevisionKeepsIdentityAndEndpointsAndAdvancesOnlyRootOnce()
    {
        var i = Ready(); var link = i.Links.First(); var version = i.Version;
        var identity = (link.Id, link.InvestigationId, link.SourceId, link.TargetId);
        i.ReviseLink(link.Id, LinkKind.Contradicts, "  " + new string('证', 20) + "  ", Now.AddMinutes(1));
        Assert.Multiple(() =>
        {
            Assert.That((link.Id, link.InvestigationId, link.SourceId, link.TargetId), Is.EqualTo(identity));
            Assert.That(link.Kind, Is.EqualTo(LinkKind.Contradicts));
            Assert.That(link.Rationale, Is.EqualTo(new string('证', 20)));
            Assert.That(link.RevisedAt, Is.EqualTo(Now.AddMinutes(1)));
            Assert.That(i.Version, Is.EqualTo(version + 1));
            Assert.That(i.Links.Count, Is.EqualTo(2));
        });
        var e = Assert.Throws<DomainRule>(() => i.ReviseLink(link.Id, link.Kind, link.Rationale!, Now));
        Assert.That(e!.Code, Is.EqualTo("link_unchanged"));
        Assert.That(i.Version, Is.EqualTo(version + 1));
    }
    [TestCase(19, false), TestCase(20, true), TestCase(500, true), TestCase(501, false)]
    public void ExplanationUsesUnicodeScalarsMatchingPostgresCharacterLength(int count, bool valid)
    {
        var i = Ready(); var link = i.Links.First(); var version = i.Version;
        var text = string.Concat(Enumerable.Repeat("🔎", count)); // Two UTF-16 code units, one scalar.
        if (valid) { i.ReviseLink(link.Id, link.Kind, text, Now); Assert.That(i.Version, Is.EqualTo(version + 1)); }
        else { Assert.Throws<DomainRule>(() => i.ReviseLink(link.Id, link.Kind, text, Now)); Assert.That(i.Version, Is.EqualTo(version)); }
    }
    [Test]
    public void UnknownLinkAndReviewStateRejectRevisionWithoutMutation()
    {
        var i = Ready(); var version = i.Version;
        Assert.That(Assert.Throws<DomainRule>(() => i.ReviseLink(Guid.NewGuid(), LinkKind.Contradicts, new string('证', 20), Now))!.Code, Is.EqualTo("link_not_found"));
        Assert.That(i.Version, Is.EqualTo(version));
        i.Review(Now); version = i.Version;
        Assert.That(Assert.Throws<DomainRule>(() => i.ReviseLink(i.Links.First().Id, LinkKind.Contradicts, new string('证', 20), Now))!.Code, Is.EqualTo("investigation_readonly"));
        Assert.That(i.Version, Is.EqualTo(version));
        Assert.That(i.Links.All(l => l.Rationale is null), Is.True);
    }
}
