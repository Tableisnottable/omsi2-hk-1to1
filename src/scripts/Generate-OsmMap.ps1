[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OsmPath,
    [ValidatePattern("^[A-Z0-9]{2,8}$")]
    [string]$MapCode = "CW",
    [string]$OutputRoot = (Join-Path $PSScriptRoot "..\.."),
    [switch]$Download
)

$ErrorActionPreference = "Stop"
$source = $OsmPath

if ($Download) {
    $uri = [Uri]$OsmPath
    $downloadPath = Join-Path ([System.IO.Path]::GetTempPath()) ("omsi-osm-" + [Guid]::NewGuid().ToString("N") + ".osm")
    Invoke-WebRequest -Uri $uri -OutFile $downloadPath
    $OsmPath = $downloadPath
}

if (-not (Test-Path $OsmPath -PathType Leaf)) {
    throw "OSM input file does not exist: $OsmPath"
}

$root = (Resolve-Path $OutputRoot).Path
$mapDirectory = Join-Path $root "maps\HP1C_$MapCode"
New-Item -Path $mapDirectory -ItemType Directory -Force | Out-Null

$osm = New-Object System.Xml.XmlDocument
$osm.Load((Resolve-Path $OsmPath).Path)
$nodeById = @{}
$nodeRows = [System.Collections.Generic.List[object]]::new()
$stopRows = [System.Collections.Generic.List[object]]::new()

function Get-OsmTag {
    param([System.Xml.XmlElement]$Element, [string]$Key)
    $tag = $Element.SelectSingleNode("./tag[@k='$Key']")
    if ($null -eq $tag) { return $null }
    return [string]$tag.v
}

foreach ($node in $osm.osm.node) {
    $id = [string]$node.id
    $lat = [double]::Parse([string]$node.lat, [Globalization.CultureInfo]::InvariantCulture)
    $lon = [double]::Parse([string]$node.lon, [Globalization.CultureInfo]::InvariantCulture)
    $nodeById[$id] = [pscustomobject]@{ Id = $id; Latitude = $lat; Longitude = $lon }
    $nodeRows.Add([pscustomobject]@{
        id = $id
        latitude = $lat
        longitude = $lon
        name = (Get-OsmTag $node "name")
    })

    $isStop = (Get-OsmTag $node "highway") -eq "bus_stop" -or
        (Get-OsmTag $node "public_transport") -in @("platform", "stop_position")
    if ($isStop) {
        $stopRows.Add([pscustomobject]@{
            id = $id
            name = (Get-OsmTag $node "name")
            latitude = $lat
            longitude = $lon
        })
    }
}

$wayRows = [System.Collections.Generic.List[object]]::new()
foreach ($way in $osm.osm.way) {
    $highway = Get-OsmTag $way "highway"
    if ([string]::IsNullOrWhiteSpace($highway)) { continue }
    $refs = @($way.nd | ForEach-Object { [string]$_.ref })
    $coordinates = @($refs | ForEach-Object {
        if ($nodeById.ContainsKey($_)) {
            $point = $nodeById[$_]
            "$($point.Longitude.ToString('R',[Globalization.CultureInfo]::InvariantCulture)),$($point.Latitude.ToString('R',[Globalization.CultureInfo]::InvariantCulture))"
        }
    })
    if ($coordinates.Count -lt 2) { continue }
    $wayRows.Add([pscustomobject]@{
        id = [string]$way.id
        highway = $highway
        name = (Get-OsmTag $way "name")
        oneway = (Get-OsmTag $way "oneway")
        nodes = ($refs -join " ")
        coordinates = ($coordinates -join " ")
    })
}

@(
    "[name]"
    "HP1C $MapCode"
    ""
    "[friendlyname]"
    "HK 1:1 Map ($MapCode) - OSM import"
) -join [Environment]::NewLine | Set-Content (Join-Path $mapDirectory "global.cfg") -Encoding utf8

if (-not (Test-Path (Join-Path $mapDirectory "tile_0_0.map"))) {
    @("[map]", "0", "0", "", "[terrain]", "0", "0", "0") -join [Environment]::NewLine |
        Set-Content (Join-Path $mapDirectory "tile_0_0.map") -Encoding utf8
}
if (-not (Test-Path (Join-Path $mapDirectory "drivers.txt"))) {
    "DefaultDriver" | Set-Content (Join-Path $mapDirectory "drivers.txt") -Encoding utf8
}
if (-not (Test-Path (Join-Path $mapDirectory "ailists.cfg"))) {
    @("[sorts]", "1", "0", "", "[ailist]", "0", "-1") -join [Environment]::NewLine |
        Set-Content (Join-Path $mapDirectory "ailists.cfg") -Encoding utf8
}

$nodeRows | Export-Csv (Join-Path $mapDirectory "osm_nodes.csv") -NoTypeInformation -Encoding utf8
$wayRows | Export-Csv (Join-Path $mapDirectory "osm_ways.csv") -NoTypeInformation -Encoding utf8
$stopRows | Export-Csv (Join-Path $mapDirectory "osm_stops.csv") -NoTypeInformation -Encoding utf8

$manifest = [ordered]@{
    source = $source
    importedUtc = [DateTime]::UtcNow.ToString("o")
    mapCode = $MapCode
    nodes = $nodeRows.Count
    highwayWays = $wayRows.Count
    stops = $stopRows.Count
    nextStep = "Convert osm_ways.csv and osm_stops.csv into OMSI spline and scenery files."
}
$manifest | ConvertTo-Json | Set-Content (Join-Path $mapDirectory "osm_import.json") -Encoding utf8

Write-Host "Imported OSM data into $mapDirectory"
Write-Host "Nodes: $($nodeRows.Count); highway ways: $($wayRows.Count); stops: $($stopRows.Count)"
