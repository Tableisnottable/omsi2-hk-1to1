[CmdletBinding()]
param(
    [string]$OutputZip = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "release\omsi2-hk-1to1-scaffold.zip")
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$validator = Join-Path $PSScriptRoot "Test-MapStructure.ps1"

if (-not (Test-Path -LiteralPath $validator)) {
    throw "Missing validation script: $validator"
}

& $validator

$outputDir = Split-Path -Path $OutputZip -Parent
if (-not (Test-Path -LiteralPath $outputDir)) {
    New-Item -Path $outputDir -ItemType Directory -Force | Out-Null
}
if (Test-Path -LiteralPath $OutputZip) {
    Remove-Item -LiteralPath $OutputZip -Force
}

$stagingRoot = Join-Path $repositoryRoot "release\_staging"
if (Test-Path -LiteralPath $stagingRoot) {
    Remove-Item -LiteralPath $stagingRoot -Recurse -Force
}
New-Item -Path $stagingRoot -ItemType Directory -Force | Out-Null

Copy-Item -LiteralPath (Join-Path $repositoryRoot "maps") -Destination (Join-Path $stagingRoot "maps") -Recurse -Force
Copy-Item -LiteralPath (Join-Path $repositoryRoot "src\\extensions") -Destination (Join-Path $stagingRoot "src\\extensions") -Recurse -Force
Copy-Item -LiteralPath (Join-Path $repositoryRoot "README.md") -Destination (Join-Path $stagingRoot "README.md") -Force

Compress-Archive -Path (Join-Path $stagingRoot "*") -DestinationPath $OutputZip -CompressionLevel Optimal
Remove-Item -LiteralPath $stagingRoot -Recurse -Force

Write-Host "Release package created: $OutputZip" -ForegroundColor Green
