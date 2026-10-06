[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SimulatorRoot,
    [switch]$IncludeAllMaps
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$validator = Join-Path $PSScriptRoot "Test-MapStructure.ps1"

if (-not (Test-Path -LiteralPath $validator)) {
    throw "Missing validation script: $validator"
}

& $validator

if (-not (Test-Path -LiteralPath $SimulatorRoot)) {
    throw "Simulator root does not exist: $SimulatorRoot"
}

$mapsDestination = Join-Path $SimulatorRoot "maps"
if (-not (Test-Path -LiteralPath $mapsDestination)) {
    New-Item -Path $mapsDestination -ItemType Directory -Force | Out-Null
}

$mapNames = @("HK_HP1C_DEV")
if ($IncludeAllMaps) {
    $mapNames = Get-ChildItem -LiteralPath (Join-Path $repositoryRoot "maps") -Directory | Select-Object -ExpandProperty Name
}

foreach ($mapName in $mapNames) {
    $source = Join-Path $repositoryRoot "maps\\$mapName"
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Source map not found: $source"
    }

    $destination = Join-Path $mapsDestination $mapName
    if (Test-Path -LiteralPath $destination) {
        Remove-Item -LiteralPath $destination -Recurse -Force
    }
    Copy-Item -LiteralPath $source -Destination $destination -Recurse -Force
    Write-Host "Installed map: $mapName"
}

Write-Host "Install complete. Launch OpenOMSI/OMSI and select map: HK 1:1 OpenOMSI Scaffold (DEV)." -ForegroundColor Green
