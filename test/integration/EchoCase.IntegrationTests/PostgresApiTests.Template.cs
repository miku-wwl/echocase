using System.Net;
using System.Net.Http.Json;
using System.Security.Claims;
using EchoCase.Application;
using EchoCase.Application.Common.Interfaces;
using EchoCase.Application.Common.Models;
using EchoCase.Application.Investigations;
using EchoCase.Domain;
using EchoCase.Infrastructure;
using MediatR;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.TestHost;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using NUnit.Framework;

namespace EchoCase.IntegrationTests;

public sealed partial class PostgresApiTests
{
    private sealed class FailSecondIdentityLookup : IIdentityService
    {
        public int Calls;
        public Task<string?> GetUserNameAsync(string userId) => Interlocked.Increment(ref Calls) == 1
            ? Task.FromResult<string?>("fixture-user")
            : throw new InvalidOperationException("An auxiliary identity lookup after commit must not run");
        public Task<bool> IsInRoleAsync(string userId, string role) => throw new NotSupportedException();
        public Task<bool> AuthorizeAsync(string userId, string policyName) => throw new NotSupportedException();
        public Task<(Result Result, string UserId)> CreateUserAsync(string userName, string password) => throw new NotSupportedException();
        public Task<Result> DeleteUserAsync(string userId) => throw new NotSupportedException();
    }
    private sealed class SlowAfterCommitStore(PostgresInvestigationStore inner) : IInvestigationStore
    {
        public Task<IReadOnlyList<SessionView>> ListAsync(string ownerId, CancellationToken ct) => inner.ListAsync(ownerId, ct);
        public Task<SessionView> GetAsync(Guid id, string ownerId, CancellationToken ct) => inner.GetAsync(id, ownerId, ct);
        public async Task<SessionView> WriteAsync(Change change, Func<Investigation?, Investigation> apply, CancellationToken ct)
        {
            var committed = await inner.WriteAsync(change, apply, ct);
            await Task.Delay(600, ct); // Exercise the template's >500ms telemetry branch.
            return committed;
        }
    }

    [Test]
    public async Task SlowCommittedWriteIsNotConvertedToFailureByTelemetryIdentityLookup()
    {
        var identity = new FailSecondIdentityLookup();
        using var factory = new Factory(_connection).WithWebHostBuilder(builder => builder.ConfigureTestServices(services =>
        {
            services.AddSingleton<IIdentityService>(identity);
            services.AddScoped<PostgresInvestigationStore>();
            services.AddScoped<IInvestigationStore>(sp => new SlowAfterCommitStore(sp.GetRequiredService<PostgresInvestigationStore>()));
        }));
        using var client = factory.CreateClient(new() { HandleCookies = true, AllowAutoRedirect = false });
        var token = (await client.GetFromJsonAsync<CsrfResponse>("/api/auth/csrf"))!.Token;
        using var login = await Send(client, token, HttpMethod.Post, "/api/auth/login", new Credentials("alice@example.test", "StrongLabPassword42"));
        Assert.That(login.StatusCode, Is.EqualTo(HttpStatusCode.OK));
        token = (await client.GetFromJsonAsync<CsrfResponse>("/api/auth/csrf"))!.Token;
        var key = Guid.NewGuid().ToString();
        var result = await Success(await Send(client, token, HttpMethod.Post, "/api/investigations", new StartRequest("harbor-01"), key: key));
        Assert.That(identity.Calls, Is.EqualTo(1), "Only pre-handler logging may resolve the display name");
        await using var db = Context();
        Assert.That(await db.Receipts.CountAsync(x => x.Key == key), Is.EqualTo(1));
        Assert.That(await db.Audit.CountAsync(x => x.InvestigationId == result.Id), Is.EqualTo(1));
    }

    [Test]
    public async Task TemplateAuthorizationProtectsDirectSenderWithoutHttpEndpoint()
    {
        await using var scope = _factory.Services.CreateAsyncScope();
        var sender = scope.ServiceProvider.GetRequiredService<ISender>();
        Assert.ThrowsAsync<UnauthorizedAccessException>(async () => await sender.Send(new GetCasesQuery()));
    }

    [Test]
    public async Task TemplateValidationRejectsDirectSenderBeforeAnyTransactionWrites()
    {
        var session = await Start();
        var owner = (await _alice.GetFromJsonAsync<UserView>("/api/auth/me"))!;
        await using var scope = _factory.Services.CreateAsyncScope();
        var accessor = scope.ServiceProvider.GetRequiredService<IHttpContextAccessor>();
        var previous = accessor.HttpContext;
        try
        {
            accessor.HttpContext = new DefaultHttpContext
            {
                User = new ClaimsPrincipal(new ClaimsIdentity([new Claim(ClaimTypes.NameIdentifier, owner.Id)], "EchoCase"))
            };
            var sender = scope.ServiceProvider.GetRequiredService<ISender>();
            var exception = Assert.ThrowsAsync<Application.Common.Exceptions.ValidationException>(async () =>
                await sender.Send(new SaveNotesCommand(session.Id, "not-a-uuid", session.Version, new NotesRequest("must not commit"))));
            Assert.That(exception!.Errors, Contains.Key("Key"));
        }
        finally { accessor.HttpContext = previous; }
        await using var db = Context();
        Assert.That((await db.Investigations.SingleAsync(x => x.Id == session.Id)).Version, Is.EqualTo(session.Version));
        Assert.That(await db.Receipts.AnyAsync(x => x.Key == "not-a-uuid"), Is.False);
        Assert.That(await db.Audit.CountAsync(x => x.InvestigationId == session.Id), Is.EqualTo(1));
    }

    [Test]
    public async Task FormerOwnerCannotReplayReceiptAfterResourceOwnershipChanges()
    {
        var session = await Start();
        var key = Guid.NewGuid().ToString();
        var body = new NotesRequest("receipt must remain behind resource ownership verification");
        await Success(await Change(session, "notes", body, key, method: HttpMethod.Put));
        var bob = (await _bob.GetFromJsonAsync<UserView>("/api/auth/me"))!;
        // Fixture-only transfer: there is deliberately no production transfer API.
        await using (var db = Context())
            await db.Database.ExecuteSqlInterpolatedAsync($"UPDATE \"Investigations\" SET \"OwnerId\"={bob.Id} WHERE \"Id\"={session.Id}");
        using var replay = await Change(session, "notes", body, key, method: HttpMethod.Put);
        Assert.That(replay.StatusCode, Is.EqualTo(HttpStatusCode.NotFound));
        var visibleToBob = (await _bob.GetFromJsonAsync<SessionView>($"/api/investigations/{session.Id}"))!;
        Assert.That(visibleToBob.Notes, Is.EqualTo(body.Notes));
        Assert.That(visibleToBob.Version, Is.EqualTo(session.Version + 1));
        await using var check = Context();
        Assert.That(await check.Receipts.CountAsync(x => x.Key == key), Is.EqualTo(1));
    }

    [Test]
    public async Task TemplateIntegrationIntroducesNoDatabaseModelOrMigrationDrift()
    {
        await using var db = Context();
        Assert.That(db.Database.HasPendingModelChanges(), Is.False);
        Assert.That(await db.Database.GetAppliedMigrationsAsync(), Is.EqualTo(new[] {
            "20261111024947_InitialInvestigation", "20261111030224_InvestigationOwnerTimeline", "20261111060117_LinkRevisionExplanation"
        }));
    }
}
