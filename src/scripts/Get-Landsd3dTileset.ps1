[CmdletBinding()]
param(
    [string]$OutputRoot = "",
    [ValidateSet("building", "infrastructure", "terrain")]
    [string]$Dataset = "building",
    [string]$ApiKey = $env:LANDSD_3D_API_KEY
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
if ([string]::IsNullOrWhiteSpace($OutputRoot)) {
    $OutputRoot = Join-Path $scriptRoot "..\.."
}

if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    throw "Set LANDSD_3D_API_KEY in the local environment before requesting Lands Department 3D data."
}

$root = (Resolve-Path $OutputRoot).Path
$outputDirectory = Join-Path $root "src\landsd3d"
New-Item -Path $outputDirectory -ItemType Directory -Force | Out-Null
$outputPath = Join-Path $outputDirectory "$Dataset-tileset.json"
$uri = "https://data.map.gov.hk/api/3d-data/3dsd/WGS84/$Dataset/tileset.json?key=$([Uri]::EscapeDataString($ApiKey))"

try {
    $response = Invoke-WebRequest -Uri $uri -Headers @{ "User-Agent" = "omsi2-hk-1to1 LandsD 3D importer" } -TimeoutSec 120
    $response.Content | Set-Content -Path $outputPath -Encoding utf8
} catch {
    throw "Lands Department 3D API request failed for '$Dataset'. The key was not written to disk or output: $($_.Exception.Message)"
}

try {
    Get-Content $outputPath -Raw | ConvertFrom-Json | Out-Null
} catch {
    Remove-Item $outputPath -Force -ErrorAction SilentlyContinue
    throw "The Lands Department response for '$Dataset' was not valid JSON."
}

Write-Host "Saved Lands Department $Dataset tileset metadata to $outputPath"
Write-Host "The API key was read from the environment and was not saved."
