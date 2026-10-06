# Data and texture attribution

This file records sources used to author the OMSI package. Update it whenever
new map data, reference imagery, or third-party texture material is added.

## OpenStreetMap

Map geometry and stop locations are imported from OpenStreetMap contributors.

- Website: <https://www.openstreetmap.org/>
- Licence: Open Database Licence (ODbL)
- Attribution: `© OpenStreetMap contributors`

The generated OSM source and import manifests are kept under `src\osm` and
`maps\HK_HP1C_*\osm_import.json`.

## Hong Kong Lands Department

Hong Kong orthophotos and map products may be used as authoring reference only
after checking the current terms for the selected dataset.

- Digital orthophoto information:
  <https://www.landsd.gov.hk/en/survey-mapping/mapping/aerial-photo-photogrammetric-products/digital-orthophoto.html>
- HK Map Service open-data information:
  <https://www.hkmapservice.gov.hk/OneStopSystem/faqDownloadOpenDigitalMaps>
- CSDI portal:
  <https://portal.csdi.gov.hk/csdi-webpage/>

When Lands Department data is used in an output, preserve the provider
attribution, copyright notice, logo requirements, and any dataset-specific
licence conditions. Do not assume that a web map tile may be redistributed
merely because it can be viewed or downloaded.

## Google imagery

Google Maps and Google Earth imagery is not included in this repository or in
release archives. Do not commit screenshots, downloaded tiles, or textures
derived from Google imagery unless the applicable licence explicitly permits
the intended use and redistribution.

## Project-authored textures

Textures created by this project should identify their source in the
corresponding asset notes and should not contain unlicensed logos, trademarks,
or copied imagery.
