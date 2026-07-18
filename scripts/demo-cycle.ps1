param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [ValidateRange(1, 120)]
    [int]$HoldSeconds = 5,
    [ValidateRange(0, 1000)]
    [int]$Loops = 1,
    [ValidateRange(1, 120)]
    [int]$DefaultRotationSeconds = 9
)

$ErrorActionPreference = "Stop"

function Invoke-DeskDeckPost {
    param(
        [string]$Path,
        [object]$Body = $null
    )

    $params = @{
        Method = "Post"
        Uri = "$BaseUrl$Path"
    }
    if ($null -ne $Body) {
        $params.ContentType = "application/json"
        $params.Body = $Body | ConvertTo-Json -Compress
    }
    Invoke-RestMethod @params | Out-Null
}

function Show-DemoStep {
    param(
        [string]$Name,
        [scriptblock]$Activate,
        [int]$Seconds = $HoldSeconds
    )

    Write-Host "Demo: $Name ($Seconds seconds)"
    & $Activate
    Start-Sleep -Seconds $Seconds
}

try {
    $iteration = 0
    while ($Loops -eq 0 -or $iteration -lt $Loops) {
        $iteration++
        Write-Host "Starting Desk Deck demo cycle $iteration. Press Ctrl+C to stop."

        Show-DemoStep -Name "NOTIFICATION" -Activate {
            Invoke-DeskDeckPost -Path "/api/debug/reset"
            Invoke-DeskDeckPost -Path "/api/debug/inputs" -Body @{ notification = $true }
        }
        Show-DemoStep -Name "MEETING SOON" -Activate {
            Invoke-DeskDeckPost -Path "/api/debug/inputs" -Body @{ meeting_soon = $true }
        }
        Show-DemoStep -Name "MEETING NOW" -Activate {
            Invoke-DeskDeckPost -Path "/api/debug/inputs" -Body @{ active_meeting = $true }
        }
        Show-DemoStep -Name "AGENT WORKING" -Activate {
            Invoke-DeskDeckPost -Path "/api/debug/inputs" -Body @{
                spotify_playing = $true
                spotify_title = "Somebody Told Me"
                spotify_artist = "The Killers"
            }
            Invoke-DeskDeckPost -Path "/api/agent/status/working"
        }
        Show-DemoStep -Name "SONG SKIP: MR BRIGHTSIDE" -Activate {
            Invoke-DeskDeckPost -Path "/api/debug/inputs" -Body @{
                spotify_playing = $true
                spotify_title = "Mr. Brightside"
                spotify_artist = "The Killers"
            }
        }
        Show-DemoStep -Name "AGENT WAITING" -Activate {
            Invoke-DeskDeckPost -Path "/api/agent/status/waiting"
        }
        Show-DemoStep -Name "AGENT DONE" -Activate {
            Invoke-DeskDeckPost -Path "/api/agent/status/done"
        }
        Show-DemoStep -Name "ONE DANCE" -Activate {
            Invoke-DeskDeckPost -Path "/api/debug/inputs" -Body @{
                spotify_playing = $true
                spotify_title = "One Dance"
                spotify_artist = "Drake"
            }
        }
        Show-DemoStep -Name "TEMPERATURES AND TIME" -Seconds $DefaultRotationSeconds -Activate {
            Invoke-DeskDeckPost -Path "/api/debug/inputs" -Body @{ demo_default_rotation = $true }
        }
    }
} finally {
    try {
        Invoke-DeskDeckPost -Path "/api/debug/reset"
        Write-Host "Desk Deck demo reset complete."
    } catch {
        Write-Warning "Could not reset the Desk Deck demo state: $($_.Exception.Message)"
    }
}
