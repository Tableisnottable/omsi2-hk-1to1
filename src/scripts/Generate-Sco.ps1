[CmdletBinding()]
param(
    [string]$ModelDirectory = (Join-Path $PSScriptRoot "..\..\Sceneryobjects\HK_Objects\model"),
    [string]$OutputDirectory = (Join-Path $PSScriptRoot "..\..\Sceneryobjects\HK_Objects")
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $ModelDirectory -PathType Container)) {
    throw "Model directory does not exist: $ModelDirectory"
}
New-Item -Path $OutputDirectory -ItemType Directory -Force | Out-Null

$models = @(Get-ChildItem -Path $ModelDirectory -Filter "*.o3d" -File)
foreach ($model in $models) {
    $sco = @(
        "[friendlyname]"
        $model.BaseName
        ""
        "[groups]"
        "2"
        "Hong Kong"
        "Buildings"
        ""
        "[mesh]"
        $model.Name
    ) -join [Environment]::NewLine
    Set-Content -Path (Join-Path $OutputDirectory "$($model.BaseName).sco") -Value $sco -Encoding utf8
}
Write-Host "Generated $($models.Count) scenery object definition(s)."