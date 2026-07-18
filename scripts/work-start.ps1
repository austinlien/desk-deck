param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

try {
    $state = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/work/start"
    Write-Host "Desk Deck work session started: $($state.elapsed_seconds) seconds"
} catch {
    Write-Warning "Could not start the Desk Deck work session: $($_.Exception.Message)"
}
