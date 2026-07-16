param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

try {
    Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/agent/status/working" | Out-Null
    Write-Host "Desk Deck agent status: working"
} catch {
    Write-Warning "Desk Deck agent status unavailable: $($_.Exception.Message)"
}
