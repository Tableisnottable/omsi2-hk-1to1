[CmdletBinding()]
param(
    [string]$OutputPath = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "Vehicles\Annan_HK\HK_Routes.hof")
)

$ErrorActionPreference = "Stop"
$outputDir = Split-Path -Path $OutputPath -Parent
if (-not (Test-Path -LiteralPath $outputDir)) {
    New-Item -Path $outputDir -ItemType Directory -Force | Out-Null
}

$content = @(
    "[name]",
    "HK_Routes",
    "",
    "[servicetrip]",
    "Out of Service",
    "",
    "[line]",
    "101",
    "10100",
    "00",
    "",
    "[stop]",
    "Cross Harbour Tunnel",
    "Cross Harbour Tunnel",
    "10101"
) -join "`r`n"

Set-Content -LiteralPath $OutputPath -Value $content -Encoding UTF8
Write-Host "Generated: $OutputPath" -ForegroundColor Green
