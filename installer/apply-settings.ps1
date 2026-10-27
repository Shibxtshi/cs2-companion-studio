# Apply private runtime settings without rebuilding the Docker image.
[CmdletBinding()]
param([string] $Language = '', [switch] $NonInteractive)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
. (Join-Path $PSScriptRoot 'i18n.ps1')
try {
    Select-InstallLanguage ([bool]$NonInteractive) $Language
    Write-Host (T 'settings_intro') -ForegroundColor Cyan
    Test-DockerReady
    Invoke-ComposeSettings
    Write-Host (T 'settings_ok') -ForegroundColor Green
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
