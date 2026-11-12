using EchoCase.Application.Common.Interfaces;
using EchoCase.Api.Services;

namespace Microsoft.Extensions.DependencyInjection;

public static class WebDependencyInjection
{
    public static void AddWebServices(this IHostApplicationBuilder builder)
    {
        builder.Services.AddScoped<IUser, CurrentUser>();
        builder.Services.AddHttpContextAccessor();
        builder.Services.AddEndpointsApiExplorer();
        builder.Services.AddOpenApi(options => options.OpenApiVersion = Microsoft.OpenApi.OpenApiSpecVersion.OpenApi3_0);
    }
}
