using EchoCase.Application;
using EchoCase.Application.Common.Interfaces;
using EchoCase.Infrastructure;
using EchoCase.Infrastructure.Identity;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;

namespace Microsoft.Extensions.DependencyInjection;

public static class InfrastructureDependencyInjection
{
    public static void AddInfrastructureServices(this IHostApplicationBuilder builder)
    {
        var connection = builder.Configuration.GetConnectionString("EchoCase")
            ?? throw new InvalidOperationException("Set ConnectionStrings__EchoCase. No default database credentials are shipped.");
        builder.Services.AddDbContext<EchoDbContext>(o => o.UseNpgsql(connection, p => p.CommandTimeout(5)));
        builder.Services.AddIdentityCore<Investigator>(o =>
        {
            o.User.RequireUniqueEmail = true;
            o.Password.RequiredLength = 12; o.Password.RequireNonAlphanumeric = false;
            o.Lockout.MaxFailedAccessAttempts = 5; o.Lockout.DefaultLockoutTimeSpan = TimeSpan.FromMinutes(5);
        }).AddRoles<IdentityRole>().AddEntityFrameworkStores<EchoDbContext>().AddSignInManager();
        builder.Services.AddAuthentication("EchoCase").AddCookie("EchoCase", o =>
        {
            o.Cookie.Name = "echocase.session"; o.Cookie.HttpOnly = true; o.Cookie.SameSite = Microsoft.AspNetCore.Http.SameSiteMode.Strict;
            o.Cookie.SecurePolicy = builder.Environment.IsDevelopment() || builder.Environment.IsEnvironment("Testing")
                ? Microsoft.AspNetCore.Http.CookieSecurePolicy.SameAsRequest : Microsoft.AspNetCore.Http.CookieSecurePolicy.Always;
            o.ExpireTimeSpan = TimeSpan.FromHours(2); o.SlidingExpiration = false;
            o.Events.OnRedirectToLogin = ctx => { ctx.Response.StatusCode = 401; return Task.CompletedTask; };
            o.Events.OnRedirectToAccessDenied = ctx => { ctx.Response.StatusCode = 403; return Task.CompletedTask; };
        });
        builder.Services.AddAuthorization();
        builder.Services.AddSingleton(TimeProvider.System);
        builder.Services.AddScoped<IInvestigationStore, PostgresInvestigationStore>();
        builder.Services.AddScoped<IIdentityService, IdentityService>();
    }
}
