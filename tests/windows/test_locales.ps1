# Windows PowerShell 5.1-compatible localization checks using an extracted synthetic archive.
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$tempParent = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath())
$temporary = Join-Path $tempParent ('ccs-locales-' + [guid]::NewGuid().ToString('N'))
function Assert-True([bool] $Condition, [string] $Message) { if (-not $Condition) { throw $Message } }
try {
    $bundle = Join-Path $temporary 'bundle'
    New-Item -ItemType Directory -Path (Join-Path $bundle 'static/locales') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $root 'installer') -Destination $bundle -Recurse
    Copy-Item -Path (Join-Path $root 'static/locales/*.json') -Destination (Join-Path $bundle 'static/locales')
    $archive = Join-Path $temporary 'source.zip'
    Compress-Archive -Path (Join-Path $bundle '*') -DestinationPath $archive
    $extracted = Join-Path $temporary 'extracted'
    Expand-Archive -LiteralPath $archive -DestinationPath $extracted
    $languageData = Get-Content -LiteralPath (Join-Path $extracted 'static/locales/languages.json') -Encoding UTF8 -Raw | ConvertFrom-Json
    foreach ($requestedLanguage in (@('') + @($languageData.languages.code))) {
        $selection = & {
            param([string] $Language, [string] $LocaleScript)
            $script:languagePromptCalls = 0
            function Read-Host {
                param([string] $Prompt)
                $script:languagePromptCalls++
                return '2'
            }
            # Dot-sourcing must not overwrite the installer's Language parameter.
            . $LocaleScript
            $loadedLanguage = $Language
            Select-InstallLanguage $false $Language
            [pscustomobject]@{
                requested = $loadedLanguage
                prompts = $script:languagePromptCalls
                selected = $script:InstallLanguage
            }
        } $requestedLanguage (Join-Path $extracted 'installer/i18n.ps1')
        Assert-True ($selection.requested -ceq $requestedLanguage) 'Loading catalogs changed the requested language'
        if ($requestedLanguage -eq '') {
            Assert-True ($selection.prompts -eq 1 -and $selection.selected -ceq 'FR') 'Default startup did not ask for language'
        } else {
            Assert-True ($selection.prompts -eq 0 -and $selection.selected -ceq $requestedLanguage) 'Explicit language was ignored or prompted again'
        }
    }
    . (Join-Path $extracted 'installer/i18n.ps1')
    . (Join-Path $extracted 'installer/common.ps1')
    Set-InstallLanguage 'FR'
    Assert-True ((T 'installer.network.title') -ceq 'Accès au réseau local') 'UTF-8 accents were lost'
    Assert-True ((T 'installer.network.warning').Contains('ne chiffre pas')) 'LAN encryption warning missing'
    Assert-True ((T 'installer.network.warning').Contains('pare-feu')) 'Firewall disclosure missing'
    Set-InstallLanguage 'RU'
    Assert-True ((T 'widgets.health.title') -ceq 'Здоровье') 'Russian UTF-8 text was lost'
    Set-InstallLanguage 'UK'
    Assert-True ((T 'widgets.health.title') -ceq "Здоров’я") 'Ukrainian UTF-8 text was lost'
    Set-InstallLanguage 'FR'
    $personal = 'Émilie "quoted" $() <tag> {unchanged}'
    Assert-True ((T 'status_path' @{ path=$personal }).Contains($personal)) 'Parameter data was interpreted or modified'
    $failed = $false
    try { T 'status_path' @{ other='wrong' } | Out-Null } catch { $failed=$true }
    Assert-True $failed 'Missing/extra parameters were accepted'
    $failed = $false
    try { T 'status_path' @{ Path='wrong case' } | Out-Null } catch { $failed=$true }
    Assert-True $failed 'Parameter case mismatch was accepted'
    Assert-True ((T 'missing_key') -ceq '[installer.missing_key]') 'Unknown-key behavior changed'
    Select-InstallLanguage $true ''
    Assert-True ($script:InstallLanguage -ceq 'EN') 'Noninteractive default changed'
    function Read-Host { return $script:answer }
    $script:answer = '2'
    Select-InstallLanguage $false ''
    Assert-True ($script:InstallLanguage -ceq 'FR') 'Interactive registry selection failed'
    foreach ($entry in $script:LanguageRegistry.languages) {
        Set-InstallLanguage $entry.code
        $script:answer = $entry.confirmYes
        Assert-True (Confirm-Action 'Synthetic confirmation' $false) 'Explicit confirmation failed'
        $script:answer = 'wrong'
        Assert-True (-not (Confirm-Action 'Synthetic confirmation' $false)) 'Unrecognized answer granted consent'
        $script:answer = ''
        Assert-True (-not (Confirm-Action 'Synthetic confirmation' $false)) 'Empty input granted consent'
        Assert-True (-not (Confirm-Action 'Synthetic confirmation' $true)) 'Noninteractive input granted consent'
    }
    Remove-Item Function:Read-Host
    $registryPath = Join-Path $extracted 'static/locales/languages.json'
    $registry = Get-Content -LiteralPath $registryPath -Encoding UTF8 -Raw | ConvertFrom-Json
    $registry.languages = @($registry.languages) + @([pscustomobject]@{ code='ZZ'; name='Synthetic'; file='zz.json'; confirmYes='Y' })
    [System.IO.File]::WriteAllText($registryPath, ($registry | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
    $thirdPath = Join-Path $extracted 'static/locales/zz.json'
    $third = Get-Content -LiteralPath (Join-Path $extracted 'static/locales/en.json') -Encoding UTF8 -Raw | ConvertFrom-Json
    $third.PSObject.Properties['installer.intro'].Value = 'Synthetic installer'
    [System.IO.File]::WriteAllText($thirdPath, ($third | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
    . (Join-Path $extracted 'installer/i18n.ps1')
    Set-InstallLanguage 'ZZ'
    Assert-True ((T 'intro') -ceq 'Synthetic installer') 'Data-only third language failed'
    $complete = [System.IO.File]::ReadAllBytes($thirdPath)
    $third.PSObject.Properties.Remove('studio.publish')
    [System.IO.File]::WriteAllText($thirdPath, ($third | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
    $failed = $false
    try { . (Join-Path $extracted 'installer/i18n.ps1') } catch { $failed=$true }
    Assert-True $failed 'Incomplete listed language was accepted'
    [System.IO.File]::WriteAllBytes($thirdPath, $complete)
    $wrapper = Join-Path $temporary 'run-synthetic.ps1'
    $wrapperText = @'
param($RootPath, $GamePath, $Action, $Language)
$ErrorActionPreference='Stop'
function global:docker { $global:LASTEXITCODE=0; 'synthetic-docker' }
function global:Invoke-RestMethod { @{ service='ok'; version='synthetic' } }
if ($Action -eq 'install') { & (Join-Path $RootPath 'installer/install.ps1') -Cs2Path $GamePath -NoStart -NonInteractive -Language $Language }
elseif ($Action -eq 'status') { & (Join-Path $RootPath 'installer/status.ps1') -Language $Language }
else { & (Join-Path $RootPath 'installer/uninstall.ps1') -Yes -KeepDocker -Language $Language }
'@
    [System.IO.File]::WriteAllText($wrapper, $wrapperText, [System.Text.UTF8Encoding]::new($true))
    foreach ($language in $languageData.languages.code) {
        $game = Join-Path $temporary ($language + '/game/csgo/cfg')
        New-Item -ItemType Directory -Path $game -Force | Out-Null
        $output = & powershell.exe -NoProfile -File $wrapper -RootPath $extracted -GamePath $game -Action install -Language $language 2>&1
        Assert-True ($LASTEXITCODE -eq 0) ('Synthetic install failed: ' + $language)
        $envPath = Join-Path $extracted '.env'
        $before = (Get-FileHash -LiteralPath $envPath -Algorithm SHA256).Hash
        $output = & powershell.exe -NoProfile -File $wrapper -RootPath $extracted -GamePath $game -Action status -Language $language 2>&1
        Assert-True ($LASTEXITCODE -eq 0) ('Synthetic diagnostics failed: ' + $language)
        Assert-True (($output -join ' ') -notmatch 'GSI_TOKEN=|DASHBOARD_PIN=') 'Diagnostics leaked credential assignments'
        $output = & powershell.exe -NoProfile -File $wrapper -RootPath $extracted -GamePath $game -Action uninstall -Language $language 2>&1
        Assert-True ($LASTEXITCODE -eq 0) ('Synthetic uninstall failed: ' + $language)
        Assert-True ((Get-FileHash -LiteralPath $envPath -Algorithm SHA256).Hash -eq $before) 'Uninstall changed synthetic credentials'
    }
    Write-Host 'OK: shared catalogs, UTF-8, named parameters, Y/O/no-consent, EN/FR installation/status/uninstall from ZIP; Docker and HTTP mocked.'
} finally {
    $resolved = [System.IO.Path]::GetFullPath($temporary)
    if (-not $resolved.StartsWith($tempParent, [System.StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe synthetic cleanup path' }
    if (Test-Path -LiteralPath $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
