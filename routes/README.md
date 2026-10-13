# Hong Kong bus routes

`hk_bus_routes.csv` is a normalized snapshot of the route catalogue from
[HK Bus Crawling](https://github.com/hkbus/hk-bus-crawling). It includes the
operators present in that source, including KMB, Citybus, NLB, MTR bus, and
other public-transport services.

`nr_routes.csv` is intentionally separate. It contains the approved
Residents' Service routes published by the Transport Department for Hong Kong
Island, Kowloon, and the New Territories. The importer reads the official
HTML route tables and records the source page for every row. The linked PDF
schedule remains the authoritative detailed timetable for each route.

HKeMobility's public route-search page is useful for manual verification, but
its `getrouteinfo7` backend is an interactive service and rejected direct bulk
requests during validation.

`other_routes.csv` records the Transport Department's approved contract-hire
services and regular hotel services. These listings are not fixed route
catalogues in the same sense as franchised buses; the linked official PDF
contains the detailed schedule and stops.

Regenerate the snapshots with:

```powershell
python .\src\scripts\Import-BusRoutes.py
```

The route data is time-sensitive; check `routes\sources.json` for the source
URL and generation timestamp.

`cancelled_routes.csv` lists 909 cancelled Hong Kong bus routes (Citybus,
NWFB, CMB, KMB, Long Win, NLB, KCR/MTR buses, cross-harbour, joint and
residents' services) with their cancellation dates and reasons, imported
from the Chinese Wikipedia list of cancelled bus routes. Regenerate with:

```powershell
python .\src\scripts\Import-CancelledRoutes.py
```

Every route CSV carries a `category` column (regular, cross-harbour,
airport/Lantau, overnight, border, express, recreational, school or
residents), assigned by `src\scripts\RouteCategories.py`. Recompute with:

```powershell
python .\src\scripts\Classify-BusRoutes.py
```

`category_summary.json` records the category counts per dataset.
