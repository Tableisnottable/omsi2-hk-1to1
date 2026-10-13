"""Import the list of cancelled Hong Kong bus routes from Chinese Wikipedia.

Source: https://zh.wikipedia.org/wiki/香港已取消巴士路線列表
Fetched as raw wikitext via the MediaWiki API and parsed into
routes/cancelled_routes.csv.

The list covers franchised buses (Citybus, NWFB, CMB, KMB, Long Win, NLB),
cross-harbour and joint routes, KCR/MTR buses, and residents' services.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from RouteCategories import classify  # noqa: E402

SOURCE_URL = "https://zh.wikipedia.org/wiki/香港已取消巴士路線列表"
API_URL = "https://zh.wikipedia.org/w/api.php"

SECTION_COMPANIES = {
    "專營權一": "ctb",
    "專營權二": "ctb",
    "固定租賃服務": "ctb",
    "新世界第一巴士": "nwfb",
    "中華巴士": "cmb",
    "九廣鐵路公司": "kcr",
    "港鐵巴士": "mtr",
    "港鐵接駁巴士": "mtr",
    "九巴": "kmb",
    "龍運巴士": "lwb",
    "新大嶼山巴士": "nlb",
    "過海巴士路線": "cross_harbour",
    "非過海聯營路線": "joint",
    "居民巴士路線": "residents",
}

COMPANY_FULL = {
    "ctb": "Citybus",
    "nwfb": "NWFB",
    "cmb": "CMB",
    "kcr": "KCR",
    "mtr": "MTR Bus",
    "kmb": "KMB",
    "lwb": "Long Win",
    "nlb": "NLB",
    "cross_harbour": "Cross-harbour",
    "joint": "Joint non-cross-harbour",
    "residents": "Residents' service",
}


def fetch_wikitext() -> str:
    query = urllib.parse.urlencode(
        {
            "action": "parse",
            "page": "香港已取消巴士路線列表",
            "prop": "wikitext",
            "format": "json",
            "formatversion": "2",
        }
    )
    req = urllib.request.Request(API_URL + "?" + query, headers={"User-Agent": "omsi2-hk-1to1 route importer"})
    with urllib.request.urlopen(req, timeout=120) as response:
        data = json.load(response)
    return data["parse"]["wikitext"]


def strip_wiki(text: str) -> str:
    """Remove wikilinks, html tags, refs, templates and table pipes; collapse space."""
    text = re.sub(r"\{\{noteGT\|1=.*?\}\}", "", text, flags=re.S)
    text = re.sub(r"\{\{.*?\}\}", "", text, flags=re.S)
    text = re.sub(r"\}\}+", "", text)
    text = re.sub(r"<ref.*?</ref>", "", text, flags=re.S)
    text = re.sub(r"<ref[^>]*/>", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("'''", "").replace("''", "")
    # wikilinks: keep only the display text after the last pipe
    text = re.sub(r"\[\[[^\]\]]*\|([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    # drop cell-level attributes like rowspan="2"
    text = re.sub(r"(?<=\|)\s*rowspan=[\"']?\d+[\"']?\s*", "", text)
    text = re.sub(r"\|", " ", text)
    text = text.replace("&nbsp;", " ").replace("<br />", " ").replace("<br>", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def split_cells(body: str):
    """Split a wikitable row body on '||', ignoring pipes inside [[wikilinks]].

    Returns a list of (content, rowspan) tuples.
    """
    parts = []
    depth = 0
    cur = []
    i = 0
    while i < len(body):
        if body.startswith("[[", i):
            depth += 1
            cur.append("[[")
            i += 2
        elif body.startswith("]]", i) and depth:
            depth -= 1
            cur.append("]]")
            i += 2
        elif body.startswith("||", i) and depth == 0:
            parts.append("".join(cur))
            cur = []
            i += 2
        else:
            cur.append(body[i])
            i += 1
    parts.append("".join(cur))

    out = []
    for p in parts:
        out.append(parse_cell(p))
    return out


def parse_cell(p: str):
    """Return (content, rowspan) for one raw cell token.

    Tokens look like '|content', ' attrs |content' or plain 'content'.
    A leading '|' or an attribute block ending in '|' is stripped.
    """
    rs = 1
    m = re.match(r"^\s*([^|]*?)\|(.*)$", p, re.S)
    if m:
        attrs, content = m.group(1), m.group(2)
        if "=" not in attrs and "[[" not in attrs:
            # leading plain '|' divider
            p = content
        elif "[[" not in attrs:
            rsm = re.search(r"rowspan\s*=\s*[\"']?(\d+)", attrs)
            if rsm:
                rs = int(rsm.group(1))
            p = content
    return strip_wiki(p).strip(), rs


def parse_table_rows(section_body: str):
    """Yield row cell lists from wikitable rows, honouring rowspan inheritance."""
    pending = {}  # column index -> [value, remaining_rows]
    for line in section_body.splitlines():
        line = line.strip()
        if not line.startswith("||"):
            continue
        raw = split_cells(line[2:])
        ncols = len(pending) + len(raw)
        row = []
        it = iter(raw)
        new_pending = {}
        for col in range(ncols):
            if col in pending:
                value, remaining = pending[col]
                row.append(value)
                if remaining - 1 > 0:
                    new_pending[col] = [value, remaining - 1]
            else:
                content, rs = next(it)
                row.append(content)
                if rs > 1:
                    new_pending[col] = [content, rs - 1]
        pending = new_pending
        yield row


def route_number(cell: str) -> str:
    """Extract the route number from the first cell.

    Handles plain numbers ('2B', '2B第1代'), residents' numbers ('HR36 (36R)'),
    and editorial notes ('待查NR202?' -> NR202).
    """
    if not cell:
        return ""
    # editorial notes: look for a residents'-style token anywhere
    m = re.search(r"(HR|KR|DB|NR)\d+[A-Z]?", cell, re.IGNORECASE)
    if m:
        return m.group(0).upper()
    # plain route number at the start (letters optional, e.g. 'SN3', 'B1', '90C')
    m = re.match(r"^([A-Z]{0,3}\d+[A-Z]?\d*)", cell)
    if m:
        return m.group(1).upper()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-file")
    parser.add_argument("--output-root", default=str(Path(__file__).parents[2]))
    args = parser.parse_args()

    root = Path(args.output_root).resolve()
    routes_dir = root / "routes"

    if args.source_file:
        wikitext = Path(args.source_file).read_text(encoding="utf-8")
    else:
        wikitext = fetch_wikitext()

    # split into sections
    lines = wikitext.splitlines()
    section_starts = []
    for i, line in enumerate(lines):
        m = re.match(r"^==+\s*(.*?)\s*==+\s*$", line.strip())
        if m:
            section_starts.append((i, m.group(1)))

    rows = []
    for si, (start, title) in enumerate(section_starts):
        end = section_starts[si + 1][0] if si + 1 < len(section_starts) else len(lines)
        # skip subsection markers (=== ... ===) for company detection
        company = None
        for key, code in SECTION_COMPANIES.items():
            if key in title:
                company = code
                break
        if company is None:
            continue
        body = "\n".join(lines[start:end])
        for cells in parse_table_rows(body):
            if not cells or not cells[0]:
                continue
            num = route_number(cells[0])
            route = cells[1] if len(cells) > 1 else ""
            cancel_date = cells[2] if len(cells) > 2 else ""
            if company in ("cross_harbour", "joint", "residents"):
                operator = cells[3] if len(cells) > 3 else ""
                reason = cells[4] if len(cells) > 4 else ""
            else:
                operator = COMPANY_FULL[company]
                reason = cells[3] if len(cells) > 3 else ""
            rows.append(
                {
                    "route_number": num,
                    "route": route,
                    "cancelled_date": cancel_date,
                    "operator": operator,
                    "reason": reason,
                    "company": company,
                    "category": classify(num, route, company),
                    "source": SOURCE_URL,
                }
            )

    # dedupe (a route may appear under multiple operators for joint services)
    seen = set()
    unique = []
    for r in rows:
        key = (r["route_number"], r["route"], r["cancelled_date"], r["operator"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(r)

    fields = ["route_number", "route", "cancelled_date", "operator", "reason", "company", "category", "source"]
    with (routes_dir / "cancelled_routes.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(unique)

    print(f"Wrote {len(unique)} cancelled route records to {routes_dir / 'cancelled_routes.csv'}")
    from collections import Counter
    print("by company:", dict(Counter(r["company"] for r in unique)))


if __name__ == "__main__":
    main()
