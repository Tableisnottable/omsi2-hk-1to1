[CmdletBinding()]
param(
    [string]$OutputPath = (Join-Path $PSScriptRoot "..\..\release\omsi2-hk-1to1-full.zip")
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
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
Compress-Archive -Path $content -DestinationPath $output
Write-Host "Release written to $output"