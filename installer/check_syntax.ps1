# Parse-only regression test. Compatible with Windows PowerShell 5.1 and PowerShell 7.
$ErrorActionPreference = 'Stop'
$files = Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.ps1' -File
$errorsFound = $false
foreach ($file in $files) {
    $tokens = $null
    $parseErrors = $null
    [void][System.Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count -gt 0) {
        Write-Host ('ERROR: ' + $file.Name) -ForegroundColor Red
        foreach ($e in $parseErrors) { Write-Host ($e.Extent.StartLineNumber.ToString() + ': ' + $e.Message) }
        $errorsFound = $true
    } else {
        Write-Host ('OK: ' + $file.Name) -ForegroundColor Green
    }
}
if ($errorsFound) { exit 1 }
Write-Host 'All installer scripts passed the PowerShell syntax check.' -ForegroundColor Green
