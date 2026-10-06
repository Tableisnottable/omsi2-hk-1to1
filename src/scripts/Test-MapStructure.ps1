[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..") ).Path,
    [string]$ScaffoldMapName = "HK_HP1C_DEV"
)

$ErrorActionPreference = "Stop"

$requiredRootPaths = @(
    "maps",
    "src\\scripts",
    "src\\extensions\\terrain",
    "src\\extensions\\splines",
    "src\\extensions\\scenery",
    "src\\extensions\\tiles",
    "src\\extensions\\ai-traffic",
    "src\\extensions\\bus-stops",
    "src\\extensions\\routes",
    "src\\extensions\\reference-data"
)

$errors = New-Object System.Collections.Generic.List[string]
foreach ($relativePath in $requiredRootPaths) {
    $fullPath = Join-Path $RepositoryRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath)) {
        $errors.Add("Missing required path: $relativePath")
    }
}

$mapsRoot = Join-Path $RepositoryRoot "maps"
$mapDirs = @()
if (Test-Path -LiteralPath $mapsRoot) {
    $mapDirs = Get-ChildItem -LiteralPath $mapsRoot -Directory
}
if ($mapDirs.Count -eq 0) {
    $errors.Add("No map directories found under maps/.")
}

$requiredMapFiles = @("global.cfg", "tile_0_0.map", "ailists.cfg", "drivers.txt", "parklist_p.txt")
foreach ($mapDir in $mapDirs) {
    foreach ($fileName in $requiredMapFiles) {
        $candidate = Join-Path $mapDir.FullName $fileName
        if (-not (Test-Path -LiteralPath $candidate)) {
            $errors.Add("Map '$($mapDir.Name)' is missing required file '$fileName'.")
        }
    }

    $globalCfgPath = Join-Path $mapDir.FullName "global.cfg"
    if (Test-Path -LiteralPath $globalCfgPath) {
        $globalCfgText = Get-Content -LiteralPath $globalCfgPath -Raw
        if ($globalCfgText -notmatch "\[name\]") { $errors.Add("Map '$($mapDir.Name)' global.cfg is missing [name].") }
        if ($globalCfgText -notmatch "\[friendlyname\]") { $errors.Add("Map '$($mapDir.Name)' global.cfg is missing [friendlyname].") }
    }

    $tilePath = Join-Path $mapDir.FullName "tile_0_0.map"
    if (Test-Path -LiteralPath $tilePath) {
        $tileText = Get-Content -LiteralPath $tilePath -Raw
        if ($tileText -notmatch "\[map\]") { $errors.Add("Map '$($mapDir.Name)' tile_0_0.map is missing [map].") }
        if ($tileText -notmatch "\[terrain\]") { $errors.Add("Map '$($mapDir.Name)' tile_0_0.map is missing [terrain].") }
    }
}

$scaffoldPath = Join-Path $mapsRoot $ScaffoldMapName
if (-not (Test-Path -LiteralPath $scaffoldPath)) {
    $errors.Add("Expected scaffold map '$ScaffoldMapName' was not found under maps/.")
}

if ($errors.Count -gt 0) {
    Write-Error ("Map structure validation failed:`n - " + ($errors -join "`n - "))
    exit 1
}

Write-Host "Map structure validation passed for $($mapDirs.Count) map directories." -ForegroundColor Green
