using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Text.Json;
using EchoCase.Application;
using EchoCase.Domain;
using Microsoft.EntityFrameworkCore;
using Npgsql;

namespace EchoCase.Infrastructure;

public sealed class PostgresInvestigationStore(EchoDbContext db, TimeProvider clock) : IInvestigationStore
{
    public static readonly ActivitySource Activities = new("EchoCase");
    private static readonly Meter Meter = new("EchoCase");
    private static readonly Counter<long> Conflicts = Meter.CreateCounter<long>("echocase.conflicts");
    private static readonly Counter<long> Replays = Meter.CreateCounter<long>("echocase.idempotent_replays");
    // One statement gives a coherent MVCC snapshot. This case bounds children to 6 / 15.
    private IQueryable<Investigation> Graph => db.Investigations.Include(x => x.Discoveries).Include(x => x.Links).AsSingleQuery();

    public async Task<IReadOnlyList<SessionView>> ListAsync(string ownerId, CancellationToken ct) =>
        (await Graph.AsNoTracking().Where(x => x.OwnerId == ownerId).OrderByDescending(x => x.UpdatedAt).Take(50).ToListAsync(ct)).Select(SessionPresenter.Map).ToArray();
    public async Task<SessionView> GetAsync(Guid id, string ownerId, CancellationToken ct) =>
        SessionPresenter.Map(await Graph.AsNoTracking().SingleOrDefaultAsync(x => x.Id == id && x.OwnerId == ownerId, ct) ?? throw Missing());

    public async Task<SessionView> WriteAsync(Change c, Func<Investigation?, Investigation> apply, CancellationToken ct)
    {
        using var activity = Activities.StartActivity("investigation." + c.Operation);
        await using var tx = await db.Database.BeginTransactionAsync(ct);
        // A database-scoped lock, released on commit/rollback; unrelated keys proceed independently.
        var lockName = c.OwnerId + ":" + c.Key;
        await db.Database.ExecuteSqlInterpolatedAsync($"SELECT pg_advisory_xact_lock(hashtextextended({lockName}, 0))", ct);
        Investigation? aggregate = null;
        if (c.SessionId is { } id)
            aggregate = await Graph.SingleOrDefaultAsync(x => x.Id == id && x.OwnerId == c.OwnerId, ct) ?? throw Missing();
        var previous = await db.Receipts.AsNoTracking().SingleOrDefaultAsync(x => x.OwnerId == c.OwnerId && x.Key == c.Key, ct);
        if (previous is not null)
        {
            if (previous.Fingerprint != c.Fingerprint) throw new ApplicationFault(409, "key_reused", "此幂等键已用于其他请求。");
            Replays.Add(1);
            return JsonSerializer.Deserialize<SessionView>(previous.Response)!;
        }
        if (aggregate is not null && aggregate.Version != c.ExpectedVersion)
        {
            Conflicts.Add(1);
            throw new ApplicationFault(412, "version_conflict", "档案已被其他窗口修改。请刷新后重新确认操作。");
        }
        var result = apply(aggregate);
        if (aggregate is null) db.Investigations.Add(result);
        var response = SessionPresenter.Map(result);
        db.Receipts.Add(new() { OwnerId = c.OwnerId, Key = c.Key, Fingerprint = c.Fingerprint, Response = JsonSerializer.Serialize(response), CreatedAt = clock.GetUtcNow() });
        db.Audit.Add(new() { OwnerId = c.OwnerId, InvestigationId = result.Id, Operation = c.Operation, Version = result.Version, OccurredAt = clock.GetUtcNow() });
        try
        {
            await db.SaveChangesAsync(ct);
            await tx.CommitAsync(ct);
        }
        catch (DbUpdateConcurrencyException)
        {
            Conflicts.Add(1);
            throw new ApplicationFault(412, "version_conflict", "并发写入冲突。请刷新后重新确认操作。");
        }
        catch (DbUpdateException e) when (e.InnerException is PostgresException { SqlState: "23505", ConstraintName: "IX_Audit_InvestigationId_Version" })
        {
            // Audit can be inserted before the aggregate UPDATE in EF's batch.
            Conflicts.Add(1);
            throw new ApplicationFault(412, "version_conflict", "并发写入冲突。请刷新后重新确认操作。");
        }
        return response;
    }
    private static ApplicationFault Missing() => new(404, "investigation_not_found", "调查不存在或不可访问。");
}
