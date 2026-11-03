[CmdletBinding()]
param([string] $Language = '')
. (Join-Path $PSScriptRoot 'common.ps1')
. (Join-Path $PSScriptRoot 'i18n.ps1')
Select-InstallLanguage $true $Language
Write-Host (T 'status_title') -ForegroundColor Cyan
$envPath = Join-Path $script:StudioRoot '.env'
$values = Read-EnvValues $envPath
Write-Host (T 'status_env' @{ state=$(if (Test-Path -LiteralPath $envPath) { T 'present' } else { T 'absent' }) })
Write-Host (T 'status_token' @{ state=$(if ($values.ContainsKey('GSI_TOKEN') -and $values['GSI_TOKEN'].Length -ge 12) { T 'secret_present' } else { T 'secret_absent' }) })
$state = Read-InstallerState
if ($null -eq $state) { Write-Host (T 'status_unmanaged') }
else {
    Write-Host (T 'status_path' @{ path=[string]$state.cfg_path })
    $exists = Test-Path -LiteralPath ([string]$state.cfg_path) -PathType Leaf
    Write-Host (T 'status_exists' @{ state=$(if ($exists) { T 'yes' } else { T 'no' }) })
    if ($exists) {
        $unchanged = (Get-FileHash -LiteralPath $state.cfg_path -Algorithm SHA256).Hash -eq $state.installed_hash
        Write-Host (T 'status_unchanged' @{ state=$(if ($unchanged) { T 'yes' } else { T 'no' }) })
    }
}
if (Get-Command 'docker' -ErrorAction SilentlyContinue) {
    & docker compose -f (Join-Path $script:StudioRoot 'compose.yaml') ps
} else { Write-Host (T 'status_docker_missing') }
$port = if ($values.ContainsKey('PORT')) { $values['PORT'] } else { '8080' }
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 3
    Write-Host (T 'status_server' @{ service=$health.service; version=$health.version })
} catch { Write-Host (T 'status_offline') -ForegroundColor Yellow }
Write-Host (T 'status_privacy')
