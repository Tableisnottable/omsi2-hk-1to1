#!/usr/bin/env python3
"""Download reproducible local inputs for Build-TsingYi.py (never commit binaries)."""
import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCES = {
    'hong-kong-latest.osm.pbf': 'https://download.geofabrik.de/asia/china/hong-kong-latest.osm.pbf',
    'N22E114.hgt.gz': 'https://s3.amazonaws.com/elevation-tiles-prod/skadi/N22/N22E114.hgt.gz',
}


def fetch(folder, force=False):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, url in SOURCES.items():
        path = folder / name
        if force or not path.exists():
            print(f'Downloading {name}', flush=True)
            request = urllib.request.Request(url, headers={'User-Agent': 'OMSI-TsingYi-Builder/1.0'})
            temporary = path.with_suffix(path.suffix + '.part')
            with urllib.request.urlopen(request, timeout=180) as response, temporary.open('wb') as out:
                while chunk := response.read(1024 * 1024):
                    out.write(chunk)
            temporary.replace(path)
        manifest[name] = {'url': url, 'bytes': path.stat().st_size,
                          'sha256': hashlib.file_digest(path.open('rb'), 'sha256').hexdigest()}
    manifest['recorded_utc'] = datetime.now(timezone.utc).isoformat()
    (folder / 'sources.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, default=Path(__file__).resolve().parents[2] / 'work' / 'tsingyi-inputs')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()
    fetch(args.cache, args.force)
