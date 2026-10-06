[CmdletBinding()]
param(
    [string]$OpenOmsiExePath,
    [string]$SimulatorRoot
)

$ErrorActionPreference = "Stop"

$candidates = @()
if ($OpenOmsiExePath) {
    $candidates += $OpenOmsiExePath
}
if ($SimulatorRoot) {
    $candidates += (Join-Path $SimulatorRoot "OpenOMSI.exe")
}
$candidates += "C:\\Program Files (x86)\\Steam\\steamapps\\common\\OMSI 2\\OpenOMSI.exe"

$exePath = $candidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $exePath) {
    throw "OpenOMSI.exe not found. Provide -OpenOmsiExePath or -SimulatorRoot with a valid OpenOMSI installation."
}

Start-Process -FilePath $exePath
Write-Host "Launched: $exePath" -ForegroundColor Green
