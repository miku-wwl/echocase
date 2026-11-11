using EchoCase.Domain;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Identity.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore;

namespace EchoCase.Infrastructure;

public sealed class Investigator : IdentityUser;
public sealed class Receipt
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string OwnerId { get; set; } = "";
    public string Key { get; set; } = "";
    public string Fingerprint { get; set; } = "";
    public string Response { get; set; } = "";
    public DateTimeOffset CreatedAt { get; set; }
}
public sealed class AuditEntry
{
    public long Id { get; set; }
    public Guid InvestigationId { get; set; }
    public string OwnerId { get; set; } = "";
    public string Operation { get; set; } = "";
    public int Version { get; set; }
    public DateTimeOffset OccurredAt { get; set; }
}

public sealed class EchoDbContext(DbContextOptions<EchoDbContext> options) : IdentityDbContext<Investigator>(options)
{
    public DbSet<Investigation> Investigations => Set<Investigation>();
    public DbSet<Discovery> Discoveries => Set<Discovery>();
    public DbSet<EvidenceLink> Links => Set<EvidenceLink>();
    public DbSet<Receipt> Receipts => Set<Receipt>();
    public DbSet<AuditEntry> Audit => Set<AuditEntry>();
    protected override void OnModelCreating(ModelBuilder b)
    {
        base.OnModelCreating(b);
        var i = b.Entity<Investigation>();
        i.ToTable("Investigations", t => { t.HasCheckConstraint("ck_version", "\"Version\" > 0"); t.HasCheckConstraint("ck_status", "\"Status\" IN ('Active','Reviewing','Submitted')"); t.HasCheckConstraint("ck_verdict", "(\"Status\" = 'Submitted') = (\"Score\" IS NOT NULL)"); });
        i.HasKey(x => x.Id);
        i.Property(x => x.OwnerId).HasMaxLength(450);
        i.HasOne<Investigator>().WithMany().HasForeignKey(x => x.OwnerId).OnDelete(DeleteBehavior.Restrict);
        i.Property(x => x.CaseId).HasMaxLength(64);
        i.Property(x => x.Status).HasConversion<string>().HasMaxLength(24);
        i.Property(x => x.Version).IsConcurrencyToken();
        i.Property(x => x.Notes).HasMaxLength(4000);
        i.Property(x => x.Reasoning).HasMaxLength(4000);
        i.Property(x => x.Suspect).HasMaxLength(100);
        i.Property(x => x.SupportingEvidence).HasMaxLength(1000);
        i.HasMany(x => x.Discoveries).WithOne().HasForeignKey(x => x.InvestigationId).OnDelete(DeleteBehavior.Cascade);
        i.Navigation(x => x.Discoveries).UsePropertyAccessMode(PropertyAccessMode.Field);
        i.HasMany(x => x.Links).WithOne().HasForeignKey(x => x.InvestigationId).OnDelete(DeleteBehavior.Cascade);
        i.Navigation(x => x.Links).UsePropertyAccessMode(PropertyAccessMode.Field);
        var d = b.Entity<Discovery>();
        d.HasKey(x => new { x.InvestigationId, x.EvidenceId });
        d.Property(x => x.EvidenceId).HasMaxLength(64);
        var l = b.Entity<EvidenceLink>();
        l.ToTable("Links", t => { t.HasCheckConstraint("ck_no_self_link", "\"SourceId\" <> \"TargetId\""); t.HasCheckConstraint("ck_link_kind", "\"Kind\" IN ('Corroborates','Contradicts')"); t.HasCheckConstraint("ck_canonical_pair", "\"SourceId\" < \"TargetId\""); });
        l.HasKey(x => x.Id); l.Property(x => x.Id).ValueGeneratedNever();
        l.Property(x => x.SourceId).HasMaxLength(64); l.Property(x => x.TargetId).HasMaxLength(64);
        l.Property(x => x.Kind).HasConversion<string>().HasMaxLength(24);
        l.HasIndex(x => new { x.InvestigationId, x.SourceId, x.TargetId }).IsUnique();
        l.HasOne<Discovery>().WithMany().HasForeignKey(x => new { x.InvestigationId, x.SourceId }).OnDelete(DeleteBehavior.Restrict);
        l.HasOne<Discovery>().WithMany().HasForeignKey(x => new { x.InvestigationId, x.TargetId }).OnDelete(DeleteBehavior.Restrict);
        var r = b.Entity<Receipt>();
        r.HasKey(x => x.Id); r.Property(x => x.OwnerId).HasMaxLength(450); r.Property(x => x.Key).HasMaxLength(36); r.Property(x => x.Fingerprint).HasMaxLength(64);
        r.HasIndex(x => new { x.OwnerId, x.Key }).IsUnique(); r.HasIndex(x => x.CreatedAt);
        var a = b.Entity<AuditEntry>();
        a.HasKey(x => x.Id); a.Property(x => x.Operation).HasMaxLength(32); a.Property(x => x.OwnerId).HasMaxLength(450);
        a.HasIndex(x => new { x.InvestigationId, x.Version }).IsUnique();
    }
}
