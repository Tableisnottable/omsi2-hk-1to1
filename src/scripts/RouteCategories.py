#!/usr/bin/env python3
"""Classify Hong Kong bus routes into service categories.

Takes route_number (+ optional route/operator text) and assigns one of the
standard Hong Kong bus route categories from numbering conventions and name
hints:

  cross_harbour  過海隧道 (100-199, 300s peak, 600s, 9xx, or 過海 in text)
  airport        機場／北大嶼山 (A/NA/E prefix or 機場/Airport)
  overnight      通宵 (N prefix or 通宵)
  border         邊境口岸 (B prefix or 口岸/Port/Bay/Huanggang/Lok Ma Chau)
  recreational   假日／康樂 (R suffix or 馬場/Racecourse)
  express        特快／快速 (X in the number)
  school         學校 (學校/School)
  residents      居民服務 (NR/HR/KR/DB prefix)
  regular        一般市區新界路線 (everything else)

Used by Import-CancelledRoutes.py and Classify-BusRoutes.py.
"""

from __future__ import annotations

import re


def _num_prefix(number: str) -> tuple[str, int, str]:
    """Split a route number into (letters, numeric part, trailing letters)."""
    m = re.match(r"^([A-Z]*)(\d+)([A-Z]*)", number.upper())
    if not m:
        return number.upper(), 0, ""
    return m.group(1), int(m.group(2)), m.group(3)


CROSS_HARBOUR_HINTS = ("過海", "海隧", "紅隧", "西隧", "東隧")
AIRPORT_HINTS = ("機場", "airport", "北大嶼山", "東涌", "tung chung")
OVERNIGHT_HINTS = ("通宵", "overnight", "清晨")
BORDER_HINTS = (
    "口岸", "落馬洲", "lok ma chau", "shenzhen bay", "深圳灣",
    "huanggang", "黃崗", "香園圍", "heung yuen wai", "蓮塘",
    "liantang", "港珠澳", "hzmb", "hong kong port",
)
RECREATIONAL_HINTS = ("馬場", "racecourse", "泳季", "假日", "沙灘", "beach")


def classify(number: str, text: str = "", operator: str = "") -> str:
    """Return the category for a route.

    number: route number like '969', 'A41', 'NR933'
    text: optional route description / name used for keyword hints
    operator: optional operator code
    """
    number = (number or "").strip().upper()
    text_l = (text or "").lower()

    # Residents' services keep their own group
    if re.match(r"^(NR|HR|KR|DB)\d", number):
        return "residents"

    letters, numeric, suffix = _num_prefix(number)

    # Overnight: N prefix (N121, N241) or text
    if letters.startswith("N") and numeric > 0:
        return "overnight"
    if any(h in text or h.lower() in text_l for h in OVERNIGHT_HINTS):
        return "overnight"

    # Airport / Lantau
    if letters in ("A", "NA", "E", "S") and numeric > 0:
        return "airport"
    if any(h in text or h.lower() in text_l for h in AIRPORT_HINTS):
        return "airport"

    # Border crossings
    if letters == "B" and numeric > 0:
        return "border"
    if any(h in text_l for h in BORDER_HINTS):
        return "border"

    # Recreational / racecourse (R suffix)
    if suffix == "R":
        return "recreational"
    if any(h in text or h.lower() in text_l for h in RECREATIONAL_HINTS):
        return "recreational"

    # School
    if "學校" in text or "school" in text_l:
        return "school"

    # Cross-harbour by classic numbering ranges
    if letters == "" and numeric:
        if 100 <= numeric <= 199:
            return "cross_harbour"
        if 300 <= numeric <= 399:
            return "cross_harbour"
        if 600 <= numeric <= 699:
            return "cross_harbour"
        if 900 <= numeric <= 999:
            return "cross_harbour"
    if any(h in text for h in CROSS_HARBOUR_HINTS):
        return "cross_harbour"

    # Express
    if "X" in number:
        return "express"

    return "regular"


CATEGORY_LABELS = {
    "cross_harbour": "Cross-harbour 過海",
    "airport": "Airport / Lantau 機場",
    "overnight": "Overnight 通宵",
    "border": "Border 口岸",
    "recreational": "Recreational 康樂",
    "express": "Express 特快",
    "school": "School 學校",
    "residents": "Residents 居民",
    "regular": "Regular 常規",
}
