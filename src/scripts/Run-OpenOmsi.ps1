[CmdletBinding()]
param(
    [string]$OmsiPath = "",
    [string]$MapName = ""
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

# Stock OMSI 2 requires Steam DRM: launching Omsi.exe directly exits with
# code 53. Use the Steam URL protocol instead when running the stock game.
$isStock = (Split-Path -Leaf $OmsiPath) -eq "Omsi.exe"
if ($isStock) {
    $steamUrl = "steam://rungameid/252530"
    if (-not [string]::IsNullOrWhiteSpace($MapName)) {
        # Steam does not forward -map; launch via Steam then the map must be
        # selected in-game, or use OpenOMSI which accepts -map directly.
        Write-Host "Note: Steam launch cannot pass -map; select '$MapName' in the OMSI menu." -ForegroundColor Yellow
    }
    Write-Host "Launching via Steam: $steamUrl" -ForegroundColor Green
    Start-Process $steamUrl
} else {
    $args = @()
    if (-not [string]::IsNullOrWhiteSpace($MapName)) {
        $args += @("-map", $MapName)
    }
    Write-Host "Launching: $OmsiPath $($args -join ' ')" -ForegroundColor Green
    Start-Process -FilePath $OmsiPath -ArgumentList $args -WorkingDirectory (Split-Path -Parent $OmsiPath)
}