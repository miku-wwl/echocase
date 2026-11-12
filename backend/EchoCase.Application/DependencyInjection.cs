using System.Reflection;
using EchoCase.Application;
using EchoCase.Application.Common.Behaviours;
using Microsoft.Extensions.Hosting;

namespace Microsoft.Extensions.DependencyInjection;

// Derived from the generated ca-sln registration, not a parallel dispatcher.
public static class ApplicationDependencyInjection
{
    public static void AddApplicationServices(this IHostApplicationBuilder builder)
    {
        builder.Services.AddValidatorsFromAssembly(Assembly.GetExecutingAssembly());
        builder.Services.AddMediatR(cfg =>
        {
            cfg.RegisterServicesFromAssembly(Assembly.GetExecutingAssembly());
            cfg.AddOpenRequestPreProcessor(typeof(LoggingBehaviour<>));
            cfg.AddOpenBehavior(typeof(UnhandledExceptionBehaviour<,>));
            cfg.AddOpenBehavior(typeof(AuthorizationBehaviour<,>));
            cfg.AddOpenBehavior(typeof(ValidationBehaviour<,>));
            cfg.AddOpenBehavior(typeof(PerformanceBehaviour<,>));
        });
        builder.Services.AddScoped<InvestigationService>();
    }
}
