#!/usr/bin/env python3
"""Classify Hong Kong bus routes by the HK Bus Wiki numbering method.

Implements the scheme from the Hong Kong Bus Wiki article
「巴士路線編號方法」(https://hkbus.fandom.com/wiki/巴士路線編號方法):
letter prefixes, letter suffixes and regional number ranges.

Categories:
  regular, cross_harbour 過海, airport 機場, overnight 通宵, border 口岸,
  express 特快, recreational 康樂, hospital 醫院, mtr_feeder 港鐵接駁,
  residents 居民

Region (inferred from origin/destination place names):
  hk_island 港島, kowloon_nt 九龍新界, cross_harbour 過海, lantau 大嶼山,
  unknown
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Letter prefixes (字母開首) - from the HK Bus Wiki numbering method
# ---------------------------------------------------------------------------
PREFIX_CATEGORY = {
    "A": "airport",       # 機場巴士路線
    "B": "border",        # 過境口岸接駁路線
    "D": "recreational",  # 迪士尼樂園路線之計劃編號 (unused; Disney)
    "E": "airport",       # 北大嶼山對外路線
    "FE": "recreational", # Formula E 臨時路線
    "H": "recreational",  # 觀光城巴 / 醫院路線 (H1 hospital)
    "HK": "recreational", # 奧運穿梭 / 九巴遊香港
    "K": "mtr_feeder",    # 港鐵巴士及接駁巴士
    "M": "mtr_feeder",    # 機場快綫車站接駁 (defunct)
    "N": "overnight",     # 通宵路線
    "NA": "overnight",    # 深宵機場巴士
    "NB": "border",       # 通宵過境口岸接駁
    "P": "express",       # 北大嶼山特別 / 九巴星級尊線 (P960/P968 premium)
    "R": "recreational",  # 迪士尼樂園 / 特別旅遊路線
    "S": "airport",       # 北大嶼山穿梭路線
    "SP": "recreational", # 啟德體育園特別路線
    "T": "regular",       # 鐵路輔助 / 臨時 / 旅遊
    "W": "express",       # 高鐵西九龍站特快
    "X": "express",       # 亞博館 / 特快路線
    "Y": "regular",       # 颱風路線
}

# ---------------------------------------------------------------------------
# Letter suffixes (字母結尾) - from the HK Bus Wiki numbering method
# ---------------------------------------------------------------------------
SUFFIX_CATEGORY = {
    "H": "hospital",      # 醫院路線
    "K": "mtr_feeder",    # 接駁九廣東鐵
    "M": "mtr_feeder",    # 接駁港鐵
    "N": "overnight",     # 深宵路線 (962N, 967N, 969N)
    "R": "recreational",  # 旅遊／特別路線
    "X": "express",       # 特快／半直通
    "D": "recreational",  # 迪士尼樂園
    "U": "regular",       # 屯門公路轉車站接駁
    "C": None,            # 飛機維修區 (E-prefix only; stays airport)
}

# ---------------------------------------------------------------------------
# Cross-harbour number ranges (過海隧道) - 100-199, 300-399 peak,
# 600-699 (東隧), 900-999 (西隧). 800-899 were Sha Tin Racecourse
# cross-harbour routes (all defunct).
# ---------------------------------------------------------------------------
def _cross_harbour_number(number: str) -> bool:
    m = re.match(r"^(\d{3})$", number)
    if not m:
        return False
    n = int(m.group(1))
    return 100 <= n <= 199 or 300 <= n <= 399 or 600 <= n <= 699 or 900 <= n <= 999


# ---------------------------------------------------------------------------
# Region inference from place names
# ---------------------------------------------------------------------------
HK_ISLAND_HINTS = (
    # English
    "central", "admiralty", "western", "kennedy town", "sai ying pun", "sheung wan",
    "wan chai", "causeway bay", "happy valley", "tin hau", "fortress hill",
    "north point", "quarry bay", "taikoo", "shau kei wan", "sai wan ho",
    "chai wan", "siu sai wan", "heng fa chuen", "aberdeen", "wong chuk hang",
    "ap lei chau", "pok fu lam", "wah fu", "cyberport", "stanley", "repulse bay",
    "deep water bay", "shek o", "the peak", "mid-levels", "braemar hill",
    "jardine", "island resort", "lei tung", "south horizons", "tai hang",
    "taikoo shing", "mount davis", "kellett", "kornhill",
    "wan chai gap", "hong kong parkview", "hill road", "victoria peak",
    "gloucester", "hennessy", "des voeux", "connaught", "queen's road",
    "kennedy", "sai wan", "shau kei",
    # Chinese
    "中環", "金鐘", "上環", "西環", "西營盤", "堅尼地城", "灣仔", "銅鑼灣",
    "跑馬地", "天后", "炮台山", "北角", "鰂魚涌", "太古城", "筲箕灣", "西灣河",
    "柴灣", "小西灣", "杏花邨", "香港仔", "黃竹坑", "鴨脷洲", "薄扶林",
    "華富", "數碼港", "赤柱", "淺水灣", "深水灣", "石澳", "山頂", "半山",
    "寶馬山", "渣甸山", "海怡", "利東", "置富", "貝沙灣", "田灣", "石排灣",
    "軒尼詩道", "皇后大道", "德輔道", "干諾道", "士美非路", "卑路乍",
)

KOWLOON_NT_HINTS = (
    # English - Kowloon
    "tsim sha tsui", "yau ma tei", "mong kok", "prince edward", "sham shui po",
    "cheung sha wan", "lai chi kok", "mei foo", "kowloon tong", "kowloon city",
    "hung hom", "to kwa wan", "kwun tong", "ngau tau kok", "kowloon bay",
    "lam tin", "yau tong", "wong tai sin", "diamond hill", "lok fu", "choi hung",
    "san po kong", "tai kok tsui", "stonecutters island", "whampoa", "ho man tin",
    "kowloon peak", "lei yue mun", "sau mau ping", "shun lee", "ping tin",
    "kai tak", "kowloon station", "kowloon", "hung hom station",
    # English - New Territories
    "tsuen wan", "kwai chung", "kwai fong", "tsing yi", "tuen mun", "yuen long",
    "tin shui wai", "hung shui kiu", "sha tin", "ma on shan", "tai po",
    "fanling", "sheung shui", "sai kung", "fo tan", "tai wai", "siu lek yuen",
    "city one", "shi mun", "tseung kwan o", "po lam", "hang hau",
    "lok ma chau", "kam tin", "pat heung", "ping shan", "kam sheung", "au tau",
    "tai lam", "tsing lung tau", "sham tseng", "ting kau", "ma wan",
    "lo wu", "kwu tung", "ta kwu ling", "sha tau kok", "wo sheung tung",
    "fanling", "sheung shui", "high speed rail west kowloon",
    # Chinese - Kowloon
    "尖沙咀", "油麻地", "旺角", "太子", "深水埗", "長沙灣", "荔枝角", "美孚",
    "九龍塘", "九龍城", "紅磡", "土瓜灣", "觀塘", "牛頭角", "九龍灣", "藍田",
    "油塘", "黃大仙", "鑽石山", "樂富", "彩虹", "新蒲崗", "大角咀", "黃埔",
    "何文田", "秀茂坪", "順天", "坪石", "啟德", "九龍站", "旺角東", "石硤尾",
    "白田", "蘇屋", "青山道", "長沙灣道", "彌敦道",
    # Chinese - New Territories
    "荃灣", "葵涌", "葵芳", "青衣", "屯門", "元朗", "天水圍", "洪水橋",
    "沙田", "馬鞍山", "大埔", "粉嶺", "上水", "西貢", "火炭", "大圍",
    "小瀝源", "第一城", "石門", "將軍澳", "寶林", "坑口", "落馬洲", "錦田",
    "八鄉", "屏山", "錦上路", "大欖", "青龍頭", "深井", "汀九", "馬灣",
    "羅湖", "古洞", "打鼓嶺", "沙頭角", "和合石", "大埔墟",
    "科學園", "白石角", "十四鄉", "北區", "林村", "嘉道理",
)

LANTAU_HINTS = (
    "tung chung", "tai o", "mui wo", "ngong ping", "discovery bay",
    "cheung chau", "peng chau", "lantau", "airport", "asiaworld", "asia world",
    "skycity", "sky city", "香港國際機場", "機場", "東涌", "大澳", "梅窩",
    "昂坪", "愉景灣", "長洲", "坪洲", "大嶼山", "博覽館",
)


def infer_region(origin: str, destination: str) -> str:
    """Infer the route region from its endpoints.

    Returns hk_island, kowloon_nt, cross_harbour, lantau or unknown.
    """
    text = " ".join((origin or "", destination or "")).lower()

    def hit(hints) -> bool:
        return any(h in text for h in hints)

    island = hit(HK_ISLAND_HINTS)
    klnnt = hit(KOWLOON_NT_HINTS)
    lantau = hit(LANTAU_HINTS)

    if island and klnnt:
        return "cross_harbour"
    if island and lantau:
        return "cross_harbour"
    if lantau:
        return "lantau"
    if island:
        return "hk_island"
    if klnnt:
        return "kowloon_nt"
    return "unknown"


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------
def classify(number: str, text: str = "", operator: str = "") -> str:
    """Return the category for a route number (HK Bus Wiki numbering method)."""
    number = (number or "").strip().upper()
    text_l = (text or "").lower()

    # Residents' services keep their own group
    if re.match(r"^(NR|HR|KR|DB)\d", number):
        return "residents"

    m = re.match(r"^([A-Z]{1,3})(\d+)([A-Z]{0,2})$", number)
    if not m:
        # digit-first: suffix only, e.g. '14H', '962N', or plain number
        m2 = re.match(r"^(\d+)([A-Z]{0,2})$", number)
        if m2:
            numeric, suffix = int(m2.group(1)), m2.group(2)
            cat = SUFFIX_CATEGORY.get(suffix)
            if cat == "overnight":
                return cat
            if cat == "hospital":
                return cat
            if cat == "mtr_feeder":
                # M/K suffix feeder only for franchised buses, not green minibus
                if "gmb" not in operator:
                    return cat
            if cat == "recreational":
                return cat
            if _cross_harbour_number(str(numeric)):
                return "cross_harbour"
            return "regular"
        return "regular"

    prefix, numeric, suffix = m.group(1), int(m.group(2)), m.group(3)

    # Prefix takes priority (longest match first)
    cat = None
    for plen in (3, 2, 1):
        p = prefix[:plen]
        if p in PREFIX_CATEGORY:
            cat = PREFIX_CATEGORY[p]
            break

    # Suffix refines (some override the prefix, e.g. N-suffix overnight)
    if suffix:
        scat = SUFFIX_CATEGORY.get(suffix)
        if scat == "overnight" or (scat and cat not in ("border", "airport")):
            if scat == "mtr_feeder" and "gmb" in operator:
                scat = None
            cat = scat if scat else cat

    # Cross-harbour number ranges (3-digit numbers)
    if _cross_harbour_number(str(numeric)) and cat is None:
        cat = "cross_harbour"

    # 過海 in the text overrides
    if any(h in text for h in ("過海", "海隧", "紅隧", "西隧", "東隧")):
        cat = "cross_harbour"

    return cat or "regular"


CATEGORY_LABELS = {
    "cross_harbour": "Cross-harbour 過海",
    "airport": "Airport / Lantau 機場",
    "overnight": "Overnight 通宵",
    "border": "Border 口岸",
    "recreational": "Recreational 康樂",
    "express": "Express 特快",
    "hospital": "Hospital 醫院",
    "mtr_feeder": "MTR feeder 港鐵接駁",
    "school": "School 學校",
    "residents": "Residents 居民",
    "regular": "Regular 常規",
}

REGION_LABELS = {
    "hk_island": "Hong Kong Island 港島",
    "kowloon_nt": "Kowloon / NT 九龍新界",
    "cross_harbour": "Cross-harbour 過海",
    "lantau": "Lantau 大嶼山",
    "unknown": "Unknown 未定",
}
