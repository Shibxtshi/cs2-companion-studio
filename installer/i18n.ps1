# Shared JSON catalogs; compatible with Windows PowerShell 5.1 and PowerShell 7.
$script:LocaleRoot = Join-Path (Split-Path $PSScriptRoot -Parent) 'static/locales'
$script:LanguageRegistry = Get-Content -LiteralPath (Join-Path $script:LocaleRoot 'languages.json') -Encoding UTF8 -Raw | ConvertFrom-Json
$script:Languages = [ordered]@{}
$script:LocaleCatalogs = @{}
$script:InstallLanguage = 'EN'
foreach ($entry in $script:LanguageRegistry.languages) {
    if ([string]$entry.code -cnotmatch '^[A-Z][A-Z0-9-]*$' -or [string]$entry.file -cnotmatch '^[a-z0-9-]+\.json$' -or [string]$entry.confirmYes -cnotmatch '^[A-Z]$' -or $script:Languages.Contains([string]$entry.code)) { throw 'invalid_locale_registry' }
    if ($entry.confirmYes -ceq 'N' -or ($entry.code -ceq 'EN' -and $entry.confirmYes -cne 'Y') -or ($entry.code -ceq 'FR' -and $entry.confirmYes -cne 'O')) { throw 'unsafe_confirmation_letter' }
    $script:Languages[[string]$entry.code] = [string]$entry.name
    $catalog = Get-Content -LiteralPath (Join-Path $script:LocaleRoot $entry.file) -Encoding UTF8 -Raw | ConvertFrom-Json
    $values = @{}
    foreach ($property in $catalog.PSObject.Properties) { $values[$property.Name] = [string]$property.Value }
    $script:LocaleCatalogs[[string]$entry.code] = $values
}
# Refuse an incomplete listed language instead of hiding errors through fallback.
$reference = $script:LocaleCatalogs.EN
foreach ($languageCode in $script:Languages.Keys) {
    $catalog = $script:LocaleCatalogs[$languageCode]
    if ($catalog.Count -ne $reference.Count) { throw ('incomplete_locale_catalog:' + $languageCode) }
    foreach ($key in $reference.Keys) {
        if (@($catalog.Keys) -cnotcontains $key -or [string]::IsNullOrWhiteSpace($catalog[$key])) { throw ('invalid_locale_message:' + $languageCode + ':' + $key) }
        $expected = @([regex]::Matches($reference[$key], '\{([A-Za-z][A-Za-z0-9]*)\}') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
        $actual = @([regex]::Matches($catalog[$key], '\{([A-Za-z][A-Za-z0-9]*)\}') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
        if (($expected -join ',') -cne ($actual -join ',')) { throw ('locale_parameter_mismatch:' + $languageCode + ':' + $key) }
    }
}
function Set-InstallLanguage([string] $Code) {
    $normalized = if ([string]::IsNullOrWhiteSpace($Code)) { 'EN' } else { $Code.Trim().ToUpperInvariant() }
    if (-not $script:Languages.Contains($normalized)) { throw (T 'unsupported_language' @{ code=$Code; available=($script:Languages.Keys -join ', ') }) }
    $script:InstallLanguage = $normalized
}
function T([string] $Key, [hashtable] $Parameters = @{}) {
    $fullKey = if ($Key.Contains('.')) { $Key } else { 'installer.' + $Key }
    $catalog = $script:LocaleCatalogs[$script:InstallLanguage]
    $item = $catalog[$fullKey]
    if ($null -eq $item) { $item = $script:LocaleCatalogs.EN[$fullKey] }
    if ($null -eq $item) { return '[' + $fullKey + ']' }
    $required = @([regex]::Matches($item, '\{([A-Za-z][A-Za-z0-9]*)\}') | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique)
    foreach ($name in $required) { if (@($Parameters.Keys) -cnotcontains $name) { throw ('locale_parameter_missing:' + $fullKey + ':' + $name) } }
    foreach ($name in $Parameters.Keys) { if ($required -cnotcontains $name) { throw ('locale_parameter_extra:' + $fullKey + ':' + $name) } }
    return [regex]::Replace($item, '\{([A-Za-z][A-Za-z0-9]*)\}', [System.Text.RegularExpressions.MatchEvaluator]{ param($match) [string]$Parameters[$match.Groups[1].Value] })
}
function Select-InstallLanguage([bool] $NonInteractive, [string] $Requested = '') {
    if (-not [string]::IsNullOrWhiteSpace($Requested)) { Set-InstallLanguage $Requested; return }
    if ($NonInteractive) { Set-InstallLanguage 'EN'; return }
    Write-Host (T 'language') -ForegroundColor Cyan
    $count = 0
    foreach ($entry in $script:Languages.GetEnumerator()) {
        $count++
        Write-Host ('  ' + $count + ') ' + $entry.Key + ' — ' + $entry.Value + $(if ($entry.Key -eq 'EN') { ' [' + (T 'default_marker') + ']' } else { '' }))
    }
    $choice = (Read-Host (T 'language_prompt')).Trim().ToUpperInvariant()
    if ($choice -eq '') { Set-InstallLanguage 'EN'; return }
    $codes = @($script:Languages.Keys)
    $index = 0
    if ([int]::TryParse($choice,[ref]$index) -and $index -ge 1 -and $index -le $codes.Count) {
        Set-InstallLanguage $codes[$index-1]
    } elseif ($script:Languages.Contains($choice)) {
        Set-InstallLanguage $choice
    } else {
        Write-Host (T 'invalid_lang') -ForegroundColor Yellow
        Set-InstallLanguage 'EN'
    }
}
