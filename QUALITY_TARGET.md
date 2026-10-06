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

The repository currently implements stage 1 and the route catalogue. The
Cesium preview supports stage 2 reference work. Stages 3-6 require authored
meshes, texture production, and OpenOMSI runtime profiling; they cannot be
replaced by a route CSV or a single API call.

## Quality gate

An HP1C area should not be called high fidelity until it has:

- terrain and road data covering the actual area rather than a copied
  placeholder snapshot;
- visible building and infrastructure meshes;
- authored materials with documented sources;
- collision and LOD data;
- validated bus stops and route paths;
- a measured OpenOMSI test run without unacceptable stutter or missing assets.

