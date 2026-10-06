[CmdletBinding()]
param(
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $scriptRoot "..\..\Vehicles\Annan_HK\HK_Routes.hof"
}
New-Item -Path (Split-Path -Parent $OutputPath) -ItemType Directory -Force | Out-Null
$hof = @(
    "[name]"
    "HK_Routes"
    ""
    "[servicetrip]"
    "Out of Service"
    ""
    "[line]"
    "101"
    "10100"
    "00"
    ""
    "[stop]"
    "Cross Harbour Tunnel"
    "Cross Harbour Tunnel"
    "10101"
) -join [Environment]::NewLine
Set-Content -Path $OutputPath -Value $hof -Encoding utf8
Write-Host "Route file written to $OutputPath"