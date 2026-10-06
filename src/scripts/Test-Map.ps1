[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Join-Path $PSScriptRoot "..\..")
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path $RepositoryRoot).Path
$mapRoot = Join-Path $root "maps"
$requiredDirectories = @("maps", "Sceneryobjects", "Vehicles")
$errors = [System.Collections.Generic.List[string]]::new()

foreach ($directory in $requiredDirectories) {
    if (-not (Test-Path (Join-Path $root $directory) -PathType Container)) {
        $errors.Add("Missing required directory: $directory")
    }
}

$maps = @(Get-ChildItem $mapRoot -Directory -Filter "HK_HP1C_*" -ErrorAction SilentlyContinue)
if ($maps.Count -ne 19) {
    $errors.Add("Expected 19 HP1C map directories, found $($maps.Count)")
}

foreach ($map in $maps) {
    foreach ($file in @("global.cfg", "tile_0_0.map", "drivers.txt", "ailists.cfg")) {
        if (-not (Test-Path (Join-Path $map.FullName $file) -PathType Leaf)) {
            $errors.Add("$($map.Name) is missing $file")
        }
    }
    $global = Get-Content (Join-Path $map.FullName "global.cfg") -Raw
    if ($global -notmatch "(?m)^\[name\]\s*$" -or $global -notmatch "(?m)^\[friendlyname\]\s*$") {
        $errors.Add("$($map.Name)\global.cfg is missing [name] or [friendlyname]")
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "Validated $($maps.Count) HP1C map directories and required package folders."
