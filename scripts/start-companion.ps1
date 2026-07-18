param(
    [string]$BindAddress = "0.0.0.0",
    [int]$Port = 8000,
    [string]$EnvFile = "",
    [string]$Python = "",
    [switch]$RestartExisting
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$CompanionDir = Join-Path $RepoRoot "companion"

if ($EnvFile -eq "") {
    $EnvFile = Join-Path $CompanionDir "secrets\local-env.ps1"
}

if (Test-Path $EnvFile) {
    . $EnvFile
    Write-Host "Loaded local companion environment: $EnvFile"
} else {
    Write-Warning "Local companion environment not found: $EnvFile"
    Write-Warning "Copy companion\local-env.example.ps1 to companion\secrets\local-env.ps1 and fill in local secrets."
}

if ($Python -eq "") {
    $Python311 = Join-Path $CompanionDir ".venv311\Scripts\python.exe"
    $PythonDefault = Join-Path $CompanionDir ".venv\Scripts\python.exe"

    if (Test-Path $Python311) {
        $Python = $Python311
    } elseif (Test-Path $PythonDefault) {
        $Python = $PythonDefault
    } else {
        $Python = "python3.11"
    }
}

Push-Location $CompanionDir
try {
    $ExistingListeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($ExistingListeners) {
        $ExistingProcessIds = $ExistingListeners | Select-Object -ExpandProperty OwningProcess -Unique
        if ($RestartExisting) {
            foreach ($ProcessId in $ExistingProcessIds) {
                $Process = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
                if ($Process) {
                    Write-Host "Stopping existing process on port ${Port}: $($Process.ProcessName) ($ProcessId)"
                    Stop-Process -Id $ProcessId -Force
                }
            }
            Start-Sleep -Seconds 1
        } else {
            $ExistingDescription = ($ExistingProcessIds | ForEach-Object {
                $Process = Get-Process -Id $_ -ErrorAction SilentlyContinue
                if ($Process) {
                    "$($Process.ProcessName) ($_)"
                } else {
                    "process $_"
                }
            }) -join ", "

            throw "Port $Port is already in use by $ExistingDescription. Re-run with -RestartExisting to stop it first."
        }
    }

    & $Python -m uvicorn app.main:app --host $BindAddress --port $Port
} finally {
    Pop-Location
}
