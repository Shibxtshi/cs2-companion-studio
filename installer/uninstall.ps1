[CmdletBinding()]
param([switch] $Yes, [switch] $KeepDocker, [string] $Language='')
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
. (Join-Path $PSScriptRoot 'i18n.ps1')
try {
    Select-InstallLanguage ([bool]$Yes) $Language
    Write-Host ("`n=== " + (T 'uninstall') + " ===") -ForegroundColor Cyan
    $state = Read-InstallerState
    if ($null -eq $state) {
        Write-Host (T 'uninstall_none')
    } else {
        $target = [string]$state.cfg_path
        if (Test-Path -LiteralPath $target -PathType Leaf) {
            $actualHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
            if ($actualHash -ne [string]$state.installed_hash) {
                Write-Host (T 'uninstall_unchanged') -ForegroundColor Yellow
            } elseif ($Yes -or (Confirm-Action (T 'uninstall_q') $false)) {
                if ([bool]$state.original_existed -and [string]::IsNullOrWhiteSpace([string]$state.backup_path)) {
                    Write-Host (T 'gsi_identical') -ForegroundColor Yellow
                } elseif ([bool]$state.original_existed) {
                    if ([string]::IsNullOrWhiteSpace([string]$state.backup_path) -or
                        -not (Test-Path -LiteralPath ([string]$state.backup_path) -PathType Leaf)) {
                        throw (T 'backup_missing')
                    }
                    Copy-Item -LiteralPath ([string]$state.backup_path) -Destination $target -Force
                    Write-Host (T 'uninstall_old') -ForegroundColor Green
                } else {
                    Remove-Item -LiteralPath $target -Force
                    Write-Host (T 'uninstall_removed') -ForegroundColor Green
                }
                Remove-Item -LiteralPath $script:StateFile -Force
            } else { Write-Host (T 'uninstall_keep') }
        } else {
            Write-Host (T 'gsi_absent')
            Remove-Item -LiteralPath $script:StateFile -Force
        }
    }
    if (-not $KeepDocker) {
        if (Get-Command 'docker' -ErrorAction SilentlyContinue) {
            Push-Location $script:StudioRoot
            try { & docker compose -f (Join-Path $script:StudioRoot 'compose.yaml') down }
            finally { Pop-Location }
        }
    }
    Write-Host (T 'uninstall_preserve')
    Write-Host (T 'uninstall_restart')
    exit 0
} catch {
    Write-Host (T 'error' @{ message=$_.Exception.Message }) -ForegroundColor Red
    exit 1
}
