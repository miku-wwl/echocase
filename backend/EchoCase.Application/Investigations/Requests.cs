using EchoCase.Application.Common.Interfaces;
using EchoCase.Application.Common.Security;

namespace EchoCase.Application.Investigations;

[Authorize] public sealed record GetCasesQuery : IRequest<CaseSummary[]>;
[Authorize] public sealed record ListInvestigationsQuery : IRequest<IReadOnlyList<SessionView>>;
[Authorize] public sealed record GetInvestigationQuery(Guid Id) : IRequest<SessionView>;

public interface IInvestigationCommand : IRequest<SessionView> { string Key { get; } }
[Authorize] public sealed record StartInvestigationCommand(string Key, StartRequest Body) : IInvestigationCommand;
[Authorize] public sealed record ExamineEvidenceCommand(Guid Id, string Key, int Version, string EvidenceId) : IInvestigationCommand;
[Authorize] public sealed record CreateLinkCommand(Guid Id, string Key, int Version, LinkRequest Body) : IInvestigationCommand;
[Authorize] public sealed record ReviseLinkCommand(Guid Id, string Key, int Version, Guid LinkId, ReviseLinkRequest Body) : IInvestigationCommand;
[Authorize] public sealed record RemoveLinkCommand(Guid Id, string Key, int Version, Guid LinkId) : IInvestigationCommand;
[Authorize] public sealed record SaveNotesCommand(Guid Id, string Key, int Version, NotesRequest Body) : IInvestigationCommand;
[Authorize] public sealed record TransitionInvestigationCommand(Guid Id, string Key, int Version, string Action) : IInvestigationCommand;
[Authorize] public sealed record SubmitVerdictCommand(Guid Id, string Key, int Version, VerdictRequest Body) : IInvestigationCommand;

// Owner is a scoped authenticated identity, never a request-body field. Resource
// ownership is checked again inside the store transaction BEFORE receipt lookup.
internal static class RequestOwner
{
    public static string Required(IUser user) => user.Id ?? throw new UnauthorizedAccessException();
}

public sealed class GetCasesHandler : IRequestHandler<GetCasesQuery, CaseSummary[]>
{
    public Task<CaseSummary[]> Handle(GetCasesQuery request, CancellationToken ct) => Task.FromResult(InvestigationService.Cases());
}
public sealed class ListInvestigationsHandler(InvestigationService service, IUser user) : IRequestHandler<ListInvestigationsQuery, IReadOnlyList<SessionView>>
{
    public Task<IReadOnlyList<SessionView>> Handle(ListInvestigationsQuery request, CancellationToken ct) => service.List(RequestOwner.Required(user), ct);
}
public sealed class GetInvestigationHandler(InvestigationService service, IUser user) : IRequestHandler<GetInvestigationQuery, SessionView>
{
    public Task<SessionView> Handle(GetInvestigationQuery request, CancellationToken ct) => service.Get(request.Id, RequestOwner.Required(user), ct);
}
public sealed class StartInvestigationHandler(InvestigationService service, IUser user) : IRequestHandler<StartInvestigationCommand, SessionView>
{
    public Task<SessionView> Handle(StartInvestigationCommand r, CancellationToken ct) => service.Start(RequestOwner.Required(user), r.Key, r.Body, ct);
}
public sealed class ExamineEvidenceHandler(InvestigationService service, IUser user) : IRequestHandler<ExamineEvidenceCommand, SessionView>
{
    public Task<SessionView> Handle(ExamineEvidenceCommand r, CancellationToken ct) => service.Examine(r.Id, RequestOwner.Required(user), r.Key, r.Version, r.EvidenceId, ct);
}
public sealed class CreateLinkHandler(InvestigationService service, IUser user) : IRequestHandler<CreateLinkCommand, SessionView>
{
    public Task<SessionView> Handle(CreateLinkCommand r, CancellationToken ct) => service.Link(r.Id, RequestOwner.Required(user), r.Key, r.Version, r.Body, ct);
}
public sealed class ReviseLinkHandler(InvestigationService service, IUser user) : IRequestHandler<ReviseLinkCommand, SessionView>
{
    public Task<SessionView> Handle(ReviseLinkCommand r, CancellationToken ct) => service.ReviseLink(r.Id, RequestOwner.Required(user), r.Key, r.Version, r.LinkId, r.Body, ct);
}
public sealed class RemoveLinkHandler(InvestigationService service, IUser user) : IRequestHandler<RemoveLinkCommand, SessionView>
{
    public Task<SessionView> Handle(RemoveLinkCommand r, CancellationToken ct) => service.RemoveLink(r.Id, RequestOwner.Required(user), r.Key, r.Version, r.LinkId, ct);
}
public sealed class SaveNotesHandler(InvestigationService service, IUser user) : IRequestHandler<SaveNotesCommand, SessionView>
{
    public Task<SessionView> Handle(SaveNotesCommand r, CancellationToken ct) => service.Notes(r.Id, RequestOwner.Required(user), r.Key, r.Version, r.Body, ct);
}
public sealed class TransitionInvestigationHandler(InvestigationService service, IUser user) : IRequestHandler<TransitionInvestigationCommand, SessionView>
{
    public Task<SessionView> Handle(TransitionInvestigationCommand r, CancellationToken ct) => service.Transition(r.Id, RequestOwner.Required(user), r.Key, r.Version, r.Action, ct);
}
public sealed class SubmitVerdictHandler(InvestigationService service, IUser user) : IRequestHandler<SubmitVerdictCommand, SessionView>
{
    public Task<SessionView> Handle(SubmitVerdictCommand r, CancellationToken ct) => service.Verdict(r.Id, RequestOwner.Required(user), r.Key, r.Version, r.Body, ct);
}

// Syntax validation is in the template pipeline. State/visibility/version rules
// remain in the existing domain and store; validation does not replay receipts,
// begin transactions, change aggregate versions, or save a DbContext.
public abstract class WriteCommandValidator<T> : AbstractValidator<T> where T : IInvestigationCommand
{
    protected WriteCommandValidator() => RuleFor(x => x.Key)
        .Must(key => Guid.TryParseExact(key, "D", out _))
        .WithMessage("写操作需要 UUID 格式的 Idempotency-Key。");
}
public sealed class StartInvestigationValidator : WriteCommandValidator<StartInvestigationCommand>;
public sealed class ExamineEvidenceValidator : WriteCommandValidator<ExamineEvidenceCommand>;
public sealed class CreateLinkValidator : WriteCommandValidator<CreateLinkCommand>;
public sealed class ReviseLinkValidator : WriteCommandValidator<ReviseLinkCommand>;
public sealed class RemoveLinkValidator : WriteCommandValidator<RemoveLinkCommand>;
public sealed class SaveNotesValidator : WriteCommandValidator<SaveNotesCommand>;
public sealed class TransitionInvestigationValidator : WriteCommandValidator<TransitionInvestigationCommand>;
public sealed class SubmitVerdictValidator : WriteCommandValidator<SubmitVerdictCommand>;
