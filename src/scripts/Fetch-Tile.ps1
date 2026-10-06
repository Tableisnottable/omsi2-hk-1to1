param (
    [string]$SheetNo = "11-SE-1D"
)

$TargetUrl = "https://download.map.gov.hk/so/3d-zip/3D-BIT00_${SheetNo}_FBX.zip"
$OutPath   = Join-Path $PSScriptRoot "..\gis\3D-BIT00_${SheetNo}_FBX.zip"

Write-Host "Downloading 3D-BIT00 FBX tile: $SheetNo..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $TargetUrl -OutFile $OutPath
Expand-Archive -Path $OutPath -DestinationPath (Join-Path $PSScriptRoot "..\gis\${SheetNo}") -Force
Write-Host "Extracted 3D models to src/gis/${SheetNo}" -ForegroundColor Green