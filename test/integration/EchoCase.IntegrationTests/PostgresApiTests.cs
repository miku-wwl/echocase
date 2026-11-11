using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using EchoCase.Application;
using EchoCase.Infrastructure;
using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.EntityFrameworkCore;
using Npgsql;
using NUnit.Framework;

namespace EchoCase.IntegrationTests;

[TestFixture, Category("Integration"), NonParallelizable]
public sealed partial class PostgresApiTests
{
    private WebApplicationFactory<Program> _factory = null!;
    private HttpClient _alice = null!, _bob = null!;
    private string _aliceToken = "", _bobToken = "", _connection = "", _admin = "", _database = "";
    private static readonly JsonSerializerOptions Json = new(JsonSerializerDefaults.Web);
    private sealed class Factory(string connection) : WebApplicationFactory<Program>
    {
        protected override void ConfigureWebHost(IWebHostBuilder builder) => builder.UseEnvironment("Testing").UseSetting("ConnectionStrings:EchoCase", connection);
    }
    [OneTimeSetUp]
    public async Task Setup()
    {
        _admin = Environment.GetEnvironmentVariable("ECHOCASE_TEST_CONNECTION") ?? throw new InvalidOperationException("Set ECHOCASE_TEST_CONNECTION to a disposable PostgreSQL admin connection. Integration tests NEVER silently skip.");
        _database = "echocase_test_" + Guid.NewGuid().ToString("N");
        await using (var conn = new NpgsqlConnection(_admin)) { await conn.OpenAsync(); await new NpgsqlCommand($"CREATE DATABASE \"{_database}\"", conn).ExecuteNonQueryAsync(); }
        var cs = new NpgsqlConnectionStringBuilder(_admin) { Database = _database }; _connection = cs.ConnectionString;
        await using (var db = Context()) await db.Database.MigrateAsync();
        _factory = new Factory(_connection);
        (_alice, _aliceToken) = await User("alice"); (_bob, _bobToken) = await User("bob");
    }
    [OneTimeTearDown]
    public async Task Cleanup()
    {
        _alice?.Dispose(); _bob?.Dispose(); if (_factory is not null) await _factory.DisposeAsync();
        NpgsqlConnection.ClearAllPools();
        if (_database.StartsWith("echocase_test_", StringComparison.Ordinal))
        { await using var conn = new NpgsqlConnection(_admin); await conn.OpenAsync(); await new NpgsqlCommand($"DROP DATABASE IF EXISTS \"{_database}\" WITH (FORCE)", conn).ExecuteNonQueryAsync(); }
    }
    private EchoDbContext Context() => new(new DbContextOptionsBuilder<EchoDbContext>().UseNpgsql(_connection).Options);
    private async Task<(HttpClient, string)> User(string name)
    {
        var client = _factory.CreateClient(new() { HandleCookies = true, AllowAutoRedirect = false });
        var token = (await client.GetFromJsonAsync<CsrfResponse>("/api/auth/csrf"))!.Token;
        var credentials = new Credentials(name + "@example.test", "StrongLabPassword42");
        using var register = await Send(client, token, HttpMethod.Post, "/api/auth/register", credentials);
        Assert.That(register.StatusCode, Is.EqualTo(HttpStatusCode.OK), await register.Content.ReadAsStringAsync());
        using var login = await Send(client, token, HttpMethod.Post, "/api/auth/login", credentials);
        Assert.That(login.StatusCode, Is.EqualTo(HttpStatusCode.OK));
        token = (await client.GetFromJsonAsync<CsrfResponse>("/api/auth/csrf"))!.Token;
        return (client, token);
    }
    private static Task<HttpResponseMessage> Send(HttpClient client, string token, HttpMethod method, string url, object? body = null, int? version = null, string? key = null)
    {
        var request = new HttpRequestMessage(method, url);
        request.Headers.Add("X-CSRF-TOKEN", token); request.Headers.Add("Idempotency-Key", key ?? Guid.NewGuid().ToString());
        if (version is not null) request.Headers.TryAddWithoutValidation("If-Match", $"\"{version}\"");
        if (body is not null) request.Content = JsonContent.Create(body);
        return client.SendAsync(request);
    }
    private Task<HttpResponseMessage> Change(SessionView s, string route, object? body = null, string? key = null, int? version = null, HttpMethod? method = null) => Send(_alice, _aliceToken, method ?? HttpMethod.Post, $"/api/investigations/{s.Id}/{route}", body, version ?? s.Version, key);
    private async Task<SessionView> Start()
    {
        using var r = await Send(_alice, _aliceToken, HttpMethod.Post, "/api/investigations", new StartRequest("harbor-01"));
        Assert.That(r.StatusCode, Is.EqualTo(HttpStatusCode.OK), await r.Content.ReadAsStringAsync()); return (await r.Content.ReadFromJsonAsync<SessionView>(Json))!;
    }
    private static async Task<SessionView> Success(HttpResponseMessage r) { using (r) { Assert.That(r.StatusCode, Is.EqualTo(HttpStatusCode.OK), await r.Content.ReadAsStringAsync()); return (await r.Content.ReadFromJsonAsync<SessionView>(Json))!; } }

    [Test] public async Task AnonymousCannotReadCases() { using var client = _factory.CreateClient(new() { AllowAutoRedirect = false }); Assert.That((await client.GetAsync("/api/cases")).StatusCode, Is.EqualTo(HttpStatusCode.Unauthorized)); }
    [Test] public async Task ForeignOwnerCannotReadOrWrite() { var s = await Start(); Assert.That((await _bob.GetAsync($"/api/investigations/{s.Id}")).StatusCode, Is.EqualTo(HttpStatusCode.NotFound)); using var r = await Send(_bob, _bobToken, HttpMethod.Put, $"/api/investigations/{s.Id}/notes", new NotesRequest("intrusion"), s.Version); Assert.That(r.StatusCode, Is.EqualTo(HttpStatusCode.NotFound)); }
    [Test] public async Task CsrfIsRequiredEvenWithValidCookie() { var s = await Start(); using var r = await _alice.PutAsJsonAsync($"/api/investigations/{s.Id}/notes", new NotesRequest("x")); Assert.That(r.StatusCode, Is.EqualTo(HttpStatusCode.BadRequest)); }
    [Test] public async Task IfMatchAndIdempotencyHeadersAreRequired() { var s = await Start(); using var r = await Send(_alice, _aliceToken, HttpMethod.Put, $"/api/investigations/{s.Id}/notes", new NotesRequest("x")); Assert.That((int)r.StatusCode, Is.EqualTo(428)); using var r2 = await Change(s, "notes", new NotesRequest("x"), key: "bad", method: HttpMethod.Put); Assert.That((int)r2.StatusCode, Is.EqualTo(400)); }
    [Test] public async Task MalformedAndNullContractsAreRejected() { var s = await Start(); using var r = await Change(s, "notes", new { notes = (string?)null }, method: HttpMethod.Put); Assert.That((int)r.StatusCode, Is.EqualTo(400)); using var r2 = await Change(s, "notes", new { notes = "x", ownerId = "someone" }, method: HttpMethod.Put); Assert.That((int)r2.StatusCode, Is.EqualTo(400)); }
    [Test] public async Task HiddenEvidenceBodyNeverLeaks() { var s = await Start(); Assert.That(s.Evidence.All(e => e.Body is null), Is.True); using var r = await Change(s, "evidence/dispatch/examine"); Assert.That((int)r.StatusCode, Is.EqualTo(422)); }
    [Test] public async Task ReplayingStartReturnsSameInvestigation() { var key = Guid.NewGuid().ToString(); using var r1 = await Send(_alice, _aliceToken, HttpMethod.Post, "/api/investigations", new StartRequest("harbor-01"), key: key); using var r2 = await Send(_alice, _aliceToken, HttpMethod.Post, "/api/investigations", new StartRequest("harbor-01"), key: key); Assert.That(await r2.Content.ReadAsStringAsync(), Is.EqualTo(await r1.Content.ReadAsStringAsync())); }
    [Test] public async Task ReusedKeyWithChangedPayloadIsConflict() { var s = await Start(); var key = Guid.NewGuid().ToString(); await Success(await Change(s, "notes", new NotesRequest("first"), key: key, method: HttpMethod.Put)); using var r = await Change(s, "notes", new NotesRequest("different"), key: key, method: HttpMethod.Put); Assert.That((int)r.StatusCode, Is.EqualTo(409)); }
    [Test] public async Task SameKeyConcurrentRequestsCommitOnce() { var s = await Start(); var key = Guid.NewGuid().ToString(); var rs = await Task.WhenAll(Change(s, "notes", new NotesRequest("atomic"), key: key, method: HttpMethod.Put), Change(s, "notes", new NotesRequest("atomic"), key: key, method: HttpMethod.Put)); var a = await Success(rs[0]); var b = await Success(rs[1]); Assert.That(a.Version, Is.EqualTo(s.Version + 1)); Assert.That(b, Is.EqualTo(a).Using<SessionView>((x, y) => x.Id == y.Id && x.Version == y.Version)); await using var db = Context(); Assert.That(await db.Audit.CountAsync(x => x.InvestigationId == s.Id && x.Operation == "notes"), Is.EqualTo(1)); }
    [Test] public async Task DifferentKeysCompetingOnOneVersionHaveOneWinner() { var s = await Start(); var rs = await Task.WhenAll(Change(s, "notes", new NotesRequest("A"), method: HttpMethod.Put), Change(s, "notes", new NotesRequest("B"), method: HttpMethod.Put)); Assert.That(rs.Select(r => (int)r.StatusCode).Order(), Is.EqualTo(new[] { 200, 412 })); foreach (var r in rs) r.Dispose(); await using var db = Context(); Assert.That(await db.Receipts.CountAsync(x => x.Response.Contains(s.Id.ToString())), Is.EqualTo(2)); }
    [Test] public async Task StaleVersionDoesNotWriteOrCacheFailure() { var s = await Start(); var current = await Success(await Change(s, "notes", new NotesRequest("winner"), method: HttpMethod.Put)); var key = Guid.NewGuid().ToString(); using var r = await Change(s, "notes", new NotesRequest("loser"), key: key, method: HttpMethod.Put); Assert.That((int)r.StatusCode, Is.EqualTo(412)); await using var db = Context(); Assert.That(await db.Receipts.AnyAsync(x => x.Key == key), Is.False); var next = await Success(await Change(current, "notes", new NotesRequest("confirmed"), key: key, method: HttpMethod.Put)); Assert.That(next.Notes, Is.EqualTo("confirmed")); }
    [Test] public async Task DomainFailureRollsBackReceiptAndAudit() { var s = await Start(); var key = Guid.NewGuid().ToString(); using var r = await Change(s, "state/review", key: key); Assert.That((int)r.StatusCode, Is.EqualTo(422)); await using var db = Context(); Assert.That(await db.Receipts.AnyAsync(x => x.Key == key), Is.False); Assert.That(await db.Audit.CountAsync(x => x.InvestigationId == s.Id), Is.EqualTo(1)); }
    [Test] public async Task DatabaseRejectsLinkToUndiscoveredEvidence() { var s = await Start(); await using var conn = new NpgsqlConnection(_connection); await conn.OpenAsync(); var cmd = new NpgsqlCommand("INSERT INTO \"Links\" (\"Id\",\"InvestigationId\",\"SourceId\",\"TargetId\",\"Kind\") VALUES (@id,@i,'access-log','camera','Corroborates')", conn); cmd.Parameters.AddWithValue("id", Guid.NewGuid()); cmd.Parameters.AddWithValue("i", s.Id); var e = Assert.ThrowsAsync<PostgresException>(async () => await cmd.ExecuteNonQueryAsync()); Assert.That(e!.SqlState, Is.EqualTo("23503")); }
    [Test] public async Task FullWorkflowSurvivesFreshReadAndSubmissionIsImmutable() { var s = await Start(); foreach (var e in new[] { "access-log", "badge-ledger", "dispatch" }) s = await Success(await Change(s, $"evidence/{e}/examine")); s = await Success(await Change(s, "links", new LinkRequest("access-log", "badge-ledger", "Corroborates"))); s = await Success(await Change(s, "links", new LinkRequest("badge-ledger", "dispatch", "Corroborates"))); s = await Success(await Change(s, "state/review")); s = await Success(await Change(s, "verdict", new VerdictRequest("林澈", "门禁、领用册与调度消息形成互相印证的证据链，故提交此结论。", ["access-log", "badge-ledger", "dispatch"]))); var fresh = (await _alice.GetFromJsonAsync<SessionView>($"/api/investigations/{s.Id}", Json))!; Assert.That(fresh.Verdict!.Score, Is.EqualTo(100)); using var rejected = await Change(s, "notes", new NotesRequest("no"), method: HttpMethod.Put); Assert.That((int)rejected.StatusCode, Is.EqualTo(422)); }
    [Test] public async Task ReadinessIsRealDatabaseCheck() { Assert.That((await _alice.GetAsync("/health/ready")).StatusCode, Is.EqualTo(HttpStatusCode.OK)); }
    [Test] public async Task TraceAndSecurityHeadersArePresent() { using var r = await _alice.GetAsync("/api/cases"); Assert.That(r.Headers.Contains("X-Trace-Id"), Is.True); Assert.That(r.Headers.GetValues("Content-Security-Policy").Single(), Does.Contain("frame-ancestors 'none'")); Assert.That(r.Headers.CacheControl!.NoStore, Is.True); }
    [Test, Order(100)] public async Task AuthenticationRateLimitActuallyRejectsBurst() { using var client = _factory.CreateClient(); var token = (await client.GetFromJsonAsync<CsrfResponse>("/api/auth/csrf"))!.Token; var statuses = new List<int>(); for (var n = 0; n < 16; n++) { using var r = await Send(client, token, HttpMethod.Post, "/api/auth/login", new Credentials("missing@example.test", "IncorrectPassword42")); statuses.Add((int)r.StatusCode); } Assert.That(statuses, Does.Contain(429)); }
}
