using EchoCase.Domain;
using EchoCase.Infrastructure;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql;
using NUnit.Framework;

namespace EchoCase.IntegrationTests;

[TestFixture, Category("Integration")]
public sealed class MigrationTests
{
    [Test]
    public async Task UpgradePreservesExistingInvestigationAndEfRejectsStaleTrackedWriter()
    {
        var admin = Environment.GetEnvironmentVariable("ECHOCASE_TEST_CONNECTION") ?? throw new InvalidOperationException("Set ECHOCASE_TEST_CONNECTION");
        var name = "echocase_test_" + Guid.NewGuid().ToString("N");
        await using var control = new NpgsqlConnection(admin); await control.OpenAsync();
        await new NpgsqlCommand($"CREATE DATABASE \"{name}\"", control).ExecuteNonQueryAsync();
        var connection = new NpgsqlConnectionStringBuilder(admin) { Database = name }.ConnectionString;
        var sql = new SqlObservation();
        EchoDbContext New() => new(new DbContextOptionsBuilder<EchoDbContext>().UseNpgsql(connection).AddInterceptors(sql).Options);
        try
        {
            Guid id; var linkId = Guid.NewGuid();
            await using (var db = New())
            {
                await db.GetService<IMigrator>().MigrateAsync("20261111030224_InvestigationOwnerTimeline");
                var user = new Investigator { UserName = "migration@example.test", Email = "migration@example.test" }; db.Users.Add(user);
                var i = Investigation.Start(user.Id, "harbor-01", DateTimeOffset.UtcNow);
                i.SaveNotes("升级前的数据必须保留", DateTimeOffset.UtcNow);
                i.Examine("access-log", DateTimeOffset.UtcNow); i.Examine("badge-ledger", DateTimeOffset.UtcNow);
                id = i.Id; db.Investigations.Add(i); await db.SaveChangesAsync();
                // Use the old column list: current EF's Link model requires columns not present yet.
                await db.Database.ExecuteSqlInterpolatedAsync($"INSERT INTO \"Links\" (\"Id\",\"InvestigationId\",\"SourceId\",\"TargetId\",\"Kind\") VALUES ({linkId},{id},'access-log','badge-ledger','Corroborates')");
                await db.Database.MigrateAsync(); db.ChangeTracker.Clear();
                var upgraded = await db.Investigations.Include(x => x.Links).SingleAsync(x => x.Id == id);
                Assert.That(upgraded.Notes, Is.EqualTo("升级前的数据必须保留"));
                Assert.That(upgraded.Links.Single().Id, Is.EqualTo(linkId));
                Assert.That(upgraded.Links.Single().Rationale, Is.Null);
                Assert.That(upgraded.Links.Single().RevisedAt, Is.Null);
                Assert.That((await db.Database.GetAppliedMigrationsAsync()).Count(), Is.EqualTo(3));
                // The database also rejects a half-populated revision pair.
                var rejected = Assert.ThrowsAsync<PostgresException>(async () => await db.Database.ExecuteSqlInterpolatedAsync($"UPDATE \"Links\" SET \"Rationale\"={new string('证', 20)} WHERE \"Id\"={linkId}"));
                Assert.That(rejected!.ConstraintName, Is.EqualTo("ck_link_revision"));
            }
            await using var first = New(); await using var second = New();
            var a = await first.Investigations.Include(x => x.Links).SingleAsync(x => x.Id == id);
            var b = await second.Investigations.Include(x => x.Links).SingleAsync(x => x.Id == id);
            var originalVersion = a.Version;
            first.ChangeTracker.AutoDetectChangesEnabled = false;
            a.ReviseLink(linkId, LinkKind.Contradicts, new string('胜', 20), DateTimeOffset.UtcNow);
            var beforeDetect = first.ChangeTracker.Entries().Select(e => new { Entity = e.Entity.GetType().Name, State = e.State.ToString() }).ToArray();
            first.ChangeTracker.DetectChanges();
            var afterDetect = first.ChangeTracker.Entries().Select(e => new { Entity = e.Entity.GetType().Name, State = e.State.ToString(), Modified = e.Properties.Where(p => p.IsModified).Select(p => p.Metadata.Name).ToArray() }).ToArray();
            Assert.That(afterDetect.Single(e => e.Entity == "EvidenceLink").Modified, Is.EquivalentTo(new[] { "Kind", "Rationale", "RevisedAt" }));
            Assert.That(afterDetect.Single(e => e.Entity == "Investigation").Modified, Does.Contain("Version"));
            b.ReviseLink(linkId, LinkKind.Contradicts, new string('败', 20), DateTimeOffset.UtcNow);
            await first.SaveChangesAsync();
            Assert.ThrowsAsync<DbUpdateConcurrencyException>(async () => await second.SaveChangesAsync());
            await using var fresh = New();
            var saved = await fresh.Investigations.Include(x => x.Links).SingleAsync(x => x.Id == id);
            Assert.That(saved.Version, Is.EqualTo(originalVersion + 1));
            Assert.That(saved.Links.Single().Rationale, Is.EqualTo(new string('胜', 20)), "The stale child's UPDATE must roll back with the failed root UPDATE.");
            Assert.That(sql.Commands.Any(c => c.Contains("UPDATE \"Investigations\"") && c.Contains("AND \"Version\" =")), Is.True);
            SqlObservation.Save("migration-tracking", new { legacyId = id, linkId, beforeDetect, afterDetect, originalVersion, savedVersion = saved.Version, legacyRationale = (string?)null, staleWrite = "DbUpdateConcurrencyException; child mutation rolled back", commands = sql.Commands.ToArray() });
        }
        finally
        {
            NpgsqlConnection.ClearAllPools();
            await new NpgsqlCommand($"DROP DATABASE \"{name}\" WITH (FORCE)", control).ExecuteNonQueryAsync();
        }
    }
}
