[CmdletBinding()]
param(
    [string]$RepositoryRoot = ""
)

$ErrorActionPreference = "Stop"
if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) "..\.."
}
$root = (Resolve-Path $RepositoryRoot).Path
$mapRoot = Join-Path $root "maps"
$routeRoot = Join-Path $root "routes"
$requiredDirectories = @("maps", "Sceneryobjects", "Vehicles")
$errors = [System.Collections.Generic.List[string]]::new()

foreach ($directory in $requiredDirectories) {
    if (-not (Test-Path (Join-Path $root $directory) -PathType Container)) {
        $errors.Add("Missing required directory: $directory")
    }
}

$maps = @(Get-ChildItem $mapRoot -Directory -Filter "HP1C_*" -ErrorAction SilentlyContinue)
if ($maps.Count -ne 19) {
    $errors.Add("Expected 19 HP1C map directories, found $($maps.Count)")
}

foreach ($map in $maps) {
    foreach ($file in @("global.cfg", "tile_0_0.map", "drivers.txt", "ailists.cfg")) {
        if (-not (Test-Path (Join-Path $map.FullName $file) -PathType Leaf)) {
            $errors.Add("$($map.Name) is missing $file")
        }
    }
    $global = Get-Content (Join-Path $map.FullName "global.cfg") -Raw
    if ($global -notmatch "(?m)^\[name\]\s*$" -or $global -notmatch "(?m)^\[friendlyname\]\s*$") {
        $errors.Add("$($map.Name)\global.cfg is missing [name] or [friendlyname]")
    }
    if ($global -notmatch "(?m)^HP1C\s+") {
        $errors.Add("$($map.Name)\global.cfg does not use HP1C naming")
    }
    foreach ($jsonFile in Get-ChildItem $map.FullName -Filter "*.json" -File) {
        try {
            Get-Content $jsonFile.FullName -Raw | ConvertFrom-Json | Out-Null
        } catch {
            $errors.Add("$($map.Name)\$($jsonFile.Name) is not valid JSON: $($_.Exception.Message)")
        }
    }
    foreach ($csvFile in Get-ChildItem $map.FullName -Filter "*.csv" -File) {
        if ((Get-Content $csvFile.FullName -TotalCount 1).Count -eq 0) {
            $errors.Add("$($map.Name)\$($csvFile.Name) is empty")
        }
    }
}

foreach ($requiredRouteFile in @("hk_bus_routes.csv", "nr_routes.csv", "other_routes.csv", "route_details.csv", "sources.json")) {
    if (-not (Test-Path (Join-Path $routeRoot $requiredRouteFile) -PathType Leaf)) {
        $errors.Add("Missing route file: routes\$requiredRouteFile")
    }
}
if (Test-Path (Join-Path $routeRoot "hk_bus_routes.csv") -PathType Leaf) {
    $routeRows = @(Import-Csv (Join-Path $routeRoot "hk_bus_routes.csv"))
    if ($routeRows.Count -lt 1) {
        $errors.Add("routes\hk_bus_routes.csv contains no route rows")
    }
}
if (Test-Path (Join-Path $routeRoot "nr_routes.csv") -PathType Leaf) {
    $nrHeaders = (Get-Content (Join-Path $routeRoot "nr_routes.csv") -TotalCount 1)
    if ($nrHeaders -notmatch "route_id" -or $nrHeaders -notmatch "region") {
        $errors.Add("routes\nr_routes.csv has an invalid header")
    }
    if (Test-Path (Join-Path $routeRoot "other_routes.csv") -PathType Leaf) {
        $otherRows = @(Import-Csv (Join-Path $routeRoot "other_routes.csv"))
        if ($otherRows.Count -lt 1) {
            $errors.Add("routes\other_routes.csv contains no approved non-franchised service rows")
        }
    }
}
if (Test-Path (Join-Path $routeRoot "sources.json") -PathType Leaf) {
    try {
        Get-Content (Join-Path $routeRoot "sources.json") -Raw | ConvertFrom-Json | Out-Null
    } catch {
        $errors.Add("routes\sources.json is not valid JSON: $($_.Exception.Message)")
    }
    if (Test-Path (Join-Path $routeRoot "route_details.csv") -PathType Leaf) {
        $detailRows = @(Import-Csv (Join-Path $routeRoot "route_details.csv"))
        $requiredDetailHeaders = @("route_id", "route_map", "timetable", "vehicle_type", "fare", "depot")
        foreach ($header in $requiredDetailHeaders) {
            if ($detailRows.Count -eq 0 -or -not ($detailRows[0].PSObject.Properties.Name -contains $header)) {
                $errors.Add("routes\route_details.csv is missing the $header column")
            }
        }
        if ($detailRows.Count -lt 1) {
            $errors.Add("routes\route_details.csv contains no route rows")
        }
    }
}

if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_ }
    exit 1
}

Write-Host "Validated $($maps.Count) HP1C map directories and required package folders."
