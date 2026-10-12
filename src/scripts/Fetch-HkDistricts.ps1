# Fetch a Hong Kong 1:1 OSM extract per HP1C district into src\osm\<code>.osm
#
# Each district map is a single OMSI map tile (300 m x 300 m) centred on the
# district's HP1C sheet centre (Lands Department 1:1000 sheet grid).  We ask
# Overpass for a bbox around that centre, sized so the whole district fits in
# the tile with a margin; the actual clipping happens in Convert-OsmToMap.ps1.
[CmdletBinding()]
param(
    [string]$Overpass = "https://overpass-api.de/api/interpreter",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$osmDir = Join-Path $root "src\osm"
New-Item -Path $osmDir -ItemType Directory -Force | Out-Null

# HP1C sheet centres (WGS84).  These are the sheet centres of the Lands
# Department 1:1000 maps that HP1C codes are derived from, chosen so that the
# 300 m OMSI tile covers the built-up core of each district.  Coordinates are
# approximate to ~100 m; the importer clips to the exact tile bbox.
$centres = @{
    CW   = @{ lat = 22.2825; lon = 114.1580 }   # Central / Western
    WCH  = @{ lat = 22.2810; lon = 114.1890 }   # Wan Chai
    EAS  = @{ lat = 22.2790; lon = 114.2260 }   # Eastern
    SOU  = @{ lat = 22.2470; lon = 114.1580 }   # Southern
    YTM  = @{ lat = 22.3040; lon = 114.1700 }   # Yau Tsim Mong
    SSP  = @{ lat = 22.3300; lon = 114.1620 }   # Sham Shui Po
    KCT  = @{ lat = 22.3370; lon = 114.1760 }   # Kowloon City
    WTS  = @{ lat = 22.3260; lon = 114.1990 }   # Wong Tai Sin
    KTN  = @{ lat = 22.3150; lon = 114.2220 }   # Kwun Tong
    KWT  = @{ lat = 22.3540; lon = 114.1250 }   # Kwai Tsing
    TWW  = @{ lat = 22.3700; lon = 114.1120 }   # Tsuen Wan
    TMM  = @{ lat = 22.3860; lon = 114.2040 }   # Tuen Mun
    YLN  = @{ lat = 22.4440; lon = 114.0220 }   # Yuen Long
    NTH  = @{ lat = 22.5000; lon = 114.1350 }   # North
    TPO  = @{ lat = 22.4520; lon = 114.1670 }   # Tai Po
    STN  = @{ lat = 22.3820; lon = 114.1920 }   # Sha Tin
    SKG  = @{ lat = 22.3260; lon = 114.2630 }   # Sai Kung
    ISL  = @{ lat = 22.2580; lon = 114.2500 }   # Islands
    HZMB = @{ lat = 22.2770; lon = 113.7600 }   # Hong Kong-Zhuhai-Macao Bridge
}

# bbox half-size in degrees.  A 300 m tile is ~0.0027 deg; use a margin so
# buildings that straddle the tile edge are fully captured and we can clip.
$half = 0.006

$failed = @()
foreach ($code in ($centres.Keys | Sort-Object)) {
    $c = $centres[$code]
    $out = Join-Path $osmDir "$code.osm"
    if ((Test-Path $out) -and -not $Force) {
        Write-Host "$code : already present, skipping (-Force to re-fetch)" -ForegroundColor DarkGray
        continue
    }
    $south = $c.lat - $half
    $north = $c.lat + $half
    $west  = $c.lon - $half
    $east  = $c.lon + $half
    $query = @"
[out:xml][timeout:120];
(
  node($south,$west,$north,$east);
  way($south,$west,$north,$east);
  relation($south,$west,$north,$east);
);
out body;
"@
    Write-Host "Fetching $code ($($c.lat), $($c.lon)) ..." -ForegroundColor Cyan
    try {
        $body = @{ data = $query }
        $resp = Invoke-WebRequest -Uri $Overpass -Method Post -Body $body -UseBasicParsing -TimeoutSec 180
        [System.IO.File]::WriteAllBytes($out, $resp.Content)
        Write-Host "  wrote $out ($($resp.RawContentLength) bytes)" -ForegroundColor Green
        Start-Sleep -Seconds 2
    } catch {
        Write-Host "  FAILED: $_" -ForegroundColor Red
        $failed += $code
    }
}

if ($failed.Count -gt 0) {
    Write-Host "Failed districts: $($failed -join ', ')" -ForegroundColor Yellow
    exit 1
}
Write-Host "All districts fetched." -ForegroundColor Green
