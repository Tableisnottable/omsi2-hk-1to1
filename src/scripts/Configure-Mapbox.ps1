param (
    [string]$Token = "YOUR_MAPBOX_TOKEN"
)

$OmsiDir = $null
$SearchPaths = @(
    "C:\Program Files (x86)\Steam\steamapps\common\OMSI 2",
    "D:\SteamLibrary\steamapps\common\OMSI 2",
    "E:\SteamLibrary\steamapps\common\OMSI 2",
    "D:\Program Files (x86)\Steam\steamapps\common\OMSI 2"
)

foreach ($p in $SearchPaths) {
    if (Test-Path "$p\Omsi.exe") {
        $OmsiDir = $p
        break
    }
}

if ($OmsiDir) {
    $Cfg = "$OmsiDir\options.cfg"
    if (-not (Test-Path $Cfg)) {
        New-Item -Path $Cfg -ItemType File -Force | Out-Null
    }
    
    $txt = [System.IO.File]::ReadAllText($Cfg)
    $AerialStr = "`r`n[aerial_imagery]`r`nhttp://api.mapbox.com/v4/mapbox.satellite/{z}/{x}/{y}.png?access_token=$Token`r`n"
    
    if ($txt -notmatch "\[aerial_imagery\]") {
        $txt += $AerialStr
    } else {
        $txt = $txt -replace "\[aerial_imagery\][\s\S]*?(?=\r?\n\[|$)", $AerialStr.Trim()
    }
    
    [System.IO.File]::WriteAllText($Cfg, $txt, [System.Text.Encoding]::UTF8)
    Write-Host "Successfully configured Mapbox in $Cfg" -ForegroundColor Green
} else {
    Write-Host "OMSI 2 directory not found!" -ForegroundColor Red
}
