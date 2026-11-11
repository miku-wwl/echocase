using EchoCase.Domain;
using EchoCase.Infrastructure;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql;
using NUnit.Framework;

namespace EchoCase.Tests;

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
        EchoDbContext New() => new(new DbContextOptionsBuilder<EchoDbContext>().UseNpgsql(connection).Options);
        try
        {
            Guid id;
            await using (var db = New())
            {
                await db.GetService<IMigrator>().MigrateAsync("20261111024947_InitialInvestigation");
                var user = new Investigator { UserName = "migration@example.test", Email = "migration@example.test" }; db.Users.Add(user);
                var i = Investigation.Start(user.Id, "harbor-01", DateTimeOffset.UtcNow); i.SaveNotes("升级前的数据必须保留", DateTimeOffset.UtcNow); id = i.Id; db.Investigations.Add(i); await db.SaveChangesAsync();
                await db.Database.MigrateAsync(); db.ChangeTracker.Clear();
                Assert.That((await db.Investigations.SingleAsync(x => x.Id == id)).Notes, Is.EqualTo("升级前的数据必须保留"));
                Assert.That((await db.Database.GetAppliedMigrationsAsync()).Count(), Is.GreaterThanOrEqualTo(2));
            }
            await using var first = New(); await using var second = New();
            var a = await first.Investigations.SingleAsync(x => x.Id == id); var b = await second.Investigations.SingleAsync(x => x.Id == id);
            a.SaveNotes("first", DateTimeOffset.UtcNow); b.SaveNotes("second", DateTimeOffset.UtcNow); await first.SaveChangesAsync();
            Assert.ThrowsAsync<DbUpdateConcurrencyException>(async () => await second.SaveChangesAsync());
        }
        finally
        {
            NpgsqlConnection.ClearAllPools();
            await new NpgsqlCommand($"DROP DATABASE \"{name}\" WITH (FORCE)", control).ExecuteNonQueryAsync();
        }
    }
}
