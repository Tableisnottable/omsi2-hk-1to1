# High-fidelity OpenOMSI target

The project targets a modern simulator presentation rather than an old
low-detail OMSI conversion. OpenOMSI's 64-bit address space removes the old
32-bit memory ceiling, but visual quality still comes from the authored
assets, materials, lighting, and level-of-detail strategy.

## Asset targets

- Use accurate road alignment and terrain height data for each HP1C area.
- Build hero buildings and transport interchanges as authored meshes, not only
  flat OSM footprints.
- Use physically based material sets where the runtime supports them:
  base colour, normal, roughness, metalness, and ambient occlusion.
- Keep separate high-detail, mid-detail, and distant representations so
  dense districts remain performant.
- Add collision geometry separately from render geometry.
- Prefer modular signage, street furniture, vegetation, and road markings so
  repeated assets can be instanced.
- Use the Lands Department 3D Tiles service as a live reference or licensed
  conversion input; do not assume that a web tileset is already an OMSI mesh.

## Generation stages

1. Import OSM roads, stops, and building footprints.
2. Import permitted terrain and 3D reference data without committing API keys.
3. Convert selected districts into authored OMSI scenery, splines, and
   collision assets.
4. Create PBR companion textures and LOD variants.
5. Validate geometry, materials, route stops, and tile boundaries.
6. Profile loading and frame time in OpenOMSI before expanding the detail area.

The repository currently implements stages 1-5 and the route catalogue.
Stage 2 terrain: every HP1C tile now carries real elevation from the ASTER
30 m DEM (fetched via OpenTopoData, no key) interpolated onto the 61x61
OMSI terrain grid; HZMB is the sea-level artificial island it is.
Stage 3 geometry: buildings are extruded from their real OSM footprint
polygons (ear-clipped roofs, wall quads) instead of bounding boxes, and
the converter preserves existing elevation terrain on re-runs.
Stage 4 materials: procedural facade textures (glass, residential,
retail, concrete) with UV mapping and per-type diffuse colours, plus
[LOD] 50 box variants for every building.
Stage 5 validation: Validate-Stage5.py checks the quality gate per area
(terrain, roads, meshes, materials, collision, LOD, stops, routes) and
all 19 HP1C areas pass.
Stage 6 requires an OpenOMSI runtime profiling run; it cannot be replaced
by a route CSV or a single API call.

## Quality gate

An HP1C area should not be called high fidelity until it has:

- terrain and road data covering the actual area rather than a copied
  placeholder snapshot;
- visible building and infrastructure meshes;
- authored materials with documented sources;
- collision and LOD data;
- validated bus stops and route paths;
- a measured OpenOMSI test run without unacceptable stutter or missing assets.

