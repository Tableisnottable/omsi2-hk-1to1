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
- Selectable **248M_TEST** timetable, Tsing Yi Station ↔ Cheung Wang, two duties
  and 74 daily departures. It uses the 5 outbound and 4 inbound platforms recorded
  in OSM, native `.ttl`/`.ttp` files, seven station links and a `TsingYi_Test` HOF.
  Times and shortest-road tracks are provisional, not the published KMB timetable
  or a surveyed route. Junctions and passenger operation still need runtime checks.

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

The builder also generates the test timetable. To add or regenerate just the
small timetable files in an existing build, without rebuilding scenery or
starting the simulator:

```powershell
py src/scripts/Generate-TsingYi-Timetable.py
# Optional installation into an existing Tsing Yi map and installed bus folders:
py src/scripts/Generate-TsingYi-Timetable.py --install "A:\SteamLibrary\steamapps\common\OMSI 2" --hof-root "A:\openomsi"
```

The generator rejects disconnected stop chains. The offline validator checks
native path IDs, tile indices, stop IDs, profile times and overlapping duty trips.
This does not certify junction driving, bus compatibility or passenger behavior.

The ZIP, generated maps, downloaded inputs, meshes and textures stay local and
are excluded from Git. GitHub contains the small generator, validator, packager
and documentation. Existing tracked project assets are not removed from history.

## Install the local development package

### First manual test on this PC

For **OpenOMSI**, refresh the map list or reopen the launcher when you are ready.
Select **Tsing Yi 1:1 - development**, then **Timetable**, line **248M_TEST**, duty
**01**, departure **17:30**, **Tsing Yi Station → Cheung Wang**. Select your installed
bus and depot/HOF **TsingYi_Test**. The timetable runs on all days, including the
year 2000. A game launch is not required for file installation.

Station departures run every 30 minutes from 05:30 to 23:30. Return departures
run 05:55–23:55. Outbound running time is 20 minutes; inbound is 25 minutes, with
5 minutes at Cheung Wang and 10 minutes at Tsing Yi Station between trips.
These are development estimates. The inbound shortest-road route is about
4.05 km and the outbound about 2.73 km; exact KMB road routing is not certified.
At Tsing Yi Station, arrival and departure use different platform objects.

HOF route codes are **24801** outbound and **24802** inbound. Matrix and IBIS
setup varies by bus. On this PC the project HOF was added beside real installed
bus definitions and to the shared OpenOMSI HOF folder. Existing bus models and
other HOF files were preserved.

### Optional stock OMSI startup

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
and check road contact, visible terrain and building placement. The 248M test
service uses a small stock MAN AI depot; passenger operation and junctions are
unverified. The stock MAN is a compatibility test vehicle,
not a Hong Kong bus model. Close other demanding games before your own test.

If there is a blank screen, error dialog or startup stall, stop the test and
report the error plus `work/omsi-user-test/logfile.txt`. Do not reinstall the
whole simulator or replace its existing vehicle library for this test.

### Standard installation

1. Extract `OMSI2-TsingYi-development.zip` into the OMSI 2 installation folder,
   merging `maps`, `Splines` and `Sceneryobjects`.
2. In the OMSI editor or map selector, choose **Tsing Yi 1:1 - development**.
3. Start with **Tsing Yi Station** and use your own installed bus.

The optional timetable AI depot references the stock MAN NL202 EN92. You can
select your own installed bus to drive. The ZIP includes the project HOF in
`HOFs` and `Vehicles/MAN_NL_NG`; for another bus in native OMSI, copy
`maps/HK_TsingYi/TsingYi_Test.hof` beside its `.bus` file. No bus model or
third-party OMSI asset is redistributed.

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
- Verify the provisional 248M road paths, platform approach directions, passenger
  exchange, terminal movements, HOF compatibility and running times in-engine.
  Author 249M and further services after their road connections are verified.
- Test stock OMSI 2 loading and memory use, then profile frame time and add LOD.

`route_references.json` remains an OSM reference dataset. The separate
`timetable_manifest.json` records the provisional 248M schedule and road tracks;
249M is still a reference only. Neither dataset certifies runtime operation.

## Sources and attribution

- © OpenStreetMap contributors, ODbL: <https://www.openstreetmap.org/copyright>
- Hong Kong OSM extract: <https://download.geofabrik.de/asia/china/hong-kong.html>
- Elevation: AWS Skadi / Tilezen terrain tiles,
  <https://registry.opendata.aws/terrain-tiles/> and
  <https://github.com/tilezen/joerd/blob/master/docs/attribution.md>.
  This is a composite elevation dataset, not an official Hong Kong road survey.
- All packaged facade, ground and road textures are generated by this project.

See `ATTRIBUTION.md` for the wider project's sources and terms.
