[CmdletBinding()]
param(
    [string]$ModelDirectory = "",
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($ModelDirectory) -or [string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
    if ([string]::IsNullOrWhiteSpace($ModelDirectory)) {
        $ModelDirectory = Join-Path $scriptRoot "..\..\Sceneryobjects\HK_Objects\model"
    }
    if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
        $OutputDirectory = Join-Path $scriptRoot "..\..\Sceneryobjects\HK_Objects"
    }
}
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