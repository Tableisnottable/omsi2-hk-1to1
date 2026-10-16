[CmdletBinding()]
param(
    [string]$OmsiPath = ""
)

# Auto-detect: OpenOMSI first, then stock OMSI 2 (Steam / alternate libraries)
$candidates = @(
    "C:\Program Files (x86)\Steam\steamapps\common\OMSI 2\OpenOMSI.exe",
    "A:\SteamLibrary\steamapps\common\OMSI 2\OpenOMSI.exe",
    "C:\Program Files (x86)\Steam\steamapps\common\OMSI 2\Omsi.exe",
    "A:\SteamLibrary\steamapps\common\OMSI 2\Omsi.exe",
    "D:\SteamLibrary\steamapps\common\OMSI 2\Omsi.exe",
    "E:\SteamLibrary\steamapps\common\OMSI 2\Omsi.exe"
)
if ([string]::IsNullOrWhiteSpace($OmsiPath)) {
    $OmsiPath = $candidates | Where-Object { Test-Path $_ -PathType Leaf } | Select-Object -First 1
    if (-not $OmsiPath) {
        throw "No OMSI/OpenOMSI installation found. Pass -OmsiPath explicitly."
    }
}
if (-not (Test-Path $OmsiPath -PathType Leaf)) {
    throw "OMSI executable was not found at '$OmsiPath'. Pass -OmsiPath to use another installation."
}
Write-Host "Launching: $OmsiPath" -ForegroundColor Green
Start-Process -FilePath $OmsiPath -WorkingDirectory (Split-Path -Parent $OmsiPath)