using System.Collections.Concurrent;
using System.Data.Common;
using System.Text.Json;
using Microsoft.EntityFrameworkCore.Diagnostics;

namespace EchoCase.Tests;

// Records executed SQL, never credential or business parameter values.
internal sealed class SqlObservation : DbCommandInterceptor
{
    public ConcurrentQueue<string> Commands { get; } = new();
    public override ValueTask<InterceptionResult<DbDataReader>> ReaderExecutingAsync(DbCommand command, CommandEventData data, InterceptionResult<DbDataReader> result, CancellationToken ct = default)
    { Commands.Enqueue(command.CommandText); return ValueTask.FromResult(result); }
    public override ValueTask<InterceptionResult<int>> NonQueryExecutingAsync(DbCommand command, CommandEventData data, InterceptionResult<int> result, CancellationToken ct = default)
    { Commands.Enqueue(command.CommandText); return ValueTask.FromResult(result); }
    public override ValueTask<InterceptionResult<object>> ScalarExecutingAsync(DbCommand command, CommandEventData data, InterceptionResult<object> result, CancellationToken ct = default)
    { Commands.Enqueue(command.CommandText); return ValueTask.FromResult(result); }
    public static void Save(string name, object observation)
    {
        var directory = Environment.GetEnvironmentVariable("ECHOCASE_PHASE2_EVIDENCE");
        if (directory is null) return;
        Directory.CreateDirectory(directory);
        File.WriteAllText(Path.Combine(directory, name + ".json"), JsonSerializer.Serialize(observation, new JsonSerializerOptions { WriteIndented = true }));
    }
}
