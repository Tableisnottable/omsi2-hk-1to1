# Hong Kong 1:1 OpenOMSI Map

## Project process

This project is developed as a Hong Kong 1:1 OpenOMSI map in progressive
stages:

1. **Collect** Hong Kong road, building, bus-stop and public-transport data
   from permitted open-data sources.
2. **Organise** the territory into 19 HP1C map areas while keeping the
   regional structure stable for OpenOMSI installation.
3. **Build** the combined map package with roads, stops, building footprints,
   scenery folders, vehicle data and route information.
4. **Publish** one downloadable installation ZIP containing all 19 map areas.
5. **Preview** the imported data through the project website and interactive
   browser map.
6. **Verify** map files, route files and package structure before each release.
7. **Improve** the project with authored terrain, road splines, scenery,
   collisions, textures, timetables and higher-detail buildings.

The current release is a data-driven development scaffold. It is not yet a
finished Assetto Corsa-quality map: the high-detail scenery, complete
drivable spline network, full timetable system and final vehicle assets are
still being developed.

## Download process

The complete map is distributed as **one ZIP**, not 19 separate downloads:

`release\omsi2-hk-1to1-openomsi.zip`

The ZIP contains:

- all 19 `maps\HP1C_*` areas;
- `Sceneryobjects` for Hong Kong scenery;
- `Vehicles` and the current Hong Kong route HOF;
- the package structure required for OpenOMSI installation.

## Installation process

1. Download the single combined ZIP.
2. Extract it into the OpenOMSI or OMSI 2 game directory.
3. Allow the `maps`, `Sceneryobjects` and `Vehicles` folders to merge.
4. Start OpenOMSI.
5. Select one of the installed HP1C Hong Kong map areas.
6. Check the road layout, bus stops, buildings and route display.

The package is an installation release, not a copy of the development
repository. Source data, development tools, API keys and the game executable
are not included.

## Website and map preview process

The project website is the main user-facing preview:

- project overview and release information;
- one-click access to the complete map ZIP;
- interactive road, bus-stop and building map;
- HP1C area selection;
- public, NR and other service route search;
- HOF download and preview;
- current validation and development status;
- GitHub issue reporting.

The browser map is a data preview similar in purpose to a community map
viewer. It shows the imported road data and does not replace the OpenOMSI
game engine.

## Route and HOF process

Route information is maintained in separate catalogue groups:

- franchised public bus routes;
- NR Residents' Service routes;
- approved contract-hire and regular hotel services.

The current HOF is a basic shared route file for development and package
testing. The route catalogue is broader than the current HOF and will be
converted progressively into complete line, destination, stop, timetable and
AI traffic data.

## Verification process

Every release is checked for:

- all 19 HP1C map directories;
- required map files and imported data;
- public, NR and other-service route catalogues;
- HOF presence;
- OpenOMSI package folders;
- successful creation of the single combined ZIP;
- website, map-data and download links.

The repository status page distinguishes between data/package checks that are
complete and game-driving checks that require OpenOMSI installed on a local
computer.

## Data and attribution process

OpenStreetMap and Hong Kong official data are used according to their current
licences and attribution requirements. Google Maps and Google Earth imagery
are not packaged as OMSI assets. Official 3D reference data is used only
where its access terms and redistribution rights permit it.

See `ATTRIBUTION.md` for source credits and `QUALITY_TARGET.md` for the
planned high-fidelity asset stages.

## Reporting process

When an error is found, report:

1. the HP1C area or route name;
2. what was expected;
3. what happened;
4. a screenshot or relevant log, if available.

Issues can be reported through the repository's GitHub Issues page.
