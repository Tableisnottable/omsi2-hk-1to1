[CmdletBinding()]
param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $scriptRoot "..\..\release\omsi2-hk-1to1-openomsi.zip"
}
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..\..")).Path
$output = if ([System.IO.Path]::IsPathRooted($OutputPath)) {
    [System.IO.Path]::GetFullPath($OutputPath)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $repoRoot $OutputPath))
}
$outputDirectory = Split-Path -Parent $output

New-Item -Path $outputDirectory -ItemType Directory -Force | Out-Null
if (Test-Path $output) {
    Remove-Item $output -Force
}

$content = @(
    (Join-Path $repoRoot "maps")
    (Join-Path $repoRoot "Sceneryobjects")
    (Join-Path $repoRoot "Vehicles")
)
$mapDirectories = @(Get-ChildItem -Path (Join-Path $repoRoot "maps") -Directory -Filter "HP1C_*")
if ($mapDirectories.Count -ne 19) {
    throw "Expected one combined package containing 19 HP1C maps; found $($mapDirectories.Count)."
}
Compress-Archive -Path $content -DestinationPath $output
Write-Host "Release written to $output (all $($mapDirectories.Count) HP1C maps included in one ZIP)"