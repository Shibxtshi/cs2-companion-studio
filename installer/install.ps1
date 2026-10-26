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

$stage = "Initialisation"
try {
    Select-InstallLanguage ([bool]$NonInteractive) $Language
    Write-Host ("`n=== " + (T 'intro') + " ===") -ForegroundColor Cyan
    Write-Host (T 'disclaimer')
    if ($Lan -and $LocalOnly) { throw 'Options -Lan et -LocalOnly incompatibles.' }
    $stage = 'Verification Docker Desktop'
    Write-Host (T 'stage1')
    try { Test-DockerReady } catch {
        $dockerError = $_.Exception.Message
        if (-not $NonInteractive -and -not (Test-AdminSession)) {
            Write-Host $dockerError -ForegroundColor Yellow
            Write-Host (T 'elevation_reason') -ForegroundColor Yellow
            if (Confirm-Action (T 'elevation_question') $false) {
                Write-Host (T 'elevation_ok')
                $rc = Invoke-SetupElevated $PSCommandPath $Cs2Path $script:InstallLanguage ([bool]$Lan) ([bool]$LocalOnly) ([bool]$NoStart) ([bool]$ForceGsiOverwrite)
                if ($rc -ne 0) { throw (T 'elevation_failed') }
                exit 0
            }
        }
        throw $dockerError
    }
    $stage = 'Recherche de CS2'
    Write-Host (T 'stage2')
    $cfgFolder = Find-Cs2ConfigFolder $Cs2Path
    Write-Host ((T 'detected') + " $cfgFolder") -ForegroundColor Green
    $stage = 'Access to CS2 GSI folder'
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

    $stage = 'Preparation de la configuration personnelle'
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
        Write-Host (T 'lan_warning') -ForegroundColor Yellow
        if (-not (Confirm-Action (T 'confirm_lan') $NonInteractive)) {
            throw 'Mode LAN non confirme. Relancer sans -Lan pour rester local uniquement.'
        }
        $envText = Set-EnvSetting $envText 'BIND_HOST' '0.0.0.0'
    } elseif ($LocalOnly) {
        $envText = Set-EnvSetting $envText 'BIND_HOST' '127.0.0.1'
    } elseif ($createdEnv -and -not $NonInteractive) {
        Write-Host (T 'mobile_intro')
        if (Confirm-Action (T 'enable_mobile') $false) {
            Write-Host (T 'lan_warning') -ForegroundColor Yellow
            if (Confirm-Action (T 'lan_private') $false) {
                $envText = Set-EnvSetting $envText 'BIND_HOST' '0.0.0.0'
            }
        }
    }
    $tmpValues = @{}
    foreach ($line in ($envText -split "`r?`n")) {
        if ($line -match '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { $tmpValues[$Matches[1]] = $Matches[2].Trim() }
    }
    $token = [string]$tmpValues['GSI_TOKEN']
    $pin = [string]$tmpValues['DASHBOARD_PIN']
    $hostBinding = [string]$tmpValues['BIND_HOST']
    $port = 8080
    if ($tmpValues.ContainsKey('PORT')) {
        if (-not [int]::TryParse([string]$tmpValues['PORT'], [ref]$port)) { throw 'PORT invalide dans .env.' }
    }
    if ($token.Length -lt 12 -or $pin.Length -lt 6) { throw 'Identifiants manquants/invalides dans .env.' }
    if ($port -lt 1024 -or $port -gt 65535) { throw 'PORT doit etre compris entre 1024 et 65535.' }
    if ($hostBinding -ne '127.0.0.1' -and $hostBinding -ne '0.0.0.0') {
        Write-Host "Bind personnalise conserve : $hostBinding" -ForegroundColor Yellow
    }

    $target = Join-Path $cfgFolder $script:GsiName
    $cfgText = New-GsiConfig $token $port
    $oldState = Read-InstallerState
    if ($null -ne $oldState -and $oldState.cfg_path -ne $target) {
        throw 'Installation precedente associee a un autre CS2. Desinstaller depuis cet emplacement avant de changer de destination.'
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
            throw 'Fichier GSI existant non modifie. Relancer avec -ForceGsiOverwrite ou confirmer en mode interactif.'
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
        version='1.0.0'; cfg_path=$target; installed_hash=$sha
        original_existed=$originalExisted; backup_path=$backup
        created_env= $(if ($null -ne $oldState) { [bool]$oldState.created_env } else { $createdEnv })
        installed_at=(Get-Date).ToString('o')
    })
    Write-Host (T 'gsi_ok') -ForegroundColor Green
    if (-not $NoStart) {
        $stage = 'Demarrage Docker Compose'
        Write-Host (T 'stage4')
        Push-Location $script:StudioRoot
        try {
            & docker compose -f (Join-Path $script:StudioRoot 'compose.yaml') config --quiet
            if ($LASTEXITCODE -ne 0) { throw 'Configuration Docker Compose invalide.' }
            & docker compose -f (Join-Path $script:StudioRoot 'compose.yaml') up -d --build --force-recreate
            if ($LASTEXITCODE -ne 0) { throw 'Impossible de demarrer Docker (port deja utilise ?).' }
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
        Write-Host ((T 'page_phone') + " : http://YOUR_PC_LAN_IP:$port")
        Write-Host (T 'lan_warning') -ForegroundColor Yellow
        try {
            Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
                Where-Object { $_.IPAddress -notmatch '^(127\.|169\.254\.)' -and $_.InterfaceAlias -notmatch '(Docker|vEthernet|Loopback|WSL)' } |
                Select-Object -ExpandProperty IPAddress | ForEach-Object { Write-Host "IP possible : $_" }
        } catch {}
    }
    Write-Host ((T 'personal_pin') + " : $pin") -ForegroundColor Cyan
    Write-Host (T 'secrets')
    Write-Host (T 'other_tools')
    exit 0
} catch {
    Write-Host ((T 'failstage') + " : $stage") -ForegroundColor Yellow
    Write-Host ("ERREUR : " + $_.Exception.Message) -ForegroundColor Red
    Write-Host ((T 'source') + " : " + $_.InvocationInfo.ScriptName + ':' + $_.InvocationInfo.ScriptLineNumber) -ForegroundColor DarkGray
    Write-Host (T 'fail_note')
    exit 1
}
