# Data and texture attribution

This file records sources used to author the OMSI package. Update it whenever
new map data, reference imagery, or third-party texture material is added.

## OpenStreetMap

Map geometry and stop locations are imported from OpenStreetMap contributors.

- Website: <https://www.openstreetmap.org/>
- Licence: Open Database Licence (ODbL)
- Attribution: `© OpenStreetMap contributors`

The generated OSM source and import manifests are kept under `src\osm` and
`maps\HP1C_*\osm_import.json`.

## Hong Kong Lands Department

Hong Kong orthophotos and map products may be used as authoring reference only
after checking the current terms for the selected dataset.

- Digital orthophoto information:
  <https://www.landsd.gov.hk/en/survey-mapping/mapping/aerial-photo-photogrammetric-products/digital-orthophoto.html>
- HK Map Service open-data information:
  <https://www.hkmapservice.gov.hk/OneStopSystem/faqDownloadOpenDigitalMaps>
- CSDI portal:
  <https://portal.csdi.gov.hk/csdi-webpage/>
- 3D Visualisation Map (individualised models):
  <https://portal.csdi.gov.hk/csdi-webpage/dataset/landsd_rcd_1671676915450_88604>
- 3D Visualisation Map (non-textured models):
  <https://portal.csdi.gov.hk/csdi-webpage/dataset/landsd_rcd_1742809441342_98380>
- 3D Spatial Data API:
  <https://portal.csdi.gov.hk/csdi-webpage/apidoc/3d-spatial-data-api>

When Lands Department data is used in an output, preserve the provider
attribution, copyright notice, logo requirements, and any dataset-specific
licence conditions. Do not assume that a web map tile may be redistributed
merely because it can be viewed or downloaded.

The Lands Department 3D Spatial Data API documents Cesium 3D Tiles in WGS84
and requires an API key obtained from the Lands Department. The published
dataset pages confirm territory-wide 3D building, infrastructure, terrain,
and (for the individualised model set) texture data. They do not by
themselves confirm that FBX, OBJ, IFC, OSGB, or indoor-network downloads are
available. Do not describe or build against those formats unless a separate
official dataset page and licence confirms them.

## Google imagery

Google Maps and Google Earth imagery is not included in this repository or in
release archives. Do not commit screenshots, downloaded tiles, or textures
derived from Google imagery unless the applicable licence explicitly permits
the intended use and redistribution.

Google Maps Platform can be used as a private, live authoring/reference
service only when an appropriately configured Google Cloud project, API key,
billing account, and attribution are provided. Its map tiles, Street View,
satellite imagery, and other rendered content must not be downloaded and
converted into OMSI scenery or texture assets under the standard Maps
Platform terms. The generator therefore does not depend on Google APIs and
does not store Google responses.

- Maps Platform: <https://mapsplatform.google.com/>
- Terms: <https://cloud.google.com/maps-platform/terms/>
- Map Tiles policies: <https://developers.google.com/maps/documentation/tile/policies>

## Project-authored textures

Textures created by this project should identify their source in the
corresponding asset notes and should not contain unlicensed logos, trademarks,
or copied imagery.
