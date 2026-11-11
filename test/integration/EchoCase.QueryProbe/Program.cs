using System.Data.Common;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Nodes;
using EchoCase.Infrastructure;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;
using Npgsql;

var admin = Environment.GetEnvironmentVariable("ECHOCASE_TEST_CONNECTION") ?? throw new InvalidOperationException("Set a disposable PostgreSQL admin connection.");
var directory = args.Length == 1 ? args[0] : "test/integration/TestResults/query-probe";
Directory.CreateDirectory(directory);
var name = "echocase_probe_" + Guid.NewGuid().ToString("N");
await using var control = new NpgsqlConnection(admin); await control.OpenAsync();
await new NpgsqlCommand($"CREATE DATABASE \"{name}\"", control).ExecuteNonQueryAsync();
var connection = new NpgsqlConnectionStringBuilder(admin) { Database = name }.ConnectionString;
var capture = new Capture();
try
{
    await using var db = new EchoDbContext(new DbContextOptionsBuilder<EchoDbContext>().UseNpgsql(connection).AddInterceptors(capture).Options);
    await db.Database.MigrateAsync();
    const int roots = 30_000, owners = 100;
    await db.Database.ExecuteSqlRawAsync("""
        INSERT INTO "AspNetUsers" ("Id","UserName","EmailConfirmed","PhoneNumberConfirmed","TwoFactorEnabled","LockoutEnabled","AccessFailedCount")
        SELECT 'probe-owner-' || g, 'probe-' || g, false,false,false,false,0 FROM generate_series(0,99) g;
        INSERT INTO "Investigations" ("Id","OwnerId","CaseId","Status","Version","Notes","CreatedAt","UpdatedAt")
        SELECT md5(g::text)::uuid, 'probe-owner-' || (g % 100), 'harbor-01','Active',4,'synthetic query probe',
            '2026-11-11T00:00:00Z'::timestamptz - g * interval '1 second',
            '2026-11-11T00:00:00Z'::timestamptz - g * interval '1 second'
        FROM generate_series(1,30000) g;
        INSERT INTO "Discoveries" ("InvestigationId","EvidenceId","ExaminedAt")
        SELECT "Id", e, "CreatedAt" FROM "Investigations" CROSS JOIN (VALUES ('access-log'),('badge-ledger')) v(e);
        INSERT INTO "Links" ("Id","InvestigationId","SourceId","TargetId","Kind")
        SELECT md5('link' || "Id"::text)::uuid, "Id", 'access-log','badge-ledger','Corroborates' FROM "Investigations";
        ANALYZE;
        """);
    // Capture the SQL and parameters from the actual production store, not a lookalike LINQ query.
    capture.Enabled = true;
    var sessions = await new PostgresInvestigationStore(db, TimeProvider.System).ListAsync("probe-owner-17", default);
    capture.Enabled = false;
    if (sessions.Count != 50 || sessions.Any(s => s.Links.Count != 1)) throw new InvalidOperationException("Unexpected production projection.");
    await using var conn = new NpgsqlConnection(connection); await conn.OpenAsync();
    async Task<JsonNode> Plan()
    {
        await using var command = new NpgsqlCommand("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + capture.Sql, conn);
        foreach (var (parameter, value) in capture.Parameters) command.Parameters.AddWithValue(parameter, value);
        return JsonNode.Parse((string)(await command.ExecuteScalarAsync())!)![0]!;
    }
    async Task<object> Sample()
    {
        var warmup = await Plan();
        var plans = new List<JsonNode>();
        for (var n = 0; n < 7; n++) plans.Add(await Plan());
        return new { warmupExcludedMs = (double)warmup["Execution Time"]!, executionMs = plans.Select(p => (double)p["Execution Time"]!).ToArray(), representativePlan = plans[3] };
    }
    // Only this newly created database is changed. Initial schema used OwnerId
    // alone; migration 2 replaced it with the composite. Compare both and no index.
    await new NpgsqlCommand("DROP INDEX \"IX_Investigations_OwnerId_UpdatedAt\"", conn).ExecuteNonQueryAsync();
    var withoutComposite = await Sample();
    await new NpgsqlCommand("CREATE INDEX \"IX_Investigations_OwnerId\" ON \"Investigations\" (\"OwnerId\")", conn).ExecuteNonQueryAsync();
    var ownerOnly = await Sample();
    await new NpgsqlCommand("DROP INDEX \"IX_Investigations_OwnerId\"", conn).ExecuteNonQueryAsync();
    await new NpgsqlCommand("CREATE INDEX \"IX_Investigations_OwnerId_UpdatedAt\" ON \"Investigations\" (\"OwnerId\", \"UpdatedAt\" DESC)", conn).ExecuteNonQueryAsync();
    var withComposite = await Sample();
    var output = new {
        capturedAtUtc = DateTimeOffset.UtcNow, runtime = RuntimeInformation.FrameworkDescription,
        os = RuntimeInformation.OSDescription, postgres = conn.PostgreSqlVersion.ToString(),
        roots, owners, rootsForOwner = roots / owners, discoveries = roots * 2, links = roots,
        returnedInvestigations = sessions.Count, returnedJoinRows = sessions.Count * 2,
        querySource = "PostgresInvestigationStore.ListAsync, actual intercepted DbCommand",
        sql = capture.Sql, parameters = capture.Parameters,
        withoutComposite, ownerOnly, withComposite,
        limits = "Synthetic data in real application tables; single local PostgreSQL instance; seven warm-cache observations per arm in a fixed order; no concurrent writers, network latency or production distribution. Demonstrates an existing index, not a new product optimization."
    };
    await File.WriteAllTextAsync(Path.Combine(directory, "application-query-plan.json"), JsonSerializer.Serialize(output, new JsonSerializerOptions { WriteIndented = true }));
    Console.WriteLine($"Recorded real store query: {sessions.Count} investigations, {roots} seeded roots; disposable database removed in finally.");
}
finally
{
    NpgsqlConnection.ClearAllPools();
    // Name is a constant prefix plus a generated GUID, never a user supplied identifier.
    await new NpgsqlCommand($"DROP DATABASE \"{name}\" WITH (FORCE)", control).ExecuteNonQueryAsync();
}

sealed class Capture : DbCommandInterceptor
{
    public bool Enabled { get; set; }
    public string Sql { get; private set; } = "";
    public Dictionary<string, object> Parameters { get; private set; } = new();
    public override ValueTask<InterceptionResult<DbDataReader>> ReaderExecutingAsync(DbCommand command, CommandEventData data, InterceptionResult<DbDataReader> result, CancellationToken ct = default)
    {
        if (Enabled) { Sql = command.CommandText; Parameters = command.Parameters.Cast<DbParameter>().ToDictionary(p => p.ParameterName, p => p.Value!); }
        return ValueTask.FromResult(result);
    }
}
