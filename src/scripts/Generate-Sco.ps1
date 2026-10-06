[CmdletBinding()]
param(
    [string]$SceneryRoot = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path "Sceneryobjects\HK_Objects")
)

$ErrorActionPreference = "Stop"
$modelDir = Join-Path $SceneryRoot "model"
if (-not (Test-Path -LiteralPath $modelDir)) {
    throw "Model directory not found: $modelDir"
}

$o3dFiles = Get-ChildItem -LiteralPath $modelDir -Filter "*.o3d" -File
if ($o3dFiles.Count -eq 0) {
    throw "No .o3d files found in $modelDir"
}

foreach ($file in $o3dFiles) {
    $scoPath = Join-Path $SceneryRoot ("{0}.sco" -f $file.BaseName)
    $content = @(
        "[friendlyname]",
        $file.BaseName,
        "",
        "[groups]",
        "2",
        "Hong Kong",
        "Buildings",
        "",
        "[mesh]",
        $file.Name
    ) -join "`r`n"
    Set-Content -LiteralPath $scoPath -Value $content -Encoding UTF8
    Write-Host "Generated: $scoPath"
}
