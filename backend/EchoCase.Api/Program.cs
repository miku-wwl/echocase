using System.Diagnostics;
using System.Security.Claims;
using System.Threading.RateLimiting;
using EchoCase.Application;
using EchoCase.Domain;
using EchoCase.Infrastructure;
using Microsoft.AspNetCore.Antiforgery;
using Microsoft.AspNetCore.Authentication;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Npgsql;

var builder = WebApplication.CreateBuilder(args);
builder.AddApplicationServices();
builder.AddInfrastructureServices();
builder.AddWebServices();
builder.WebHost.ConfigureKestrel(o => o.Limits.MaxRequestBodySize = 16384);
builder.Services.AddAntiforgery(o => { o.HeaderName = "X-CSRF-TOKEN"; o.Cookie.Name = "echocase.csrf"; o.Cookie.SameSite = SameSiteMode.Strict; });
builder.Services.AddRateLimiter(o =>
{
    o.RejectionStatusCode = 429;
    o.AddPolicy("auth", ctx => RateLimitPartition.GetFixedWindowLimiter(ctx.Connection.RemoteIpAddress?.ToString() ?? "unknown", _ => new() { PermitLimit = 15, Window = TimeSpan.FromMinutes(1), QueueLimit = 0 }));
    o.AddPolicy("writes", ctx => RateLimitPartition.GetFixedWindowLimiter(ctx.User.FindFirstValue(ClaimTypes.NameIdentifier) ?? "anonymous", _ => new() { PermitLimit = 120, Window = TimeSpan.FromMinutes(1), QueueLimit = 0 }));
});
builder.Services.ConfigureHttpJsonOptions(o => { o.SerializerOptions.RespectNullableAnnotations = true; o.SerializerOptions.RespectRequiredConstructorParameters = true; o.SerializerOptions.NumberHandling = System.Text.Json.Serialization.JsonNumberHandling.Strict; o.SerializerOptions.UnmappedMemberHandling = System.Text.Json.Serialization.JsonUnmappedMemberHandling.Disallow; });
builder.Services.AddProblemDetails(o => o.CustomizeProblemDetails = context =>
{
    // The default writer sets Activity.Id (the full W3C parent string) first.
    // Keep the public error identifier equal to our response/log TraceId.
    context.ProblemDetails.Extensions["traceId"] = Activity.Current?.TraceId.ToString() ?? context.HttpContext.TraceIdentifier;
});
var app = builder.Build();
if (args.Contains("--migrate"))
{
    await using var scope = app.Services.CreateAsyncScope();
    await scope.ServiceProvider.GetRequiredService<EchoDbContext>().Database.MigrateAsync();
    return;
}
app.Use(async (ctx, next) =>
{
    ctx.Response.Headers["X-Content-Type-Options"] = "nosniff";
    ctx.Response.Headers["Referrer-Policy"] = "no-referrer";
    ctx.Response.Headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'";
    ctx.Response.Headers["X-Trace-Id"] = Activity.Current?.TraceId.ToString() ?? ctx.TraceIdentifier;
    if (ctx.Request.Path.StartsWithSegments("/api")) ctx.Response.Headers.CacheControl = "no-store";
    var timer = Stopwatch.StartNew();
    try { await next(); }
    catch (Exception e) when (!ctx.Response.HasStarted)
    {
        var (status, code, detail) = e switch
        {
            UnauthorizedAccessException => (401, "authentication_required", "请先登录。"),
            EchoCase.Application.Common.Exceptions.ForbiddenAccessException => (403, "forbidden", "不允许执行此操作。"),
            EchoCase.Application.Common.Exceptions.ValidationException v when v.Errors.ContainsKey("Key") => (400, "idempotency_key_required", "写操作需要 UUID 格式的 Idempotency-Key。"),
            EchoCase.Application.Common.Exceptions.ValidationException v => (400, "validation_failed", string.Join("；", v.Errors.Values.SelectMany(x => x))),
            ApplicationFault f => (f.Status, f.Code, f.Message),
            DomainRule d => (422, d.Code, d.Message),
            AntiforgeryValidationException => (400, "csrf_invalid", "防伪令牌缺失或失效。请刷新页面。"),
            BadHttpRequestException b => (b.StatusCode, "invalid_request", "请求格式不正确。"),
            NpgsqlException => (503, "database_unavailable", "数据服务暂不可用。请稍后重试。"),
            InvalidOperationException { InnerException: NpgsqlException } => (503, "database_unavailable", "数据服务暂不可用。请稍后重试。"),
            DbUpdateException => (503, "write_failed", "保存未完成。请刷新后重试。"),
            _ => (500, "internal_error", "服务发生错误，请使用追踪编号排查。")
        };
        if (status >= 500) app.Logger.LogError(e, "Request failed: {Code}", code);
        ctx.Response.StatusCode = status;
        await Results.Problem(statusCode: status, title: code, detail: detail, extensions: new Dictionary<string, object?> { ["traceId"] = Activity.Current?.TraceId.ToString() ?? ctx.TraceIdentifier }).ExecuteAsync(ctx);
    }
    finally { app.Logger.LogInformation("HTTP {Method} {Path} {Status} {DurationMs}ms trace={TraceId}", ctx.Request.Method, ctx.Request.Path, ctx.Response.StatusCode, timer.Elapsed.TotalMilliseconds, Activity.Current?.TraceId); }
});
if (!app.Environment.IsDevelopment() && !app.Environment.IsEnvironment("Testing")) app.UseHsts();
app.UseRouting();
app.UseAuthentication();
app.UseRateLimiter();
app.UseAuthorization();
app.Use(async (ctx, next) =>
{
    if (ctx.Request.Path.StartsWithSegments("/api") && !HttpMethods.IsGet(ctx.Request.Method) && !HttpMethods.IsHead(ctx.Request.Method) && !HttpMethods.IsOptions(ctx.Request.Method))
        await ctx.RequestServices.GetRequiredService<IAntiforgery>().ValidateRequestAsync(ctx);
    await next();
});
app.UseDefaultFiles(); app.UseStaticFiles();
if (app.Environment.IsDevelopment() || app.Environment.IsEnvironment("Testing")) app.MapOpenApi();
app.MapGet("/health/live", () => Results.Ok(new { status = "live" })).AllowAnonymous();
app.MapGet("/health/ready", async (EchoDbContext db, CancellationToken ct) =>
{
    try { return await db.Database.CanConnectAsync(ct) ? Results.Ok(new { status = "ready" }) : Results.StatusCode(503); }
    catch (Exception e) when (e is NpgsqlException or TimeoutException) { return Results.StatusCode(503); }
}).AllowAnonymous();
app.MapGet("/api/auth/csrf", (HttpContext ctx, IAntiforgery anti) => new CsrfResponse(anti.GetAndStoreTokens(ctx).RequestToken!)).WithName("GetCsrfToken");
app.MapPost("/api/auth/register", async (Credentials body, UserManager<Investigator> users) =>
{
    if (body.Email.Length > 254 || !System.Net.Mail.MailAddress.TryCreate(body.Email, out var email) || email.Address != body.Email)
        return Results.Problem(statusCode: 400, title: "invalid_email", detail: "请输入有效邮箱。");
    var user = new Investigator { UserName = body.Email, Email = body.Email, LockoutEnabled = true };
    var result = await users.CreateAsync(user, body.Password);
    return result.Succeeded ? Results.Ok(new MessageResponse("账户已创建，请登录。")) : Results.Problem(statusCode: 400, title: "registration_failed", detail: "无法创建账户。密码至少 12 位且含大小写字母和数字，邮箱必须唯一。");
}).WithName("Register").Produces<MessageResponse>().RequireRateLimiting("auth");
app.MapPost("/api/auth/login", async (Credentials body, UserManager<Investigator> users, HttpContext ctx) =>
{
    var user = await users.FindByEmailAsync(body.Email);
    if (user is null || await users.IsLockedOutAsync(user) || !await users.CheckPasswordAsync(user, body.Password))
    {
        if (user is not null) await users.AccessFailedAsync(user);
        return Results.Problem(statusCode: 401, title: "login_failed", detail: "邮箱、密码错误或账户暂时锁定。");
    }
    await users.ResetAccessFailedCountAsync(user);
    var principal = new ClaimsPrincipal(new ClaimsIdentity([new(ClaimTypes.NameIdentifier, user.Id), new(ClaimTypes.Name, user.Email!)], "EchoCase"));
    await ctx.SignInAsync("EchoCase", principal);
    return Results.Ok(new UserView(user.Id, user.Email!));
}).WithName("Login").Produces<UserView>().RequireRateLimiting("auth");
app.MapPost("/api/auth/logout", async (HttpContext ctx) => { await ctx.SignOutAsync("EchoCase"); return Results.NoContent(); }).WithName("Logout").Produces(204).RequireAuthorization();
app.MapGet("/api/auth/me", (ClaimsPrincipal p) => new UserView(p.FindFirstValue(ClaimTypes.NameIdentifier)!, p.Identity!.Name!)).WithName("GetCurrentUser").RequireAuthorization();
app.MapEndpoints(typeof(Program).Assembly);
app.MapFallback("/api/{**path}", () => Results.Problem(statusCode: 404, title: "route_not_found"));
app.MapFallbackToFile("index.html");
await app.RunAsync();
public sealed record MessageResponse(string Message);
public sealed record Credentials(string Email, string Password);
public sealed record UserView(string Id, string Email);
public sealed record CsrfResponse(string Token);
public partial class Program;
