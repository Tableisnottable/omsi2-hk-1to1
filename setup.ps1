[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path $PSScriptRoot).Path
)

$ErrorActionPreference = "Stop"

$requiredDirs = @(
    "src\\gis",
    "src\\models",
    "src\\scripts",
    "src\\extensions\\terrain",
    "src\\extensions\\splines",
    "src\\extensions\\scenery",
    "src\\extensions\\tiles",
    "src\\extensions\\ai-traffic",
    "src\\extensions\\bus-stops",
    "src\\extensions\\routes",
    "src\\extensions\\reference-data",
    "Sceneryobjects\\HK_Objects\\model",
    "Sceneryobjects\\HK_Objects\\texture",
    "Vehicles\\Annan_HK",
    "release"
)

foreach ($relativePath in $requiredDirs) {
    $target = Join-Path $RepositoryRoot $relativePath
    if (-not (Test-Path -LiteralPath $target)) {
        New-Item -Path $target -ItemType Directory -Force | Out-Null
    }
}

$validator = Join-Path $RepositoryRoot "src\\scripts\\Test-MapStructure.ps1"
if (-not (Test-Path -LiteralPath $validator)) {
    throw "Validation script not found: $validator"
}

& $validator -RepositoryRoot $RepositoryRoot
Write-Host "Setup complete for repository at: $RepositoryRoot" -ForegroundColor Green
