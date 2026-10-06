[CmdletBinding()]
param(
    [string]$OutputRoot = (Join-Path $PSScriptRoot "..\.."),
    [int]$Port = 8080,
    [string]$ApiKey = $env:LANDSD_3D_API_KEY
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    throw "Set LANDSD_3D_API_KEY in the local environment before starting the preview."
}

$root = (Resolve-Path $OutputRoot).Path
$template = Join-Path $root "preview\cesium\index.html"
$runtime = Join-Path $root "preview\cesium\.runtime"
New-Item -Path $runtime -ItemType Directory -Force | Out-Null
$html = (Get-Content $template -Raw).Replace("__LANDSD_3D_API_KEY__", $ApiKey)
Set-Content (Join-Path $runtime "index.html") $html -Encoding utf8

Write-Host "Open http://localhost:$Port/ in a browser. Press Ctrl+C to stop."
Push-Location $runtime
try {
    python -m http.server $Port
} finally {
    Pop-Location
    Remove-Item $runtime -Recurse -Force -ErrorAction SilentlyContinue
}
