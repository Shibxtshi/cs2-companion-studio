# Shared helpers for native Windows PowerShell 5.1+ setup.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:StudioRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$script:StateDir = Join-Path $script:StudioRoot '.installer-state'
$script:StateFile = Join-Path $script:StateDir 'install.json'
$script:GsiName = 'gamestate_integration_companion.cfg'

function Write-Utf8File([string] $Path, [string] $Text) {
    # Write beside the destination so replacement stays on the same filesystem.
    $destination = [System.IO.Path]::GetFullPath($Path)
    $directory = [System.IO.Path]::GetDirectoryName($destination)
    $temporary = Join-Path $directory ('.companion-write-' + [guid]::NewGuid().ToString('N') + '.tmp')
    $utf8 = [System.Text.UTF8Encoding]::new($false)
    try {
        [System.IO.File]::WriteAllText($temporary, $Text, $utf8)
        if ([System.IO.File]::Exists($destination)) {
            [System.IO.File]::Replace($temporary, $destination, [NullString]::Value)
        } else {
            [System.IO.File]::Move($temporary, $destination)
        }
    } finally {
        if ([System.IO.File]::Exists($temporary)) {
            [System.IO.File]::Delete($temporary)
        }
    }
}

function Read-EnvValues([string] $Path) {
    $values = @{}
    if (Test-Path -LiteralPath $Path -PathType Leaf) {
        foreach ($line in [System.IO.File]::ReadAllLines($Path)) {
            if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$') {
                $values[$Matches[1]] = $Matches[2].Trim()
            }
        }
    }
    return $values
}

function Set-EnvSetting([string] $Text, [string] $Key, [string] $Value) {
    $pattern = '(?m)^' + [regex]::Escape($Key) + '=.*$'
    if ([regex]::IsMatch($Text, $pattern)) {
        return [regex]::Replace($Text, $pattern, ($Key + '=' + $Value))
    }
    return $Text.TrimEnd([char[]]@("`r", "`n")) + "`n" + $Key + '=' + $Value + "`n"
}

function New-RandomUrlToken {
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $bytes = New-Object byte[] 36
        $rng.GetBytes($bytes)
        return [Convert]::ToBase64String($bytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
    } finally { $rng.Dispose() }
}

function New-RandomPin {
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try {
        $digits = New-Object System.Text.StringBuilder
        $one = New-Object byte[] 1
        while ($digits.Length -lt 10) {
            $rng.GetBytes($one)
            if ($one[0] -lt 250) {
                [void]$digits.Append([string]($one[0] % 10))
            }
        }
        return $digits.ToString()
    } finally { $rng.Dispose() }
}

function New-PrivateEnv([string] $Pin, [string] $Token, [string] $BindHost) {
    $result = @"
# Configuration personnelle CS2 Companion Studio. NE PAS PUBLIER.
GSI_TOKEN=$Token
DASHBOARD_PIN=$Pin
BOMB_TIMER_ENABLED=false
BOMB_DURATION_SECONDS=40
BIND_HOST=$BindHost
PORT=8080
"@
    return ($result + "`n")
}

function New-GsiConfig([string] $Token, [int] $Port) {
    $result = @"
"CS2 Companion Studio"
{
    "uri" "http://127.0.0.1:$Port/gsi"
    "timeout" "5.0"
    "buffer" "0.1"
    "throttle" "0.2"
    "heartbeat" "10.0"
    "auth" { "token" "$Token" }
    "data"
    {
        "provider" "1"
        "map" "1"
        "map_round_wins" "1"
        "round" "1"
        "player_id" "1"
        "player_state" "1"
        "player_weapons" "1"
        "player_match_stats" "1"
    }
}
"@
    return ($result + "`n")
}

# A Steam library on a disconnected mapped drive must not abort the whole installer.
function Test-ReadableDirectory([string] $Path) {
    if ([string]::IsNullOrWhiteSpace($Path)) { return $false }
    try { return [bool](Test-Path -LiteralPath $Path -PathType Container -ErrorAction Stop) }
    catch { return $false }
}

function Find-Cs2ConfigFolder([string] $Hint) {
    if (-not [string]::IsNullOrWhiteSpace($Hint)) {
        $paths = @($Hint)
        try {
            $paths += [System.IO.Path]::Combine($Hint, 'game', 'csgo', 'cfg')
            $paths += [System.IO.Path]::Combine($Hint, 'csgo', 'cfg')
        } catch { throw ((T 'bad_path') + " $Hint") }
        foreach ($p in $paths) {
            if (-not (Test-ReadableDirectory $p)) { continue }
            try {
                if (((Split-Path $p -Leaf) -ieq 'cfg') -and
                    ((Split-Path (Split-Path $p -Parent) -Leaf) -ieq 'csgo')) {
                    return (Resolve-Path -LiteralPath $p -ErrorAction Stop).Path
                }
            } catch { continue }
        }
        throw ((T 'bad_access_path') + " $Hint. Select the CS2 folder or game\csgo\cfg.")
    }

    $roots = New-Object 'System.Collections.Generic.List[string]'
    try {
        $steam = (Get-ItemProperty 'HKCU:\Software\Valve\Steam' -ErrorAction Stop).SteamPath
        if ($steam) { [void]$roots.Add($steam) }
    } catch {}
    try {
        $steam = (Get-ItemProperty 'HKLM:\SOFTWARE\WOW6432Node\Valve\Steam' -ErrorAction Stop).InstallPath
        if ($steam) { [void]$roots.Add($steam) }
    } catch {}
    if (${env:ProgramFiles(x86)}) { [void]$roots.Add([System.IO.Path]::Combine(${env:ProgramFiles(x86)}, 'Steam')) }
    if ($env:ProgramFiles) { [void]$roots.Add([System.IO.Path]::Combine($env:ProgramFiles, 'Steam')) }

    # Do not enumerate UNC shares or mapped network drives (often disconnected).
    # Steam libraryfolders.vdf can still point to a library on another local disk.
    foreach ($drive in @(Get-PSDrive -PSProvider FileSystem -ErrorAction SilentlyContinue)) {
        try {
            if ($drive.DisplayRoot -or $drive.Root -notmatch '^[A-Za-z]:\\$') { continue }
            [void]$roots.Add([System.IO.Path]::Combine($drive.Root, 'SteamLibrary'))
            [void]$roots.Add([System.IO.Path]::Combine($drive.Root, 'Steam'))
        } catch { continue }
    }

    $libraries = New-Object 'System.Collections.Generic.List[string]'
    foreach ($root in @($roots | Select-Object -Unique)) {
        if (-not (Test-ReadableDirectory $root)) { continue }
        [void]$libraries.Add($root)
        try {
            $vdf = [System.IO.Path]::Combine($root, 'steamapps', 'libraryfolders.vdf')
            if (Test-Path -LiteralPath $vdf -PathType Leaf -ErrorAction Stop) {
                foreach ($line in [System.IO.File]::ReadAllLines($vdf)) {
                    if ($line -match '^\s*"path"\s*"([^"]+)"' -or
                        $line -match '^\s*"[0-9]+"\s*"([A-Za-z]:[^"]+)"') {
                        $libraryPath = $Matches[1].Replace('\\', '\')
                        if ($libraryPath -match '^[A-Za-z]:\\' -and (Test-ReadableDirectory $libraryPath)) {
                            [void]$libraries.Add($libraryPath)
                        }
                    }
                }
            }
        } catch {
            # Inaccessible/corrupt manifest is non-fatal: try the other libraries.
            continue
        }
    }
    foreach ($library in @($libraries | Select-Object -Unique)) {
        try {
            if (-not (Test-ReadableDirectory $library)) { continue }
            $steamapps = [System.IO.Path]::Combine($library, 'steamapps')
            $manifest = [System.IO.Path]::Combine($steamapps, 'appmanifest_730.acf')
            $installName = 'Counter-Strike Global Offensive'
            if (Test-Path -LiteralPath $manifest -PathType Leaf -ErrorAction Stop) {
                $content = [System.IO.File]::ReadAllText($manifest)
                if ($content -match '"installdir"\s*"([^"]+)"') { $installName = $Matches[1] }
            }
            $cfg = [System.IO.Path]::Combine($steamapps, 'common', $installName, 'game', 'csgo', 'cfg')
            if (Test-ReadableDirectory $cfg) { return (Resolve-Path -LiteralPath $cfg -ErrorAction Stop).Path }
        } catch { continue }
    }
    throw (T 'not_found')
}

function Test-DockerReady {
    if (-not (Get-Command 'docker' -ErrorAction SilentlyContinue)) {
        throw (T 'no_docker')
    }
    # In Windows PowerShell 5.1, docker.exe stderr may otherwise be promoted
    # to a terminating NativeCommandError, concealing the actual failed step.
    $oldErrorAction = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $dockerOutput = @(& docker info --format '{{.ServerVersion}}' 2>&1)
        $dockerExit = $LASTEXITCODE
        if ($dockerExit -ne 0) {
            throw (T 'docker_down')
        }
        $composeOutput = @(& docker compose version 2>&1)
        $composeExit = $LASTEXITCODE
        if ($composeExit -ne 0) {
            throw (T 'no_compose')
        }
    } finally { $ErrorActionPreference = $oldErrorAction }
}

function Read-InstallerState {
    if (-not (Test-Path -LiteralPath $script:StateFile -PathType Leaf)) { return $null }
    return (Get-Content -LiteralPath $script:StateFile -Raw -Encoding UTF8 | ConvertFrom-Json)
}

function Write-InstallerState($State) {
    New-Item -ItemType Directory -Path $script:StateDir -Force | Out-Null
    Write-Utf8File $script:StateFile ($State | ConvertTo-Json -Depth 6)
}

function Confirm-Action([string] $Question, [bool] $NonInteractive) {
    if ($NonInteractive) { return $false }
    $answer = (Read-Host ($Question + ' ' + (T 'yes_prompt'))).Trim().ToUpperInvariant()
    if ($script:InstallLanguage -eq 'FR') { return $answer -eq 'O' }
    return $answer -eq 'Y'
}

# Probe the actual destination folder (not merely the administrator group membership).
# A failed probe may be caused by ACLs or a non-local path; escalation is optional.
function Test-GsiFolderWritable([string] $Folder) {
    $probe = Join-Path $Folder ('.cs2-companion-permission-' + [guid]::NewGuid().ToString('N') + '.tmp')
    try {
        $f = [System.IO.File]::Open($probe, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
        $f.Dispose()
        return $true
    } catch { return $false }
    finally { try { if ([System.IO.File]::Exists($probe)) { [System.IO.File]::Delete($probe) } } catch {} }
}
function Test-AdminSession {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
function Invoke-SetupElevated([string] $InstallerPath, [string] $PathHint, [string] $Language, [bool] $Lan, [bool] $LocalOnly, [bool] $NoStart, [bool] $ForceGsiOverwrite) {
    # UTF-16 encoded command avoids quoting errors in spaces or unusual paths.
    # Data is used only to invoke our own script with parameter values, not commands from the user.
    $q = { param([string]$Value) "'" + $Value.Replace("'", "''") + "'" }
    $command = '& ' + (& $q $InstallerPath) + ' -Language ' + (& $q $Language) + ' -Cs2Path ' + (& $q $PathHint)
    if ($Lan) { $command += ' -Lan' }
    if ($LocalOnly) { $command += ' -LocalOnly' }
    if ($NoStart) { $command += ' -NoStart' }
    if ($ForceGsiOverwrite) { $command += ' -ForceGsiOverwrite' }
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($command)
    $encoded = [Convert]::ToBase64String($bytes)
    try {
        $proc = Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoLogo','-NoProfile','-ExecutionPolicy','Bypass','-EncodedCommand',$encoded) -Verb RunAs -Wait -PassThru -ErrorAction Stop
    } catch {
        if ($_.Exception.Message -match '(cancell|cancel|annul|1223|refus)') { throw (T 'elevation_declined') }
        throw
    }
    return $proc.ExitCode
}


# Ask only for a new installation; reruns preserve the existing private setting.
function Select-BombTimerSetting([string] $EnvText, [bool] $CreatedEnv, [bool] $NonInteractive) {
    if (-not $CreatedEnv -or $NonInteractive) { return $EnvText }
    Write-Host (T 'bomb_warning') -ForegroundColor Yellow
    if (Confirm-Action (T 'enable_bomb_timer') $false) {
        return Set-EnvSetting $EnvText 'BOMB_TIMER_ENABLED' 'true'
    }
    return Set-EnvSetting $EnvText 'BOMB_TIMER_ENABLED' 'false'
}

function Invoke-ComposeSettings([string] $ProjectRoot = $script:StudioRoot) {
    if (-not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.env') -PathType Leaf)) {
        throw (T 'settings_missing_env')
    }
    Push-Location $ProjectRoot
    try {
        $composePath = Join-Path $ProjectRoot 'compose.yaml'
        & docker compose -f $composePath config --quiet
        if ($LASTEXITCODE -ne 0) { throw (T 'settings_invalid') }
        # Recreate the container to reload env_file; never rebuild or pull an image.
        & docker compose -f $composePath up -d --no-build --pull never --force-recreate --wait --wait-timeout 120 cs2-companion-studio
        if ($LASTEXITCODE -ne 0) { throw (T 'settings_failed') }
    } finally { Pop-Location }
}
