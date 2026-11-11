using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Design;
namespace EchoCase.Infrastructure;

public sealed class DesignTimeFactory : IDesignTimeDbContextFactory<EchoDbContext>
{
    public EchoDbContext CreateDbContext(string[] args) => new(new DbContextOptionsBuilder<EchoDbContext>().UseNpgsql(
        Environment.GetEnvironmentVariable("ConnectionStrings__EchoCase") ?? throw new InvalidOperationException("Set ConnectionStrings__EchoCase before generating migrations.")).Options);
}
