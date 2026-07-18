param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

try {
    $state = Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/work/stop"
    if ($null -ne $state.completion_elapsed_seconds) {
        Write-Host "Desk Deck work session stopped: $($state.completion_elapsed_seconds) seconds"
    } else {
        Write-Host "No Desk Deck work session was running."
    }
} catch {
    Write-Warning "Could not stop the Desk Deck work session: $($_.Exception.Message)"
}
