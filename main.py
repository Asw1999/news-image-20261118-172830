"""Broadsheet world news infographic generator for Wednesday, 18 November 2026.

Default sandbox execution relies strictly on Python 3.13 standard library modules to copy
the pre-rendered `entry.png` deterministically to `$MAKEFUN_OUTPUT_DIR/entry.png`.
When `MAKEFUN_RENDER=1` is set, Pillow renders a 2048x2048 supersampled broadsheet and
downsamples with LANCZOS to a compact 1024x1024 RGB PNG.
"""

import math
import os
import shutil
import sys
from pathlib import Path

OUT_PX = 1024
SUPERSAMPLE_W = 2048
SUPERSAMPLE_H = 2048
PNG_BYTE_LIMIT = 1_048_576

PAGE_MARGIN_X = 28
PAGE_WIDTH = SUPERSAMPLE_W - 2 * PAGE_MARGIN_X

MASTHEAD_TOP, MASTHEAD_BOT = 0, 185
GOLD_RULE_TOP, NAV_BAR_TOP = 150, 156
ROW1_TOP, ROW1_BOT = 195, 635
ROW2_TOP, ROW2_BOT = 650, 1030
ROW3_TOP, ROW3_BOT = 1045, 1425
BOTTOM_TOP, BOTTOM_BOT = 1440, 1995
FOOTER_TOP, FOOTER_BOT = 2002, 2044

PAPER_CREAM = (250, 247, 240)
PAPER_WARM_ALT = (241, 236, 226)
CARD_SURFACE = (255, 254, 250)
MASTHEAD_NAVY = (15, 30, 54)
INK_PRIMARY = (17, 24, 39)
INK_BODY = (55, 65, 81)
INK_MUTED = (100, 116, 139)
RULE_BORDER = (214, 207, 194)
GOLD_ACCENT = (217, 119, 6)
GOLD_BRIGHT = (245, 158, 11)
CALENDAR_CRIMSON = (185, 28, 28)
CALENDAR_SLATE = (30, 41, 59)

MAP_OCEAN_LIGHT = (217, 232, 245)
MAP_GRID_LINE = (195, 214, 232)
MAP_LAND_SAGE = (200, 211, 184)
MAP_LAND_EDGE = (142, 158, 125)

FONT_DIRS = (
    "/system/fonts",
    "/data/data/com.termux/files/usr/share/fonts/TTF",
    "/usr/share/fonts/truetype/noto",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/TTF",
    "/usr/share/fonts",
)

FONT_SPECS = {
    "serif_bold": ("NotoSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"),
    "serif_italic": ("NotoSerif-Italic.ttf", "DejaVuSerif-Italic.ttf"),
    "sans_bold": ("SourceSansPro-Bold.ttf", "DejaVuSans-Bold.ttf"),
    "sans_semi": ("SourceSansPro-SemiBold.ttf", "DejaVuSans-Bold.ttf"),
    "sans_reg": ("SourceSansPro-Regular.ttf", "DejaVuSans.ttf"),
    "cond_bold": ("BarlowSemiCondensed-Bold.ttf", "DejaVuSansCondensed-Bold.ttf"),
    "mono_bold": ("DejaVuSansMono-Bold.ttf", "DroidSansMono.ttf"),
}

REGION_PALETTE = [
    {"key": "AMERICAS", "name": "AMERICAS", "short": "Americas", "hex": "#0369A1"},
    {"key": "EUROPE", "name": "EUROPE", "short": "Europe", "hex": "#1D4ED8"},
    {"key": "MENA", "name": "MIDDLE EAST", "short": "Middle East", "hex": "#B91C1C"},
    {"key": "AFRICA", "name": "AFRICA", "short": "Africa", "hex": "#B45309"},
    {"key": "APAC", "name": "ASIA-PACIFIC", "short": "Asia-Pacific", "hex": "#047857"},
    {"key": "GLOBAL", "name": "GLOBAL & SCIENCE", "short": "Global", "hex": "#6D28D9"},
]
REGION_LOOKUP = {item["key"]: item for item in REGION_PALETTE}

ATLAS_BOUNDS = (-172.0, 184.0, -56.0, 80.0)

ATLAS_LANDMASSES = {
    "north_america": [
        (-166.0, 60.0), (-168.0, 66.0), (-161.0, 67.0), (-165.5, 69.0),
        (-156.5, 71.5), (-141.0, 69.5), (-125.0, 70.0), (-110.0, 69.0),
        (-95.0, 69.5), (-90.0, 64.0), (-94.5, 59.0), (-86.0, 55.0),
        (-80.0, 51.5), (-77.5, 59.0), (-74.0, 62.5), (-64.5, 60.0),
        (-56.0, 52.0), (-53.0, 47.0), (-60.0, 46.5), (-67.0, 45.0),
        (-70.5, 42.0), (-74.0, 40.5), (-76.0, 35.0), (-80.5, 32.0),
        (-80.2, 25.5), (-81.5, 25.2), (-83.0, 28.5), (-89.0, 29.0),
        (-95.0, 29.0), (-97.0, 26.0), (-96.0, 19.0), (-90.5, 19.0),
        (-90.5, 21.5), (-87.0, 21.0), (-88.0, 16.0), (-83.5, 14.5),
        (-83.5, 10.5), (-77.5, 8.5), (-78.5, 7.5), (-82.0, 7.8),
        (-86.0, 10.5), (-92.5, 14.5), (-100.0, 16.8), (-105.5, 20.5),
        (-110.0, 23.0), (-113.5, 31.0), (-117.0, 32.5), (-122.5, 37.8),
        (-124.5, 41.0), (-124.5, 48.5), (-128.5, 51.0), (-135.5, 57.0),
        (-145.5, 60.2), (-151.5, 59.2), (-156.5, 56.5), (-163.0, 55.0),
    ],
    "greenland": [
        (-44.0, 60.0), (-52.5, 64.5), (-54.5, 71.0), (-69.0, 77.0),
        (-53.0, 81.5), (-22.0, 81.5), (-18.5, 76.0), (-22.5, 70.0),
        (-34.5, 68.0), (-41.0, 63.0),
    ],
    "cuba": [(-85.0, 22.0), (-81.5, 23.2), (-77.0, 21.5), (-74.2, 20.2), (-78.0, 20.0)],
    "hispaniola": [(-74.4, 18.5), (-71.5, 19.9), (-68.5, 18.6), (-71.5, 17.7)],
    "south_america": [
        (-77.5, 8.5), (-74.0, 11.2), (-71.0, 12.2), (-66.5, 10.5),
        (-61.5, 9.8), (-55.0, 5.8), (-50.0, 1.5), (-48.5, -1.5),
        (-41.0, -3.0), (-35.0, -6.0), (-34.8, -8.5), (-38.5, -13.0),
        (-41.0, -22.0), (-43.5, -23.0), (-48.5, -27.5), (-53.5, -33.8),
        (-57.0, -35.0), (-62.5, -40.5), (-65.5, -43.0), (-67.5, -47.5),
        (-68.5, -52.5), (-67.5, -55.0), (-71.5, -54.5), (-75.0, -49.0),
        (-73.8, -42.0), (-71.6, -33.0), (-70.6, -23.5), (-70.3, -18.5),
        (-77.1, -12.0), (-81.3, -4.7), (-80.0, -2.0), (-77.5, 4.5),
    ],
    "iceland": [(-24.0, 65.5), (-18.0, 66.5), (-13.6, 65.2), (-15.2, 63.9), (-22.6, 64.0)],
    "britain": [
        (-5.5, 50.1), (-3.0, 51.4), (-4.9, 52.8), (-3.3, 54.8),
        (-5.8, 56.8), (-5.0, 58.5), (-3.0, 58.6), (-1.8, 57.5),
        (-1.4, 55.0), (1.7, 52.5), (1.4, 51.2), (-1.8, 50.6),
    ],
    "ireland": [(-10.2, 51.8), (-9.6, 54.3), (-6.1, 55.2), (-6.0, 52.2), (-8.5, 51.5)],
    "eurasia": [
        (-5.6, 36.0), (-9.0, 37.0), (-9.5, 38.8), (-9.3, 43.0),
        (-2.0, 43.4), (-2.2, 47.2), (-4.7, 48.4), (1.8, 51.0),
        (8.5, 53.7), (8.1, 57.0), (10.6, 57.7), (10.2, 54.4),
        (14.0, 54.1), (19.0, 54.5), (24.5, 57.5), (24.7, 59.4),
        (29.8, 60.0), (24.5, 60.2), (21.5, 63.0), (24.1, 65.8),
        (20.0, 63.5), (18.0, 59.3), (13.0, 55.6), (10.7, 59.9),
        (5.3, 60.4), (10.4, 63.4), (15.5, 68.5), (26.0, 71.0),
        (33.5, 69.0), (41.0, 66.5), (44.0, 68.5), (56.0, 68.5),
        (68.0, 70.0), (72.5, 73.0), (74.5, 68.0), (85.0, 73.5),
        (104.0, 77.5), (126.0, 73.5), (158.0, 70.2), (179.0, 66.5),
        (177.0, 64.5), (163.0, 59.8), (162.5, 55.8), (156.8, 51.0),
        (156.5, 59.0), (143.0, 59.2), (141.2, 53.0), (135.5, 44.0),
        (131.9, 43.1), (129.4, 35.1), (126.4, 34.6), (126.6, 37.6),
        (121.6, 39.0), (118.2, 39.0), (122.6, 37.4), (119.5, 34.5),
        (121.9, 31.2), (119.8, 26.0), (114.2, 22.3), (110.2, 20.3),
        (106.8, 20.8), (109.2, 12.2), (105.5, 8.8), (100.5, 13.5),
        (103.8, 1.3), (100.3, 5.4), (96.2, 16.8), (91.8, 22.3),
        (88.8, 21.8), (85.0, 19.5), (80.3, 13.1), (77.5, 8.1),
        (72.8, 19.0), (69.0, 22.5), (67.0, 24.8), (61.5, 25.2),
        (56.4, 27.1), (50.8, 29.0), (48.0, 29.5), (50.5, 26.2),
        (51.5, 25.2), (56.4, 26.2), (59.8, 22.5), (54.1, 17.0),
        (45.0, 12.8), (43.4, 12.7), (39.2, 21.5), (34.9, 29.5),
        (34.2, 27.8), (32.5, 29.9), (32.3, 31.2), (34.7, 32.0),
        (36.1, 36.6), (30.7, 36.8), (27.1, 38.4), (29.0, 41.2),
        (36.3, 41.3), (41.6, 41.6), (39.7, 43.6), (36.5, 45.3),
        (30.7, 46.4), (28.7, 44.2), (29.0, 41.0), (26.0, 40.4),
        (23.7, 37.9), (22.4, 36.4), (19.4, 41.3), (13.8, 45.6),
        (12.3, 45.4), (13.5, 43.6), (16.9, 41.1), (15.7, 38.0),
        (12.3, 41.7), (8.9, 44.4), (5.4, 43.3), (2.2, 41.4),
        (-0.3, 39.5), (-4.4, 36.7),
    ],
    "africa": [
        (32.5, 29.9), (32.3, 31.3), (29.9, 31.2), (25.2, 31.6),
        (20.1, 32.1), (13.2, 32.9), (10.2, 36.8), (3.0, 36.8),
        (-5.8, 35.8), (-7.6, 33.6), (-13.0, 27.5), (-16.8, 21.0),
        (-17.5, 14.7), (-13.7, 9.5), (-10.8, 6.3), (-7.7, 4.4),
        (-4.0, 5.3), (3.4, 6.4), (6.0, 4.3), (9.7, 4.0),
        (9.4, 0.4), (12.3, -6.0), (13.2, -8.8), (12.2, -15.5),
        (14.5, -22.9), (18.4, -34.0), (20.0, -34.8), (25.6, -34.0),
        (31.0, -29.9), (32.6, -25.9), (35.5, -23.8), (34.8, -19.8),
        (40.7, -14.5), (39.3, -6.8), (39.7, -4.0), (45.3, 2.0),
        (51.3, 11.9), (43.1, 11.6), (39.5, 15.6), (37.2, 19.6),
        (33.8, 27.2),
    ],
    "madagascar": [(49.3, -12.0), (50.4, -15.5), (47.5, -25.0), (45.0, -25.6), (43.3, -23.3), (44.4, -18.0)],
    "sri_lanka": [(80.0, 9.6), (81.8, 7.6), (80.5, 6.0), (79.8, 7.5)],
    "sicily": [(12.4, 37.8), (15.6, 38.2), (15.1, 36.7), (13.2, 37.2)],
    "cyprus": [(32.3, 35.1), (34.6, 35.7), (34.0, 35.0), (32.6, 34.7)],
    "honshu": [(130.0, 31.3), (130.8, 33.9), (135.5, 34.4), (139.8, 35.4), (141.0, 38.3), (141.3, 41.3), (139.9, 40.5), (136.5, 36.8), (132.0, 34.5)],
    "hokkaido": [(140.0, 41.5), (141.6, 45.4), (145.4, 43.3), (143.2, 42.0), (140.8, 42.3)],
    "taiwan": [(121.5, 25.2), (121.6, 23.0), (120.8, 21.9), (120.1, 23.2), (120.9, 24.8)],
    "philippines": [(120.0, 18.5), (122.3, 16.5), (124.0, 12.8), (126.2, 8.2), (125.5, 5.8), (122.0, 6.9), (121.0, 14.2)],
    "sumatra": [(95.3, 5.5), (99.5, 3.0), (104.5, -2.5), (105.8, -5.9), (102.0, -4.0), (97.5, 1.5)],
    "java": [(105.4, -6.1), (114.4, -7.8), (114.0, -8.7), (106.5, -7.2)],
    "borneo": [(109.2, 1.6), (117.0, 6.8), (118.9, 5.2), (117.5, -1.0), (114.5, -3.7), (110.2, -3.0)],
    "sulawesi": [(119.3, 1.0), (125.0, 1.5), (122.8, -4.8), (119.5, -5.5), (119.0, -2.0)],
    "new_guinea": [(131.0, -1.5), (141.0, -2.6), (150.5, -10.3), (145.0, -8.2), (138.0, -8.2), (132.5, -4.0)],
    "australia": [
        (129.0, -14.5), (136.8, -12.2), (136.0, -15.5), (141.0, -17.5),
        (142.5, -10.7), (146.0, -18.0), (153.5, -28.0), (151.3, -33.9),
        (149.9, -37.5), (144.8, -38.4), (138.5, -35.0), (135.5, -34.8),
        (129.0, -31.8), (121.9, -33.9), (115.1, -34.3), (114.1, -22.0),
        (122.2, -18.0),
    ],
    "tasmania": [(144.8, -40.7), (148.3, -41.0), (147.3, -43.4), (145.4, -42.5)],
    "nz_north": [(172.7, -34.5), (178.5, -37.7), (175.3, -41.4), (174.0, -39.1), (174.7, -36.8)],
    "nz_south": [(172.8, -40.6), (174.2, -41.7), (170.5, -45.9), (166.5, -46.1), (168.5, -43.5)],
}

LEAD_CARDS = [
    # Row 1 (#1 - #3)
    {
        "id": 1,
        "row": 1,
        "region": "APAC",
        "beat": "ASIA-PACIFIC · APEC SUMMIT",
        "source": "REUTERS · AP",
        "headline": "Xi greets Trump in Shenzhen on eve of Trump–Xi–Putin summit",
        "summary": "China's leader welcomes Trump at the airport and calls for open WTO trade and AI cooperation as APEC opens; Putin joins banquet ahead of Thursday's trilateral.",
        "lat": 22.5,
        "lon": 114.1,
        "scene": "apec",
    },
    {
        "id": 2,
        "row": 1,
        "region": "MENA",
        "beat": "MIDDLE EAST · GULF ESCALATION",
        "source": "AL JAZEERA · CENTCOM",
        "headline": "Kuwait and Bahrain intercept Iranian drones after US hits Qeshm",
        "summary": "Iran says it targeted Ali Al Salem base and Bahrain radar after US jets struck an IRGC missile site on Qeshm Island; an ADNOC tanker is hit in Hormuz (1 missing).",
        "lat": 27.5,
        "lon": 52.0,
        "scene": "gulf",
    },
    {
        "id": 3,
        "row": 1,
        "region": "GLOBAL",
        "beat": "SPACE · HISTORIC MILESTONE",
        "source": "NASA · JPL",
        "headline": "Voyager 1 is the first craft one light-day from Earth",
        "summary": "NASA's probe passes 25.9 billion km (16.1B miles) away in interstellar space, a record for any human-made object: a radio command sent today takes 24 hours to arrive.",
        "lat": 34.2,
        "lon": -118.2,
        "scene": "voyager",
    },
    # Row 2 (#4 - #8)
    {
        "id": 4,
        "row": 2,
        "region": "AMERICAS",
        "beat": "AMERICAS · US POLITICS",
        "source": "AP",
        "headline": "Democrat Peltola wins Alaska; Senate now 56–44",
        "summary": "Mary Peltola beats Dan Sullivan 144,302 to 131,844 in ranked-choice tabulation, widening Democrats' Senate edge.",
        "lat": 61.2,
        "lon": -149.9,
        "scene": "alaska",
    },
    {
        "id": 5,
        "row": 2,
        "region": "EUROPE",
        "beat": "EUROPE · UKRAINE WAR",
        "source": "EU · KYIV",
        "headline": "EU proposes €45bn loan; Russia fires 141 drones",
        "summary": "Loan backed by Russian assets moves forward as Kyiv says 126 drones were downed; deadly strikes hit Odesa.",
        "lat": 48.5,
        "lon": 18.0,
        "scene": "ukraine",
    },
    {
        "id": 6,
        "row": 2,
        "region": "APAC",
        "beat": "ASIA · DISASTER",
        "source": "IMD",
        "headline": "Cyclone Akvan strengthens in the Bay of Bengal",
        "summary": "Storm intensifies toward 145 km/h landfall; Andhra Pradesh and Odisha ready 204,000 people for evacuation.",
        "lat": 16.5,
        "lon": 84.5,
        "scene": "cyclone",
    },
    {
        "id": 7,
        "row": 2,
        "region": "EUROPE",
        "beat": "EUROPE · ECONOMY",
        "source": "ONS",
        "headline": "UK inflation rises to 3.6%, highest in a year",
        "summary": "Rising fuel prices push October CPI up from 3.5% in September while Bank of England holds rate at 4.0%.",
        "lat": 51.5,
        "lon": -0.1,
        "scene": "uk_cpi",
    },
    {
        "id": 8,
        "row": 2,
        "region": "AFRICA",
        "beat": "AFRICA · SUDAN WAR",
        "source": "AMNESTY · UN",
        "headline": "Amnesty: RSF drone strikes killed 37 in El Obeid",
        "summary": "Group urges war-crimes inquiry as UN counts 2,230 civilians killed in Sudan in 2026; RSF denies strike claims.",
        "lat": 13.2,
        "lon": 30.2,
        "scene": "sudan",
    },
    # Row 3 (#9 - #13)
    {
        "id": 9,
        "row": 3,
        "region": "AMERICAS",
        "beat": "AMERICAS · TECH & SECURITY",
        "source": "CNBC · CISA",
        "headline": "Nvidia Q3 hits $115.8bn; CISA flags Java4Shell",
        "summary": "Data-center sales double (+103% YoY), board rules out Huang return; CISA warns on flaw CVE-2026-114938.",
        "lat": 37.4,
        "lon": -121.9,
        "scene": "nvidia_cisa",
    },
    {
        "id": 10,
        "row": 3,
        "region": "GLOBAL",
        "beat": "GLOBAL · COP31 CLIMATE",
        "source": "ANADOLU · UN",
        "headline": "COP31 splits on fossil phase-out; 75 back '35x35'",
        "summary": "Antalya ministers weigh divided draft as 75 nations back Türkiye's target of 35% clean electricity by 2035.",
        "lat": 36.9,
        "lon": 30.7,
        "scene": "cop31",
    },
    {
        "id": 11,
        "row": 3,
        "region": "MENA",
        "beat": "MIDDLE EAST · GAZA",
        "source": "AP · WHO",
        "headline": "Board of Peace warns UN Gaza truce may collapse",
        "summary": "Report faults ceasefire breaches as tanks advance into central Gaza and heavy rains flood displaced camps.",
        "lat": 31.4,
        "lon": 34.4,
        "scene": "gaza",
    },
    {
        "id": 12,
        "row": 3,
        "region": "GLOBAL",
        "beat": "GLOBAL · CULTURE",
        "source": "SENSOR TOWER",
        "headline": "Grand Theft Auto VI goes on sale after 13-year wait",
        "summary": "Midnight rollout starts in New Zealand across time zones; Sensor Tower estimates 15m pre-orders (~$1.45bn).",
        "lat": -36.8,
        "lon": 174.8,
        "scene": "gtavi",
    },
    {
        "id": 13,
        "row": 3,
        "region": "APAC",
        "beat": "ASIA & OCEANIA · LABOUR",
        "source": "REUTERS",
        "headline": "Bangladesh garment protests shut 55 factories",
        "summary": "Dhaka highway blocked in Tk 30,000 wage demand; separately, Australia sanctions settler leader Daniella Weiss.",
        "lat": 23.8,
        "lon": 90.4,
        "scene": "garment",
    },
]

BRIEF_ITEMS = [
    {"id": 14, "region": "AFRICA", "lead": "Abuja:", "text": "Nigeria Senate advances constitutional bill to establish state police", "lat": 9.1, "lon": 7.5},
    {"id": 15, "region": "AFRICA", "lead": "Lake Chad:", "text": "Nigeria, Chad, Cameroon & Niger sign 5 km cross-border terror pact", "lat": 13.0, "lon": 14.0},
    {"id": 16, "region": "AFRICA", "lead": "Pretoria:", "text": "South Africa reprimands Nigerian envoy; US ends SA & Rwanda AGOA Jan 2027", "lat": -25.7, "lon": 28.2},
    {"id": 17, "region": "AFRICA", "lead": "Kinshasa:", "text": "WHO & DRC launch Tumaini Ebola vaccine trial as cases top 11,300", "lat": -4.3, "lon": 15.3},
    {"id": 18, "region": "AFRICA", "lead": "Dakar:", "text": "Senegal ruling Pastef party expels Pres. Faye & 31 allies in Sonko split", "lat": 14.7, "lon": -17.5},
    {"id": 19, "region": "AFRICA", "lead": "Nairobi:", "text": "Kenya and EU seal data adequacy pact as Pres. Ruto delivers state address", "lat": -1.3, "lon": 36.8},
    {"id": 20, "region": "AFRICA", "lead": "Horn of Africa:", "text": "Ethiopia and Eritrea mass troops along border within striking distance", "lat": 14.5, "lon": 38.8},
    {"id": 21, "region": "AFRICA", "lead": "Conakry:", "text": "Guinea courts sentence 224 people in crackdown on illegal gold mining", "lat": 9.5, "lon": -13.7},
    {"id": 22, "region": "MENA", "lead": "Jerusalem:", "text": "Knesset elects Matan Kahana speaker 66–52 and backs media-law repeal", "lat": 31.8, "lon": 35.2},
    {"id": 23, "region": "MENA", "lead": "Riyadh:", "text": "Saudi-led coalition downs Houthi cruise missile and 2 Aden drones", "lat": 24.7, "lon": 46.7},
    {"id": 24, "region": "MENA", "lead": "Cairo:", "text": "IMF and Egypt reach staff-level agreement on 8th EFF economic review", "lat": 30.0, "lon": 31.2},
    {"id": 25, "region": "EUROPE", "lead": "Berlin:", "text": "E5 defense ministers prep Ukraine talks; Germany cuts power tax & caps fuel", "lat": 52.5, "lon": 13.4},
    {"id": 26, "region": "EUROPE", "lead": "Rome:", "text": "Italy backs E5 diplomacy but rules out sending troops to Ukraine", "lat": 41.9, "lon": 12.5},
    {"id": 27, "region": "EUROPE", "lead": "Frankfurt:", "text": "Eurozone Oct CPI hits 4.0%; EU forecasts 1.4% GDP growth", "lat": 50.1, "lon": 8.7},
    {"id": 28, "region": "EUROPE", "lead": "Cambridge:", "text": "Cambridge Dictionary names \"human\" as its 2026 Word of the Year", "lat": 52.2, "lon": 0.1},
    {"id": 29, "region": "EUROPE", "lead": "Kemerovo:", "text": "Russian An-12 transport plane crash in Siberia kills all 19 aboard", "lat": 55.3, "lon": 86.1},
    {"id": 30, "region": "APAC", "lead": "Tokyo:", "text": "PM Takaichi proposes 'Asian IEA' oil reserve pact; jets scramble", "lat": 35.7, "lon": 139.7},
    {"id": 31, "region": "APAC", "lead": "Seoul:", "text": "Pres. Lee meets Xi on FTA services; court acquits Daegu mayor", "lat": 37.6, "lon": 127.0},
    {"id": 32, "region": "APAC", "lead": "Manila:", "text": "Trump hails Philippine trade talks after first Quad summit in 2 years", "lat": 14.6, "lon": 121.0},
    {"id": 33, "region": "APAC", "lead": "Jakarta:", "text": "Pres. Prabowo inks $71.8bn in China tech and smart-city commitments", "lat": -6.2, "lon": 106.8},
    {"id": 34, "region": "APAC", "lead": "Kuala Lumpur:", "text": "Malaysia Q3 GDP grows 5.5% YoY on strong tech exports", "lat": 3.1, "lon": 101.7},
    {"id": 35, "region": "APAC", "lead": "New Delhi:", "text": "Modi hosts UK royals; India approves H5N1 poultry vaccine trial", "lat": 28.6, "lon": 77.2},
    {"id": 36, "region": "APAC", "lead": "Sydney:", "text": "World-first kids mRNA brain cancer trial begins; Tame Impala sweeps ARIAs", "lat": -33.9, "lon": 151.2},
    {"id": 37, "region": "APAC", "lead": "Cook Islands:", "text": "Cyclone Xavier reaches Category 5; New Zealand lifts tsunami advisory", "lat": -21.2, "lon": -159.8},
    {"id": 38, "region": "AMERICAS", "lead": "Ottawa:", "text": "PM Carney renews China currency swap and cuts pork/seafood tariffs", "lat": 45.4, "lon": -75.7},
    {"id": 39, "region": "AMERICAS", "lead": "Washington:", "text": "NSA confirms outage on classified NSANet; Rubio cites maintenance", "lat": 38.9, "lon": -77.0},
    {"id": 40, "region": "AMERICAS", "lead": "Washington:", "text": "PAHO revokes measles-free status for US, Mexico, and Bolivia", "lat": 19.4, "lon": -99.1},
    {"id": 41, "region": "AMERICAS", "lead": "Panama City:", "text": "Darién Gap migrant crossings plunge 90% YoY as flows shift south", "lat": 8.9, "lon": -79.5},
    {"id": 42, "region": "GLOBAL", "lead": "New York:", "text": "Wall Street slides (Dow -849, S&P ~7,341); Bitcoin dips near $64,000", "lat": 40.7, "lon": -74.0},
    {"id": 43, "region": "GLOBAL", "lead": "San Francisco:", "text": "Anthropic prices IPO for Thursday trading; Optimizely breach hits 178 firms", "lat": 37.8, "lon": -122.4},
    {"id": 44, "region": "AMERICAS", "lead": "Lima & Bogotá:", "text": "Peru M5.9 quake & Tumbes flood alert; Colombia Q3 GDP shrinks 0.8%", "lat": -12.0, "lon": -77.0},
    {"id": 45, "region": "GLOBAL", "lead": "Zurich:", "text": "France's Diallo announces bid to challenge Infantino for FIFA presidency", "lat": 47.4, "lon": 8.5},
]

NUMBER_KPIS = [
    {"value": "$115.8bn", "label": "Nvidia Q3 FY27 (+103% YoY)", "hex": "#0369A1"},
    {"value": "$3,780/oz", "label": "Gold spot (-2.0% on USD)", "hex": "#B45309"},
    {"value": "$91.70/bbl", "label": "Brent crude (-1.2% on stocks)", "hex": "#B91C1C"},
    {"value": "25.9bn km", "label": "Voyager 1 (1 light-day away)", "hex": "#6D28D9"},
]

ATTESTATION_TEXT = (
    "Every story happened, or was first reported, on Wednesday 18 November 2026; "
    "disputed claims by warring sides are attributed.  |  "
    "Sources: Reuters, AP, AFP, BBC, Al Jazeera, CNBC, ONS, IMD, NASA, UN, WHO, Amnesty. Original drawings."
)


def copy_prebuilt_png() -> Path:
    """Copy pre-rendered entry.png to MAKEFUN_OUTPUT_DIR using Python stdlib only."""
    src_path = Path(__file__).resolve().parent / "entry.png"
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dst_path = out_dir / "entry.png"
    shutil.copyfile(src_path, dst_path)
    return dst_path


def rgb_from_hex(code: str) -> tuple[int, int, int]:
    """Parse a #RRGGBB hex color into an RGB tuple."""
    clean = code.lstrip("#")
    return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def mix_rgb(
    c1: tuple[int, int, int], c2: tuple[int, int, int], ratio: float
) -> tuple[int, int, int]:
    """Blend two RGB colors linearly; ratio=1.0 yields c2."""
    inv = 1.0 - ratio
    return (
        int(round(c1[0] * inv + c2[0] * ratio)),
        int(round(c1[1] * inv + c2[1] * ratio)),
        int(round(c1[2] * inv + c2[2] * ratio)),
    )


def resolve_font_path(candidates: tuple[str, ...]) -> str:
    """Locate the first available TTF font file from candidate filenames."""
    for fname in candidates:
        for base in FONT_DIRS:
            p = Path(base) / fname
            if p.is_file():
                return str(p)
    for fname in candidates:
        for base in FONT_DIRS:
            bp = Path(base)
            if bp.is_dir():
                for found in bp.rglob(fname):
                    if found.is_file():
                        return str(found)
    raise FileNotFoundError(f"None of fonts found: {candidates}")


def build_font_getter(image_font_mod):
    """Create a cached TrueType font accessor keyed by (role, pixel_size)."""
    resolved = {role: resolve_font_path(cands) for role, cands in FONT_SPECS.items()}
    cache: dict[tuple[str, int], object] = {}

    def get_font(role: str, size: int):
        key = (role, size)
        if key not in cache:
            cache[key] = image_font_mod.truetype(resolved[role], size=size)
        return cache[key]

    return get_font


def fit_single_line_font(
    draw, get_font, role: str, text: str, max_w: int, start_sz: int, min_sz: int
):
    """Shrink font size until single-line text fits inside max_w cleanly."""
    for sz in range(start_sz, min_sz - 1, -1):
        font = get_font(role, sz)
        if draw.textlength(text, font=font) <= max_w:
            return font, sz
    return get_font(role, min_sz), min_sz


def wrap_lines_to_box(
    draw,
    get_font,
    role: str,
    text: str,
    max_w: int,
    max_h: int,
    start_sz: int,
    min_sz: int,
    line_gap: int = 4,
):
    """Word-wrap text and pick the largest font size that fits inside max_w x max_h."""
    words = text.split()
    for sz in range(start_sz, min_sz - 1, -1):
        font = get_font(role, sz)
        ascent, descent = font.getmetrics()
        line_h = ascent + descent + line_gap
        lines: list[str] = []
        cur = ""
        fits_width = True
        for w in words:
            if draw.textlength(w, font=font) > max_w:
                fits_width = False
                break
            cand = w if not cur else f"{cur} {w}"
            if draw.textlength(cand, font=font) <= max_w:
                cur = cand
            else:
                lines.append(cur)
                cur = w
        if not fits_width:
            continue
        if cur:
            lines.append(cur)
        total_h = len(lines) * line_h - line_gap if lines else 0
        if total_h <= max_h:
            return font, lines, line_h
    font = get_font(role, min_sz)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + line_gap
    lines = []
    cur = ""
    for w in words:
        cand = w if not cur else f"{cur} {w}"
        if draw.textlength(cand, font=font) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return font, lines, line_h


def draw_centered(draw, cx: float, cy: float, text: str, font, fill) -> None:
    """Draw text centered optically around (cx, cy) via textbbox metrics."""
    bx0, by0, bx1, by1 = draw.textbbox((0, 0), text, font=font)
    tx = cx - (bx0 + bx1) / 2.0
    ty = cy - (by0 + by1) / 2.0
    draw.text((tx, ty), text, font=font, fill=fill)


def draw_badge_circle(
    draw,
    cx: float,
    cy: float,
    radius: float,
    label: str,
    fill_rgb: tuple[int, int, int],
    text_rgb: tuple[int, int, int],
    font,
    ring_rgb: tuple[int, int, int] | None = None,
) -> None:
    """Draw a crisp circular numbered badge with optional outer border."""
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=fill_rgb,
        outline=ring_rgb,
        width=2 if ring_rgb is not None else 0,
    )
    draw_centered(draw, cx, cy, label, font, text_rgb)


def draw_broadsheet_masthead(draw, get_font) -> None:
    """Render the navy broadsheet masthead, red calendar block, and 6-region bar."""
    draw.rectangle((0, MASTHEAD_TOP, SUPERSAMPLE_W, GOLD_RULE_TOP), fill=MASTHEAD_NAVY)
    draw.rectangle((0, GOLD_RULE_TOP, SUPERSAMPLE_W, NAV_BAR_TOP), fill=GOLD_ACCENT)
    draw.rectangle((0, NAV_BAR_TOP, SUPERSAMPLE_W, MASTHEAD_BOT), fill=PAPER_WARM_ALT)
    draw.line((0, MASTHEAD_BOT, SUPERSAMPLE_W, MASTHEAD_BOT), fill=RULE_BORDER, width=2)

    # Red calendar tile (x=28..156, y=13..137)
    tx0, ty0, tx1, ty1 = PAGE_MARGIN_X, 13, PAGE_MARGIN_X + 128, 137
    draw.rectangle((tx0, ty0, tx1, ty0 + 30), fill=CALENDAR_CRIMSON)
    draw.rectangle((tx0, ty0 + 30, tx1, ty0 + 94), fill=(255, 255, 255))
    draw.rectangle((tx0, ty0 + 94, tx1, ty1), fill=CALENDAR_SLATE)
    draw.rectangle((tx0, ty0, tx1, ty1), outline=(232, 224, 208), width=2)

    cal_mon_font = get_font("cond_bold", 21)
    cal_day_font = get_font("serif_bold", 54)
    cal_yr_font = get_font("cond_bold", 16)
    draw_centered(draw, (tx0 + tx1) / 2.0, ty0 + 15, "NOV", cal_mon_font, (255, 255, 255))
    draw_centered(draw, (tx0 + tx1) / 2.0, ty0 + 61, "18", cal_day_font, MASTHEAD_NAVY)
    draw_centered(draw, (tx0 + tx1) / 2.0, ty0 + 109, "WED · 2026", cal_yr_font, (241, 245, 249))

    # Kicker row & right stats
    text_x0 = tx1 + 24
    right_x = SUPERSAMPLE_W - PAGE_MARGIN_X
    kicker_font = get_font("cond_bold", 21)
    stats_font = get_font("cond_bold", 20)
    draw.text((text_x0, 12), "THE DAY IN WORLD NEWS", font=kicker_font, fill=GOLD_BRIGHT)
    stats_txt = "45 STORIES  ·  6 CONTINENTS  ·  ONE FRONT PAGE"
    sw = draw.textlength(stats_txt, font=stats_font)
    draw.text((right_x - sw, 13), stats_txt, font=stats_font, fill=(203, 213, 225))

    # Main masthead serif title
    mast_title = "Wednesday 18 November 2026"
    mast_font, _ = fit_single_line_font(
        draw, get_font, "serif_bold", mast_title, right_x - text_x0, 82, 54
    )
    draw.text((text_x0, 31), mast_title, font=mast_font, fill=(255, 255, 255))

    # Italic subtitle
    sub_txt = "Every story on this page happened, or was first reported, on Wednesday 18 November 2026."
    sub_font, _ = fit_single_line_font(
        draw, get_font, "serif_italic", sub_txt, right_x - text_x0, 22, 16
    )
    draw.text((text_x0 + 2, 117), sub_txt, font=sub_font, fill=(226, 232, 240))

    # Slim 6-region color bar
    n_reg = len(REGION_PALETTE)
    seg_w = PAGE_WIDTH / n_reg
    bar_font = get_font("cond_bold", 16)
    mid_y = (NAV_BAR_TOP + MASTHEAD_BOT) / 2.0
    for idx, reg in enumerate(REGION_PALETTE):
        sx0 = PAGE_MARGIN_X + idx * seg_w
        sx1 = sx0 + seg_w
        cx = (sx0 + sx1) / 2.0
        col = rgb_from_hex(reg["hex"])
        label = reg["name"]
        lw = draw.textlength(label, font=bar_font)
        total_w = 18 + lw
        start_x = cx - total_w / 2.0
        draw.ellipse((start_x, mid_y - 6, start_x + 12, mid_y + 6), fill=col)
        draw_centered(draw, start_x + 18 + lw / 2.0, mid_y, label, bar_font, INK_PRIMARY)
        if idx > 0:
            draw.line(
                (sx0, NAV_BAR_TOP + 6, sx0, MASTHEAD_BOT - 6),
                fill=RULE_BORDER,
                width=2,
            )


def draw_scene_apec(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #1: Shenzhen skyline, presidential jet on red carpet, and 3-way summit flags."""
    sc = image_cls.new("RGB", (w, h), (254, 243, 199))
    d = draw_cls.Draw(sc)
    d.rectangle((0, 0, w, 78), fill=(253, 230, 138))

    # Shenzhen skyline silhouettes on right
    towers = [
        (256, 66, 294, 138, (203, 213, 225)),
        (298, 46, 342, 138, (148, 163, 184)),
        (348, 76, 386, 138, (203, 213, 225)),
        (392, 36, 428, 138, (148, 163, 184)),
        (468, 50, 512, 138, (203, 213, 225)),
        (518, 60, 560, 138, (148, 163, 184)),
        (566, 78, 608, 138, (203, 213, 225)),
    ]
    for x0, y0, x1, y1, col in towers:
        d.rectangle((x0, y0, x1, y1), fill=col)
    # Tapered Ping An spire
    d.polygon([(434, 138), (444, 24), (450, 8), (456, 24), (466, 138)], fill=(100, 116, 139))

    # Tarmac & red welcome carpet
    d.rectangle((0, 136, w, 174), fill=(226, 232, 240))
    d.line((0, 136, w, 136), fill=(100, 116, 139), width=2)
    d.polygon([(142, 138), (274, 138), (294, 166), (128, 166)], fill=(220, 38, 38))

    # Presidential jet on left
    d.polygon([(28, 106), (18, 62), (44, 62), (62, 106)], fill=(30, 58, 138))
    d.rectangle((36, 100, 206, 124), fill=(255, 255, 255), outline=(30, 58, 138), width=2)
    d.polygon([(206, 100), (234, 115), (206, 124)], fill=(255, 255, 255), outline=(30, 58, 138))
    d.line((38, 112, 218, 112), fill=(30, 58, 138), width=3)
    d.polygon([(94, 116), (72, 134), (122, 134), (132, 116)], fill=(148, 163, 184))
    d.line((158, 124, 158, 138), fill=(30, 41, 59), width=3)
    d.line((90, 124, 90, 138), fill=(30, 41, 59), width=3)
    d.line((170, 118, 150, 140), fill=(71, 85, 105), width=3)

    # Summit table with 3 mini flags (China, USA, Russia)
    d.rectangle((328, 132, 578, 164), fill=(146, 64, 14), outline=(120, 53, 15), width=2)
    d.rectangle((334, 128, 572, 134), fill=(217, 119, 6))

    # China flag
    d.line((374, 78, 374, 128), fill=(51, 65, 85), width=3)
    d.rectangle((376, 78, 424, 108), fill=(220, 38, 38), outline=(153, 27, 27), width=1)
    d.ellipse((382, 83, 392, 93), fill=(250, 204, 21))

    # USA flag
    d.line((454, 78, 454, 128), fill=(51, 65, 85), width=3)
    d.rectangle((456, 78, 504, 108), fill=(255, 255, 255), outline=(148, 163, 184), width=1)
    for sy in range(78, 108, 6):
        d.rectangle((456, sy, 504, min(sy + 3, 108)), fill=(220, 38, 38))
    d.rectangle((456, 78, 476, 94), fill=(30, 58, 138))

    # Russia flag
    d.line((534, 78, 534, 128), fill=(51, 65, 85), width=3)
    d.rectangle((536, 78, 584, 88), fill=(255, 255, 255))
    d.rectangle((536, 88, 584, 98), fill=(29, 78, 216))
    d.rectangle((536, 98, 584, 108), fill=(220, 38, 38))
    d.rectangle((536, 78, 584, 108), outline=(148, 163, 184), width=1)

    # Bottom banner
    d.rectangle((0, 174, w, h), fill=MASTHEAD_NAVY)
    draw_centered(d, w / 2.0, 191, "SHENZHEN  ·  3-WAY TALKS THU", get_font("cond_bold", 17), (253, 224, 71))
    return sc


def draw_starburst(draw, cx: float, cy: float, r_out: float, r_in: float, pts_n: int, fill, outline) -> None:
    """Draw a crisp polygonal starburst marker for strikes and interceptions."""
    verts = []
    for i in range(pts_n * 2):
        ang = i * math.pi / pts_n
        r = r_out if i % 2 == 0 else r_in
        verts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(verts, fill=fill, outline=outline)


def draw_dashed_line(draw, x0: float, y0: float, x1: float, y1: float, fill, width: int = 3, dash: int = 10) -> None:
    """Draw a crisp dashed line segment between two points."""
    dist = math.hypot(x1 - x0, y1 - y0)
    if dist < 1:
        return
    steps = max(1, int(dist // (dash * 1.8)))
    for i in range(steps):
        t0 = i / steps
        t1 = min(1.0, (i + 0.58) / steps)
        draw.line(
            (x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0, x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1),
            fill=fill,
            width=width,
        )


def draw_scene_gulf(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #2: Tactical Gulf map with Qeshm strike, Kuwait/Bahrain intercepts, and Hormuz tanker."""
    sc = image_cls.new("RGB", (w, h), (207, 226, 243))
    d = draw_cls.Draw(sc)

    land_fill = (232, 223, 206)
    land_edge = (168, 155, 132)
    d.polygon(
        [(135, 0), (w, 0), (w, 120), (565, 114), (520, 126), (475, 122), (430, 100), (360, 86), (285, 66), (210, 44), (155, 20)],
        fill=land_fill,
        outline=land_edge,
    )
    d.polygon(
        [(0, 0), (135, 0), (150, 28), (118, 58), (96, 92), (72, 116), (0, 126)],
        fill=land_fill,
        outline=land_edge,
    )
    d.polygon(
        [(0, 126), (95, 122), (155, 140), (190, 156), (225, 162), (242, 138), (264, 168), (355, 172), (455, 150), (495, 142), (508, 162), (550, h), (0, h)],
        fill=land_fill,
        outline=land_edge,
    )
    # Qeshm Island
    d.polygon([(444, 116), (484, 108), (492, 116), (454, 126)], fill=(254, 215, 170), outline=(185, 28, 28))
    # Bahrain island
    d.ellipse((178, 122, 192, 136), fill=(254, 215, 170), outline=(185, 28, 28), width=2)

    lbl_font = get_font("cond_bold", 15)
    d.text((16, 50), "KUWAIT", font=lbl_font, fill=INK_PRIMARY)
    d.text((384, 26), "IRAN", font=lbl_font, fill=INK_PRIMARY)
    d.text((156, 144), "BAHRAIN", font=lbl_font, fill=INK_PRIMARY)
    d.text((438, 84), "QESHM", font=lbl_font, fill=(153, 27, 27))
    d.text((542, 122), "HORMUZ", font=lbl_font, fill=INK_BODY)

    # Drone trajectories and intercept bursts
    draw_dashed_line(d, 315, 76, 102, 72, (220, 38, 38), width=3, dash=9)
    draw_dashed_line(d, 342, 82, 194, 122, (220, 38, 38), width=3, dash=9)
    draw_starburst(d, 122, 72, 14, 6, 7, (250, 204, 21), (185, 28, 28))
    draw_starburst(d, 212, 116, 14, 6, 7, (250, 204, 21), (185, 28, 28))

    # US Strike at Qeshm
    draw_starburst(d, 468, 116, 15, 6, 8, (220, 38, 38), (127, 29, 29))
    d.rounded_rectangle((354, 122, 444, 144), radius=4, fill=(185, 28, 28))
    draw_centered(d, 399, 133, "US STRIKE", get_font("cond_bold", 13), (255, 255, 255))

    # Intercept pill
    d.rounded_rectangle((132, 22, 292, 46), radius=4, fill=MASTHEAD_NAVY)
    draw_centered(d, 212, 34, "DRONES INTERCEPTED", get_font("cond_bold", 13), (253, 224, 71))

    # Tanker in Strait of Hormuz
    d.polygon([(504, 148), (546, 148), (540, 158), (508, 158)], fill=(30, 41, 59))
    d.rectangle((514, 140, 526, 148), fill=(220, 38, 38))
    d.rounded_rectangle((464, 172, 616, 196), radius=4, fill=(153, 27, 27))
    draw_centered(d, 540, 184, "TANKER HIT · 1 MISSING", get_font("cond_bold", 13), (255, 255, 255))
    return sc


def draw_scene_voyager(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #3: Deep space Voyager 1 at 1 light-day (25.9B km) from Earth."""
    sc = image_cls.new("RGB", (w, h), (11, 19, 43))
    d = draw_cls.Draw(sc)

    for i in range(72):
        sx = (i * 97 + 19) % w
        sy = (i * 53 + 11) % (h - 36)
        sr = 2 if i % 7 == 0 else 1
        scol = (253, 224, 71) if i % 5 == 0 else (226, 232, 240)
        d.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=scol)

    # Earth on left
    ex, ey, er = 78, 94, 32
    d.ellipse((ex - er - 4, ey - er - 4, ex + er + 4, ey + er + 4), outline=(56, 189, 248), width=2)
    d.ellipse((ex - er, ey - er, ex + er, ey + er), fill=(29, 78, 216))
    d.polygon([(62, 74), (86, 76), (82, 100), (66, 106)], fill=(34, 197, 94))
    d.polygon([(90, 82), (106, 90), (96, 110), (84, 104)], fill=(34, 197, 94))
    draw_centered(d, ex, 144, "EARTH", get_font("cond_bold", 16), (147, 197, 253))

    # Signal dashed arc
    draw_dashed_line(d, 120, 94, 488, 94, (250, 204, 21), width=3, dash=12)
    d.polygon([(488, 88), (502, 94), (488, 100)], fill=(250, 204, 21))
    draw_centered(d, 304, 58, "1 LIGHT-DAY  ·  24H RADIO SIGNAL", get_font("cond_bold", 19), (253, 224, 71))
    draw_centered(d, 304, 124, "25.9 BILLION KM (16.1B MI)", get_font("sans_bold", 17), (226, 232, 240))

    # Voyager 1 probe on right
    vx, vy = 534, 92
    d.line((vx, vy, 602, 38), fill=(203, 213, 225), width=3)
    d.line((vx, vy, 596, 138), fill=(148, 163, 184), width=3)
    d.ellipse((vx - 28, vy - 20, vx + 10, vy + 20), fill=(248, 250, 252), outline=(148, 163, 184), width=2)
    d.ellipse((vx - 20, vy - 12, vx + 2, vy + 12), outline=(148, 163, 184), width=1)
    d.rectangle((vx + 2, vy - 10, vx + 24, vy + 10), fill=(217, 119, 6))
    d.line((vx - 8, vy, vx - 28, vy - 16), fill=(51, 65, 85), width=2)
    d.line((vx - 8, vy, vx - 28, vy + 16), fill=(51, 65, 85), width=2)
    draw_centered(d, 544, 144, "VOYAGER 1", get_font("cond_bold", 16), (253, 224, 71))

    d.rectangle((0, 174, w, h), fill=(15, 23, 42))
    d.line((0, 174, w, 174), fill=(51, 65, 85), width=2)
    draw_centered(d, w / 2.0, 191, "INTERSTELLAR SPACE  ·  NASA HISTORIC FIRST", get_font("cond_bold", 16), (192, 132, 252))
    return sc


def draw_scene_alaska(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #4: Capitol dome, Alaska state silhouette, and 56-44 Senate majority bar."""
    sc = image_cls.new("RGB", (w, h), (224, 242, 254))
    d = draw_cls.Draw(sc)

    # US Capitol silhouette on left
    d.rectangle((20, 96, 98, 132), fill=(30, 58, 138))
    d.rectangle((36, 74, 82, 96), fill=(30, 58, 138))
    d.chord((38, 36, 80, 78), start=180, end=360, fill=(30, 58, 138))
    d.rectangle((56, 22, 62, 38), fill=(30, 58, 138))
    for px in range(28, 92, 12):
        d.line((px, 98, px, 130), fill=(224, 242, 254), width=2)

    # Alaska state silhouette
    ak = [(126, 28), (178, 24), (178, 72), (198, 92), (186, 92), (168, 74), (144, 80), (118, 98), (108, 90), (124, 72), (114, 50)]
    d.polygon(ak, fill=(3, 105, 161), outline=(12, 74, 110))
    draw_centered(d, 150, 118, "ALASKA", get_font("cond_bold", 16), (12, 74, 110))

    # 56-44 Senate seat chart on right
    draw_centered(d, 282, 28, "SENATE  56–44", get_font("serif_bold", 22), INK_PRIMARY)
    bx0, by0, bx1, by1 = 206, 52, 356, 82
    split_x = bx0 + int(round((bx1 - bx0) * 0.56))
    d.rectangle((bx0, by0, split_x, by1), fill=(37, 99, 235))
    d.rectangle((split_x, by0, bx1, by1), fill=(220, 38, 38))
    d.rectangle((bx0, by0, bx1, by1), outline=INK_PRIMARY, width=2)
    draw_centered(d, (bx0 + split_x) / 2.0, 67, "56 DEM", get_font("cond_bold", 15), (255, 255, 255))
    draw_centered(d, (split_x + bx1) / 2.0, 67, "44 REP", get_font("cond_bold", 15), (255, 255, 255))
    d.rounded_rectangle((214, 98, 348, 128), radius=5, fill=(30, 58, 138))
    draw_centered(d, 281, 113, "PELTOLA RCV WIN", get_font("cond_bold", 15), (253, 224, 71))
    return sc


def draw_scene_ukraine(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #5: EU €45bn loan stars + drones intercepted over Ukrainian power pylon."""
    sc = image_cls.new("RGB", (w, h), (51, 65, 85))
    d = draw_cls.Draw(sc)

    # Left half: EU blue + 12 stars + €45BN
    d.rectangle((0, 0, 174, h), fill=(30, 58, 138))
    cx, cy, r = 87, 62, 41
    for i in range(12):
        ang = i * (2.0 * math.pi / 12.0)
        sx = cx + r * math.cos(ang)
        sy = cy + r * math.sin(ang)
        d.ellipse((sx - 4, sy - 4, sx + 4, sy + 4), fill=(250, 204, 21))
    draw_centered(d, cx, cy, "€45BN", get_font("serif_bold", 21), (255, 255, 255))
    d.rectangle((46, 114, 128, 124), fill=(37, 99, 235))
    d.rectangle((46, 124, 128, 134), fill=(250, 204, 21))

    # Right half: power pylon + wires + bolt + drones + intercepts
    d.line((268, 38, 244, 118), fill=(203, 213, 225), width=3)
    d.line((268, 38, 292, 118), fill=(203, 213, 225), width=3)
    d.line((236, 66, 300, 66), fill=(203, 213, 225), width=3)
    d.line((232, 88, 304, 88), fill=(203, 213, 225), width=3)
    d.line((296, 66, 367, 56), fill=(148, 163, 184), width=1)
    d.line((300, 88, 367, 78), fill=(148, 163, 184), width=1)
    d.polygon([(268, 46), (258, 68), (270, 68), (262, 88), (278, 62), (266, 62)], fill=(250, 204, 21))

    for dx, dy in [(204, 26), (324, 32)]:
        d.polygon([(dx - 16, dy), (dx + 8, dy - 6), (dx + 2, dy + 8)], fill=(15, 23, 42))
        draw_dashed_line(d, dx + 4, dy + 6, dx + 20, dy + 22, (248, 113, 113), width=2, dash=4)
    draw_starburst(d, 228, 52, 12, 5, 6, (250, 204, 21), (220, 38, 38))
    draw_starburst(d, 314, 58, 12, 5, 6, (250, 204, 21), (220, 38, 38))

    d.rounded_rectangle((192, 114, 350, 140), radius=4, fill=(185, 28, 28))
    draw_centered(d, 271, 127, "126 / 141 DOWNED", get_font("cond_bold", 15), (255, 255, 255))
    return sc


def draw_scene_cyclone(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #6: Bay of Bengal coastline + Cyclone Akvan spiral & track."""
    sc = image_cls.new("RGB", (w, h), (216, 236, 248))
    d = draw_cls.Draw(sc)

    # Indian east coast
    d.polygon(
        [(0, 0), (154, 0), (132, 34), (104, 64), (82, 96), (74, h), (0, h)],
        fill=(232, 223, 206),
        outline=(168, 155, 132),
    )
    lbl = get_font("cond_bold", 14)
    d.text((16, 24), "ODISHA", font=lbl, fill=INK_PRIMARY)
    d.text((14, 78), "ANDHRA", font=lbl, fill=INK_PRIMARY)

    # Spiral arms around eye
    cx, cy = 248, 66
    for offset in (0.0, math.pi):
        pts = []
        for t in range(36):
            ang = offset + t * 0.17
            rad = 10.0 + t * 1.5
            pts.append((cx + rad * math.cos(ang), cy + rad * 0.72 * math.sin(ang)))
        d.line(pts, fill=(15, 118, 110), width=6)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(220, 38, 38), outline=(255, 255, 255), width=2)

    draw_dashed_line(d, cx - 12, cy - 6, 126, 40, (185, 28, 28), width=3, dash=7)
    d.polygon([(120, 38), (134, 34), (130, 48)], fill=(185, 28, 28))

    d.rounded_rectangle((110, 114, 354, 140), radius=4, fill=(15, 118, 110))
    draw_centered(d, 232, 127, "145 KM/H  ·  204,000 EVAC", get_font("cond_bold", 15), (255, 255, 255))
    return sc


def draw_scene_uk_cpi(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #7: UK fuel pump with £ sign + 3.5% SEP -> 3.6% OCT CPI bar chart."""
    sc = image_cls.new("RGB", (w, h), (238, 242, 246))
    d = draw_cls.Draw(sc)

    # Fuel pump on left
    d.rounded_rectangle((34, 28, 108, 128), radius=6, fill=(15, 23, 42))
    d.rectangle((26, 126, 116, 134), fill=(51, 65, 85))
    d.rectangle((44, 40, 98, 78), fill=(255, 255, 255))
    draw_centered(d, 71, 59, "£", get_font("serif_bold", 28), (29, 78, 216))
    d.arc((104, 46, 134, 116), start=270, end=90, fill=(15, 23, 42), width=5)
    d.line((122, 40, 122, 60), fill=(220, 38, 38), width=5)

    # Bar chart on right
    d.line((158, 114, 344, 114), fill=(100, 116, 139), width=2)
    d.rectangle((174, 58, 228, 114), fill=(37, 99, 235))
    d.rectangle((252, 34, 306, 114), fill=(220, 38, 38))
    draw_centered(d, 201, 44, "3.5%", get_font("cond_bold", 18), (30, 58, 138))
    draw_centered(d, 279, 20, "3.6%", get_font("cond_bold", 19), (185, 28, 28))
    draw_centered(d, 201, 130, "SEP", get_font("cond_bold", 15), INK_BODY)
    draw_centered(d, 279, 130, "OCT", get_font("cond_bold", 15), (185, 28, 28))

    d.line((204, 28, 254, 16), fill=(185, 28, 28), width=3)
    d.rounded_rectangle((312, 52, 360, 98), radius=4, fill=(185, 28, 28))
    draw_centered(d, 336, 66, "1-YR", get_font("cond_bold", 14), (255, 255, 255))
    draw_centered(d, 336, 84, "HIGH", get_font("cond_bold", 14), (253, 224, 71))
    return sc


def draw_scene_sudan(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #8: Sudan El Obeid map, drone strike, and Amnesty 37 KILLED report."""
    sc = image_cls.new("RGB", (w, h), (244, 234, 213))
    d = draw_cls.Draw(sc)

    # Simplified Sudan map outline
    sudan = [(44, 18), (132, 18), (154, 52), (144, 94), (118, 132), (46, 130), (28, 84)]
    d.polygon(sudan, fill=(226, 211, 179), outline=(146, 125, 92))
    # El Obeid target
    ex, ey = 86, 82
    d.ellipse((ex - 7, ey - 7, ex + 7, ey + 7), fill=(220, 38, 38), outline=(255, 255, 255), width=2)
    draw_centered(d, ex, 106, "EL OBEID", get_font("cond_bold", 14), (127, 29, 29))

    # Drone icon top-left
    d.polygon([(38, 32), (62, 26), (56, 40)], fill=(30, 41, 59))
    draw_dashed_line(d, 56, 38, ex - 4, ey - 6, (220, 38, 38), width=2, dash=4)

    # Amnesty report sheet on right
    d.rectangle((188, 16, 348, 134), fill=(255, 255, 255), outline=(148, 163, 184), width=2)
    draw_centered(d, 268, 33, "AMNESTY REPORT", get_font("cond_bold", 15), INK_PRIMARY)
    for ly in (52, 65, 78):
        d.line((204, ly, 332, ly), fill=(203, 213, 225), width=3)
    d.rounded_rectangle((202, 90, 334, 122), radius=4, fill=(185, 28, 28))
    draw_centered(d, 268, 106, "37 KILLED", get_font("cond_bold", 18), (255, 255, 255))
    return sc


def draw_scene_nvidia_cisa(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #9: Nvidia AI GPU chip ($115.8B / +103%) + CISA Java4Shell alert shield."""
    sc = image_cls.new("RGB", (w, h), (254, 242, 242))
    d = draw_cls.Draw(sc)

    # Left dark silicon half
    d.rectangle((0, 0, 188, h), fill=(15, 23, 42))
    for px in range(48, 142, 14):
        d.line((px, 14, px, 26), fill=(245, 158, 11), width=3)
        d.line((px, 92, px, 104), fill=(245, 158, 11), width=3)
    for py in range(34, 86, 14):
        d.line((28, py, 42, py), fill=(245, 158, 11), width=3)
        d.line((146, py, 160, py), fill=(245, 158, 11), width=3)
    d.rectangle((42, 24, 146, 94), fill=(6, 78, 59), outline=(16, 185, 129), width=3)
    draw_centered(d, 94, 48, "$115.8B", get_font("cond_bold", 22), (255, 255, 255))
    draw_centered(d, 94, 74, "NVIDIA Q3", get_font("cond_bold", 14), (110, 231, 183))
    d.rounded_rectangle((32, 112, 156, 138), radius=4, fill=(16, 185, 129))
    draw_centered(d, 94, 125, "+103% DATA CTR", get_font("cond_bold", 14), (6, 78, 59))

    # Right security alert shield
    shield = [(240, 18), (314, 18), (314, 58), (277, 94), (240, 58)]
    d.polygon(shield, fill=(185, 28, 28), outline=(127, 29, 29))
    draw_centered(d, 277, 52, "!", get_font("serif_bold", 40), (255, 255, 255))
    draw_centered(d, 277, 110, "JAVA4SHELL", get_font("cond_bold", 17), (153, 27, 27))
    draw_centered(d, 277, 131, "CVE-2026-114938", get_font("cond_bold", 13), INK_BODY)
    return sc


def draw_scene_cop31(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #10: Earth globe, thermometer, and 35x35 clean-power pledge."""
    sc = image_cls.new("RGB", (w, h), (236, 253, 245))
    d = draw_cls.Draw(sc)

    # Globe on left
    gx, gy, gr = 68, 74, 44
    d.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=(56, 189, 248), outline=(2, 132, 199), width=2)
    d.polygon([(44, 50), (74, 44), (72, 74), (50, 80)], fill=(22, 163, 74))
    d.polygon([(80, 58), (104, 68), (94, 102), (76, 92)], fill=(22, 163, 74))
    d.line((gx - gr, gy, gx + gr, gy), fill=(186, 230, 253), width=1)

    # Thermometer
    d.rounded_rectangle((126, 22, 142, 110), radius=8, fill=(255, 255, 255), outline=(71, 85, 105), width=2)
    d.rectangle((131, 42, 137, 112), fill=(220, 38, 38))
    d.ellipse((122, 100, 146, 124), fill=(220, 38, 38), outline=(71, 85, 105), width=2)

    # 35x35 goal callout
    draw_centered(d, 258, 38, "35x35", get_font("serif_bold", 38), (4, 120, 87))
    draw_centered(d, 258, 78, "75 BACK CLEAN POWER", get_font("cond_bold", 16), INK_PRIMARY)
    d.rounded_rectangle((164, 102, 354, 134), radius=5, fill=(180, 83, 9))
    draw_centered(d, 259, 118, "ANTALYA SPLIT ON FOSSILS", get_font("cond_bold", 14), (255, 255, 255))
    return sc


def draw_scene_gaza(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #11: Broken olive branch over rain-flooded Gaza shelter tents."""
    sc = image_cls.new("RGB", (w, h), (203, 213, 225))
    d = draw_cls.Draw(sc)

    # Rain streaks
    for rx in range(18, w, 28):
        d.line((rx, 8, rx - 10, 48), fill=(100, 116, 139), width=2)
        d.line((rx + 12, 46, rx + 2, 86), fill=(100, 116, 139), width=2)

    # Broken olive branch at top
    d.line((78, 34, 168, 26), fill=(77, 124, 15), width=4)
    d.line((198, 26, 288, 34), fill=(77, 124, 15), width=4)
    for lx, ly in [(104, 22), (138, 18), (228, 18), (262, 22)]:
        d.ellipse((lx - 8, ly - 5, lx + 8, ly + 5), fill=(101, 163, 13))
    d.line((176, 14, 190, 40), fill=(220, 38, 38), width=4)
    d.line((190, 14, 176, 40), fill=(220, 38, 38), width=4)

    # Tents & rising floodwaters
    for tx in (62, 166, 270):
        d.polygon([(tx, 64), (tx - 38, 118), (tx + 38, 118)], fill=(248, 250, 252), outline=(71, 85, 105))
        d.polygon([(tx, 84), (tx - 12, 118), (tx + 12, 118)], fill=(51, 65, 85))

    d.rectangle((0, 112, w, h), fill=(2, 132, 199))
    for wx in range(0, w + 24, 24):
        d.arc((wx - 12, 104, wx + 12, 120), start=180, end=360, fill=(186, 230, 253), width=3)
    d.rounded_rectangle((78, 120, 288, 143), radius=4, fill=MASTHEAD_NAVY)
    draw_centered(d, 183, 131.5, "TRUCE RISK  ·  FLOODED CAMPS", get_font("cond_bold", 14), (253, 224, 71))
    return sc


def draw_scene_gtavi(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #12: Vice-sunset horizon, game controller, 00:00 clock, and 15M pre-orders."""
    sc = image_cls.new("RGB", (w, h), (49, 16, 66))
    d = draw_cls.Draw(sc)

    # Vice sunset bands & sun disc
    d.rectangle((0, 74, w, 112), fill=(131, 24, 67))
    d.rectangle((0, 112, w, h), fill=(15, 23, 42))
    d.ellipse((32, 36, 108, 112), fill=(249, 115, 22))
    d.rectangle((26, 76, 114, 82), fill=(131, 24, 67))
    d.rectangle((26, 90, 114, 96), fill=(131, 24, 67))
    # Palm silhouette
    d.line((34, 114, 46, 46), fill=(15, 23, 42), width=5)
    for ang in (-2.4, -1.6, -0.7, 0.3):
        d.line((46, 46, 46 + 24 * math.cos(ang), 46 + 18 * math.sin(ang)), fill=(15, 23, 42), width=4)

    # Game controller
    d.rounded_rectangle((126, 38, 246, 92), radius=22, fill=(241, 245, 249), outline=(148, 163, 184), width=2)
    d.line((152, 54, 152, 74), fill=(15, 23, 42), width=5)
    d.line((142, 64, 162, 64), fill=(15, 23, 42), width=5)
    d.ellipse((210, 52, 221, 63), fill=(236, 72, 153))
    d.ellipse((223, 63, 234, 74), fill=(6, 182, 212))

    # Midnight 00:00 clock
    cx, cy, cr = 304, 60, 32
    d.ellipse((cx - cr, cy - cr, cx + cr, cy + cr), fill=(255, 255, 255), outline=(236, 72, 153), width=3)
    d.line((cx, cy, cx, cy - 22), fill=INK_PRIMARY, width=3)
    d.line((cx, cy, cx + 10, cy - 12), fill=(220, 38, 38), width=2)
    draw_centered(d, cx, cy + 16, "00:00", get_font("cond_bold", 13), INK_PRIMARY)

    d.rounded_rectangle((128, 114, 348, 140), radius=4, fill=(236, 72, 153))
    draw_centered(d, 238, 127, "NZ LAUNCH  ·  15M PRE-ORDERS", get_font("cond_bold", 15), (255, 255, 255))
    return sc


def draw_scene_garment(image_cls, draw_cls, get_font, w: int, h: int):
    """Illustrate #13: Closed Bangladesh garment factory (55 SHUT) and Tk 30,000 wage placard."""
    sc = image_cls.new("RGB", (w, h), (254, 243, 199))
    d = draw_cls.Draw(sc)

    # Sawtooth factory silhouette
    roof = [(18, 62), (48, 40), (48, 62), (82, 40), (82, 62), (116, 40), (116, 62), (168, 62), (168, 134), (18, 134)]
    d.polygon(roof, fill=(51, 65, 85), outline=(15, 23, 42))
    # Bangladesh flag
    d.line((142, 18, 142, 62), fill=(15, 23, 42), width=3)
    d.rectangle((144, 18, 182, 42), fill=(4, 120, 87))
    d.ellipse((155, 24, 169, 36), fill=(220, 38, 38))

    # Shuttered gate
    d.rectangle((54, 76, 132, 134), fill=(226, 232, 240), outline=(15, 23, 42), width=2)
    d.rectangle((44, 92, 142, 118), fill=(185, 28, 28))
    draw_centered(d, 93, 105, "55 SHUT", get_font("cond_bold", 17), (255, 255, 255))

    # Wage demand placard on right
    d.line((274, 92, 274, 140), fill=(146, 64, 14), width=6)
    d.rectangle((198, 20, 350, 96), fill=(255, 255, 255), outline=(15, 23, 42), width=3)
    draw_centered(d, 274, 46, "TK 30,000", get_font("serif_bold", 23), (15, 23, 42))
    draw_centered(d, 274, 75, "WAGE PROTEST", get_font("cond_bold", 16), (185, 28, 28))
    return sc


SCENE_ARTISTS = {
    "apec": draw_scene_apec,
    "gulf": draw_scene_gulf,
    "voyager": draw_scene_voyager,
    "alaska": draw_scene_alaska,
    "ukraine": draw_scene_ukraine,
    "cyclone": draw_scene_cyclone,
    "uk_cpi": draw_scene_uk_cpi,
    "sudan": draw_scene_sudan,
    "nvidia_cisa": draw_scene_nvidia_cisa,
    "cop31": draw_scene_cop31,
    "gaza": draw_scene_gaza,
    "gtavi": draw_scene_gtavi,
    "garment": draw_scene_garment,
}


def draw_lead_card_rows(
    base_img, draw, get_font, image_cls, draw_cls, scene_artists: dict
) -> None:
    """Render Row 1 (3 wide lead cards) and Rows 2-3 (5 illustrated cards each)."""
    row_specs = [
        (1, 3, 18, ROW1_TOP, ROW1_BOT, 208, 14, 29, 21, 20, 16),
        (2, 5, 14, ROW2_TOP, ROW2_BOT, 150, 12, 22, 17, 18, 14),
        (3, 5, 14, ROW3_TOP, ROW3_BOT, 150, 12, 22, 17, 18, 14),
    ]
    for row_num, cols, gap, ry0, ry1, ill_h, badge_r, hl_max, hl_min, sm_max, sm_min in row_specs:
        cards = [c for c in LEAD_CARDS if c["row"] == row_num]
        card_w = (PAGE_WIDTH - (cols - 1) * gap) // cols
        pad_x = 12 if row_num == 1 else 10

        for idx, card in enumerate(cards):
            cx0 = PAGE_MARGIN_X + idx * (card_w + gap)
            cx1 = (SUPERSAMPLE_W - PAGE_MARGIN_X) if idx == cols - 1 else (cx0 + card_w)
            reg_col = rgb_from_hex(REGION_LOOKUP[card["region"]]["hex"])

            draw.rounded_rectangle(
                (cx0, ry0, cx1, ry1),
                radius=6,
                fill=CARD_SURFACE,
                outline=RULE_BORDER,
                width=2,
            )
            draw.rectangle((cx0 + 4, ry0, cx1 - 4, ry0 + 5), fill=reg_col)

            # Illustration frame (clipped to exact iw x ih scene image)
            ix0, iy0 = cx0 + pad_x, ry0 + 11
            ix1, iy1 = cx1 - pad_x, ry0 + 11 + ill_h
            iw, ih = ix1 - ix0, iy1 - iy0
            artist = scene_artists.get(card["scene"])
            if artist is not None:
                scene_img = artist(image_cls, draw_cls, get_font, iw, ih)
                base_img.paste(scene_img, (ix0, iy0))
            else:
                draw.rectangle((ix0, iy0, ix1, iy1), fill=PAPER_WARM_ALT)
            draw.rectangle((ix0, iy0, ix1, iy1), outline=(203, 213, 225), width=1)

            # Metadata strip (badge + beat + source)
            meta_cy = iy1 + (16 if row_num == 1 else 15)
            bx = cx0 + pad_x + badge_r
            badge_font = get_font("sans_bold", 16 if row_num == 1 else 14)
            draw_badge_circle(
                draw, bx, meta_cy, badge_r, str(card["id"]), reg_col, (255, 255, 255), badge_font
            )

            src_font = get_font("cond_bold", 15 if row_num == 1 else 13)
            src_w = draw.textlength(card["source"], font=src_font)
            src_x = cx1 - pad_x - src_w
            draw_centered(draw, src_x + src_w / 2.0, meta_cy, card["source"], src_font, INK_MUTED)

            beat_x = bx + badge_r + 8
            max_beat_w = int(src_x - beat_x - 8)
            beat_font, _ = fit_single_line_font(
                draw,
                get_font,
                "cond_bold",
                card["beat"],
                max(max_beat_w, 40),
                17 if row_num == 1 else 14,
                11,
            )
            bw = draw.textlength(card["beat"], font=beat_font)
            draw_centered(draw, beat_x + bw / 2.0, meta_cy, card["beat"], beat_font, reg_col)

            # Bold serif headline
            inner_w = (cx1 - cx0) - 2 * pad_x
            hl_top = meta_cy + badge_r + 5
            hl_h = 80 if row_num == 1 else 82
            hl_font, hl_lines, hl_lh = wrap_lines_to_box(
                draw,
                get_font,
                "serif_bold",
                card["headline"],
                inner_w,
                hl_h,
                hl_max,
                hl_min,
                line_gap=3,
            )
            hy = hl_top
            for line in hl_lines:
                draw.text((cx0 + pad_x, hy), line, font=hl_font, fill=INK_PRIMARY)
                hy += hl_lh

            # Concise summary body
            sum_top = hy + (6 if row_num == 1 else 5)
            sum_h = (ry1 - 8) - sum_top
            sm_font, sm_lines, sm_lh = wrap_lines_to_box(
                draw,
                get_font,
                "sans_reg",
                card["summary"],
                inner_w,
                sum_h,
                sm_max,
                sm_min,
                line_gap=4,
            )
            sy = sum_top
            for line in sm_lines:
                draw.text((cx0 + pad_x, sy), line, font=sm_font, fill=INK_BODY)
                sy += sm_lh


def geo_to_px(
    lat: float,
    lon: float,
    bounds: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[float, float]:
    """Project (lat, lon) onto an equirectangular viewport."""
    lon_min, lon_max, lat_min, lat_max = bounds
    px = (lon - lon_min) / (lon_max - lon_min) * width
    py = (lat_max - lat) / (lat_max - lat_min) * height
    return (px, py)


def resolve_pin_positions(
    pin_items: list[dict],
    bounds: tuple[float, float, float, float],
    width: int,
    height: int,
    pin_r: float,
) -> list[dict]:
    """Compute collision-free map badge coordinates near true geo anchors."""
    anchors = []
    for item in pin_items:
        ax, ay = geo_to_px(item["lat"], item["lon"], bounds, width, height)
        anchors.append((item, ax, ay))

    placed: list[dict] = []
    min_dist = 2.0 * pin_r + 6.5
    pad = pin_r + 4.0
    radii = [0.0, 1.8 * pin_r, 2.7 * pin_r, 3.6 * pin_r, 4.6 * pin_r, 5.6 * pin_r]
    angles = [k * (2.0 * math.pi / 16.0) for k in range(16)]

    for item, ax, ay in anchors:
        best_pos = (min(max(ax, pad), width - pad), min(max(ay, pad), height - pad))
        best_score = float("inf")

        for rad in radii:
            dirs = [(0.0, 0.0)] if rad == 0.0 else [(math.cos(a), math.sin(a)) for a in angles]
            for dx, dy in dirs:
                cx = ax + rad * dx
                cy = ay + rad * dy
                if cx < pad or cx > width - pad or cy < pad or cy > height - pad:
                    continue
                score = rad * 1.5
                for other in placed:
                    dist = math.hypot(cx - other["px"], cy - other["py"])
                    if dist < min_dist:
                        score += 10000.0 * (min_dist - dist)
                for other_item, oax, oay in anchors:
                    if other_item["id"] == item["id"]:
                        continue
                    adist = math.hypot(cx - oax, cy - oay)
                    if adist < pin_r + 5.0:
                        score += 90.0 * (pin_r + 5.0 - adist)
                if score < best_score:
                    best_score = score
                    best_pos = (cx, cy)
                    if score == 0.0:
                        break
            if best_score == 0.0:
                break

        placed.append(
            {
                "item": item,
                "ax": ax,
                "ay": ay,
                "px": best_pos[0],
                "py": best_pos[1],
            }
        )
    return placed


def draw_where_and_kpis(base_img, draw, get_font, image_cls, draw_cls) -> None:
    """Render bottom-left WHERE IT HAPPENED world map and BY THE NUMBERS KPI grid."""
    left_x0, left_x1 = PAGE_MARGIN_X, 690
    map_y0, map_y1 = BOTTOM_TOP, 1802

    # Map panel shell
    draw.rounded_rectangle(
        (left_x0, map_y0, left_x1, map_y1),
        radius=6,
        fill=CARD_SURFACE,
        outline=RULE_BORDER,
        width=2,
    )
    hdr_font = get_font("cond_bold", 18)
    note_font = get_font("cond_bold", 13)
    draw.text((left_x0 + 14, map_y0 + 9), "WHERE IT HAPPENED", font=hdr_font, fill=MASTHEAD_NAVY)
    note_txt = "1–13 numbered  ·  14–45 dots"
    nw = draw.textlength(note_txt, font=note_font)
    draw.text((left_x1 - 14 - nw, map_y0 + 12), note_txt, font=note_font, fill=INK_MUTED)

    # Map viewport
    vx0, vy0, vx1, vy1 = left_x0 + 10, map_y0 + 36, left_x1 - 10, map_y1 - 36
    vw, vh = vx1 - vx0, vy1 - vy0
    map_img = image_cls.new("RGB", (vw, vh), MAP_OCEAN_LIGHT)
    md = draw_cls.Draw(map_img)

    for lon in range(-150, 181, 30):
        gx, _ = geo_to_px(0.0, float(lon), ATLAS_BOUNDS, vw, vh)
        md.line((gx, 0, gx, vh), fill=MAP_GRID_LINE, width=1)
    for lat in range(-30, 61, 30):
        _, gy = geo_to_px(float(lat), 0.0, ATLAS_BOUNDS, vw, vh)
        md.line((0, gy, vw, gy), fill=MAP_GRID_LINE, width=2 if lat == 0 else 1)

    for poly in ATLAS_LANDMASSES.values():
        pts = [geo_to_px(lat, lon, ATLAS_BOUNDS, vw, vh) for (lon, lat) in poly]
        md.polygon(pts, fill=MAP_LAND_SAGE, outline=MAP_LAND_EDGE)

    # Small dots for stories #14-#45
    for b_item in BRIEF_ITEMS:
        bx, by = geo_to_px(b_item["lat"], b_item["lon"], ATLAS_BOUNDS, vw, vh)
        col = rgb_from_hex(REGION_LOOKUP[b_item["region"]]["hex"])
        md.ellipse((bx - 3.6, by - 3.6, bx + 3.6, by + 3.6), fill=col, outline=(255, 255, 255), width=1)

    # Special Voyager 1 callout in Southern Ocean so pin #3 stays legible and clean
    v_pin_items = []
    for c in LEAD_CARDS:
        if c["id"] == 3:
            v_pin_items.append({**c, "lat": -41.0, "lon": -26.0})
        else:
            v_pin_items.append(c)

    vax, vay = geo_to_px(-41.0, -26.0, ATLAS_BOUNDS, vw, vh)
    draw_dashed_line(md, vax + 12, vay, vax + 98, vay, (109, 40, 217), width=2, dash=6)
    md.polygon([(vax + 98, vay - 4), (vax + 108, vay), (vax + 98, vay + 4)], fill=(109, 40, 217))
    md.text((vax + 114, vay - 8), "to Voyager 1 -> 25.9bn km", font=get_font("cond_bold", 13), fill=(76, 29, 149))

    pin_r = 10.0
    placed = resolve_pin_positions(v_pin_items, ATLAS_BOUNDS, vw, vh, pin_r)
    for p in placed:
        col = rgb_from_hex(REGION_LOOKUP[p["item"]["region"]]["hex"])
        if math.hypot(p["px"] - p["ax"], p["py"] - p["ay"]) > pin_r + 2:
            md.line((p["ax"], p["ay"], p["px"], p["py"]), fill=INK_PRIMARY, width=2)
            md.ellipse((p["ax"] - 3, p["ay"] - 3, p["ax"] + 3, p["ay"] + 3), fill=col, outline=(255, 255, 255), width=1)

    pin_font = get_font("sans_bold", 12)
    for p in placed:
        col = rgb_from_hex(REGION_LOOKUP[p["item"]["region"]]["hex"])
        draw_badge_circle(
            md, p["px"], p["py"], pin_r, str(p["item"]["id"]), col, (255, 255, 255), pin_font, ring_rgb=(255, 255, 255)
        )

    base_img.paste(map_img, (vx0, vy0))
    draw.rectangle((vx0, vy0, vx1, vy1), outline=RULE_BORDER, width=1)

    # Compact region legend strip under map
    leg_y = (vy1 + map_y1) / 2.0
    leg_font = get_font("cond_bold", 13)
    lx = left_x0 + 14
    seg = (left_x1 - left_x0 - 28) / len(REGION_PALETTE)
    for idx, reg in enumerate(REGION_PALETTE):
        rx = lx + idx * seg
        col = rgb_from_hex(reg["hex"])
        draw.ellipse((rx, leg_y - 5, rx + 10, leg_y + 5), fill=col)
        draw.text((rx + 14, leg_y - 7), reg["short"], font=leg_font, fill=INK_BODY)

    # BY THE NUMBERS 2x2 KPI grid (y=1812..1995)
    kpi_hdr_y = 1812
    draw.text((left_x0 + 4, kpi_hdr_y), "BY THE NUMBERS", font=get_font("cond_bold", 17), fill=MASTHEAD_NAVY)

    grid_y0 = 1838
    gap_x, gap_y = 12, 11
    card_w = (left_x1 - left_x0 - gap_x) // 2
    card_h = (BOTTOM_BOT - grid_y0 - gap_y) // 2
    for idx, kpi in enumerate(NUMBER_KPIS):
        col_i = idx % 2
        row_i = idx // 2
        kx0 = left_x0 + col_i * (card_w + gap_x)
        kx1 = left_x1 if col_i == 1 else (kx0 + card_w)
        ky0 = grid_y0 + row_i * (card_h + gap_y)
        ky1 = BOTTOM_BOT if row_i == 1 else (ky0 + card_h)
        accent = rgb_from_hex(kpi["hex"])

        draw.rounded_rectangle(
            (kx0, ky0, kx1, ky1), radius=6, fill=CARD_SURFACE, outline=RULE_BORDER, width=2
        )
        draw.rectangle((kx0 + 2, ky0 + 8, kx0 + 8, ky1 - 8), fill=accent)

        val_font, _ = fit_single_line_font(
            draw, get_font, "serif_bold", kpi["value"], (kx1 - kx0) - 26, 26, 18
        )
        draw.text((kx0 + 16, ky0 + 7), kpi["value"], font=val_font, fill=accent)
        lbl_font, _ = fit_single_line_font(
            draw, get_font, "sans_semi", kpi["label"], (kx1 - kx0) - 24, 15, 11
        )
        draw.text((kx0 + 16, ky0 + 43), kpi["label"], font=lbl_font, fill=INK_BODY)


def draw_brief_columns(draw, get_font) -> None:
    """Render bottom-right 2-column directory of 32 verified briefs (#14-#45)."""
    rx0, ry0, rx1, ry1 = 706, BOTTOM_TOP, SUPERSAMPLE_W - PAGE_MARGIN_X, BOTTOM_BOT
    draw.rounded_rectangle(
        (rx0, ry0, rx1, ry1), radius=6, fill=CARD_SURFACE, outline=RULE_BORDER, width=2
    )
    hdr_h = 40
    draw.rectangle((rx0 + 2, ry0 + 2, rx1 - 2, ry0 + hdr_h), fill=PAPER_WARM_ALT)
    draw.rectangle((rx0 + 2, ry0 + 2, rx1 - 2, ry0 + 6), fill=GOLD_ACCENT)
    draw.line((rx0 + 2, ry0 + hdr_h, rx1 - 2, ry0 + hdr_h), fill=RULE_BORDER, width=2)

    hdr_txt = "ALSO ON WEDNESDAY 18 NOVEMBER — 32 MORE VERIFIED STORIES (#14–#45)"
    hdr_font, _ = fit_single_line_font(
        draw, get_font, "serif_bold", hdr_txt, (rx1 - rx0) - 32, 19, 14
    )
    draw.text((rx0 + 16, ry0 + 11), hdr_txt, font=hdr_font, fill=MASTHEAD_NAVY)

    col_pad = 14
    mid_x = (rx0 + rx1) // 2
    draw.line((mid_x, ry0 + hdr_h + 8, mid_x, ry1 - 8), fill=RULE_BORDER, width=2)

    col_bounds = [
        (rx0 + col_pad, mid_x - 10, BRIEF_ITEMS[:16]),
        (mid_x + 10, rx1 - col_pad, BRIEF_ITEMS[16:]),
    ]
    body_y0 = ry0 + hdr_h + 6
    body_y1 = ry1 - 6
    row_h = (body_y1 - body_y0) / 16.0
    badge_r = 10.0
    badge_font = get_font("sans_bold", 12)

    for cx0, cx1, items in col_bounds:
        text_x = cx0 + 28
        max_w = cx1 - text_x - 2
        for idx, item in enumerate(items):
            y_top = body_y0 + idx * row_h
            y_mid = y_top + row_h / 2.0
            if idx > 0:
                draw.line(
                    (cx0, y_top, cx1, y_top),
                    fill=mix_rgb(CARD_SURFACE, RULE_BORDER, 0.55),
                    width=1,
                )

            col = rgb_from_hex(REGION_LOOKUP[item["region"]]["hex"])
            draw_badge_circle(
                draw, cx0 + 11, y_mid, badge_r, str(item["id"]), col, (255, 255, 255), badge_font
            )

            lead_str = item["lead"] + " "
            body_str = item["text"]
            chosen_sz = 12
            for sz in range(16, 11, -1):
                f_b = get_font("sans_bold", sz)
                f_r = get_font("sans_reg", sz)
                if draw.textlength(lead_str, font=f_b) + draw.textlength(body_str, font=f_r) <= max_w:
                    chosen_sz = sz
                    break
            f_b = get_font("sans_bold", chosen_sz)
            f_r = get_font("sans_reg", chosen_sz)
            lead_w = draw.textlength(lead_str, font=f_b)

            bx0, by0, bx1, by1 = draw.textbbox((0, 0), "AH", font=f_b)
            ty = y_mid - (by0 + by1) / 2.0
            draw.text((text_x, ty), lead_str, font=f_b, fill=INK_PRIMARY)
            draw.text((text_x + lead_w, ty), body_str, font=f_r, fill=INK_BODY)


def draw_footer_attestation(draw, get_font) -> None:
    """Render bottom hairline and attribution attestation bar."""
    draw.line(
        (PAGE_MARGIN_X, FOOTER_TOP, SUPERSAMPLE_W - PAGE_MARGIN_X, FOOTER_TOP),
        fill=RULE_BORDER,
        width=2,
    )
    ft_font, _ = fit_single_line_font(
        draw, get_font, "sans_semi", ATTESTATION_TEXT, PAGE_WIDTH - 16, 16, 11
    )
    draw_centered(
        draw,
        SUPERSAMPLE_W / 2.0,
        (FOOTER_TOP + FOOTER_BOT) / 2.0 + 1,
        ATTESTATION_TEXT,
        ft_font,
        INK_BODY,
    )


def render_infographic() -> Path:
    """Render the 2048x2048 broadsheet and save downsampled 1024x1024 RGB PNG."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (SUPERSAMPLE_W, SUPERSAMPLE_H), PAPER_CREAM)
    draw = ImageDraw.Draw(img)
    get_font = build_font_getter(ImageFont)

    draw_broadsheet_masthead(draw, get_font)
    draw_lead_card_rows(img, draw, get_font, Image, ImageDraw, SCENE_ARTISTS)
    draw_where_and_kpis(img, draw, get_font, Image, ImageDraw)
    draw_brief_columns(draw, get_font)
    draw_footer_attestation(draw, get_font)

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dst_path = out_dir / "entry.png"
    final_img = img.resize((OUT_PX, OUT_PX), Image.Resampling.LANCZOS)
    final_img = final_img.quantize(
        colors=256, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE
    ).convert("RGB")
    final_img.save(dst_path, format="PNG", optimize=True, compress_level=9)
    if dst_path.stat().st_size > PNG_BYTE_LIMIT:
        raise ValueError(f"Output exceeds 1 MiB limit: {dst_path.stat().st_size} bytes")
    return dst_path


def main() -> int:
    flag = os.environ.get("MAKEFUN_RENDER", "").strip().lower()
    if flag in {"1", "true", "yes", "on"}:
        render_infographic()
    else:
        copy_prebuilt_png()
    return 0


if __name__ == "__main__":
    sys.exit(main())
