using EchoCase.Application;
using EchoCase.Application.Investigations;

namespace EchoCase.Api.Endpoints;

public sealed class Investigations : IEndpointGroup
{
    public static string RoutePrefix => "/api";

    public static void Map(RouteGroupBuilder group)
    {
        group.RequireAuthorization();
        group.MapGet(GetCases, "/cases").Produces<CaseSummary[]>();
        group.MapGet(ListInvestigations, "/investigations").Produces<IReadOnlyList<SessionView>>();
        group.MapGet(GetInvestigation, "/investigations/{id:guid}").Produces<SessionView>();
        group.MapPost(StartInvestigation, "/investigations").Produces<SessionView>().RequireRateLimiting("writes");
        group.MapPost(ExamineEvidence, "/investigations/{id:guid}/evidence/{evidenceId}/examine").Produces<SessionView>().RequireRateLimiting("writes");
        group.MapPost(CreateLink, "/investigations/{id:guid}/links").Produces<SessionView>().RequireRateLimiting("writes");
        group.MapPut(ReviseLink, "/investigations/{id:guid}/links/{linkId:guid}").Produces<SessionView>().RequireRateLimiting("writes");
        group.MapDelete(RemoveLink, "/investigations/{id:guid}/links/{linkId:guid}").Produces<SessionView>().RequireRateLimiting("writes");
        group.MapPut(SaveNotes, "/investigations/{id:guid}/notes").Produces<SessionView>().RequireRateLimiting("writes");
        group.MapPost(TransitionInvestigation, "/investigations/{id:guid}/state/{action}").Produces<SessionView>().RequireRateLimiting("writes");
        group.MapPost(SubmitVerdict, "/investigations/{id:guid}/verdict").Produces<SessionView>().RequireRateLimiting("writes");
    }

    public static Task<CaseSummary[]> GetCases(ISender sender, CancellationToken ct) => sender.Send(new GetCasesQuery(), ct);
    public static Task<IReadOnlyList<SessionView>> ListInvestigations(ISender sender, CancellationToken ct) => sender.Send(new ListInvestigationsQuery(), ct);
    public static async Task<IResult> GetInvestigation(Guid id, ISender sender, HttpContext ctx, CancellationToken ct) => Respond(ctx, await sender.Send(new GetInvestigationQuery(id), ct));
    public static async Task<IResult> StartInvestigation(StartRequest body, ISender sender, HttpContext ctx, CancellationToken ct) => Respond(ctx, await sender.Send(new StartInvestigationCommand(Key(ctx), body), ct));
    public static async Task<IResult> ExamineEvidence(Guid id, string evidenceId, ISender sender, HttpContext ctx, CancellationToken ct) => Respond(ctx, await sender.Send(new ExamineEvidenceCommand(id, Key(ctx), Version(ctx), evidenceId), ct));
    public static async Task<IResult> CreateLink(Guid id, LinkRequest body, ISender sender, HttpContext ctx, CancellationToken ct) => Respond(ctx, await sender.Send(new CreateLinkCommand(id, Key(ctx), Version(ctx), body), ct));
    public static async Task<IResult> ReviseLink(Guid id, Guid linkId, ReviseLinkRequest body, ISender sender, HttpContext ctx, CancellationToken ct) => Respond(ctx, await sender.Send(new ReviseLinkCommand(id, Key(ctx), Version(ctx), linkId, body), ct));
    public static async Task<IResult> RemoveLink(Guid id, Guid linkId, ISender sender, HttpContext ctx, CancellationToken ct) => Respond(ctx, await sender.Send(new RemoveLinkCommand(id, Key(ctx), Version(ctx), linkId), ct));
    public static async Task<IResult> SaveNotes(Guid id, NotesRequest body, ISender sender, HttpContext ctx, CancellationToken ct) => Respond(ctx, await sender.Send(new SaveNotesCommand(id, Key(ctx), Version(ctx), body), ct));
    public static async Task<IResult> TransitionInvestigation(Guid id, string action, ISender sender, HttpContext ctx, CancellationToken ct) => Respond(ctx, await sender.Send(new TransitionInvestigationCommand(id, Key(ctx), Version(ctx), action), ct));
    public static async Task<IResult> SubmitVerdict(Guid id, VerdictRequest body, ISender sender, HttpContext ctx, CancellationToken ct) => Respond(ctx, await sender.Send(new SubmitVerdictCommand(id, Key(ctx), Version(ctx), body), ct));

    private static string Key(HttpContext ctx) => ctx.Request.Headers["Idempotency-Key"].ToString();
    private static int Version(HttpContext ctx)
    {
        var value = ctx.Request.Headers.IfMatch.ToString();
        if (value.Length < 3 || value[0] != '"' || value[^1] != '"' || !int.TryParse(value[1..^1], out var version) || version < 1)
            throw new ApplicationFault(428, "precondition_required", "需要 If-Match: \"版本号\"。");
        return version;
    }
    private static IResult Respond(HttpContext ctx, SessionView value)
    {
        ctx.Response.Headers.ETag = $"\"{value.Version}\"";
        return Results.Ok(value);
    }
}
