# Prepare a local, separate OMSI test profile; run only when the user is ready.
# Existing OMSI files are read as input. Original vehicles/configuration are untouched.
[CmdletBinding()]
param(
    [string]$OmsiPath = 'A:\SteamLibrary\steamapps\common\OMSI 2',
    [string]$TestRoot = '',
    [switch]$PrepareOnly
)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$source = [IO.Path]::GetFullPath($OmsiPath)
if ([string]::IsNullOrWhiteSpace($TestRoot)) { $TestRoot = Join-Path $repo 'work\omsi-user-test' }
$target = [IO.Path]::GetFullPath($TestRoot)
$sourcePrefix = $source.TrimEnd([char]92) + [char]92
if ($target.TrimEnd([char]92) -eq $source.TrimEnd([char]92) -or $target.StartsWith($sourcePrefix,[StringComparison]::OrdinalIgnoreCase)) {
    throw 'The separate test profile must be outside the installed OMSI directory.'
}
if (-not (Test-Path -LiteralPath (Join-Path $source 'Omsi.exe'))) { throw "OMSI executable not found: $source" }
if (-not (Test-Path -LiteralPath (Join-Path $repo 'maps\HK_TsingYi\global.cfg'))) {
    throw 'Generate the local Tsing Yi map first with Build-TsingYi.py.'
}
if (Get-Process Omsi -ErrorAction SilentlyContinue) { throw 'Close OMSI before preparing this profile.' }
New-Item -ItemType Directory -Path $target -Force | Out-Null
$marker = Join-Path $target '.tsingyi-test-profile'
if (-not (Test-Path -LiteralPath $marker) -and (Get-ChildItem -LiteralPath $target -Force | Measure-Object).Count -gt 0) {
    throw "Refusing to modify an existing unrelated folder: $target"
}
[IO.File]::WriteAllText($marker,'Dedicated local Tsing Yi test profile',[Text.Encoding]::ASCII)
foreach ($file in Get-ChildItem -LiteralPath $source -File) {
    if ($file.Extension -eq '.dll' -or $file.Name -eq 'Omsi.exe') {
        Copy-Item -LiteralPath $file.FullName -Destination $target -Force
    }
}
# Junctions share read-only reference content without duplicating the whole game.
# Do not write through these reference directories from this script.
foreach ($name in @('Fonts','Humans','Money','TicketPacks','Weather','Languages','Inputs','Drivers','Scripts','Sounds','GUI','Trains','helper','template','program','option_presets')) {
    $from = Join-Path $source $name
    $to = Join-Path $target $name
    if ((Test-Path -LiteralPath $from) -and -not (Test-Path -LiteralPath $to)) {
        New-Item -ItemType Junction -Path $to -Target $from | Out-Null
    }
}
foreach ($name in @('maps','Splines','Sceneryobjects','Vehicles','Situations','Texture','cfg')) {
    New-Item -ItemType Directory -Path (Join-Path $target $name) -Force | Out-Null
}
foreach ($category in @('maps','Splines','Sceneryobjects')) {
    $from = Join-Path $repo "$category\HK_TsingYi"
    $to = Join-Path $target "$category\HK_TsingYi"
    # Copy contents into the dedicated destination; no folder nesting on reruns.
    New-Item -ItemType Directory -Path $to -Force | Out-Null
    Get-ChildItem -LiteralPath $from -Force | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $to -Recurse -Force }
}
foreach ($name in @('Generic','Buildings_MC')) {
    $from = Join-Path $source "Sceneryobjects\$name"
    $to = Join-Path $target "Sceneryobjects\$name"
    if ((Test-Path -LiteralPath $from) -and -not (Test-Path -LiteralPath $to)) {
        New-Item -ItemType Junction -Path $to -Target $from | Out-Null
    }
}
# Copy only one stock bus family, excluding unrelated HOF collections. Robocopy
# performs a copy only; it never deletes or moves source files.
$busSource = Join-Path $source 'Vehicles\MAN_NL_NG'
$busTarget = Join-Path $target 'Vehicles\MAN_NL_NG'
if (-not (Test-Path -LiteralPath (Join-Path $busSource 'MAN_EN92_main.bus'))) { throw 'Stock MAN NL202 bus is missing.' }
& robocopy.exe $busSource $busTarget /E /XF '*.hof' /R:0 /W:0 /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Bus copy failed (robocopy exit $LASTEXITCODE)" }
# Omit obsolete internet-advertising manifests, which can stall a clean launch.
Get-ChildItem -LiteralPath (Join-Path $source 'Texture') -File | Where-Object { $_.Extension -notin @('.itx','.ipr') } |
    ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $target 'Texture') -Force }
Copy-Item -LiteralPath (Join-Path $source 'envir.cfg') -Destination $target -Force
$options = [IO.File]::ReadAllText((Join-Path $source 'options.cfg'),[Text.Encoding]::GetEncoding(1252))
$options = [regex]::Replace($options,'(?m)(\[last_map\]\r?\n)[^\r\n]*', { param($m) $m.Groups[1].Value+'maps\HK_TsingYi\global.cfg' })
$options = [regex]::Replace($options,'(?m)(\[performance_tiledistmax\]\r?\n)[^\r\n]*', { param($m) $m.Groups[1].Value+'1' })
$options = [regex]::Replace($options,'(?m)(\[maxFPS\]\r?\n)[^\r\n]*', { param($m) $m.Groups[1].Value+'30' })
[IO.File]::WriteAllText((Join-Path $target 'options.cfg'),$options,[Text.Encoding]::GetEncoding(1252))
[IO.File]::WriteAllText((Join-Path $target 'cfg\omsi.cfg'),"[graphics]`r`n[adapter]`r`n0`r`n[fullscreen]`r`n0`r`n[resolution]`r`n1280`r`n720`r`n",[Text.Encoding]::ASCII)
[IO.File]::WriteAllText((Join-Path $target 'steam_appid.txt'),'252530',[Text.Encoding]::ASCII)
Write-Host "Separate profile: $target"
Write-Host 'Choose Tsing Yi 1:1 - development, load without buses, then add MAN NL202 - EN92 at Tsing Yi Station.'
if ($PrepareOnly) { return }
if (-not (Get-Process steam -ErrorAction SilentlyContinue)) { throw 'Open Steam first, then run this script again.' }
$env:SteamAppId='252530'
$env:SteamGameId='252530'
# Visible interactive launch is intentional: this script is the user's test entry.
# Choose the map in the menu; stock OMSI argument behavior varies by version.
Start-Process -FilePath (Join-Path $target 'Omsi.exe') -WorkingDirectory $target -WindowStyle Normal
