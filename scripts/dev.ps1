param([ValidateSet('api','web','migrate','test')][string]$Action='api')
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$true
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:ConnectionStrings__EchoCase='Host=127.0.0.1;Port=55432;Database=echocase;Username=echocase;Password=echocase-local-only'
$env:ECHOCASE_TEST_CONNECTION=$env:ConnectionStrings__EchoCase
$env:ASPNETCORE_ENVIRONMENT='Development'
switch($Action){
    'api' { dotnet run --project src/EchoCase.Api --no-launch-profile --urls http://127.0.0.1:5080 }
    'web' { Set-Location frontend; npm run dev }
    'migrate' { dotnet tool restore; dotnet ef database update --project src/EchoCase.Infrastructure --startup-project src/EchoCase.Api }
    'test' { dotnet test --logger 'trx;LogFileName=backend.trx' --results-directory evidence/backend }
}
