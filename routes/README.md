# Hong Kong bus routes

`hk_bus_routes.csv` is a normalized snapshot of the route catalogue from
[HK Bus Crawling](https://github.com/hkbus/hk-bus-crawling). It includes the
operators present in that source, including KMB, Citybus, NLB, MTR bus, and
other public-transport services.

`nr_routes.csv` is intentionally separate. Hong Kong NR (Residents' Service)
routes are approved and published by the Transport Department through
non-franchised-bus approval information rather than the same complete route
API. HKeMobility's public route-search page is useful for manual verification,
but its `getrouteinfo7` backend is an interactive service and rejected direct
bulk requests during validation. The file is ready for NR records, and
`sources.json` records both the HKeMobility page and the official Transport
Department source boundary. No NR route is invented when an authoritative
machine-readable record is unavailable.

Regenerate the snapshots with:

```powershell
python .\src\scripts\Import-BusRoutes.py
```

The route data is time-sensitive; check `routes\sources.json` for the source
URL and generation timestamp.
