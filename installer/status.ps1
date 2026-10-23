[CmdletBinding()]
param()
. (Join-Path $PSScriptRoot 'common.ps1')
Write-Host '=== CS2 Companion Studio : diagnostic ===' -ForegroundColor Cyan
$envPath = Join-Path $script:StudioRoot '.env'
$values = Read-EnvValues $envPath
Write-Host ('Configuration .env : ' + $(if (Test-Path -LiteralPath $envPath) { 'presente' } else { 'absente' }))
Write-Host ('GSI token : ' + $(if ($values.ContainsKey('GSI_TOKEN') -and $values['GSI_TOKEN'].Length -ge 12) { 'present (non affiche)' } else { 'absent/invalide' }))
$state = Read-InstallerState
if ($null -eq $state) { Write-Host 'Installation GSI : non suivie par assistant' }
else {
    Write-Host ('Fichier GSI : ' + [string]$state.cfg_path)
    $exists = Test-Path -LiteralPath ([string]$state.cfg_path) -PathType Leaf
    Write-Host ('Existant : ' + $exists)
    if ($exists) { Write-Host ('Non modifie depuis installation : ' + ((Get-FileHash -LiteralPath $state.cfg_path -Algorithm SHA256).Hash -eq $state.installed_hash)) }
}
if (Get-Command 'docker' -ErrorAction SilentlyContinue) {
    & docker compose -f (Join-Path $script:StudioRoot 'compose.yaml') ps
} else { Write-Host 'Docker : introuvable' }
$port = if ($values.ContainsKey('PORT')) { $values['PORT'] } else { '8080' }
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$port/health" -TimeoutSec 3
    Write-Host ('Serveur : ' + $health.service + ' / ' + $health.version)
} catch { Write-Host 'Serveur : inaccessible depuis localhost' -ForegroundColor Yellow }
Write-Host 'Aucun PIN/token affiche ou ecrit dans les diagnostics.'
