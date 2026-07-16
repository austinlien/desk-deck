param(
    [string]$BaseUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"

try {
    Invoke-RestMethod -Method Post -Uri "$BaseUrl/api/agent/reset" | Out-Null
    Write-Host "Desk Deck agent status: reset"
} catch {
    Write-Warning "Desk Deck agent status unavailable: $($_.Exception.Message)"
}
