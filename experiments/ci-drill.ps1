param([Parameter(Mandatory=$true)][string]$ReviewBranch)
$ErrorActionPreference='Stop'
$PSNativeCommandUseErrorActionPreference=$true
Set-Location (Split-Path $PSScriptRoot -Parent)
$currentBranch=git branch --show-current
if ($currentBranch -ne $ReviewBranch -or -not $currentBranch.StartsWith('codex/')) { throw 'Run only on the explicitly named codex/ review branch, never main.' }
if (git status --porcelain) { throw 'Commit or preserve existing changes first; the drill requires a clean checkout.' }
if (-not (Test-Path -LiteralPath evidence/manifest.json)) { throw 'Known-good evidence manifest required.' }
$knownGood=git rev-parse HEAD
function Wait-Run([string]$Revision) {
    $deadline=[DateTime]::UtcNow.AddMinutes(15)
    while ([DateTime]::UtcNow -lt $deadline) {
        $runs=gh run list --branch $ReviewBranch --commit $Revision --limit 1 --json databaseId,status,conclusion,url | ConvertFrom-Json
        if ($runs.Count -gt 0 -and $runs[0].status -eq 'completed') { return $runs[0] }
        Start-Sleep -Seconds 5
    }
    throw 'CI completion timeout. Inspect GitHub Actions before repeating.'
}
try {
    git rm -- evidence/manifest.json
    git commit -m 'test: controlled missing evidence manifest drill'
    git push
    $badRevision=git rev-parse HEAD
    $rejected=Wait-Run $badRevision
    if ($rejected.conclusion -ne 'failure') { throw 'Corrupted evidence was not rejected.' }
    $rejectionLog=gh run view $rejected.databaseId --log-failed
    if (-not ($rejectionLog -match 'manifest.json')) { throw 'Workflow failed for an unrelated reason; inspect the logs.' }
    Write-Output ('Observed rejection: '+$rejected.url)
}
finally {
    git restore --source=$knownGood --staged --worktree -- evidence/manifest.json
    if (git diff --cached --name-only) { git commit -m 'fix: restore evidence after controlled CI drill'; git push }
}
$repaired=Wait-Run (git rev-parse HEAD)
if ($repaired.conclusion -ne 'success') { throw ('Repaired workflow did not pass: '+$repaired.url) }
Write-Output ('Observed recovery: '+$repaired.url)
