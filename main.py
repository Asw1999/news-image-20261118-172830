"""Editorial broadsheet world news infographic for Wednesday, 18 November 2026.

Default sandbox mode uses only Python 3.13 standard library modules (`os`, `shutil`,
`pathlib`, `sys`) to copy the pre-rendered `entry.png` deterministically to
`$MAKEFUN_OUTPUT_DIR/entry.png`. Setting `MAKEFUN_RENDER=1` invokes Pillow to render
the 2048x2048 supersampled broadsheet and LANCZOS-downsample to 1024x1024 RGB PNG.
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

# Vertical section coordinates on 2048x2048 canvas
MASTHEAD_TOP, MASTHEAD_BOT = 0, 220
ROW1_TOP, ROW1_BOT = 228, 680
ROW2_TOP, ROW2_BOT = 694, 1068
ROW3_TOP, ROW3_BOT = 1082, 1456
BOTTOM_TOP, BOTTOM_BOT = 1472, 1996
FOOTER_TOP, FOOTER_BOT = 2004, 2044

# Warm broadsheet ink & paper palette
PAPER_CREAM = (250, 247, 240)
PAPER_WARM_ALT = (242, 237, 227)
INK_PRIMARY = (15, 23, 42)
INK_BODY = (51, 65, 85)
INK_MUTED = (100, 116, 139)
RULE_DIVIDER = (213, 207, 194)
RULE_HAIRLINE = (229, 224, 213)
CRIMSON_KICKER = (185, 28, 28)
SLATE_KICKER = (30, 41, 59)

# Map palette
MAP_OCEAN_LIGHT = (216, 230, 242)
MAP_GRID_LINE = (196, 215, 232)
MAP_LAND_SAGE = (194, 206, 178)
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
    "mast_bold": ("DejaVuSerif-Bold.ttf", "NotoSerif-Bold.ttf"),
    "serif_bold": ("NotoSerif-Bold.ttf", "DejaVuSerif-Bold.ttf"),
    "serif_italic": ("NotoSerif-Italic.ttf", "DejaVuSerif-Italic.ttf"),
    "serif_reg": ("NotoSerif-Regular.ttf", "DejaVuSerif.ttf"),
    "sans_bold": ("SourceSansPro-Bold.ttf", "DejaVuSans-Bold.ttf"),
    "sans_semi": ("SourceSansPro-SemiBold.ttf", "DejaVuSans-Bold.ttf"),
    "sans_reg": ("SourceSansPro-Regular.ttf", "DejaVuSans.ttf"),
    "cond_bold": ("BarlowSemiCondensed-Bold.ttf", "DejaVuSansCondensed-Bold.ttf"),
    "mono_bold": ("DejaVuSansMono-Bold.ttf", "DroidSansMono.ttf"),
}

REGION_PALETTE = [
    {"key": "APAC", "name": "ASIA-PACIFIC", "short": "Asia-Pacific", "hex": "#6D28D9"},
    {"key": "MENA", "name": "MIDDLE EAST", "short": "Middle East", "hex": "#B45309"},
    {"key": "EUROPE", "name": "EUROPE", "short": "Europe", "hex": "#1D4ED8"},
    {"key": "AFRICA", "name": "AFRICA", "short": "Africa", "hex": "#15803D"},
    {"key": "AMERICAS", "name": "AMERICAS", "short": "Americas", "hex": "#B91C1C"},
    {"key": "GLOBAL", "name": "GLOBAL & SPACE", "short": "Global & Space", "hex": "#0F766E"},
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

LEAD_STORIES = [
    # Row 1 (#1 - #3)
    {
        "id": 1,
        "row": 1,
        "region": "APAC",
        "beat": "ASIA-PACIFIC · APEC SUMMIT",
        "source": "AFP · AP · REUTERS",
        "headline": "Xi greets Trump on the tarmac as APEC opens in Shenzhen",
        "summary": "China's leader welcomes Trump at the airport and urges open WTO trade and AI cooperation; Putin joins the banquet ahead of Thursday's three-way summit.",
        "lat": 22.5,
        "lon": 114.1,
        "scene": "apec",
    },
    {
        "id": 2,
        "row": 1,
        "region": "MENA",
        "beat": "MIDDLE EAST · IRAN WAR",
        "source": "REUTERS · CENTCOM",
        "headline": "Iran fires drones at US base in Kuwait; Bahrain intercepts",
        "summary": "Iran says it targeted Ali Al Salem after US jets struck Qeshm Island; Kuwait reports no hit as Bahrain downs attacks and a Hormuz tanker is struck.",
        "lat": 27.6,
        "lon": 51.5,
        "scene": "gulf",
    },
    {
        "id": 3,
        "row": 1,
        "region": "GLOBAL",
        "beat": "SPACE · SCIENCE",
        "source": "NASA · JPL",
        "headline": "Voyager 1 becomes the first craft one light-day from Earth",
        "summary": "At 10:16 UTC NASA's probe passes 25.9 billion km (16.1B miles) away in interstellar space; a radio command sent today takes 24 hours to arrive.",
        "lat": -42.0,
        "lon": -118.0,
        "scene": "voyager",
    },
    # Row 2 (#4 - #8)
    {
        "id": 4,
        "row": 2,
        "region": "EUROPE",
        "beat": "EUROPE · UKRAINE AID",
        "source": "EU COMMISSION",
        "headline": "EU proposes a €45bn loan to fund Ukraine in 2027",
        "summary": "Package pairs €25bn military and €20bn budget aid, repaid only once Russia pays war reparations.",
        "lat": 50.8,
        "lon": 4.4,
        "scene": "eu_loan",
    },
    {
        "id": 5,
        "row": 2,
        "region": "EUROPE",
        "beat": "EUROPE · UKRAINE WAR",
        "source": "KYIV · AP",
        "headline": "Russia fires 141 drones at Ukraine; Odesa hit",
        "summary": "126 drones downed overnight, Kyiv says; double-tap strikes kill four in Odesa and cut power in Rivne.",
        "lat": 46.5,
        "lon": 30.7,
        "scene": "ukraine_drones",
    },
    {
        "id": 6,
        "row": 2,
        "region": "AMERICAS",
        "beat": "AMERICAS · US POLITICS",
        "source": "AP",
        "headline": "Democrat Peltola wins Alaska; Senate now 56–44",
        "summary": "Mary Peltola beats Dan Sullivan 144,302 to 131,844 in final count, widening Democrats' Senate majority.",
        "lat": 61.2,
        "lon": -149.9,
        "scene": "alaska_senate",
    },
    {
        "id": 7,
        "row": 2,
        "region": "GLOBAL",
        "beat": "GLOBAL · CLIMATE",
        "source": "UNFCCC · ANADOLU",
        "headline": "Draft deal splits COP31 talks in Antalya; 75 back '35x35'",
        "summary": "Ministers clash over fossil phase-out as 75 states back Türkiye's 35% clean power goal by 2035.",
        "lat": 36.9,
        "lon": 30.7,
        "scene": "cop31",
    },
    {
        "id": 8,
        "row": 2,
        "region": "EUROPE",
        "beat": "EUROPE · ECONOMY",
        "source": "ONS · EUROSTAT",
        "headline": "Inflation climbs: UK 3.6%, euro area hits 4.0%",
        "summary": "Higher fuel costs lift UK CPI to a 1-yr high while euro-area inflation hits 4.0% on energy +21%.",
        "lat": 51.5,
        "lon": -0.1,
        "scene": "inflation",
    },
    # Row 3 (#9 - #13)
    {
        "id": 9,
        "row": 3,
        "region": "APAC",
        "beat": "ASIA · WEATHER",
        "source": "IMD",
        "headline": "India braces for Cyclone Akvan in Bay of Bengal",
        "summary": "Storm intensifies toward 145 km/h landfall; Odisha and Andhra readied 204,000 people for evacuation.",
        "lat": 16.5,
        "lon": 84.5,
        "scene": "cyclone",
    },
    {
        "id": 10,
        "row": 3,
        "region": "AFRICA",
        "beat": "AFRICA · SUDAN WAR",
        "source": "AMNESTY · UN",
        "headline": "Amnesty: RSF drones killed 37 civilians in El Obeid",
        "summary": "Group urges war-crimes inquiry as UN counts 2,230 killed in 2026; RSF denies strike claims.",
        "lat": 13.2,
        "lon": 30.2,
        "scene": "sudan",
    },
    {
        "id": 11,
        "row": 3,
        "region": "AMERICAS",
        "beat": "AMERICAS · TECH & MARKETS",
        "source": "CNBC · CISA",
        "headline": "Nvidia Q3 doubles to $115.8bn; gold falls below $3,800",
        "summary": "Data-center sales rise +103% YoY while spot gold slides 2% to $3,780; CISA flags Java4Shell.",
        "lat": 37.4,
        "lon": -121.9,
        "scene": "nvidia_gold",
    },
    {
        "id": 12,
        "row": 3,
        "region": "GLOBAL",
        "beat": "OCEANIA & GLOBAL · CULTURE",
        "source": "SENSOR TOWER",
        "headline": "GTA VI unlocks first in New Zealand after 13-year wait",
        "summary": "Rolling midnight release starts in NZ at 11:00 GMT; Sensor Tower estimates 15M pre-orders (~$1.45bn).",
        "lat": -36.8,
        "lon": 174.8,
        "scene": "gtavi",
    },
    {
        "id": 13,
        "row": 3,
        "region": "MENA",
        "beat": "MIDDLE EAST & AFRICA · CRISIS",
        "source": "AP · WHO · REUTERS",
        "headline": "Board warns Gaza truce may collapse; Horn troops mass",
        "summary": "UN report cites truce breaches as rains flood camps; Ethiopia and Eritrea mass border troops.",
        "lat": 31.4,
        "lon": 34.4,
        "scene": "gaza_horn",
    },
]

BRIEF_STORIES = [
    {"id": 14, "region": "AFRICA", "lead": "Abuja:", "text": "Nigeria Senate passes constitutional bill to establish state police", "lat": 9.1, "lon": 7.5},
    {"id": 15, "region": "AFRICA", "lead": "Lake Chad:", "text": "Four nations sign 5 km cross-border counter-terror pursuit pact", "lat": 13.0, "lon": 14.0},
    {"id": 16, "region": "AFRICA", "lead": "Kinshasa:", "text": "WHO & DRC launch Ebola vaccine trial as cases pass 11,300", "lat": -4.3, "lon": 15.3},
    {"id": 17, "region": "AFRICA", "lead": "Dakar:", "text": "Senegal ruling Pastef party expels Pres. Faye in Sonko split", "lat": 14.7, "lon": -17.5},
    {"id": 18, "region": "AFRICA", "lead": "Pretoria:", "text": "South Africa rebukes Nigerian envoy; inflation rises to 5.2%", "lat": -25.7, "lon": 28.2},
    {"id": 19, "region": "AFRICA", "lead": "Conakry:", "text": "Guinea courts jail 224 people in illegal gold-mining crackdown", "lat": 9.5, "lon": -13.7},
    {"id": 20, "region": "MENA", "lead": "Jerusalem:", "text": "Knesset elects Matan Kahana speaker 66–52; repeals media law", "lat": 31.8, "lon": 35.2},
    {"id": 21, "region": "MENA", "lead": "Riyadh:", "text": "Saudi-led coalition downs Houthi missile and strikes 60 sites", "lat": 24.7, "lon": 46.7},
    {"id": 22, "region": "MENA", "lead": "Cairo:", "text": "IMF and Egypt reach staff-level deal on 8th EFF economic review", "lat": 30.0, "lon": 31.2},
    {"id": 23, "region": "APAC", "lead": "Dhaka:", "text": "Bangladesh garment wage protests shut 55 factories on highway", "lat": 23.8, "lon": 90.4},
    {"id": 24, "region": "APAC", "lead": "Tokyo:", "text": "PM Takaichi pitches 'Asian IEA' oil reserve pact; jets scramble", "lat": 35.7, "lon": 139.7},
    {"id": 25, "region": "APAC", "lead": "Seoul:", "text": "Pres. Lee meets Xi on FTA services; Kospi chip stocks rally +2.7%", "lat": 37.6, "lon": 127.0},
    {"id": 26, "region": "APAC", "lead": "Manila:", "text": "Trump hails Philippine trade talks after first Quad summit", "lat": 14.6, "lon": 121.0},
    {"id": 27, "region": "APAC", "lead": "Jakarta:", "text": "Pres. Prabowo inks $71.8bn in China tech & smart-city deals", "lat": -6.2, "lon": 106.8},
    {"id": 28, "region": "APAC", "lead": "Kuala Lumpur:", "text": "Malaysia Q3 GDP grows 5.5% YoY on strong tech exports", "lat": 3.1, "lon": 101.7},
    {"id": 29, "region": "APAC", "lead": "New Delhi:", "text": "Modi hosts UK royals; India approves H5N1 poultry vaccine trial", "lat": 28.6, "lon": 77.2},
    {"id": 30, "region": "APAC", "lead": "Sydney:", "text": "Kids mRNA brain cancer trial; Australia sanctions Daniella Weiss", "lat": -33.9, "lon": 151.2},
    {"id": 31, "region": "APAC", "lead": "Cook Islands:", "text": "Cyclone Xavier holds at Cat 5; NZ lifts tsunami advisory", "lat": -21.2, "lon": -159.8},
    {"id": 32, "region": "EUROPE", "lead": "Berlin:", "text": "E5 prep Ukraine talks; Germany cuts power tax to EU floor", "lat": 52.5, "lon": 13.4},
    {"id": 33, "region": "EUROPE", "lead": "Kemerovo:", "text": "Russian An-12 transport plane crash in Siberia kills all 19 aboard", "lat": 55.3, "lon": 86.1},
    {"id": 34, "region": "EUROPE", "lead": "Cambridge:", "text": "Cambridge Dictionary names \"human\" as 2026 Word of the Year", "lat": 52.2, "lon": 0.1},
    {"id": 35, "region": "AMERICAS", "lead": "Ottawa:", "text": "PM Carney renews China currency swap and cuts pork/seafood tariffs", "lat": 45.4, "lon": -75.7},
    {"id": 36, "region": "AMERICAS", "lead": "Washington:", "text": "NSA confirms NSANet outage; PAHO revokes US measles status", "lat": 38.9, "lon": -77.0},
    {"id": 37, "region": "AMERICAS", "lead": "New York:", "text": "Dow drops 849 pts, Brent crude $91.70, Bitcoin dips near $64,000", "lat": 40.7, "lon": -74.0},
    {"id": 38, "region": "AMERICAS", "lead": "San Francisco:", "text": "Anthropic prices IPO for Thu; Optimizely breach hits 178 firms", "lat": 37.8, "lon": -122.4},
    {"id": 39, "region": "AMERICAS", "lead": "Lima & Zurich:", "text": "Peru M6.0 offshore quake; Diallo challenges Infantino for FIFA", "lat": -12.0, "lon": -77.0},
]

NUMBER_KPIS = [
    {"value": "141", "label": "Russian drones fired; 126 downed", "hex": "#1D4ED8"},
    {"value": "25.9bn km", "label": "Voyager 1 at 1 light-day from Earth", "hex": "#0F766E"},
    {"value": "$115.8bn", "label": "Nvidia Q3 +103%; gold $3,780", "hex": "#B45309"},
    {"value": "56–44", "label": "Democratic Senate after Alaska", "hex": "#B91C1C"},
]

ATTESTATION_LEFT = (
    "Every story happened, or was first reported, on Wednesday 18 November 2026; "
    "claims by warring sides are attributed. Original drawings."
)
ATTESTATION_RIGHT = (
    "Sources: Reuters · AP · AFP · BBC · Al Jazeera · CNBC · NASA · "
    "EU Commission · ONS · Eurostat · IMD · UNFCCC · WHO · Amnesty"
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
    """Parse a #RRGGBB hex string into an RGB tuple."""
    clean = code.lstrip("#")
    return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def mix_rgb(
    c1: tuple[int, int, int], c2: tuple[int, int, int], ratio: float
) -> tuple[int, int, int]:
    """Linearly interpolate between two RGB colors."""
    inv = 1.0 - ratio
    return (
        int(round(c1[0] * inv + c2[0] * ratio)),
        int(round(c1[1] * inv + c2[1] * ratio)),
        int(round(c1[2] * inv + c2[2] * ratio)),
    )


def resolve_font_path(candidates: tuple[str, ...]) -> str:
    """Find the first matching TTF font file in system or Termux font directories."""
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
    raise FileNotFoundError(f"Font not found among candidates: {candidates}")


def build_font_getter(image_font_mod):
    """Return a cached TrueType loader keyed by (font_role, px_size)."""
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
    """Return the largest font size in [min_sz, start_sz] fitting text within max_w."""
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
    """Word-wrap text into max_w x max_h using the largest legible font size."""
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
    """Draw text centered optically around (cx, cy) using textbbox bounds."""
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
    ring_w: int = 2,
) -> None:
    """Draw a circular numbered badge with optional outer halo ring."""
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=fill_rgb,
        outline=ring_rgb,
        width=ring_w if ring_rgb is not None else 0,
    )
    draw_centered(draw, cx, cy, label, font, text_rgb)


def draw_pill(
    draw,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
    text: str,
    font,
    fill_rgb: tuple[int, int, int],
    text_rgb: tuple[int, int, int],
    outline_rgb: tuple[int, int, int] | None = None,
    radius: int = 5,
) -> None:
    """Draw a crisp rounded badge pill with centered label text."""
    draw.rounded_rectangle(
        (x0, y0, x1, y1),
        radius=radius,
        fill=fill_rgb,
        outline=outline_rgb,
        width=2 if outline_rgb is not None else 0,
    )
    draw_centered(draw, (x0 + x1) / 2.0, (y0 + y1) / 2.0, text, font, text_rgb)


def draw_starburst(
    draw, cx: float, cy: float, r_out: float, r_in: float, pts_n: int, fill, outline
) -> None:
    """Draw a crisp polygonal starburst marker for strikes and interceptions."""
    verts = []
    for i in range(pts_n * 2):
        ang = i * math.pi / pts_n
        r = r_out if i % 2 == 0 else r_in
        verts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(verts, fill=fill, outline=outline)


def draw_dashed_line(
    draw, x0: float, y0: float, x1: float, y1: float, fill, width: int = 3, dash: int = 10
) -> None:
    """Draw a crisp dashed line segment between two endpoints."""
    dist = math.hypot(x1 - x0, y1 - y0)
    if dist < 1:
        return
    steps = max(1, int(dist // (dash * 1.75)))
    for i in range(steps):
        t0 = i / steps
        t1 = min(1.0, (i + 0.58) / steps)
        draw.line(
            (x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0, x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1),
            fill=fill,
            width=width,
        )


def draw_broadsheet_masthead(draw, get_font) -> None:
    """Render full-width light broadsheet masthead on warm #FAF7F0 paper + 6-region ribbon."""
    kicker_font = get_font("cond_bold", 22)
    draw.text((PAGE_MARGIN_X, 13), "THE DAY IN WORLD NEWS", font=kicker_font, fill=CRIMSON_KICKER)
    stats_txt = "39 STORIES  ·  6 CONTINENTS  ·  ONE DAY"
    sw = draw.textlength(stats_txt, font=kicker_font)
    draw.text((SUPERSAMPLE_W - PAGE_MARGIN_X - sw, 13), stats_txt, font=kicker_font, fill=SLATE_KICKER)

    # Giant full-width date masthead directly on cream paper
    mast_title = "Wednesday 18 November 2026"
    mast_font, _ = fit_single_line_font(
        draw, get_font, "mast_bold", mast_title, PAGE_WIDTH, 136, 92
    )
    bx0, by0, bx1, by1 = draw.textbbox((0, 0), mast_title, font=mast_font)
    tx = SUPERSAMPLE_W / 2.0 - (bx0 + bx1) / 2.0
    ty = 40.0 - by0
    draw.text((tx, ty), mast_title, font=mast_font, fill=INK_PRIMARY)

    # Centered italic deck clearly below Wednesday descenders
    deck_txt = "Everything on this page happened, or was first reported, on Wednesday 18 November 2026."
    deck_font, _ = fit_single_line_font(
        draw, get_font, "serif_italic", deck_txt, PAGE_WIDTH - 40, 21, 16
    )
    draw_centered(draw, SUPERSAMPLE_W / 2.0, 166, deck_txt, deck_font, INK_BODY)

    # Crisp dark rule above 6-segment colored Region Count Ribbon
    draw.line((PAGE_MARGIN_X, 182, SUPERSAMPLE_W - PAGE_MARGIN_X, 182), fill=INK_PRIMARY, width=2)

    all_stories = LEAD_STORIES + BRIEF_STORIES
    counts = {
        reg["key"]: sum(1 for item in all_stories if item["region"] == reg["key"])
        for reg in REGION_PALETTE
    }
    rib_y0, rib_y1 = 186, 218
    gap = 3
    n_seg = len(REGION_PALETTE)
    seg_w = (PAGE_WIDTH - (n_seg - 1) * gap) / n_seg
    rib_font = get_font("cond_bold", 18)

    for idx, reg in enumerate(REGION_PALETTE):
        sx0 = PAGE_MARGIN_X + idx * (seg_w + gap)
        sx1 = (SUPERSAMPLE_W - PAGE_MARGIN_X) if idx == n_seg - 1 else (sx0 + seg_w)
        col = rgb_from_hex(reg["hex"])
        draw.rectangle((sx0, rib_y0, sx1, rib_y1), fill=col)
        seg_label = f"{reg['name']} {counts[reg['key']]}"
        draw_centered(draw, (sx0 + sx1) / 2.0, (rib_y0 + rib_y1) / 2.0, seg_label, rib_font, (255, 255, 255))


def draw_scene_apec(image_cls, draw_cls, get_font, w: int, h: int):
    """#1: Warm sunset Shenzhen skyline, presidential jet on red carpet tarmac, 3-nation podium & pills."""
    sc = image_cls.new("RGB", (w, h), (254, 215, 170))
    d = draw_cls.Draw(sc)
    # Warm sunset sky bands + glowing sun
    d.rectangle((0, 0, w, 54), fill=(253, 186, 116))
    d.rectangle((0, 54, w, 108), fill=(254, 215, 170))
    d.rectangle((0, 108, w, 146), fill=(254, 240, 199))
    d.ellipse((248, 34, 336, 122), fill=(254, 249, 195))

    # Distant Shenzhen skyline silhouettes + tapered Ping An spire
    towers = [
        (216, 72, 254, 146, (148, 163, 184)),
        (258, 52, 298, 146, (100, 116, 139)),
        (304, 82, 344, 146, (148, 163, 184)),
        (398, 44, 438, 146, (100, 116, 139)),
        (444, 62, 488, 146, (148, 163, 184)),
        (494, 78, 536, 146, (100, 116, 139)),
        (542, 54, 584, 146, (148, 163, 184)),
        (590, 86, 628, 146, (100, 116, 139)),
    ]
    for x0, y0, x1, y1, col in towers:
        d.rectangle((x0, y0, x1, y1), fill=col)
    d.polygon([(354, 146), (366, 22), (373, 6), (380, 22), (392, 146)], fill=(71, 85, 105))

    # Tarmac & red welcome carpet
    d.rectangle((0, 144, w, h), fill=(226, 232, 240))
    d.line((0, 144, w, 144), fill=(71, 85, 105), width=2)
    d.polygon([(148, 146), (296, 146), (322, 198), (124, 198)], fill=(185, 28, 28))

    # Presidential jet on left
    d.polygon([(28, 108), (18, 58), (48, 58), (68, 108)], fill=(30, 58, 138))
    d.rectangle((36, 100, 226, 126), fill=(255, 255, 255), outline=(30, 58, 138), width=2)
    d.polygon([(226, 100), (260, 116), (226, 126)], fill=(255, 255, 255), outline=(30, 58, 138))
    d.line((38, 113, 242, 113), fill=(29, 78, 216), width=4)
    for wx in range(62, 206, 16):
        d.rectangle((wx, 105, wx + 8, 110), fill=(30, 58, 138))
    d.polygon([(102, 118), (76, 138), (132, 138), (144, 118)], fill=(148, 163, 184))
    d.line((98, 126, 98, 144), fill=INK_PRIMARY, width=3)
    d.line((178, 126, 178, 144), fill=INK_PRIMARY, width=3)
    d.line((192, 120, 166, 146), fill=(71, 85, 105), width=4)

    # Summit podium & 3 national flags (China, USA, Russia)
    d.rectangle((360, 136, 610, 170), fill=(120, 53, 15), outline=(69, 26, 3), width=2)
    d.rectangle((368, 130, 602, 138), fill=(217, 119, 6))
    # China flag
    d.line((402, 76, 402, 130), fill=(51, 65, 85), width=3)
    d.rectangle((404, 76, 456, 110), fill=(220, 38, 38), outline=(153, 27, 27), width=1)
    d.ellipse((410, 82, 422, 94), fill=(250, 204, 21))
    # USA flag
    d.line((484, 76, 484, 130), fill=(51, 65, 85), width=3)
    d.rectangle((486, 76, 538, 110), fill=(255, 255, 255), outline=(148, 163, 184), width=1)
    for sy in range(76, 110, 6):
        d.rectangle((486, sy, 538, min(sy + 3, 110)), fill=(220, 38, 38))
    d.rectangle((486, 76, 508, 94), fill=(30, 58, 138))
    # Russia flag
    d.line((566, 76, 566, 130), fill=(51, 65, 85), width=3)
    d.rectangle((568, 76, 620, 87), fill=(255, 255, 255))
    d.rectangle((568, 87, 620, 99), fill=(29, 78, 216))
    d.rectangle((568, 99, 620, 110), fill=(220, 38, 38))
    d.rectangle((568, 76, 620, 110), outline=(148, 163, 184), width=1)

    # Crisp white editorial pills at bottom
    pill_font = get_font("cond_bold", 16)
    draw_pill(d, 14, 174, 214, 200, "XI · TRUMP · PUTIN", pill_font, (255, 255, 255), INK_PRIMARY, outline_rgb=INK_PRIMARY)
    draw_pill(d, 412, 174, 634, 200, "3-WAY TALKS · THURSDAY", pill_font, (255, 255, 255), CRIMSON_KICKER, outline_rgb=INK_PRIMARY)
    return sc


def draw_scene_gulf(image_cls, draw_cls, get_font, w: int, h: int):
    """#2: High-contrast Persian Gulf map with Kuwait/Bahrain intercepts, Qeshm strike, and Hormuz tanker."""
    sc = image_cls.new("RGB", (w, h), (30, 58, 95))
    d = draw_cls.Draw(sc)

    land_fill = (218, 206, 180)
    land_edge = (140, 126, 102)
    # Iran north/east shore
    d.polygon(
        [(165, 0), (w, 0), (w, 124), (576, 118), (528, 130), (478, 126), (434, 104), (366, 88), (288, 66), (222, 42), (176, 18)],
        fill=land_fill,
        outline=land_edge,
    )
    # Iraq / Kuwait northwest
    d.polygon(
        [(0, 0), (165, 0), (174, 28), (132, 62), (104, 96), (78, 122), (0, 128)],
        fill=land_fill,
        outline=land_edge,
    )
    # Saudi Arabia / Bahrain / UAE south shore
    d.polygon(
        [(0, 128), (104, 124), (164, 144), (198, 162), (236, 168), (254, 142), (278, 174), (368, 178), (464, 156), (506, 146), (522, 168), (566, h), (0, h)],
        fill=land_fill,
        outline=land_edge,
    )
    # Qeshm Island & Bahrain marker
    d.polygon([(452, 118), (496, 109), (504, 118), (462, 128)], fill=(254, 202, 202), outline=(185, 28, 28))
    d.ellipse((186, 126, 202, 142), fill=(254, 215, 170), outline=(185, 28, 28), width=2)

    lbl_font = get_font("cond_bold", 15)
    d.text((16, 16), "IRAQ", font=lbl_font, fill=INK_PRIMARY)
    d.text((20, 68), "KUWAIT", font=lbl_font, fill=INK_PRIMARY)
    d.text((394, 24), "IRAN", font=lbl_font, fill=INK_PRIMARY)
    d.text((24, 174), "SAUDI ARABIA", font=lbl_font, fill=INK_PRIMARY)
    d.text((164, 168), "BAHRAIN", font=lbl_font, fill=INK_PRIMARY)
    d.text((444, 84), "QESHM", font=lbl_font, fill=(153, 27, 27))
    d.text((554, 126), "HORMUZ", font=lbl_font, fill=(226, 232, 240))

    # Drone arcs from Iran + bright intercept starbursts
    draw_dashed_line(d, 336, 78, 114, 72, (248, 113, 113), width=3, dash=9)
    draw_dashed_line(d, 360, 86, 206, 126, (248, 113, 113), width=3, dash=9)
    draw_starburst(d, 134, 72, 15, 6, 8, (254, 240, 138), (220, 38, 38))
    draw_starburst(d, 224, 120, 15, 6, 8, (254, 240, 138), (220, 38, 38))

    # US Strike marker on Qeshm
    draw_starburst(d, 478, 118, 16, 7, 8, (239, 68, 68), (255, 255, 255))
    draw_pill(d, 332, 124, 430, 148, "US STRIKE", get_font("cond_bold", 14), (185, 28, 28), (255, 255, 255))

    # White intercept pill
    draw_pill(d, 136, 16, 304, 42, "DRONES INTERCEPTED", get_font("cond_bold", 14), (255, 255, 255), INK_PRIMARY, outline_rgb=INK_PRIMARY)

    # Hormuz tanker + alert pill
    d.polygon([(520, 154), (566, 154), (558, 165), (524, 165)], fill=(15, 23, 42), outline=(226, 232, 240))
    d.rectangle((532, 146, 544, 154), fill=(239, 68, 68))
    draw_pill(d, 456, 176, 634, 202, "TANKER HIT · HORMUZ", get_font("cond_bold", 14), (185, 28, 28), (255, 255, 255))
    return sc


def draw_scene_voyager(image_cls, draw_cls, get_font, w: int, h: int):
    """#3: Deep starry space, glowing Earth, gold 1 light-day ruler, and Voyager 1 with dish, boom & golden record."""
    sc = image_cls.new("RGB", (w, h), (10, 17, 40))
    d = draw_cls.Draw(sc)

    for i in range(85):
        sx = (i * 97 + 19) % w
        sy = (i * 53 + 11) % h
        sr = 2 if i % 6 == 0 else 1
        scol = (253, 224, 71) if i % 5 == 0 else (226, 232, 240)
        d.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=scol)

    # Glowing blue Earth on left
    ex, ey, er = 82, 102, 34
    d.ellipse((ex - er - 6, ey - er - 6, ex + er + 6, ey + er + 6), outline=(56, 189, 248), width=2)
    d.ellipse((ex - er, ey - er, ex + er, ey + er), fill=(29, 78, 216))
    d.polygon([(64, 80), (90, 84), (84, 110), (68, 114)], fill=(34, 197, 94))
    d.polygon([(94, 88), (112, 98), (100, 118), (88, 110)], fill=(34, 197, 94))
    draw_centered(d, ex, 158, "EARTH", get_font("cond_bold", 17), (147, 197, 253))

    # Gold measurement ruler across center
    rx0, rx1, ry = 132, 492, 104
    d.line((rx0, ry - 10, rx0, ry + 10), fill=(250, 204, 21), width=3)
    d.line((rx1, ry - 10, rx1, ry + 10), fill=(250, 204, 21), width=3)
    draw_dashed_line(d, rx0 + 4, ry, rx1 - 4, ry, (250, 204, 21), width=3, dash=12)
    draw_centered(d, (rx0 + rx1) / 2.0, 62, "1 LIGHT-DAY  ·  25.9 BILLION KM", get_font("cond_bold", 20), (253, 224, 71))
    draw_centered(d, (rx0 + rx1) / 2.0, 134, "24-HOUR RADIO SIGNAL", get_font("sans_bold", 16), (226, 232, 240))

    # Detailed Voyager 1 probe on right (dish, boom, golden record)
    vx, vy = 548, 96
    d.line((vx + 8, vy - 6, 626, 22), fill=(203, 213, 225), width=3)  # magnetometer boom
    d.line((vx + 8, vy + 8, 610, 144), fill=(148, 163, 184), width=4)  # RTG boom
    d.ellipse((vx - 32, vy - 24, vx + 12, vy + 24), fill=(248, 250, 252), outline=(148, 163, 184), width=2)
    d.ellipse((vx - 22, vy - 14, vx + 2, vy + 14), outline=(148, 163, 184), width=1)
    d.rectangle((vx + 4, vy - 12, vx + 28, vy + 12), fill=(180, 83, 9), outline=(253, 224, 71), width=1)
    # Golden Record disc on bus
    d.ellipse((vx + 10, vy - 6, vx + 22, vy + 6), fill=(250, 204, 21), outline=(146, 64, 14), width=1)
    d.line((vx - 10, vy, vx - 34, vy - 18), fill=(51, 65, 85), width=2)
    d.line((vx - 10, vy, vx - 34, vy + 18), fill=(51, 65, 85), width=2)
    draw_centered(d, 548, 174, "VOYAGER 1", get_font("cond_bold", 17), (253, 224, 71))
    return sc


def draw_scene_eu_loan(image_cls, draw_cls, get_font, w: int, h: int):
    """#4: Royal blue EU stars + giant €45bn badge & Ukraine flag."""
    sc = image_cls.new("RGB", (w, h), (30, 58, 138))
    d = draw_cls.Draw(sc)

    # Circle of 12 EU gold stars on left
    cx, cy, r = 92, 72, 48
    for i in range(12):
        ang = i * (2.0 * math.pi / 12.0)
        sx = cx + r * math.cos(ang)
        sy = cy + r * math.sin(ang)
        draw_starburst(d, sx, sy, 6, 2.5, 5, (250, 204, 21), (250, 204, 21))

    # Giant €45bn badge
    draw_centered(d, 256, 46, "€45bn", get_font("serif_bold", 48), (255, 255, 255))
    draw_centered(d, 256, 82, "2027 UKRAINE LOAN", get_font("cond_bold", 16), (253, 224, 71))

    # Ukraine flag bar on bottom-right
    d.rectangle((184, 102, 336, 117), fill=(37, 99, 235))
    d.rectangle((184, 117, 336, 132), fill=(250, 204, 21))
    d.rectangle((184, 102, 336, 132), outline=(255, 255, 255), width=1)
    return sc


def draw_scene_ukraine_drones(image_cls, draw_cls, get_font, w: int, h: int):
    """#5: Night sky over Ukrainian skyline & power pylon with drones, intercepts & white pill."""
    sc = image_cls.new("RGB", (w, h), (22, 33, 56))
    d = draw_cls.Draw(sc)

    # Subtle city horizon & power pylon
    d.rectangle((0, 96, w, h), fill=(30, 41, 59))
    for bx, bw, bh in [(18, 28, 36), (54, 22, 48), (84, 34, 28), (126, 26, 42)]:
        d.rectangle((bx, 96 - bh, bx + bw, 96), fill=(15, 23, 42))
        d.rectangle((bx + 6, 96 - bh + 8, bx + 12, 96 - bh + 16), fill=(250, 204, 21))
    # High-voltage power pylon on right
    px = 296
    d.line((px, 34, px - 24, 104), fill=(148, 163, 184), width=3)
    d.line((px, 34, px + 24, 104), fill=(148, 163, 184), width=3)
    d.line((px - 32, 56, px + 32, 56), fill=(148, 163, 184), width=3)
    d.line((px - 36, 76, px + 36, 76), fill=(148, 163, 184), width=3)

    # Incoming drones & intercept bursts
    for dx, dy in [(186, 26), (242, 22), (336, 30)]:
        d.polygon([(dx - 16, dy), (dx + 8, dy - 6), (dx + 2, dy + 8)], fill=(203, 213, 225))
        draw_dashed_line(d, dx + 2, dy + 6, dx + 18, dy + 24, (248, 113, 113), width=2, dash=4)
    draw_starburst(d, 208, 52, 13, 5, 7, (254, 240, 138), (220, 38, 38))
    draw_starburst(d, 264, 48, 11, 5, 7, (254, 240, 138), (220, 38, 38))

    # Crisp white pill
    draw_pill(d, 72, 108, 312, 136, "141 FIRED · 126 DOWNED", get_font("cond_bold", 16), (255, 255, 255), INK_PRIMARY, outline_rgb=INK_PRIMARY)
    return sc


def draw_scene_alaska_senate(image_cls, draw_cls, get_font, w: int, h: int):
    """#6: Blue Alaska silhouette + 56 DEM · 44 REP 100-dot Senate grid."""
    sc = image_cls.new("RGB", (w, h), (234, 244, 253))
    d = draw_cls.Draw(sc)

    # Blue Alaska silhouette on left
    ak = [(26, 24), (104, 18), (104, 72), (132, 98), (118, 102), (96, 76), (62, 82), (24, 106), (14, 96), (34, 72), (20, 48)]
    d.polygon(ak, fill=(29, 78, 216), outline=(15, 23, 42))
    draw_centered(d, 72, 124, "ALASKA · PELTOLA", get_font("cond_bold", 15), (29, 78, 216))

    # 56 DEM · 44 REP header & column-major 100-dot Senate grid on right
    draw_centered(d, 262, 21, "56 DEM · 44 REP", get_font("cond_bold", 19), INK_PRIMARY)
    gx0, gy0 = 178, 38
    step_x, step_y = 18, 8
    for col in range(10):
        for row in range(10):
            idx = col * 10 + row
            cx = gx0 + col * step_x
            cy = gy0 + row * step_y
            dot_col = (29, 78, 216) if idx < 56 else (185, 28, 28)
            d.ellipse((cx - 3.4, cy - 3.4, cx + 3.4, cy + 3.4), fill=dot_col)
    draw_pill(d, 178, 118, 344, 138, "US SENATE MAJORITY", get_font("cond_bold", 13), INK_PRIMARY, (255, 255, 255))
    return sc


def draw_scene_cop31(image_cls, draw_cls, get_font, w: int, h: int):
    """#7: Earth globe, red thermometer, torn DRAFT/PHASE-OUT doc & 35x35 GOAL badge."""
    sc = image_cls.new("RGB", (w, h), (236, 253, 245))
    d = draw_cls.Draw(sc)

    # Globe on left
    gx, gy, gr = 56, 60, 38
    d.ellipse((gx - gr, gy - gr, gx + gr, gy + gr), fill=(56, 189, 248), outline=(3, 105, 161), width=2)
    d.polygon([(36, 40), (62, 34), (60, 62), (40, 66)], fill=(21, 128, 61))
    d.polygon([(66, 48), (86, 56), (78, 86), (62, 76)], fill=(21, 128, 61))

    # Red thermometer
    d.rounded_rectangle((108, 16, 122, 94), radius=7, fill=(255, 255, 255), outline=(51, 65, 85), width=2)
    d.rectangle((112, 32, 118, 96), fill=(185, 28, 28))
    d.ellipse((104, 86, 126, 108), fill=(185, 28, 28), outline=(51, 65, 85), width=2)

    # Torn COP31 DRAFT / PHASE-OUT document split by red jagged line
    left_doc = [(146, 14), (242, 14), (236, 36), (248, 56), (234, 78), (244, 100), (146, 100)]
    right_doc = [(254, 14), (368, 14), (368, 100), (256, 100), (246, 78), (260, 56), (248, 36)]
    d.polygon(left_doc, fill=(255, 255, 255), outline=(100, 116, 139))
    d.polygon(right_doc, fill=(255, 255, 255), outline=(100, 116, 139))
    d.line([(247, 12), (241, 36), (253, 56), (239, 78), (249, 102)], fill=CRIMSON_KICKER, width=2)
    draw_centered(d, 194, 38, "COP31", get_font("cond_bold", 17), INK_PRIMARY)
    draw_centered(d, 194, 68, "PHASE-", get_font("cond_bold", 16), CRIMSON_KICKER)
    draw_centered(d, 312, 38, "DRAFT", get_font("cond_bold", 17), INK_PRIMARY)
    draw_centered(d, 312, 68, "OUT", get_font("cond_bold", 16), CRIMSON_KICKER)

    # 35x35 GOAL badge at bottom
    draw_pill(d, 144, 110, 368, 136, "35x35 GOAL · 75 BACK", get_font("cond_bold", 15), (15, 118, 110), (255, 255, 255))
    draw_pill(d, 14, 112, 132, 136, "ANTALYA", get_font("cond_bold", 14), INK_PRIMARY, (255, 255, 255))
    return sc


def draw_scene_inflation(image_cls, draw_cls, get_font, w: int, h: int):
    """#8: Side-by-side inflation bar chart for UK 3.6% (1-yr high) and Euro area 4.0%."""
    sc = image_cls.new("RGB", (w, h), (244, 247, 250))
    d = draw_cls.Draw(sc)

    # Subtle gridlines & baseline
    for gy in (28, 56, 84):
        d.line((26, gy, w - 26, gy), fill=(216, 224, 234), width=1)
    base_y = 110
    d.line((26, base_y, w - 26, base_y), fill=INK_PRIMARY, width=2)

    # UK 3.6% bar
    d.rectangle((54, 44, 152, base_y), fill=(29, 78, 216))
    draw_centered(d, 103, 28, "3.6%", get_font("serif_bold", 22), (29, 78, 216))
    draw_centered(d, 103, 76, "1-YR HIGH", get_font("cond_bold", 14), (255, 255, 255))
    draw_centered(d, 103, 126, "UK CPI", get_font("cond_bold", 16), INK_PRIMARY)

    # Euro Area 4.0% bar
    d.rectangle((224, 32, 322, base_y), fill=(185, 28, 28))
    draw_centered(d, 273, 18, "4.0%", get_font("serif_bold", 22), (185, 28, 28))
    draw_centered(d, 273, 70, "ENERGY +21%", get_font("cond_bold", 13), (255, 255, 255))
    draw_centered(d, 273, 126, "EURO AREA", get_font("cond_bold", 16), INK_PRIMARY)
    return sc


def draw_scene_cyclone(image_cls, draw_cls, get_font, w: int, h: int):
    """#9: East India coast ODISHA/ANDHRA + concentric Cyclone Akvan spiral + 145 KM/H · 204K EVAC."""
    sc = image_cls.new("RGB", (w, h), (207, 232, 247))
    d = draw_cls.Draw(sc)

    # East India coastline
    d.polygon(
        [(0, 0), (160, 0), (138, 34), (108, 66), (84, 98), (74, h), (0, h)],
        fill=(226, 216, 194),
        outline=(152, 138, 114),
    )
    lbl = get_font("cond_bold", 14)
    d.text((14, 18), "ODISHA", font=lbl, fill=INK_PRIMARY)
    d.text((12, 72), "ANDHRA", font=lbl, fill=INK_PRIMARY)

    # Concentric cyclone spiral in Bay of Bengal
    cx, cy = 260, 62
    for offset in (0.0, math.pi):
        pts = []
        for t in range(38):
            ang = offset + t * 0.17
            rad = 9.0 + t * 1.45
            pts.append((cx + rad * math.cos(ang), cy + rad * 0.72 * math.sin(ang)))
        d.line(pts, fill=(15, 118, 110), width=6)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=(185, 28, 28), outline=(255, 255, 255), width=2)

    draw_dashed_line(d, cx - 12, cy - 6, 132, 38, (185, 28, 28), width=3, dash=6)
    d.polygon([(124, 36), (138, 31), (134, 46)], fill=(185, 28, 28))

    draw_pill(d, 108, 112, 368, 138, "145 KM/H · 204K EVAC", get_font("cond_bold", 15), INK_PRIMARY, (255, 255, 255))
    return sc


def draw_scene_sudan(image_cls, draw_cls, get_font, w: int, h: int):
    """#10: Desert skyline, drone, and red target reticle over El Obeid."""
    sc = image_cls.new("RGB", (w, h), (242, 224, 190))
    d = draw_cls.Draw(sc)
    d.rectangle((0, 0, w, 66), fill=(252, 211, 152))

    # El Obeid desert buildings horizon
    d.rectangle((0, 94, w, h), fill=(208, 178, 132))
    for bx, bw, bh in [(16, 36, 26), (58, 28, 38), (94, 46, 22), (248, 38, 30), (294, 44, 40), (344, 28, 24)]:
        d.rectangle((bx, 94 - bh, bx + bw, 94), fill=(120, 88, 58))

    # Drone silhouette top-right (swept wing + tail fin)
    d.polygon([(288, 26), (336, 18), (324, 34)], fill=INK_PRIMARY)
    d.line((308, 14, 326, 38), fill=INK_PRIMARY, width=3)
    draw_dashed_line(d, 294, 32, 196, 70, (185, 28, 28), width=3, dash=5)

    # Red target reticle centered on town
    tx, ty = 188, 72
    d.ellipse((tx - 30, ty - 30, tx + 30, ty + 30), outline=(185, 28, 28), width=3)
    d.ellipse((tx - 15, ty - 15, tx + 15, ty + 15), outline=(185, 28, 28), width=3)
    d.line((tx - 38, ty, tx + 38, ty), fill=(185, 28, 28), width=2)
    d.line((tx, ty - 38, tx, ty + 38), fill=(185, 28, 28), width=2)

    draw_pill(d, 74, 110, 310, 137, "EL OBEID · 37 KILLED", get_font("cond_bold", 16), (185, 28, 28), (255, 255, 255))
    return sc


def draw_scene_nvidia_gold(image_cls, draw_cls, get_font, w: int, h: int):
    """#11: Split graphic showing green Nvidia AI GPU chip ($115.8bn +103%) & gold bars ($3,780 -2%)."""
    sc = image_cls.new("RGB", (w, h), (254, 243, 199))
    d = draw_cls.Draw(sc)

    mid = w // 2
    # Left half: dark silicon + green GPU chip
    d.rectangle((0, 0, mid, h), fill=(15, 23, 42))
    for px in range(50, mid - 46, 14):
        d.line((px, 14, px, 26), fill=(245, 158, 11), width=3)
        d.line((px, 92, px, 104), fill=(245, 158, 11), width=3)
    d.rectangle((38, 24, mid - 38, 94), fill=(6, 78, 59), outline=(16, 185, 129), width=3)
    draw_centered(d, mid / 2.0, 48, "$115.8bn", get_font("cond_bold", 24), (255, 255, 255))
    draw_centered(d, mid / 2.0, 74, "NVIDIA Q3", get_font("cond_bold", 14), (110, 231, 183))
    draw_pill(d, 26, 110, mid - 26, 136, "+103% DATA CTR", get_font("cond_bold", 14), (16, 185, 129), (6, 78, 59))

    # Right half: gold bullion bars + downward crimson arrow
    d.polygon([(mid + 24, 88), (mid + 88, 88), (mid + 78, 66), (mid + 34, 66)], fill=(234, 179, 8), outline=(146, 64, 14))
    d.polygon([(mid + 92, 88), (mid + 156, 88), (mid + 146, 66), (mid + 102, 66)], fill=(234, 179, 8), outline=(146, 64, 14))
    d.polygon([(mid + 58, 66), (mid + 122, 66), (mid + 112, 44), (mid + 68, 44)], fill=(250, 204, 21), outline=(146, 64, 14))

    # Downward crimson trend arrow
    d.line((mid + 132, 22, mid + 168, 54), fill=(185, 28, 28), width=5)
    d.polygon([(mid + 172, 58), (mid + 154, 56), (mid + 168, 40)], fill=(185, 28, 28))
    draw_centered(d, mid + 66, 24, "GOLD", get_font("cond_bold", 16), (146, 64, 14))
    draw_pill(d, mid + 24, 106, w - 20, 136, "$3,780 (-2%)", get_font("cond_bold", 15), (185, 28, 28), (255, 255, 255))
    return sc


def draw_scene_gtavi(image_cls, draw_cls, get_font, w: int, h: int):
    """#12: Dusk neon skyline with palms, white game controller, and MIDNIGHT IN NZ pill."""
    sc = image_cls.new("RGB", (w, h), (59, 14, 84))
    d = draw_cls.Draw(sc)

    # Dusk neon sunset sky bands & sun
    d.rectangle((0, 48, w, 92), fill=(157, 23, 77))
    d.rectangle((0, 92, w, h), fill=(15, 23, 42))
    d.ellipse((248, 20, 326, 98), fill=(251, 146, 60))
    d.rectangle((242, 62, 332, 68), fill=(157, 23, 77))
    d.rectangle((242, 78, 332, 84), fill=(157, 23, 77))

    # Dusk skyline & palm tree silhouettes
    for bx, bw, bh in [(12, 26, 48), (44, 22, 64), (72, 28, 38), (318, 26, 54), (350, 24, 42)]:
        d.rectangle((bx, 96 - bh, bx + bw, 96), fill=(15, 23, 42))
    d.line((36, 98, 48, 34), fill=(15, 23, 42), width=5)
    for ang in (-2.5, -1.6, -0.7, 0.2):
        d.line((48, 34, 48 + 24 * math.cos(ang), 34 + 18 * math.sin(ang)), fill=(15, 23, 42), width=4)

    # White game controller centered
    d.rounded_rectangle((116, 30, 252, 92), radius=24, fill=(248, 250, 252), outline=(148, 163, 184), width=2)
    d.line((148, 50, 148, 72), fill=INK_PRIMARY, width=6)
    d.line((137, 61, 159, 61), fill=INK_PRIMARY, width=6)
    d.ellipse((212, 46, 224, 58), fill=(236, 72, 153))
    d.ellipse((226, 60, 238, 72), fill=(6, 182, 212))

    draw_pill(d, 18, 108, 366, 136, "MIDNIGHT IN NZ · 15M PRE-ORDERS", get_font("cond_bold", 15), (255, 255, 255), INK_PRIMARY)
    return sc


def draw_scene_gaza_horn(image_cls, draw_cls, get_font, w: int, h: int):
    """#13: Split crisis scene: flooded Gaza tents + broken olive branch | Ethiopia <-> Eritrea border arrows."""
    sc = image_cls.new("RGB", (w, h), (226, 232, 240))
    d = draw_cls.Draw(sc)

    mid = w // 2
    # Left half: Gaza rain, broken olive branch, flooded tents
    for rx in range(14, mid - 8, 24):
        d.line((rx, 6, rx - 8, 40), fill=(100, 116, 139), width=2)
    d.line((24, 24, 84, 18), fill=(77, 124, 15), width=4)
    d.line((108, 18, 168, 24), fill=(77, 124, 15), width=4)
    for lx, ly in [(42, 14), (66, 12), (126, 12), (150, 14)]:
        d.ellipse((lx - 7, ly - 4, lx + 7, ly + 4), fill=(101, 163, 13))
    d.line((91, 10, 103, 32), fill=(185, 28, 28), width=3)
    d.line((103, 10, 91, 32), fill=(185, 28, 28), width=3)
    for tx in (52, 136):
        d.polygon([(tx, 46), (tx - 34, 98), (tx + 34, 98)], fill=(255, 255, 255), outline=(71, 85, 105))
        d.polygon([(tx, 66), (tx - 10, 98), (tx + 10, 98)], fill=(51, 65, 85))
    d.rectangle((0, 94, mid, h), fill=(2, 132, 199))
    draw_pill(d, 16, 110, mid - 16, 136, "GAZA TRUCE RISK", get_font("cond_bold", 14), INK_PRIMARY, (253, 224, 71))

    # Divider
    d.line((mid, 0, mid, h), fill=INK_PRIMARY, width=2)

    # Right half: Ethiopia <-> Eritrea border confrontation
    d.rectangle((mid + 1, 0, w, h), fill=(237, 226, 202))
    bx = mid + (w - mid) // 2
    draw_dashed_line(d, bx, 12, bx, 104, INK_PRIMARY, width=3, dash=6)
    draw_centered(d, mid + 48, 24, "ETHIOPIA", get_font("cond_bold", 14), (21, 128, 61))
    draw_centered(d, w - 48, 24, "ERITREA", get_font("cond_bold", 14), (185, 28, 28))
    # Opposing arrows
    d.line((mid + 18, 64, bx - 14, 64), fill=(21, 128, 61), width=6)
    d.polygon([(bx - 6, 64), (bx - 22, 54), (bx - 22, 74)], fill=(21, 128, 61))
    d.line((w - 18, 64, bx + 14, 64), fill=(185, 28, 28), width=6)
    d.polygon([(bx + 6, 64), (bx + 22, 54), (bx + 22, 74)], fill=(185, 28, 28))
    draw_pill(d, mid + 14, 110, w - 14, 136, "HORN TROOPS MASS", get_font("cond_bold", 14), (180, 83, 9), (255, 255, 255))
    return sc


SCENE_ARTISTS = {
    "apec": draw_scene_apec,
    "gulf": draw_scene_gulf,
    "voyager": draw_scene_voyager,
    "eu_loan": draw_scene_eu_loan,
    "ukraine_drones": draw_scene_ukraine_drones,
    "alaska_senate": draw_scene_alaska_senate,
    "cop31": draw_scene_cop31,
    "inflation": draw_scene_inflation,
    "cyclone": draw_scene_cyclone,
    "sudan": draw_scene_sudan,
    "nvidia_gold": draw_scene_nvidia_gold,
    "gtavi": draw_scene_gtavi,
    "gaza_horn": draw_scene_gaza_horn,
}


def draw_lead_columns(
    base_img, draw, get_font, image_cls, draw_cls, scene_artists: dict
) -> None:
    """Render Rows 1-3 as open broadsheet columns (6px top color bar, zero 4-sided card boxes)."""
    row_specs = [
        (1, 3, 24, ROW1_TOP, ROW1_BOT, 210, 14, 37, 24, 23, 18),
        (2, 5, 18, ROW2_TOP, ROW2_BOT, 145, 12, 25, 18, 19, 15),
        (3, 5, 18, ROW3_TOP, ROW3_BOT, 145, 12, 25, 18, 19, 15),
    ]
    for row_num, cols, gap, ry0, ry1, ill_h, badge_r, hl_max, hl_min, sm_max, sm_min in row_specs:
        cards = [c for c in LEAD_STORIES if c["row"] == row_num]
        col_w = (PAGE_WIDTH - (cols - 1) * gap) // cols

        for idx, card in enumerate(cards):
            cx0 = PAGE_MARGIN_X + idx * (col_w + gap)
            cx1 = (SUPERSAMPLE_W - PAGE_MARGIN_X) if idx == cols - 1 else (cx0 + col_w)
            reg_col = rgb_from_hex(REGION_LOOKUP[card["region"]]["hex"])

            if idx > 0:
                div_x = cx0 - gap / 2.0
                draw.line((div_x, ry0, div_x, ry1 - 4), fill=RULE_DIVIDER, width=1)

            # Bold 6px region-colored top accent bar (no 4-sided box)
            draw.rectangle((cx0, ry0, cx1, ry0 + 6), fill=reg_col)

            # Full-column-width vector artwork directly below top bar
            iy0 = ry0 + 8
            iy1 = iy0 + ill_h
            iw, ih = cx1 - cx0, ill_h
            artist = scene_artists.get(card["scene"])
            if artist is not None:
                scene_img = artist(image_cls, draw_cls, get_font, iw, ih)
                base_img.paste(scene_img, (cx0, iy0))
            else:
                draw.rectangle((cx0, iy0, cx1, iy1), fill=PAPER_WARM_ALT)
            draw.rectangle((cx0, iy0, cx1, iy1), outline=RULE_DIVIDER, width=1)

            # Metadata strip (badge + beat + wire source)
            meta_cy = iy1 + (19 if row_num == 1 else 17)
            bx = cx0 + badge_r
            badge_font = get_font("sans_bold", 16 if row_num == 1 else 14)
            draw_badge_circle(
                draw, bx, meta_cy, badge_r, str(card["id"]), reg_col, (255, 255, 255), badge_font
            )

            src_font = get_font("cond_bold", 16 if row_num == 1 else 13)
            src_w = draw.textlength(card["source"], font=src_font)
            src_x = cx1 - src_w
            draw_centered(draw, src_x + src_w / 2.0, meta_cy, card["source"], src_font, INK_MUTED)

            beat_x = bx + badge_r + 8
            max_beat_w = int(src_x - beat_x - 8)
            beat_font, _ = fit_single_line_font(
                draw,
                get_font,
                "cond_bold",
                card["beat"],
                max(max_beat_w, 40),
                18 if row_num == 1 else 15,
                11,
            )
            bw = draw.textlength(card["beat"], font=beat_font)
            draw_centered(draw, beat_x + bw / 2.0, meta_cy, card["beat"], beat_font, reg_col)

            # Bold serif headline across full column width
            inner_w = cx1 - cx0
            hl_top = meta_cy + badge_r + 6
            hl_h = 92 if row_num == 1 else 90
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
                draw.text((cx0, hy), line, font=hl_font, fill=INK_PRIMARY)
                hy += hl_lh

            # Summary body
            sum_top = hy + (8 if row_num == 1 else 6)
            sum_h = (ry1 - 4) - sum_top
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
                draw.text((cx0, sy), line, font=sm_font, fill=INK_BODY)
                sy += sm_lh

    draw.line((PAGE_MARGIN_X, 687, SUPERSAMPLE_W - PAGE_MARGIN_X, 687), fill=RULE_DIVIDER, width=1)
    draw.line((PAGE_MARGIN_X, 1075, SUPERSAMPLE_W - PAGE_MARGIN_X, 1075), fill=RULE_DIVIDER, width=1)
    draw.line((PAGE_MARGIN_X, 1464, SUPERSAMPLE_W - PAGE_MARGIN_X, 1464), fill=INK_PRIMARY, width=2)


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
    """Place numbered pins close to true coordinates without overlapping each other."""
    anchors = []
    for item in pin_items:
        ax, ay = geo_to_px(item["lat"], item["lon"], bounds, width, height)
        anchors.append((item, ax, ay))

    placed: list[dict] = []
    min_dist = 2.0 * pin_r + 7.0
    pad = pin_r + 4.0
    radii = [0.0, 1.9 * pin_r, 2.8 * pin_r, 3.8 * pin_r, 4.8 * pin_r, 5.8 * pin_r]
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
        placed.append({"item": item, "ax": ax, "ay": ay, "px": best_pos[0], "py": best_pos[1]})
    return placed


def draw_where_and_numbers(base_img, draw, get_font, image_cls, draw_cls) -> None:
    """Render bottom-left WHERE IT HAPPENED world map and open-typography BY THE NUMBERS callouts."""
    left_x0, left_x1 = PAGE_MARGIN_X, 685
    map_y0, map_y1 = BOTTOM_TOP, 1810

    hdr_font = get_font("cond_bold", 20)
    note_font = get_font("cond_bold", 14)
    draw.text((left_x0, map_y0), "WHERE IT HAPPENED", font=hdr_font, fill=INK_PRIMARY)
    note_txt = "1–13 pins  ·  14–39 dots"
    nw = draw.textlength(note_txt, font=note_font)
    draw.text((left_x1 - nw, map_y0 + 4), note_txt, font=note_font, fill=INK_MUTED)

    vx0, vy0, vx1, vy1 = left_x0, map_y0 + 28, left_x1, 1784
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

    # Dots for stories #14-#39
    for b_item in BRIEF_STORIES:
        bx, by = geo_to_px(b_item["lat"], b_item["lon"], ATLAS_BOUNDS, vw, vh)
        col = rgb_from_hex(REGION_LOOKUP[b_item["region"]]["hex"])
        md.ellipse((bx - 4.2, by - 4.2, bx + 4.2, by + 4.2), fill=col, outline=(255, 255, 255), width=1)

    # Terrestrial numbered pins (excluding #3 Voyager 1 shown in off-map pill)
    terrestrial_pins = [c for c in LEAD_STORIES if c["id"] != 3]
    pin_r = 11.0
    placed = resolve_pin_positions(terrestrial_pins, ATLAS_BOUNDS, vw, vh, pin_r)
    for p in placed:
        col = rgb_from_hex(REGION_LOOKUP[p["item"]["region"]]["hex"])
        if math.hypot(p["px"] - p["ax"], p["py"] - p["ay"]) > pin_r + 2:
            md.line((p["ax"], p["ay"], p["px"], p["py"]), fill=INK_PRIMARY, width=2)
            md.ellipse((p["ax"] - 3, p["ay"] - 3, p["ax"] + 3, p["ay"] + 3), fill=col, outline=(255, 255, 255), width=1)

    pin_font = get_font("sans_bold", 13)
    for p in placed:
        col = rgb_from_hex(REGION_LOOKUP[p["item"]["region"]]["hex"])
        draw_badge_circle(
            md, p["px"], p["py"], pin_r, str(p["item"]["id"]), col, (255, 255, 255), pin_font, ring_rgb=(255, 255, 255), ring_w=2
        )

    # Bold dark pill for #3 Voyager 1 off map (vector arrow avoids missing-glyph box)
    pill_y0, pill_y1 = vh - 36, vh - 8
    pill_mid = (pill_y0 + pill_y1) / 2.0
    md.rounded_rectangle((10, pill_y0, 326, pill_y1), radius=5, fill=INK_PRIMARY)
    draw_badge_circle(
        md, 26, pill_mid, 9.5, "3", rgb_from_hex(REGION_LOOKUP["GLOBAL"]["hex"]), (255, 255, 255), get_font("sans_bold", 12), ring_rgb=(255, 255, 255), ring_w=1
    )
    md.line((42, pill_mid, 60, pill_mid), fill=(250, 204, 21), width=3)
    md.polygon([(66, pill_mid), (57, pill_mid - 4.5), (57, pill_mid + 4.5)], fill=(250, 204, 21))
    md.text((73, pill_mid - 9), "VOYAGER 1, 25.9B KM OFF MAP", font=get_font("cond_bold", 15), fill=(255, 255, 255))

    base_img.paste(map_img, (vx0, vy0))
    draw.rectangle((vx0, vy0, vx1, vy1), outline=RULE_DIVIDER, width=1)

    # Proportionally spaced legend under map
    leg_y = (vy1 + map_y1) / 2.0 + 1
    leg_font = get_font("cond_bold", 14)
    item_widths = [14 + draw.textlength(reg["short"], font=leg_font) for reg in REGION_PALETTE]
    total_items_w = sum(item_widths)
    leg_gap = ((left_x1 - left_x0) - total_items_w) / (len(REGION_PALETTE) - 1)
    lx = float(left_x0)
    for reg, iw in zip(REGION_PALETTE, item_widths):
        col = rgb_from_hex(reg["hex"])
        draw.ellipse((lx, leg_y - 5, lx + 10, leg_y + 5), fill=col)
        draw.text((lx + 14, leg_y - 8), reg["short"], font=leg_font, fill=INK_BODY)
        lx += iw + leg_gap

    # BY THE NUMBERS open 2x2 typographic callouts (no 4-sided boxes)
    draw.text((left_x0, 1820), "BY THE NUMBERS", font=get_font("cond_bold", 18), fill=INK_PRIMARY)
    grid_y0 = 1846
    gap_x, gap_y = 24, 12
    col_w = (left_x1 - left_x0 - gap_x) // 2
    row_h = (BOTTOM_BOT - grid_y0 - gap_y) // 2

    for idx, kpi in enumerate(NUMBER_KPIS):
        col_i = idx % 2
        row_i = idx // 2
        kx0 = left_x0 + col_i * (col_w + gap_x)
        kx1 = left_x1 if col_i == 1 else (kx0 + col_w)
        ky0 = grid_y0 + row_i * (row_h + gap_y)
        accent = rgb_from_hex(kpi["hex"])

        draw.rectangle((kx0, ky0, kx1, ky0 + 3), fill=accent)
        val_font, _ = fit_single_line_font(draw, get_font, "serif_bold", kpi["value"], kx1 - kx0, 42, 28)
        draw.text((kx0, ky0 + 6), kpi["value"], font=val_font, fill=accent)
        lbl_font, _ = fit_single_line_font(draw, get_font, "sans_semi", kpi["label"], kx1 - kx0, 16, 12)
        draw.text((kx0, ky0 + 52), kpi["label"], font=lbl_font, fill=INK_BODY)


def draw_brief_directory(draw, get_font) -> None:
    """Render bottom-right 2-column directory (#14-#39) with colored square badges and hairline dividers."""
    draw.line((695, BOTTOM_TOP, 695, BOTTOM_BOT), fill=RULE_DIVIDER, width=1)
    rx0, ry0, rx1, ry1 = 705, BOTTOM_TOP, SUPERSAMPLE_W - PAGE_MARGIN_X, BOTTOM_BOT

    hdr_txt = "ALSO ON WEDNESDAY 18 NOVEMBER — 26 MORE VERIFIED STORIES (#14–#39)"
    hdr_font, _ = fit_single_line_font(draw, get_font, "serif_bold", hdr_txt, rx1 - rx0, 21, 15)
    draw.text((rx0, ry0), hdr_txt, font=hdr_font, fill=INK_PRIMARY)
    draw.line((rx0, ry0 + 30, rx1, ry0 + 30), fill=INK_PRIMARY, width=2)

    mid_x = (rx0 + rx1) // 2
    draw.line((mid_x, ry0 + 38, mid_x, ry1), fill=RULE_DIVIDER, width=1)

    col_bounds = [
        (rx0, mid_x - 14, BRIEF_STORIES[:13]),
        (mid_x + 14, rx1, BRIEF_STORIES[13:]),
    ]
    body_y0 = ry0 + 36
    body_y1 = ry1
    row_h = (body_y1 - body_y0) / 13.0
    sq = 24
    sq_font = get_font("sans_bold", 14)

    for cx0, cx1, items in col_bounds:
        text_x = cx0 + sq + 10
        max_w = cx1 - text_x - 2
        for idx, item in enumerate(items):
            y_top = body_y0 + idx * row_h
            y_mid = y_top + row_h / 2.0
            if idx > 0:
                draw.line((cx0, y_top, cx1, y_top), fill=RULE_HAIRLINE, width=1)

            col = rgb_from_hex(REGION_LOOKUP[item["region"]]["hex"])
            by0 = y_mid - sq / 2.0
            draw.rounded_rectangle((cx0, by0, cx0 + sq, by0 + sq), radius=3, fill=col)
            draw_centered(draw, cx0 + sq / 2.0, y_mid, str(item["id"]), sq_font, (255, 255, 255))

            lead_str = item["lead"] + " "
            body_str = item["text"]
            chosen_sz = 16
            for sz in range(19, 15, -1):
                f_b = get_font("sans_bold", sz)
                f_r = get_font("sans_reg", sz)
                if draw.textlength(lead_str, font=f_b) + draw.textlength(body_str, font=f_r) <= max_w:
                    chosen_sz = sz
                    break
            f_b = get_font("sans_bold", chosen_sz)
            f_r = get_font("sans_reg", chosen_sz)
            lead_w = draw.textlength(lead_str, font=f_b)

            _, tby0, _, tby1 = draw.textbbox((0, 0), "AH", font=f_b)
            ty = y_mid - (tby0 + tby1) / 2.0
            draw.text((text_x, ty), lead_str, font=f_b, fill=INK_PRIMARY)
            draw.text((text_x + lead_w, ty), body_str, font=f_r, fill=INK_BODY)


def draw_footer_bar(draw, get_font) -> None:
    """Render bottom rule and editorial attestation + wire sources bar."""
    draw.line((PAGE_MARGIN_X, FOOTER_TOP, SUPERSAMPLE_W - PAGE_MARGIN_X, FOOTER_TOP), fill=RULE_DIVIDER, width=2)
    mid_y = (FOOTER_TOP + FOOTER_BOT) / 2.0 + 2
    max_half = PAGE_WIDTH * 0.485
    f_l, _ = fit_single_line_font(draw, get_font, "sans_semi", ATTESTATION_LEFT, int(max_half), 16, 11)
    f_r, _ = fit_single_line_font(draw, get_font, "sans_semi", ATTESTATION_RIGHT, int(max_half), 16, 11)
    _, by0, _, by1 = draw.textbbox((0, 0), "AH", font=f_l)
    ty = mid_y - (by0 + by1) / 2.0
    draw.text((PAGE_MARGIN_X, ty), ATTESTATION_LEFT, font=f_l, fill=INK_BODY)
    rw = draw.textlength(ATTESTATION_RIGHT, font=f_r)
    draw.text((SUPERSAMPLE_W - PAGE_MARGIN_X - rw, ty), ATTESTATION_RIGHT, font=f_r, fill=INK_BODY)


def render_infographic() -> Path:
    """Render the 2048x2048 broadsheet and save downsampled 1024x1024 RGB PNG."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (SUPERSAMPLE_W, SUPERSAMPLE_H), PAPER_CREAM)
    draw = ImageDraw.Draw(img)
    get_font = build_font_getter(ImageFont)

    draw_broadsheet_masthead(draw, get_font)
    draw_lead_columns(img, draw, get_font, Image, ImageDraw, SCENE_ARTISTS)
    draw_where_and_numbers(img, draw, get_font, Image, ImageDraw)
    draw_brief_directory(draw, get_font)
    draw_footer_bar(draw, get_font)

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
