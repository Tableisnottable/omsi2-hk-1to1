$RepoPath = "C:\Users\Table\Documents\GitHub\omsi2-hk-1to1"

if (-not (Test-Path $RepoPath)) { 
    New-Item -Path $RepoPath -ItemType Directory -Force | Out-Null 
}
Set-Location $RepoPath

$Dirs = @(
    "src\gis",
    "src\models",
    "src\scripts",
    "release",
    "Sceneryobjects\HK_Objects\model",
    "Sceneryobjects\HK_Objects\texture",
    "Vehicles\Annan_HK"
)

foreach ($d in$Dirs) { 
    New-Item -Path (Join-Path $RepoPath$d) -ItemType Directory -Force | Out-Null 
}

$Codes = @("CW","WCH","EAS","SOU","YTM","SSP","KCT","WTS","KTN","KWT","TWW","TMM","YLN","NTH","TPO","STN","SKG","ISL","HZMB")

foreach ($c in $Codes) {$mp = Join-Path $RepoPath "maps\HK_HP1C_$c"
    New-Item -Path "$mp\texture" -ItemType Directory -Force | Out-Null
    [System.IO.File]::WriteAllText("$mp\global.cfg", "[name]`r`nHK HP1C $c`r`n`r`n[friendlyname]`r`nHK 1:1 Map ($c)", [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText("$mp\tile_0_0.map", "[map]`r`n0`r`n0`r`n`r`n[terrain]`r`n0`r`n0`r`n0", [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText("$mp\drivers.txt", "DefaultDriver", [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText("$mp\parklist_p.txt", "", [System.Text.Encoding]::UTF8)
    [System.IO.File]::WriteAllText("$mp\ailists.cfg", "[sorts]`r`n1`r`n0`r`n`r`n[ailist]`r`n0`r`n-1", [System.Text.Encoding]::UTF8)
}

$GenSco = '$ModelDir = Join-Path $PSScriptRoot "..\..\Sceneryobjects\HK_Objects\model"; $ScoDir = Join-Path $PSScriptRoot "..\..\Sceneryobjects\HK_Objects"; Get-ChildItem -Path $ModelDir -Filter "*.o3d" | ForEach-Object { $Name = $_.BaseName; [System.IO.File]::WriteAllText((Join-Path $ScoDir "$Name.sco"), "[friendlyname]`r`n$Name`r`n`r`n[groups]`r`n2`r`nHong Kong`r`nBuildings`r`n`r`n[mesh]`r`n$($_.Name)", [System.Text.Encoding]::UTF8) }'
[System.IO.File]::WriteAllText("$RepoPath\src\scripts\Generate-Sco.ps1", $GenSco, [System.Text.Encoding]::UTF8)

$GenHof = '$HofPath = Join-Path $PSScriptRoot "..\..\Vehicles\Annan_HK\HK_Routes.hof"; [System.IO.File]::WriteAllText($HofPath, "[name]`r`nHK_Routes`r`n`r`n[servicetrip]`r`nOut of Service`r`n`r`n[line]`r`n101`r`n10100`r`n00`r`n`r`n[stop]`r`nCross Harbour Tunnel`r`n紅磡海底隧道`n10101", [System.Text.Encoding]::UTF8)'
[System.IO.File]::WriteAllText("$RepoPath\src\scripts\Generate-Hof.ps1", $GenHof, [System.Text.Encoding]::UTF8)

$BuildRel = '$Zip = Join-Path$PSScriptRoot "..\..\release\omsi2-hk-1to1-full.zip"; if (Test-Path $Zip) { Remove-Item$Zip -Force }; Compress-Archive -Path @((Join-Path $PSScriptRoot "..\..\maps"), (Join-Path $PSScriptRoot "..\..\Sceneryobjects"), (Join-Path $PSScriptRoot "..\..\Vehicles")) -DestinationPath $Zip'
[System.IO.File]::WriteAllText("$RepoPath\src\scripts\Build-Release.ps1", $BuildRel, [System.Text.Encoding]::UTF8)

$RunOmsi = '$Exe = "C:\Program Files (x86)\Steam\steamapps\common\OMSI 2\OpenOMSI.exe"; if (Test-Path $Exe) { Start-Process$Exe } else { Write-Host "OpenOMSI.exe not found" -ForegroundColor Red }'
[System.IO.File]::WriteAllText("$RepoPath\src\scripts\Run-OpenOmsi.ps1", $RunOmsi, [System.Text.Encoding]::UTF8)

[System.IO.File]::WriteAllText("$RepoPath\.gitignore", "*.bak`r`n*.tmp`r`n*.log`r`n*.fbx`r`n*.obj`r`nrelease/*.zip", [System.Text.Encoding]::UTF8)
[System.IO.File]::WriteAllText("$RepoPath\README.md", "# OMSI 2 - Hong Kong 1:1 Scale Map Project (HP1C Scheme)", [System.Text.Encoding]::UTF8)

Write-Host "Repository setup successfully completed!" -ForegroundColor Green