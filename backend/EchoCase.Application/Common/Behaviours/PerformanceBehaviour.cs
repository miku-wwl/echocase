using System.Diagnostics;
using EchoCase.Application.Common.Interfaces;
using Microsoft.Extensions.Logging;

namespace EchoCase.Application.Common.Behaviours;

public class PerformanceBehaviour<TRequest, TResponse> : IPipelineBehavior<TRequest, TResponse>
    where TRequest : notnull
{
    private readonly Stopwatch _timer;
    private readonly ILogger<TRequest> _logger;
    private readonly IUser _user;

    public PerformanceBehaviour(
        ILogger<TRequest> logger,
        IUser user)
    {
        _timer = new Stopwatch();

        _logger = logger;
        _user = user;
    }

    public async Task<TResponse> Handle(TRequest request, RequestHandlerDelegate<TResponse> next, CancellationToken cancellationToken)
    {
        _timer.Start();

        var response = await next();

        _timer.Stop();

        var elapsedMilliseconds = _timer.ElapsedMilliseconds;

        if (elapsedMilliseconds > 500)
        {
            var requestName = typeof(TRequest).Name;
            var userId = _user.Id ?? string.Empty;
            // A successful handler may already have committed its transaction.
            // Telemetry must not add a database lookup that can turn that result
            // into an error. Use only the identity already in the request scope.
            _logger.LogWarning("EchoCase Long Running Request: {Name} ({ElapsedMilliseconds} milliseconds) {@UserId}",
                requestName, elapsedMilliseconds, userId);
        }

        return response;
    }
}
