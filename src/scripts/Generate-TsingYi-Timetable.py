#!/usr/bin/env python3
"""Generate provisional Tsing Yi bus timetables from existing native road paths.

Offline authoring only: no simulator launch. Routes fail closed if their stops
cannot be joined on the generated directed road graph. Times are test estimates.
"""
import argparse
import heapq
import json
import math
import re
import shutil
from collections import defaultdict
from pathlib import Path


def read(path):
    raw = path.read_bytes()
    return raw.decode('utf-16' if raw[:2] in (b'\xff\xfe', b'\xfe\xff') else 'ascii')


def write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(('\r\n'.join(map(str, lines)) + '\r\n').encode('ascii'))


def project(stop):
    return ((stop['lon'] - 114.074) * 111320 * math.cos(math.radians(22.3415)) + 300,
            (stop['lat'] - 22.315) * 110574 + 300)


def network(root):
    folder = root / 'maps/HK_TsingYi'
    cfg = read(folder / 'global.cfg')
    tiles = re.findall(r'\[map\]\s*\n(-?\d+)\s*\n(-?\d+)\s*\n([^\r\n]+)', cfg)
    lanes, adjacency, profiles = [], defaultdict(list), {}
    for ti, (tx, ty, name) in enumerate(tiles):
        data = read(folder / name).splitlines()
        for i, token in enumerate(data):
            if token != '[spline]':
                continue
            r = data[i + 1:i + 19]
            if float(r[10]) != 0:
                raise ValueError('This authoring tool requires straight generated splines')
            if r[1] not in profiles:
                sli = read(root / r[1].replace('\\', '/')).splitlines()
                profiles[r[1]] = [(pi, float(sli[j+2]), int(sli[j+5]))
                                  for pi, j in enumerate(k for k, t in enumerate(sli) if t == '[path]')]
            angle = math.radians(float(r[8])); length = float(r[9])
            dx, dy = math.sin(angle), math.cos(angle)
            a = (int(tx)*300 + float(r[5]), int(ty)*300 + float(r[7]), float(r[6]))
            b = (a[0] + dx*length, a[1] + dy*length, a[2] + length*float(r[11])/100)
            for direction in (0, 1):
                options = [(pi, lat) for pi, lat, d in profiles[r[1]] if d in (direction, 2)]
                if not options:
                    continue
                # Kerb-side lane for left-hand traffic, respecting native path order.
                pi, lat = (min if direction == 0 else max)(options, key=lambda p: p[1])
                start, end = (a, b) if direction == 0 else (b, a)
                key = lambda p: tuple(round(v, 2) for v in p)
                lane = dict(id=int(r[2]), path=pi, tile=ti, length=length,
                            a=start, b=end, offset=lat, direction=direction,
                            start=key(start), end=key(end), heading=float(r[8]))
                adjacency[lane['start']].append(len(lanes)); lanes.append(lane)
    return lanes, adjacency


def candidates(stop, lanes):
    x, y = project(stop); result = []
    for i, lane in enumerate(lanes):
        a, b = lane['a'], lane['b']; length = lane['length']
        dx, dy = (b[0]-a[0])/length, (b[1]-a[1])/length
        along = max(0., min(length, (x-a[0])*dx + (y-a[1])*dy))
        # Right positive, measured in the direction of travel.
        lateral = (x-a[0])*dy - (y-a[1])*dx
        offset = lane['offset'] * (1 if lane['direction'] == 0 else -1)
        distance = math.hypot(x-a[0]-along*dx-offset*dy, y-a[1]-along*dy+offset*dx)
        if distance <= 65:
            # Prefer the platform on the left of the traffic lane.
            score = distance + (30 if lateral-offset > 1 else 0)
            result.append((score, i, along, lateral-offset))
    return sorted(result)[:8]


def shortest(start, end, lanes, adjacency):
    """Return lane indices, using only shared road endpoints at matching heights."""
    _, ai, sa, _ = start; _, bi, sb, _ = end
    if ai == bi and sb > sa:
        return sb-sa, [ai]
    a, b = lanes[ai], lanes[bi]
    queue = [(a['length']-sa, a['end'])]; best = {a['end']: a['length']-sa}; prev = {}
    while queue:
        cost, node = heapq.heappop(queue)
        if cost != best[node]:
            continue
        if node == b['start']:
            route = [bi]
            while node != a['end']:
                old, li = prev[node]; route.append(li); node = old
            return cost+sb, [ai] + list(reversed(route))
        for li in adjacency.get(node, ()):
            lane = lanes[li]; new = cost + lane['length']
            if new < best.get(lane['end'], math.inf):
                best[lane['end']] = new; prev[lane['end']] = node, li
                heapq.heappush(queue, (new, lane['end']))
    return None


def plan(stops, lanes, adjacency):
    # Select one consistent lane per stop for both incoming and outgoing links.
    choices = [candidates(s, lanes) for s in stops]
    if any(not c for c in choices):
        raise ValueError('A platform has no road lane within 65 metres')
    costs = [c[0]*6 for c in choices[0]]; histories = [[] for _ in costs]
    for index in range(1, len(stops)):
        next_costs, next_histories = [], []
        for b in choices[index]:
            best = (math.inf, None)
            for k, a in enumerate(choices[index-1]):
                if math.isinf(costs[k]):
                    continue
                route = shortest(a, b, lanes, adjacency)
                if route is None:
                    continue
                distance, steps = route
                score = costs[k] + distance + b[0]*6
                if score < best[0]:
                    best = score, histories[k] + [(a, b, distance, steps)]
            next_costs.append(best[0]); next_histories.append(best[1])
        if all(math.isinf(c) for c in next_costs):
            raise ValueError(f"No directed road connection: {stops[index-1]['name']} -> {stops[index]['name']}")
        costs, histories = next_costs, next_histories
    return histories[min(range(len(costs)), key=costs.__getitem__)]


def generate(root, check_only=False):
    folder = root/'maps/HK_TsingYi'
    lanes, adjacency = network(root)
    stops = {s['object_id']: s for s in json.loads((folder/'bus_stops.json').read_text(encoding='utf-8'))}
    routes = json.loads((folder/'route_references.json').read_text(encoding='utf-8'))
    plans = []
    for relation_id, name, duration, destination in (
            (11791063, '248M_Station_CheungWang_TEST', 20, 'Cheung Wang Bus Terminus'),
            (6461179, '248M_CheungWang_Station_TEST', 25, 'Tsing Yi Station Bus Terminus')):
        relation = next(r for r in routes if r['osm_relation'] == relation_id)
        ordered = [stops[m['map_object']] for m in relation['stop_members']]
        legs = plan(ordered, lanes, adjacency)
        plans.append(dict(name=name, relation=relation_id, duration=duration,
                          destination=destination, stops=ordered, legs=legs))
    summary = {'line': '248M_TEST', 'daily': True, 'days_mask': 1023,
               'headway_minutes': 30, 'station_departures': '05:30-23:30',
               'cheung_wang_departures': '05:55-23:55', 'tours': 2,
               'provisional_times': True, 'runtime_tested': False, 'trips': []}
    for p in plans:
        summary['trips'].append(dict(name=p['name'], osm_relation=p['relation'],
            stop_ids=[s['object_id'] for s in p['stops']],
            stop_names=[s['name'] for s in p['stops']], duration_minutes=p['duration'],
            metres=round(sum(l[2] for l in p['legs'])),
            road_path_entries=sum(len(l[3]) for l in p['legs']),
            legs=[dict(from_id=a['object_id'], to_id=b['object_id'], metres=round(l[2]),
                       path_entries=len(l[3])) for a,b,l in zip(p['stops'],p['stops'][1:],p['legs'])]))
    if check_only:
        return summary
    links = ['Time Table StnLinkList File', 'Generated Tsing Yi TEST paths; no runtime certification.', '']
    for p in plans:
        trip = ['Time Table Trip File', 'Provisional test service, not the published KMB schedule.',
                '', '[trip]', '', p['destination'], '248M', '']
        for stop in p['stops']:
            trip += ['[station_typ2]', stop['object_id'], '']
        trip += ['[profile]', 'TEST - provisional running times', f"{p['duration']:.3f}", '']
        distance = sum(l[2] for l in p['legs']); elapsed = 0
        # Explicit minutes at every platform; arrival/departure dwell 20 seconds.
        moving_time = p['duration'] - max(0, len(p['stops'])-2)/3
        for si in range(len(p['stops'])):
            if si:
                elapsed += p['legs'][si-1][2]/distance*moving_time
            trip += ['[profile_man_arr_time]', si, f'{elapsed:.5f}', '']
            if 0 < si < len(p['stops'])-1:
                elapsed += 1/3
            trip += ['[profile_man_dep_time]', si, f'{elapsed:.5f}', '']
        write(folder/'TTData'/f"{p['name']}.ttp", trip)
        for source, target, leg in zip(p['stops'], p['stops'][1:], p['legs']):
            a, b, length, steps = leg
            links += ['[StnLink]', f'{length:.6f}', source['object_id'], target['object_id'],
                      f'{a[3]:.6f}', f'{b[3]:.6f}', f'{a[2]:.6f}', f'{b[2]:.6f}', 0, len(steps)-1, '']
            for li in steps:
                lane = lanes[li]
                links += ['[StnLink_entry]', lane['id'], lane['path'], lane['tile'],
                          f"{lane['length']:.6f}", -1, 0, 0, '']
    write(folder/'TTData/StnLinks.cfg', links)
    ttl = ['Time Table Line File', '248M TEST: provisional times, all days.', '', '[userallowed]', '', '[priority]', 1, '']
    # Each duty cycles once an hour: 20 min outbound, 5 min layover, 25 min
    # inbound, 10 min layover. Two duties give a 30 minute headway without overlaps.
    for tour in range(2):
        ttl += ['[newtour]', f'{tour+1:02d}', 'Tsing Yi Test', 1023, '']
        for departure in range(330+30*tour, 1411, 60):
            for p, dep in ((plans[0], departure), (plans[1], departure+25)):
                ttl += ['[addtrip]', p['name'], 0, f'{dep:.3f}', '']
    write(folder/'TTData/248M_TEST.ttl', ttl)
    write(folder/'ailists.cfg', ['[aigroup_2]', 'NormalCars', '', '[end]', '',
        '[aigroup_depot]', 'Tsing Yi Test', 'TsingYi_Test', '', '[aigroup_depot_typgroup_2]',
        'Vehicles\\MAN_NL_NG\\MAN_EN92_main.bus', '24801\tTY-2481', '24802\tTY-2482', '[end]'])
    hof = ['Generated by omsi2-hk-1to1 / Tsing Yi TEST timetable', '', '[name]', 'TsingYi_Test',
           '[servicetrip]', 'Out of Service', '', 'stringcount_terminus', 8, 'stringcount_busstop', 4, '']
    for code, p in enumerate(plans, 1):
        dest = p['destination']
        hof += ['[addterminus]', code, dest, dest, dest.upper()[:16],
                'CHEUNG WANG' if code == 1 else 'TSING YI',
                'BUS TERMINUS' if code == 1 else 'STATION', dest.upper()[:16],
                '', dest[:20], '', '', '................', '']
    for name in dict.fromkeys(s['name'] for p in plans for s in p['stops']):
        hof += ['[addbusstop]', name, name.upper()[:16], name[:16], '', name[:20], '................', '']
    for code, p in enumerate(plans, 1):
        hof += ['[infosystem_trip]', 24800+code, p['destination'].upper(), code, '248M', '',
                '[infosystem_busstop_list]', len(p['stops']), *[s['name'] for s in p['stops']], '']
    write(folder/'TsingYi_Test.hof', hof)
    (folder/'timetable_manifest.json').write_text(json.dumps(summary, indent=2)+'\n', encoding='utf-8')
    manifest = json.loads((folder/'build_manifest.json').read_text(encoding='utf-8'))
    manifest['status'] = 'development_with_provisional_248M_timetable'
    manifest['timetable'] = summary
    manifest['limitations'] = [s for s in manifest['limitations'] if not s.startswith('No scheduled passenger')]
    limitation = '248M timetable times and shortest-road tracks are provisional; passenger operation and junctions need runtime checks. 249M remains an authoring reference.'
    if limitation not in manifest['limitations']:
        manifest['limitations'].append(limitation)
    (folder/'build_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    preview_path = folder/'preview_data.json'
    if preview_path.exists():
        preview = json.loads(preview_path.read_text(encoding='utf-8'))
        preview['manifest'] = manifest
        preview_path.write_text(json.dumps(preview,ensure_ascii=False), encoding='utf-8')
    cfg = read(folder/'global.cfg').replace(
        'Real OSM road and building foundation. Free-drive development map; see TSING_YI.md.',
        'Tsing Yi development map with provisional 248M TEST timetable; see TSING_YI.md.')
    (folder/'global.cfg').write_bytes(cfg.replace('\r\n','\n').replace('\n','\r\n').encode('utf-16'))
    return summary


def install(root, game):
    """Install only project timetable metadata; preserve existing bus model files."""
    game = game.resolve(); source = root/'maps/HK_TsingYi'; target = game/'maps/HK_TsingYi'
    if not (target/'global.cfg').is_file():
        raise ValueError(f'Install the map first: {target}')
    for name in ('global.cfg', 'ailists.cfg', 'build_manifest.json', 'timetable_manifest.json', 'TsingYi_Test.hof'):
        shutil.copy2(source/name, target/name)
    for name in ('248M_TEST.ttl','248M_Station_CheungWang_TEST.ttp','248M_CheungWang_Station_TEST.ttp','StnLinks.cfg'):
        (target/'TTData').mkdir(exist_ok=True)
        shutil.copy2(source/'TTData'/name, target/'TTData'/name)
    return install_hofs(root, game)


def install_hofs(root, game):
    # OpenOMSI also searches a common HOFs folder. Native OMSI needs it beside
    # the selected .bus. Only add this project-specific HOF to real bus folders.
    destinations = {game/'HOFs'}
    if (game/'Vehicles').exists():
        destinations.update(p.parent for p in (game/'Vehicles').rglob('*.bus') if p.stat().st_size > 256)
    installed, skipped = [], []
    for directory in sorted(destinations):
        dest = directory/'TsingYi_Test.hof'
        if dest.exists() and not dest.read_bytes().startswith(b'Generated by omsi2-hk-1to1'):
            skipped.append(str(dest)); continue
        directory.mkdir(parents=True, exist_ok=True); shutil.copy2(root/'maps/HK_TsingYi/TsingYi_Test.hof', dest)
        installed.append(str(dest))
    return {'game': str(game), 'hof_folders_updated': len(installed), 'preserved_existing_hofs': skipped}


def validate_generated(root):
    """Check serialized native references, routes, profiles and duty overlaps."""
    root = Path(root); folder = root/'maps/HK_TsingYi'; tt = folder/'TTData'
    report = {'passed': False, 'runtime_tested': False, 'errors': []}
    errors = report['errors']
    try:
        manifest = json.loads((folder/'timetable_manifest.json').read_text(encoding='utf-8'))
        lanes, _ = network(root)
        by_key = {(l['id'], l['path'], l['tile']): l for l in lanes}
        busstops = {int(i) for i in re.findall(r'\[busstop\]\n[^\n]+\n\d+\n(\d+)', read(tt/'Busstops.cfg').replace('\r\n','\n'))}
        links = {}
        data = read(tt/'StnLinks.cfg').splitlines()
        for i, token in enumerate(data):
            if token == '[StnLink]':
                r = data[i+1:i+10]
                link = {'length': float(r[0]), 'from': int(r[1]), 'to': int(r[2]),
                        's0': float(r[5]), 's1': float(r[6]), 'last': int(r[8]), 'steps': []}
                links[link['from'],link['to']] = link
            elif token == '[StnLink_entry]':
                r = data[i+1:i+8]; key = tuple(map(int, r[:3]))
                if key not in by_key:
                    raise ValueError(f'Station link references missing native path {key}')
                lane = by_key[key]
                if abs(float(r[3])-lane['length']) > .001:
                    errors.append(f'Station link path length mismatch {key}')
                link['steps'].append(lane)
        for key, link in links.items():
            steps = link['steps']
            if not steps or link['last'] != len(steps)-1:
                raise ValueError(f'Invalid station link entry range {key}')
            if any(math.dist(a['b'], b['a']) > .03 for a,b in zip(steps,steps[1:])):
                errors.append(f'Road gap in station link {key}')
            length = sum(s['length'] for s in steps)-link['s0']-(steps[-1]['length']-link['s1'])
            if abs(length-link['length']) > .01:
                errors.append(f'Station link distance mismatch {key}')
        durations = {}
        for trip in manifest['trips']:
            text = read(tt/(trip['name']+'.ttp')).replace('\r\n','\n')
            ids = list(map(int, re.findall(r'\[station_typ2\]\n(\d+)', text)))
            if ids != trip['stop_ids'] or not set(ids) <= busstops:
                errors.append(f"Trip {trip['name']} references incorrect platforms")
            if any((a,b) not in links for a,b in zip(ids,ids[1:])):
                errors.append(f"Trip {trip['name']} is missing a road link")
            profile = re.search(r'\[profile\]\n[^\n]+\n([\d.]+)', text)
            duration = float(profile[1]); durations[trip['name']] = duration
            arrivals = [(int(i),float(t)) for i,t in re.findall(r'\[profile_man_arr_time\]\n(\d+)\n([\d.]+)',text)]
            departures = [(int(i),float(t)) for i,t in re.findall(r'\[profile_man_dep_time\]\n(\d+)\n([\d.]+)',text)]
            if [i for i,_ in arrivals] != list(range(len(ids))) or [i for i,_ in departures] != list(range(len(ids))):
                raise ValueError('Missing manual station times')
            if arrivals[0][1] != 0 or abs(arrivals[-1][1]-duration) > .001:
                errors.append(f"Trip {trip['name']} duration disagrees with profile")
            if any(a[1]>d[1] for a,d in zip(arrivals,departures)) or any(d[1]>a[1] for d,a in zip(departures,arrivals[1:])):
                errors.append('Station times go backwards')
        ttl = read(tt/'248M_TEST.ttl').replace('\r\n','\n')
        if '[userallowed]' not in ttl:
            errors.append('Timetable is not available to the player')
        count = 0; station_departures = []
        for block in ttl.split('[newtour]\n')[1:]:
            header = block.splitlines()
            if header[1] != 'Tsing Yi Test' or int(header[2]) != 1023:
                errors.append('Incorrect depot or all-days mask')
            end = -1
            for name, profile, minute in re.findall(r'\[addtrip\]\n([^\n]+)\n(\d+)\n([\d.]+)',block):
                start = float(minute)
                if name not in durations or int(profile) != 0:
                    raise ValueError(f'Unknown trip or profile: {name}')
                if start < end:
                    errors.append('Overlapping trips on the same duty')
                end = start+durations[name]; count += 1
                if name == '248M_Station_CheungWang_TEST':
                    station_departures.append(start)
        if sorted(station_departures) != list(range(330,1411,30)):
            errors.append('Station departures do not match the advertised 30-minute interval')
        hof = read(folder/'TsingYi_Test.hof')
        if '[name]\r\nTsingYi_Test' not in hof or '[infosystem_trip]\r\n24801' not in hof:
            errors.append('HOF depot or route code missing')
        report.update(lines=1, tours=ttl.count('[newtour]'), trips=len(durations), departures=count,
                      station_links=len(links), path_entries=sum(len(l['steps']) for l in links.values()))
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError) as exc:
        errors.append(str(exc))
    report['passed'] = not errors
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--check-only', action='store_true', help='Plan routes without writing files')
    parser.add_argument('--install', type=Path, help='Also install small timetable files and HOF into an existing map installation')
    parser.add_argument('--hof-root', type=Path, action='append', default=[], help='Additional OpenOMSI content root to receive the shared HOF')
    args = parser.parse_args(); root = args.root.resolve()
    summary = generate(root, args.check_only)
    if not args.check_only:
        summary['offline_validation'] = validate_generated(root)
        if not summary['offline_validation']['passed']:
            raise ValueError(json.dumps(summary['offline_validation']))
    if args.install and not args.check_only:
        summary['installation'] = install(root, args.install)
        for content in args.hof_root:
            summary.setdefault('additional_hof_installations', []).append(install_hofs(root, content.resolve()))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
