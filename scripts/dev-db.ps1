param([ValidateSet('start','stop')][string]$Action = 'start')
$ErrorActionPreference = 'Stop'
if ($Action -eq 'stop') { podman stop echocase-postgres; exit $LASTEXITCODE }
$existing = podman ps -a --filter 'name=^echocase-postgres$' --format '{{.Names}}'
if ($existing -eq 'echocase-postgres') { podman start echocase-postgres | Out-Null }
else {
    # Public, disposable LOCAL LAB credential. Bind only to loopback. Never use in production.
    podman run -d --name echocase-postgres --memory 384m --cpus 1 -e POSTGRES_USER=echocase -e POSTGRES_PASSWORD=echocase-local-only -e POSTGRES_DB=echocase -p 127.0.0.1:55432:5432 -v echocase-pgdata:/var/lib/postgresql/data docker.io/library/postgres:17.7-alpine | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL container could not start.' }
}
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    podman exec echocase-postgres pg_isready -U echocase -d echocase 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { Write-Output 'PostgreSQL ready at 127.0.0.1:55432'; exit 0 }
    Start-Sleep -Seconds 1
}
throw 'PostgreSQL readiness timeout.'
