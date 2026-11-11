using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using System.Text.Json.Nodes;
using EchoCase.Application;
using EchoCase.Domain;
using EchoCase.Infrastructure;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage;
using NUnit.Framework;

namespace EchoCase.Tests;

public sealed partial class PostgresApiTests
{
    [Test]
    public async Task TwoLoadedAggregateRevisionsRaceAtDatabaseAndRollbackTheLosingReceiptAndChild()
    {
        var s = await Linked();
        await using var lookup = Context();
        var owner = (await lookup.Investigations.SingleAsync(x => x.Id == s.Id)).OwnerId;
        var recorder = new SqlObservation();
        using var barrier = new Barrier(2);
        var keys = new[] { Guid.NewGuid().ToString(), Guid.NewGuid().ToString() };
        var isolations = new System.Collections.Concurrent.ConcurrentBag<string>();
        async Task<(SessionView? Result, ApplicationFault? Error)> Attempt(int n)
        {
            await using var db = new EchoDbContext(new DbContextOptionsBuilder<EchoDbContext>().UseNpgsql(_connection).AddInterceptors(recorder).Options);
            try
            {
                var result = await new PostgresInvestigationStore(db, TimeProvider.System).WriteAsync(new(owner, keys[n], new string((char)('A' + n), 64), s.Id, s.Version, "revise-link"), i =>
                {
                    isolations.Add(db.Database.CurrentTransaction!.GetDbTransaction().IsolationLevel.ToString());
                    if (!barrier.SignalAndWait(TimeSpan.FromSeconds(20))) throw new TimeoutException("Both real SQL reads must reach the race barrier.");
                    i!.ReviseLink(s.Links.Single().Id, LinkKind.Contradicts, new string((char)('甲' + n), 20), DateTimeOffset.UtcNow);
                    return i;
                }, default);
                return (result, null);
            }
            catch (ApplicationFault e) { return (null, e); }
        }
        var attempts = await Task.WhenAll(Task.Run(() => Attempt(0)), Task.Run(() => Attempt(1)));
        Assert.That(attempts.Count(x => x.Result is not null), Is.EqualTo(1));
        Assert.That(attempts.Single(x => x.Error is not null).Error!.Status, Is.EqualTo(412));
        await using var check = Context();
        var saved = await check.Investigations.Include(x => x.Links).SingleAsync(x => x.Id == s.Id);
        Assert.That(saved.Version, Is.EqualTo(s.Version + 1));
        Assert.That(saved.Links.Single().Rationale, Is.EqualTo(attempts.Single(x => x.Result is not null).Result!.Links.Single().Rationale));
        Assert.That(await check.Receipts.CountAsync(x => keys.Contains(x.Key)), Is.EqualTo(1));
        Assert.That(await check.Audit.CountAsync(x => x.InvestigationId == s.Id && x.Operation == "revise-link"), Is.EqualTo(1));
        Assert.That(isolations, Is.All.EqualTo("ReadCommitted"));
        SqlObservation.Save("store-race", new { isolation = isolations, results = attempts.Select(x => x.Error?.Status ?? 200), survivingReceipts = 1, survivingRevisionAudit = 1, finalVersion = saved.Version, commands = recorder.Commands.ToArray() });
    }
    private async Task<SessionView> Linked()
    {
        var s = await Start();
        foreach (var e in new[] { "access-log", "badge-ledger" }) s = await Success(await Change(s, $"evidence/{e}/examine"));
        return await Success(await Change(s, "links", new LinkRequest("access-log", "badge-ledger", "Corroborates")));
    }

    [Test]
    public async Task RevisionIsAtomicReplayableAndBoundToBothOwnerAndInvestigation()
    {
        var s = await Linked(); var link = s.Links.Single();
        var key = Guid.NewGuid().ToString(); var body = new ReviseLinkRequest("Contradicts", new string('证', 20));
        var path = $"links/{link.Id}";
        var responses = await Task.WhenAll(Change(s, path, body, key, method: HttpMethod.Put), Change(s, path, body, key, method: HttpMethod.Put));
        var first = await Success(responses[0]); var replay = await Success(responses[1]);
        Assert.That(JsonSerializer.Serialize(replay), Is.EqualTo(JsonSerializer.Serialize(first)));
        Assert.That(first.Version, Is.EqualTo(s.Version + 1));
        Assert.That(first.Links.Single(), Is.EqualTo(link with { Kind = "Contradicts", Rationale = body.Rationale, RevisedAt = first.Links.Single().RevisedAt }));
        Assert.That(first.Links.Single().RevisedAt, Is.Not.Null);
        await using var db = Context();
        Assert.That(await db.Audit.CountAsync(x => x.InvestigationId == s.Id && x.Operation == "revise-link"), Is.EqualTo(1));
        Assert.That(await db.Receipts.CountAsync(x => x.Key == key), Is.EqualTo(1));

        // Idempotency confirms the original result even after a different successful command.
        var later = await Success(await Change(first, "notes", new NotesRequest("newer"), method: HttpMethod.Put));
        var old = await Success(await Change(s, path, body, key, method: HttpMethod.Put));
        Assert.That(old.Version, Is.EqualTo(first.Version));
        Assert.That((await _alice.GetFromJsonAsync<SessionView>($"/api/investigations/{s.Id}", Json))!.Version, Is.EqualTo(later.Version));
        using var misuse = await Change(s, path, body with { Rationale = new string('改', 20) }, key, method: HttpMethod.Put);
        Assert.That(misuse.StatusCode, Is.EqualTo(HttpStatusCode.Conflict));
        using var foreign = await Send(_bob, _bobToken, HttpMethod.Put, $"/api/investigations/{s.Id}/{path}", body, later.Version, key);
        Assert.That(foreign.StatusCode, Is.EqualTo(HttpStatusCode.NotFound));
        var another = await Start();
        using var wrongResource = await Change(another, path, body, method: HttpMethod.Put);
        Assert.That((int)wrongResource.StatusCode, Is.EqualTo(422));
    }

    [Test]
    public async Task RevisionRejectsInvalidAndStaleWritesWithoutLeavingReceiptsOrAudit()
    {
        var s = await Linked(); var path = $"links/{s.Links.Single().Id}";
        var invalid = new[] { new ReviseLinkRequest("0", new string('证', 20)), new ReviseLinkRequest("Contradicts", "too short") };
        foreach (var body in invalid)
        {
            var key = Guid.NewGuid().ToString();
            using var r = await Change(s, path, body, key, method: HttpMethod.Put);
            Assert.That((int)r.StatusCode, Is.EqualTo(422));
            using var problem = JsonDocument.Parse(await r.Content.ReadAsStringAsync());
            Assert.That(problem.RootElement.GetProperty("traceId").GetString(), Is.EqualTo(r.Headers.GetValues("X-Trace-Id").Single()));
            await using var db = Context(); Assert.That(await db.Receipts.AnyAsync(x => x.Key == key), Is.False);
        }
        var current = await Success(await Change(s, path, new ReviseLinkRequest("Corroborates", string.Concat(Enumerable.Repeat("🔎", 500))), method: HttpMethod.Put));
        var staleKey = Guid.NewGuid().ToString();
        using var stale = await Change(s, path, new ReviseLinkRequest("Contradicts", new string('失', 20)), staleKey, method: HttpMethod.Put);
        Assert.That((int)stale.StatusCode, Is.EqualTo(412));
        await using var check = Context();
        Assert.That(await check.Receipts.AnyAsync(x => x.Key == staleKey), Is.False);
        Assert.That(await check.Audit.CountAsync(x => x.InvestigationId == s.Id && x.Operation == "revise-link"), Is.EqualTo(1));
        var fresh = (await _alice.GetFromJsonAsync<SessionView>($"/api/investigations/{s.Id}", Json))!;
        SqlObservation.Save("timestamp-precision", new { responseTicks = current.Links.Single().RevisedAt!.Value.Ticks, readTicks = fresh.Links.Single().RevisedAt!.Value.Ticks });
        Assert.That(fresh.Links.Single().RevisedAt!.Value.Ticks, Is.EqualTo(current.Links.Single().RevisedAt!.Value.Ticks), "Immediate response and PostgreSQL read must agree at their declared microsecond precision.");
        Assert.That(fresh.Links, Is.EqualTo(current.Links));
    }

    [Test]
    public async Task StoredPhaseOneLinkReceiptCanBeReplayedAfterContractExpansion()
    {
        var s = await Start();
        foreach (var e in new[] { "access-log", "badge-ledger" }) s = await Success(await Change(s, $"evidence/{e}/examine"));
        var key = Guid.NewGuid().ToString(); var body = new LinkRequest("access-log", "badge-ledger", "Corroborates");
        var result = await Success(await Change(s, "links", body, key));
        await using (var db = Context())
        {
            var receipt = await db.Receipts.SingleAsync(x => x.Key == key);
            var json = JsonNode.Parse(receipt.Response)!;
            foreach (var l in json["Links"]!.AsArray()) { l!.AsObject().Remove("Rationale"); l.AsObject().Remove("RevisedAt"); }
            receipt.Response = json.ToJsonString(); await db.SaveChangesAsync();
        }
        var replay = await Success(await Change(s, "links", body, key));
        Assert.That(replay.Version, Is.EqualTo(result.Version));
        Assert.That(replay.Links, Is.EqualTo(result.Links));
    }
}
