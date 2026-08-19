$ErrorActionPreference = "Stop"
function Wait-Url([string]$Name, [string]$Url, [int]$Attempts = 40) {
    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) {
                Write-Host "$Name OK" -ForegroundColor Green
                return
            }
        }
        catch {
            Start-Sleep -Seconds 3
        }
    }
    throw "$Name did not become available at $Url"
}
Set-Location (Join-Path $PSScriptRoot "..")
Wait-Url "Frontend" "http://127.0.0.1:3000/"
Wait-Url "Backend OpenAPI" "http://127.0.0.1:8000/openapi.json"
docker compose ps
