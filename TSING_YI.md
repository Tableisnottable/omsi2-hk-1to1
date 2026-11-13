# Tsing Yi 1:1 / 青衣

Tsing Yi is the first focused area in the Hong Kong map project. `HK_TsingYi`
is a separate OMSI 2 development map. The old district maps and `HK_BigMap`
are preserved.

This build is a geographic and free-drive foundation, **not a completed playable
bus-service release**. Offline validation does not establish that OMSI can load
or drive it. Runtime loading, driving, passenger operation and performance have
not yet been verified.

## Included

- One continuous 300 m tile grid covering Tsing Yi, its hills and surrounding sea.
- Real OSM road alignments, lane counts and one-way information, with left-hand
  lane paths, native height profiles and links along each original OSM way.
- Skadi N22E114 terrain at 1 arcsecond sample spacing (roughly 30 m), resampled
  onto OMSI's 5 m terrain grid. Resampling does not create 5 m source accuracy.
- Road profiles smoothed from DEM samples and constrained to an engineered
  maximum 8.5% grade. Nearby ground is fitted to the carriageway. These are
  **not surveyed road elevations**.
- OSM coastline, a lowered seabed and simple water meshes.
- Generic building extrusions with project-authored facade textures and collision
  meshes. Footprints crossing tile boundaries are retained.
- Native bus-stop objects, original stop metadata and six road-based spawn
  points near Tsing Yi Station, Cheung On, Cheung Hong, Tsing Yi Estate, the south
  and west of the island. Spawn vehicle clearance still requires a driving check.
- Actual OSM 248M/249M route relation memberships as authoring references.

Counts and source checksums are recorded in the local map's `build_manifest.json`.

## Build locally

Use Python 3.11 or newer in a virtual environment:

```powershell
py -m venv work/venv
work/venv/Scripts/python -m pip install -r src/scripts/requirements-tsingyi.txt
work/venv/Scripts/python src/scripts/Fetch-TsingYi.py
work/venv/Scripts/python src/scripts/Build-TsingYi.py
work/venv/Scripts/python src/scripts/Validate-TsingYi.py
work/venv/Scripts/python src/scripts/Package-TsingYi.py --output release/tsingyi
```

Fetching uses the current Geofabrik Hong Kong extract and the AWS-hosted Skadi
HGT tile. The fetch manifest records URLs and SHA-256 digests. Later rebuilds
with newer source downloads can differ; retain the cached files to reproduce a
specific build. Building after download works offline.

The builder stages a complete result under `work/`. It replaces only
`maps/HK_TsingYi`, `Sceneryobjects/HK_TsingYi` and `Splines/HK_TsingYi`, preserving
the previous dedicated folders under `work/tsingyi-previous-*`.

The ZIP, generated maps, downloaded inputs, meshes and textures stay local and
are excluded from Git. GitHub contains the small generator, validator, packager
and documentation. Existing tracked project assets are not removed from history.

## Install the local development package

### First manual test on this PC

The map has not been verified in a loaded OMSI scene. A local isolated startup
reached 3D initialization; this does not certify the map or driving behavior.

When you are ready, with Steam open and OMSI closed, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File src/scripts/Start-TsingYi-Test.ps1
```

This creates `work/omsi-user-test`, copies the generated map and one stock MAN
bus family, and uses references to installed OMSI support content. It does not
move, remove or reconfigure the original vehicle library. Its own configuration
uses a 1280×720 window, a 30 FPS cap and a one-tile draw distance. It excludes
obsolete internet advertising manifests from its local texture folder. Initial
setup needs local disk space for the stock bus. No simulator files are published.

Choose **Tsing Yi 1:1 - development**, **load map without buses**, then add
**MAN / NL202 - EN92** at **Tsing Yi Station**. Start with a short, slow drive
and check road contact, visible terrain and building placement. Passenger routes
and AI traffic are not ready. The stock MAN is a compatibility test vehicle,
not a Hong Kong bus model. Close other demanding games before your own test.

If there is a blank screen, error dialog or startup stall, stop the test and
report the error plus `work/omsi-user-test/logfile.txt`. Do not reinstall the
whole simulator or replace its existing vehicle library for this test.

### Standard installation

1. Extract `OMSI2-TsingYi-development.zip` into the OMSI 2 installation folder,
   merging `maps`, `Splines` and `Sceneryobjects`.
2. In the OMSI editor or map selector, choose **Tsing Yi 1:1 - development**.
3. Start with **Tsing Yi Station** and use your own installed bus.

There is no bus model dependency, AI fleet or scheduled passenger service in
this package. No bus model or third-party OMSI asset is redistributed.

The package also provides an offline geographic HTML preview and an offline
validation report. The preview is not an OMSI screenshot or an engine test.

## Work still required before a playable service release

- Author junctions, lane transitions, signal controllers and pedestrian crossings.
- Replace estimated bridge heights with continuous surveyed deck/ramp profiles.
  Verify vertical clearance at every grade-separated crossing.
- Build tunnel portals, interiors and terrain cuts. Tagged tunnel roads are
  intentionally omitted and recorded in `authoring_issues.json`, so some
  connections remain incomplete.
- Check road width, curvature, collision, terrain cuts, barriers, footways and
  stopping bays in the editor and by driving a full-size bus.
- Author recognizable stations, estates and transport interchanges. Generic
  extrusions are not high-detail replicas; multipolygon buildings are not imported.
- Match verified stop positions and ordered route paths, then create HOF,
  `.ttp`, `.ttr`, `.ttl`, running times and AI duties for actual passenger services.
- Test stock OMSI 2 loading and memory use, then profile frame time and add LOD.

`route_references.json` is a reference dataset. It must not be presented as a
working 248M/249M timetable. Missing members are recorded explicitly.

## Sources and attribution

- © OpenStreetMap contributors, ODbL: <https://www.openstreetmap.org/copyright>
- Hong Kong OSM extract: <https://download.geofabrik.de/asia/china/hong-kong.html>
- Elevation: AWS Skadi / Tilezen terrain tiles,
  <https://registry.opendata.aws/terrain-tiles/> and
  <https://github.com/tilezen/joerd/blob/master/docs/attribution.md>.
  This is a composite elevation dataset, not an official Hong Kong road survey.
- All packaged facade, ground and road textures are generated by this project.

See `ATTRIBUTION.md` for the wider project's sources and terms.
