# Safe to run on Windows CI: does not require Docker, Steam, or CS2.
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'common.ps1')
. (Join-Path $PSScriptRoot 'i18n.ps1')
function Assert-True([bool] $Condition, [string] $Message) {
    if (-not $Condition) { throw $Message }
}
$pin1 = New-RandomPin
$pin2 = New-RandomPin
$token1 = New-RandomUrlToken
$token2 = New-RandomUrlToken
Assert-True ($pin1 -match '^\d{10}$') 'PIN format invalid'
Assert-True ($pin2 -match '^\d{10}$') 'PIN format invalid (second)'
Assert-True ($pin1 -ne $pin2) 'Unexpected duplicate PIN'
Assert-True ($token1.Length -ge 40) 'Token too short'
Assert-True ($token1 -ne $token2) 'Duplicate token'
$envText = New-PrivateEnv $pin1 $token1 '127.0.0.1'
Assert-True ($envText.Contains('BOMB_TIMER_ENABLED=false')) 'Bomb timer enabled by default'
Assert-True ($envText.Contains('BIND_HOST=127.0.0.1')) 'Default network binding unsafe'
$envLan = Set-EnvSetting $envText 'BIND_HOST' '0.0.0.0'
Assert-True ($envLan.Contains('BIND_HOST=0.0.0.0')) 'LAN transition failed'
Assert-True ($envLan -notmatch 'BIND_HOST=127\.0\.0\.1') 'Duplicate BIND_HOST'
$cfg = New-GsiConfig $token1 8080
Assert-True ($cfg.Contains('"uri" "http://127.0.0.1:8080/gsi"')) 'GSI URL mismatch'
Assert-True ($cfg.Contains('"map_round_wins" "1"')) 'Round history disabled'
Assert-True ($cfg.Contains($token1)) 'GSI token mismatch'
$temp = Join-Path ([System.IO.Path]::GetTempPath()) ('cs2studio-check-' + [guid]::NewGuid().ToString('N'))
try {
    $cfgFolder = Join-Path $temp 'Counter-Strike Global Offensive\game\csgo\cfg'
    New-Item -ItemType Directory -Path $cfgFolder -Force | Out-Null
    $found = Find-Cs2ConfigFolder (Join-Path $temp 'Counter-Strike Global Offensive')
    Assert-True ($found -eq $cfgFolder) 'Explicit CS2 detection failed'
} finally { Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue }
Assert-True (-not (Test-ReadableDirectory '?:\not-a-drive')) 'Inaccessible path must be ignored'
Write-Host 'OK: PowerShell helpers, random credentials, GSI configuration, Steam path override, safe LAN default.'

Set-InstallLanguage 'EN'
Assert-True ((T 'intro') -match 'setup') 'English translation missing'
Assert-True ((Confirm-Action 'Test' $true) -eq $false) 'Non-interactive confirmation must default No'
Set-InstallLanguage 'FR'
Assert-True ((T 'intro') -match 'installation') 'French translation missing'
$script:MockAnswer = 'O'
function Read-Host([string] $Prompt) { return $script:MockAnswer }
Assert-True (Confirm-Action 'Example' $false) 'French O should confirm'
$script:MockAnswer = 'Y'
Assert-True (-not (Confirm-Action 'Example' $false)) 'French Y should not confirm'
Set-InstallLanguage 'EN'
Assert-True (Confirm-Action 'Example' $false) 'English Y should confirm'
$script:MockAnswer = ''
Assert-True (-not (Confirm-Action 'Example' $false)) 'Enter must default to No'
Remove-Item Function:\Read-Host -ErrorAction SilentlyContinue
$scratch = Join-Path ([System.IO.Path]::GetTempPath()) ('cs2studio-permission-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $scratch | Out-Null
try { Assert-True (Test-GsiFolderWritable $scratch) 'Writeability probe on temporary folder failed' }
finally { Remove-Item -LiteralPath $scratch -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host 'OK: EN/FR language registry, Y/N and O/N confirmations, no default consent, folder probe.'

# Failure-path checks operate only on an isolated synthetic directory.
$atomicScratch = Join-Path ([System.IO.Path]::GetTempPath()) ('cs2studio-atomic-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $atomicScratch | Out-Null
try {
    $destination = Join-Path $atomicScratch 'synthetic.env'
    Write-Utf8File $destination 'first'
    Write-Utf8File $destination 'second'
    Assert-True ([System.IO.File]::ReadAllText($destination) -eq 'second') 'Atomic replacement failed'
    Assert-True (([System.IO.File]::ReadAllBytes($destination))[0] -ne 0xEF) 'Unexpected UTF-8 BOM'
    $blocked = Join-Path $atomicScratch 'blocked'
    New-Item -ItemType Directory -Path $blocked | Out-Null
    $sentinel = Join-Path $blocked 'preserve.txt'
    [System.IO.File]::WriteAllText($sentinel, 'keep')
    $failed = $false
    try { Write-Utf8File $blocked 'must fail' } catch { $failed = $true }
    Assert-True $failed 'Replacing a directory must fail'
    Assert-True ([System.IO.File]::ReadAllText($sentinel) -eq 'keep') 'Failed write altered existing contents'
    Assert-True (@(Get-ChildItem -LiteralPath $atomicScratch -Filter '.companion-write-*.tmp').Count -eq 0) 'Temporary credential file leaked'
} finally {
    Remove-Item -LiteralPath $atomicScratch -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host 'OK: atomic UTF-8 writes, safe failure and temporary-file cleanup.'
