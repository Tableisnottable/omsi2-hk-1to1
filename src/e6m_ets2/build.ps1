param(
    [string]$Workspace = $env:E6M_WORKSPACE,
    [switch]$SkipMeshes,
    [switch]$Install
)
$ErrorActionPreference = 'Stop'
if (-not $Workspace) { $Workspace = Join-Path $PSScriptRoot '..\..\work\e6m_ets2' }
$Workspace = [System.IO.Path]::GetFullPath($Workspace)
$env:E6M_WORKSPACE = $Workspace
$toolsDir = Join-Path $Workspace 'work\tools\conversion\bin\win_x64\tools'
foreach ($required in @('work\vendor\Blender-O3D-IO-Public\o3d_io\o3dconvert.py',
                        'work\tools\conversion\bin\win_x64\tools\resconvert.exe',
                        'work\ets2_def\def\vehicle\truck\scania.streamline\data.sii',
                        'work\coach_dlc_extract\def\vehicle\bus\scania.touring_23\data.sii')) {
    if (-not (Test-Path -LiteralPath (Join-Path $Workspace $required))) {
        throw "Missing local dependency: $required. See README.md."
    }
}
if (-not $SkipMeshes) {
    python (Join-Path $PSScriptRoot 'build_e6m.py')
    if ($LASTEXITCODE -ne 0) { throw 'Mesh export failed' }
}
python (Join-Path $PSScriptRoot 'write_defs.py')
if ($LASTEXITCODE -ne 0) { throw 'Definition generation failed' }
python (Join-Path $PSScriptRoot 'write_bus_defs.py')
if ($LASTEXITCODE -ne 0) { throw 'Additional coach definitions failed' }
Push-Location -LiteralPath $toolsDir
try {
    & '.\resconvert.exe' -update -root e6m
    $conversionResult = $LASTEXITCODE
    Copy-Item -LiteralPath '.\mass_convert.log' -Destination (Join-Path $Workspace 'work\compile_final.log') -Force
    if ($conversionResult -ne 0) { throw 'SCS conversion failed; inspect work/compile_final.log' }
}
finally { Pop-Location }
python (Join-Path $PSScriptRoot 'package_e6m.py')
if ($LASTEXITCODE -ne 0) { throw 'Packaging failed' }
python (Join-Path $PSScriptRoot 'validate_e6m_defs.py')
if ($LASTEXITCODE -ne 0) { throw 'Package preflight failed; package has not been installed' }
if ($Install) {
    python (Join-Path $PSScriptRoot 'install_e6m.py')
    if ($LASTEXITCODE -ne 0) { throw 'Installation failed' }
}
