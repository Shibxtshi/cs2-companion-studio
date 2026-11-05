# Windows PowerShell 5.1 / PowerShell 7; run from project folder via INSTALLER_WINDOWS.cmd.
[CmdletBinding()]
param(
    [string] $Cs2Path = '',
    [switch] $Lan,
    [switch] $LocalOnly,
    [switch] $NoStart,
    [switch] $ForceGsiOverwrite,
    [switch] $NonInteractive,
    [string] $Language = ''
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
. (Join-Path $PSScriptRoot 'i18n.ps1')

$stage = T 'initialization'
try {
    Select-InstallLanguage ([bool]$NonInteractive) $Language
    $stage = T 'initialization'
    Write-Host ("`n=== " + (T 'intro') + " ===") -ForegroundColor Cyan
    Write-Host (T 'disclaimer')
    if ($Lan -and $LocalOnly) { throw (T 'lan_options_conflict') }
    $stage = T 'stageDocker'
    Write-Host (T 'stage1')
    # Docker availability does not justify elevating the entire installer.
    Test-DockerReady
    $stage = T 'stageCs2'
    Write-Host (T 'stage2')
    $cfgFolder = Find-Cs2ConfigFolder $Cs2Path
    Write-Host ((T 'detected') + " $cfgFolder") -ForegroundColor Green
    $stage = T 'stageFolder'
    Write-Host (T 'write_check')
    if (-not (Test-GsiFolderWritable $cfgFolder)) {
        if (Test-AdminSession) { throw (T 'denied_admin') }
        Write-Host (T 'elevation_reason') -ForegroundColor Yellow
        if ($NonInteractive -or -not (Confirm-Action (T 'elevation_question') $false)) { throw (T 'elevation_declined') }
        Write-Host (T 'elevation_ok') -ForegroundColor Yellow
        $rc = Invoke-SetupElevated $PSCommandPath $cfgFolder $script:InstallLanguage ([bool]$Lan) ([bool]$LocalOnly) ([bool]$NoStart) ([bool]$ForceGsiOverwrite)
        if ($rc -ne 0) { throw (T 'elevation_failed') }
        exit 0
    }

    $stage = T 'stageConfiguration'
    Write-Host (T 'stage3')
    $envPath = Join-Path $script:StudioRoot '.env'
    $createdEnv = -not (Test-Path -LiteralPath $envPath -PathType Leaf)
    $envText = ''
    if ($createdEnv) {
        $pin = New-RandomPin
        $token = New-RandomUrlToken
        $envText = New-PrivateEnv $pin $token '127.0.0.1'
        Write-Host (T 'new_env')
    } else {
        $envText = [System.IO.File]::ReadAllText($envPath)
        Write-Host (T 'existing_env')
    }
    if ($Lan) {
        Write-Host (T 'installer.network.warning') -ForegroundColor Yellow
        if (-not (Confirm-Action (T 'confirm_lan') $NonInteractive)) {
            throw (T 'lan_not_confirmed')
        }
        $envText = Set-EnvSetting $envText 'BIND_HOST' '0.0.0.0'
    } elseif ($LocalOnly) {
        $envText = Set-EnvSetting $envText 'BIND_HOST' '127.0.0.1'
    } elseif ($createdEnv -and -not $NonInteractive) {
        Write-Host (T 'installer.network.title') -ForegroundColor Cyan
    Write-Host (T 'installer.network.description')
        if (Confirm-Action (T 'installer.network.enable') $false) {
            Write-Host (T 'installer.network.warning') -ForegroundColor Yellow
            if (Confirm-Action (T 'lan_private') $false) {
                $envText = Set-EnvSetting $envText 'BIND_HOST' '0.0.0.0'
            }
        }
    }
    $envText = Select-BombTimerSetting $envText $createdEnv ([bool]$NonInteractive)
    $tmpValues = @{}
    foreach ($line in ($envText -split "`r?`n")) {
        if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { $tmpValues[$Matches[1]] = $Matches[2].Trim() }
    }
    $token = [string]$tmpValues['GSI_TOKEN']
    $pin = [string]$tmpValues['DASHBOARD_PIN']
    $hostBinding = [string]$tmpValues['BIND_HOST']
    $port = 8080
    if ($tmpValues.ContainsKey('PORT')) {
        if (-not [int]::TryParse([string]$tmpValues['PORT'], [ref]$port)) { throw (T 'invalid_port') }
    }
    if ($token.Length -lt 12 -or $pin.Length -lt 6) { throw (T 'invalid_credentials') }
    if ($port -lt 1024 -or $port -gt 65535) { throw (T 'port_range') }
    if ($hostBinding -ne '127.0.0.1' -and $hostBinding -ne '0.0.0.0') {
        Write-Host (T 'custom_bind' @{ address=$hostBinding }) -ForegroundColor Yellow
    }

    $target = Join-Path $cfgFolder $script:GsiName
    $cfgText = New-GsiConfig $token $port
    $oldState = Read-InstallerState
    if ($null -ne $oldState -and $oldState.cfg_path -ne $target) {
        throw (T 'other_cs2')
    }
    $existed = Test-Path -LiteralPath $target -PathType Leaf
    $different = $existed -and ([System.IO.File]::ReadAllText($target) -ne $cfgText)
    $backup = ''
    $originalExisted = $existed
    if ($null -ne $oldState) {
        $originalExisted = [bool]$oldState.original_existed
        $backup = [string]$oldState.backup_path
    }
    if ($different) {
        $managedOld = $false
        if ($null -ne $oldState -and $oldState.installed_hash -eq (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash) {
            $managedOld = $true
        }
        if (-not $managedOld -and -not $ForceGsiOverwrite -and
            -not (Confirm-Action (T 'gsi_replace') $NonInteractive)) {
            throw (T 'gsi_not_replaced')
        }
        if (-not $managedOld) {
            New-Item -ItemType Directory -Path $script:StateDir -Force | Out-Null
            $preUpdateBackup = Join-Path $script:StateDir ('gsi-pre-update-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.cfg')
            Copy-Item -LiteralPath $target -Destination $preUpdateBackup -ErrorAction Stop
            if ([string]::IsNullOrWhiteSpace($backup)) { $backup = $preUpdateBackup }
            Write-Host (T 'gsi_backup') -ForegroundColor Yellow
        }
    }
    if ($createdEnv -or ($envText -ne [System.IO.File]::ReadAllText($envPath))) {
        Write-Utf8File $envPath $envText
    }
    if (-not $existed -or $different) { Write-Utf8File $target $cfgText }
    $sha = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    Write-InstallerState ([pscustomobject]@{
        version='1.1.0'; cfg_path=$target; installed_hash=$sha
        original_existed=$originalExisted; backup_path=$backup
        created_env= $(if ($null -ne $oldState) { [bool]$oldState.created_env } else { $createdEnv })
        installed_at=(Get-Date).ToString('o')
    })
    Write-Host (T 'gsi_ok') -ForegroundColor Green
    if (-not $NoStart) {
        $stage = T 'stageCompose'
        Write-Host (T 'stage4')
        Push-Location $script:StudioRoot
        try {
            & docker compose -f (Join-Path $script:StudioRoot 'compose.yaml') config --quiet
            if ($LASTEXITCODE -ne 0) { throw (T 'settings_invalid') }
            & docker compose -f (Join-Path $script:StudioRoot 'compose.yaml') up -d --build --force-recreate
            if ($LASTEXITCODE -ne 0) { throw (T 'docker_start_failed') }
        } finally { Pop-Location }
        $healthHost = if ($hostBinding -eq '0.0.0.0') { '127.0.0.1' } else { $hostBinding }
        $healthUrl = "http://$($healthHost):$port/health"
        $healthy = $false
        for ($i=0; $i -lt 15; $i++) {
            try {
                $response = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 2
                if ($response.service -eq 'ok') { $healthy = $true; break }
            } catch { Start-Sleep -Seconds 1 }
        }
        if ($healthy) { Write-Host (T 'docker_ok') -ForegroundColor Green }
        else { Write-Host ((T 'docker_wait') + " $healthUrl") -ForegroundColor Yellow }
    }
    Write-Host ("`n" + (T 'page_pc') + " : http://localhost:$port")
    if ($hostBinding -eq '0.0.0.0') {
        Write-Host ((T 'installer.network.addressLabel') + " : http://YOUR_PC_LAN_IP:$port")
        Write-Host (T 'installer.network.addressHelp')
        Write-Host (T 'installer.network.warning') -ForegroundColor Yellow
        try {
            Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
                Where-Object { $_.IPAddress -notmatch '^(127\.|169\.254\.)' -and $_.InterfaceAlias -notmatch '(Docker|vEthernet|Loopback|WSL)' } |
                Select-Object -ExpandProperty IPAddress | ForEach-Object { Write-Host (T 'candidate_ip' @{ address=$_ }) }
        } catch {}
    }
    if ($hostBinding -eq '127.0.0.1') { Write-Host (T 'installer.network.localOnly') }
    Write-Host ((T 'personal_pin') + " : $pin") -ForegroundColor Cyan
    Write-Host (T 'secrets')
    Write-Host (T 'other_tools')
    exit 0
} catch {
    Write-Host ((T 'failstage') + " : $stage") -ForegroundColor Yellow
    Write-Host (T 'error' @{ message=$_.Exception.Message }) -ForegroundColor Red
    Write-Host ((T 'source') + " : " + $_.InvocationInfo.ScriptName + ':' + $_.InvocationInfo.ScriptLineNumber) -ForegroundColor DarkGray
    Write-Host (T 'fail_note')
    exit 1
}
