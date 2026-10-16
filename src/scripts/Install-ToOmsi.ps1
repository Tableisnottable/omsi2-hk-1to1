# Install the generated HK maps into an OMSI 2 / OpenOMSI installation.
#
# Copies maps\HP1C_*, Splines\HK_Roads and Sceneryobjects\HK_Objects into the
# game's content folders so the maps appear in the map selection screen.
[CmdletBinding()]
param(
    [string]$OmsiPath = "",
    [switch]$Remove
)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$candidates = @(
    "C:\Program Files (x86)\Steam\steamapps\common\OMSI 2",
    "A:\SteamLibrary\steamapps\common\OMSI 2",
    "D:\SteamLibrary\steamapps\common\OMSI 2",
    "E:\SteamLibrary\steamapps\common\OMSI 2"
)
if ([string]::IsNullOrWhiteSpace($OmsiPath)) {
    $OmsiPath = $candidates | Where-Object { Test-Path $_ -PathType Container } | Select-Object -First 1
    if (-not $OmsiPath) {
        throw "No OMSI 2 installation found. Pass -OmsiPath explicitly."
    }
}
if (-not (Test-Path $OmsiPath -PathType Container)) {
    throw "OMSI 2 folder not found at '$OmsiPath'."
}
Write-Host "OMSI 2 at: $OmsiPath" -ForegroundColor Cyan

$items = @(
    @{ src = "maps"; filter = "HP1C_*" },
    @{ src = "Splines"; filter = "HK_Roads" },
    @{ src = "Sceneryobjects"; filter = "HK_Objects" }
)

foreach ($item in $items) {
    $srcRoot = Join-Path $repo $item.src
    $dstRoot = Join-Path $OmsiPath $item.src
    if (-not (Test-Path $srcRoot)) { continue }
    New-Item -Path $dstRoot -ItemType Directory -Force | Out-Null
    $targets = Get-ChildItem -Path $srcRoot -Directory -Filter $item.filter
    foreach ($t in $targets) {
        $dst = Join-Path $dstRoot $t.Name
        if ($Remove) {
            if (Test-Path $dst) {
                Remove-Item $dst -Recurse -Force
                Write-Host "Removed $dst" -ForegroundColor Yellow
            }
        } else {
            Copy-Item $t.FullName -Destination $dstRoot -Recurse -Force
            Write-Host "Copied $($t.Name) -> $dst" -ForegroundColor Green
        }
    }
}

if (-not $Remove) {
    Write-Host ""
    Write-Host "Installed. Launch with: powershell.exe -File .\src\scripts\Run-OpenOmsi.ps1" -ForegroundColor Cyan
}
