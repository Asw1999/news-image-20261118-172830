"""Daily world news summary infographic generator for Wednesday, 18 November 2026.

Default sandbox execution uses Python standard library only to deterministically copy
the pre-rendered `entry.png` to `$MAKEFUN_OUTPUT_DIR/entry.png` (default `/output/entry.png`).
Setting `MAKEFUN_RENDER=1` invokes Pillow rendering to regenerate the 1024x1024 RGB PNG.
"""

import math
import os
import shutil
import sys
from pathlib import Path

EDITION_TITLE = "THE WORLD TODAY"
EDITION_DATE = "WEDNESDAY, 18 NOVEMBER 2026"
EDITION_SUBTITLE = "GLOBAL DAILY BRIEFING  •  42 VERIFIED STORIES  •  6 REGIONS & BEATS  •  EDITION: 18 NOV 2026"

TARGET_SIZE = 1024
SCALE = 2
CANVAS_W = 2048
CANVAS_H = 2048
MAX_BYTES = 1_048_576

MARGIN_X = 32
CONTENT_W = CANVAS_W - 2 * MARGIN_X
MASTHEAD_Y0, MASTHEAD_Y1 = 22, 142
HERO_Y0, HERO_Y1 = 154, 346
MAP_Y0, MAP_Y1 = 358, 922
GRID_Y0, GRID_Y1 = 934, 1932
KPI_Y0, KPI_Y1 = 1944, 2026

BG_COLOR = (7, 13, 24)
SURFACE_COLOR = (17, 28, 46)
SURFACE_ALT = (13, 23, 41)
BORDER_COLOR = (36, 52, 77)
TEXT_PRIMARY = (248, 250, 252)
TEXT_SECONDARY = (203, 213, 225)
TEXT_MUTED = (148, 163, 184)
GOLD_ACCENT = (251, 191, 36)

OCEAN_BG = (10, 22, 42)
GRID_LINE_COLOR = (24, 42, 70)
EQUATOR_COLOR = (38, 66, 104)
LAND_FILL = (36, 56, 84)
LAND_OUTLINE = (74, 106, 145)

WORLD_BOUNDS = (-172.0, 182.0, -56.0, 80.0)
INSET_BOUNDS = (-11.0, 62.0, 11.0, 59.0)

WORLD_POLYGONS = [
    # North & Central America
    [
        (-166.0, 60.0), (-168.0, 65.8), (-162.0, 66.8), (-166.0, 68.8),
        (-156.5, 71.3), (-141.0, 69.7), (-135.0, 69.3), (-124.0, 70.0),
        (-110.0, 68.8), (-95.0, 69.5), (-90.0, 64.0), (-94.5, 59.0),
        (-87.0, 55.2), (-80.0, 51.3), (-78.0, 59.0), (-75.0, 62.3),
        (-65.0, 60.2), (-56.0, 52.0), (-52.8, 47.0), (-59.5, 46.8),
        (-61.0, 45.2), (-67.0, 45.0), (-70.0, 42.0), (-74.0, 40.5),
        (-75.5, 35.2), (-80.5, 32.0), (-80.1, 25.8), (-81.2, 25.1),
        (-82.7, 27.8), (-84.5, 30.0), (-89.2, 29.1), (-94.8, 29.2),
        (-97.2, 26.0), (-96.1, 19.2), (-90.7, 18.7), (-90.4, 21.2),
        (-86.8, 21.2), (-88.2, 16.0), (-83.4, 15.0), (-83.5, 10.8),
        (-77.6, 8.6), (-78.2, 7.6), (-81.0, 7.4), (-85.7, 10.4),
        (-92.2, 14.5), (-100.0, 16.8), (-105.5, 20.5), (-109.9, 23.0),
        (-113.5, 31.3), (-117.1, 32.5), (-118.5, 34.0), (-122.5, 37.8),
        (-124.4, 40.5), (-124.6, 48.3), (-128.0, 50.8), (-135.4, 57.1),
        (-145.5, 60.3), (-151.5, 59.3), (-156.0, 56.5), (-163.0, 54.9),
        (-161.5, 58.6),
    ],
    # Greenland
    [
        (-44.0, 60.0), (-52.0, 64.2), (-54.0, 70.5), (-69.0, 77.2),
        (-54.0, 81.8), (-22.0, 81.6), (-18.0, 76.5), (-22.0, 70.3),
        (-34.0, 68.0), (-41.0, 63.0),
    ],
    # Cuba & Hispaniola
    [(-84.9, 21.9), (-82.0, 23.2), (-77.2, 21.5), (-74.2, 20.2), (-77.6, 19.9), (-81.8, 21.8)],
    [(-74.4, 18.5), (-72.0, 19.9), (-68.4, 18.6), (-71.4, 17.6)],
    # South America
    [
        (-77.6, 8.6), (-74.2, 11.1), (-71.3, 12.2), (-67.0, 10.6),
        (-61.5, 9.8), (-55.0, 5.9), (-50.0, 1.5), (-48.5, -1.2),
        (-41.0, -2.9), (-35.0, -5.8), (-34.8, -8.1), (-38.5, -13.0),
        (-41.0, -22.0), (-43.2, -23.0), (-48.5, -27.5), (-53.4, -33.7),
        (-56.8, -35.0), (-62.2, -40.5), (-65.0, -43.0), (-67.5, -47.0),
        (-68.4, -52.5), (-67.2, -55.0), (-71.2, -54.4), (-75.0, -49.0),
        (-73.8, -42.0), (-71.6, -33.0), (-70.6, -23.6), (-70.3, -18.5),
        (-77.1, -12.0), (-81.3, -4.7), (-80.0, -2.2), (-77.5, 4.5),
    ],
    # Iceland, Britain, Ireland
    [(-24.2, 65.5), (-18.0, 66.5), (-13.6, 65.2), (-15.0, 63.9), (-22.6, 64.0)],
    [
        (-5.5, 50.1), (-3.0, 51.3), (-4.9, 52.8), (-3.3, 54.8),
        (-5.8, 56.8), (-5.0, 58.5), (-3.1, 58.6), (-1.8, 57.6),
        (-1.4, 55.0), (1.7, 52.5), (1.4, 51.2), (-1.8, 50.6),
    ],
    [(-10.3, 51.8), (-9.6, 54.3), (-6.1, 55.2), (-6.0, 52.2), (-8.5, 51.5)],
    # Eurasia (continuous coastline from Gibraltar around Scandinavia, Siberia, Asia, Arabia, Med)
    [
        (-5.6, 36.0), (-9.0, 37.0), (-9.5, 38.8), (-9.3, 43.0),
        (-3.8, 43.5), (-1.8, 43.4), (-2.2, 47.2), (-4.7, 48.4),
        (-1.8, 49.6), (1.8, 51.0), (4.2, 52.1), (8.5, 53.7),
        (8.1, 57.0), (10.6, 57.7), (10.2, 54.4), (13.8, 54.1),
        (18.6, 54.4), (21.1, 56.4), (24.0, 57.3), (24.7, 59.4),
        (29.8, 60.0), (25.0, 60.2), (21.5, 63.0), (24.1, 65.8),
        (20.3, 63.8), (18.1, 59.3), (15.8, 56.1), (13.0, 55.6),
        (10.7, 59.9), (5.3, 60.4), (10.4, 63.4), (15.2, 68.4),
        (25.8, 71.1), (33.1, 69.0), (40.5, 66.5), (44.0, 68.5),
        (55.0, 68.5), (68.0, 70.0), (72.0, 73.0), (74.0, 67.8),
        (85.0, 73.5), (104.0, 77.6), (125.0, 73.5), (158.0, 70.2),
        (178.5, 66.5), (177.0, 64.5), (163.0, 59.8), (162.5, 55.8),
        (156.8, 51.0), (156.5, 59.0), (143.0, 59.2), (141.2, 53.0),
        (135.5, 44.0), (131.9, 43.1), (129.4, 35.1), (126.4, 34.6),
        (126.6, 37.6), (121.6, 39.0), (118.2, 39.0), (122.6, 37.4),
        (119.5, 34.5), (121.9, 31.2), (119.8, 26.0), (114.2, 22.3),
        (110.2, 20.3), (106.8, 20.8), (108.4, 16.0), (109.2, 12.2),
        (105.5, 8.8), (100.5, 13.5), (99.4, 9.5), (103.8, 1.3),
        (100.3, 5.4), (98.5, 9.8), (96.2, 16.8), (91.8, 22.3),
        (88.8, 21.8), (85.0, 19.5), (80.3, 13.1), (77.5, 8.1),
        (72.8, 19.0), (69.0, 22.5), (67.0, 24.8), (61.5, 25.2),
        (56.4, 27.1), (50.8, 29.0), (48.5, 30.0), (48.0, 29.3),
        (50.5, 26.2), (51.5, 25.2), (56.4, 26.2), (59.8, 22.5),
        (54.1, 17.0), (45.0, 12.8), (43.4, 12.7), (39.2, 21.5),
        (34.9, 29.5), (34.2, 27.8), (32.5, 29.9), (32.3, 31.2),
        (34.7, 32.0), (35.5, 33.9), (36.1, 36.6), (30.7, 36.8),
        (27.1, 38.4), (29.0, 41.2), (36.3, 41.3), (41.6, 41.6),
        (39.7, 43.6), (36.5, 45.3), (33.8, 44.4), (32.0, 46.2),
        (30.7, 46.4), (28.7, 44.2), (29.0, 41.0), (26.0, 40.4),
        (22.9, 40.6), (23.7, 37.9), (22.4, 36.4), (19.4, 41.3),
        (13.8, 45.6), (12.3, 45.4), (13.5, 43.6), (16.9, 41.1),
        (15.7, 38.0), (14.2, 40.8), (12.3, 41.7), (8.9, 44.4),
        (5.4, 43.3), (2.2, 41.4), (-0.3, 39.5), (-4.4, 36.7),
    ],
    # Africa
    [
        (32.5, 29.9), (32.3, 31.3), (29.9, 31.2), (25.2, 31.6),
        (20.1, 32.1), (13.2, 32.9), (10.2, 36.8), (3.0, 36.8),
        (-5.8, 35.8), (-7.6, 33.6), (-13.0, 27.5), (-16.8, 21.0),
        (-16.0, 18.1), (-17.5, 14.7), (-13.7, 9.5), (-10.8, 6.3),
        (-7.7, 4.4), (-4.0, 5.3), (3.4, 6.4), (6.0, 4.3),
        (9.7, 4.0), (9.4, 0.4), (12.3, -6.0), (13.2, -8.8),
        (12.2, -15.5), (14.5, -22.9), (18.4, -34.0), (20.0, -34.8),
        (25.6, -34.0), (31.0, -29.9), (32.6, -25.9), (35.5, -23.8),
        (34.8, -19.8), (40.7, -14.5), (39.3, -6.8), (39.7, -4.0),
        (45.3, 2.0), (51.3, 11.9), (43.1, 11.6), (39.5, 15.6),
        (37.2, 19.6), (33.8, 27.2),
    ],
    # Madagascar & Sri Lanka
    [(49.3, -12.0), (50.4, -15.5), (47.5, -25.0), (45.0, -25.6), (43.3, -23.3), (44.4, -18.0), (46.8, -15.5)],
    [(80.0, 9.6), (81.8, 7.6), (80.5, 6.0), (79.8, 7.5)],
    # Mediterranean Islands (Sicily, Sardinia, Corsica, Cyprus, Crete)
    [(12.4, 37.8), (15.6, 38.2), (15.1, 36.7), (13.2, 37.2)],
    [(8.2, 41.0), (9.8, 41.2), (9.6, 39.0), (8.4, 39.1)],
    [(9.4, 43.0), (9.5, 41.4), (8.6, 41.8), (8.7, 42.6)],
    [(32.3, 35.1), (34.6, 35.7), (34.0, 35.0), (32.6, 34.7)],
    [(23.5, 35.5), (26.3, 35.3), (26.0, 35.0), (23.6, 35.2)],
    # Japan, Taiwan, Philippines
    [(130.0, 31.3), (130.8, 33.9), (135.5, 34.4), (139.8, 35.4), (141.0, 38.3), (141.3, 41.3), (139.9, 40.5), (136.5, 36.8), (132.0, 34.5), (130.0, 32.8)],
    [(140.0, 41.5), (141.6, 45.4), (145.4, 43.3), (143.2, 42.0), (140.8, 42.3)],
    [(121.5, 25.2), (121.6, 23.0), (120.8, 21.9), (120.1, 23.2), (120.9, 24.8)],
    [(120.0, 18.5), (122.3, 16.5), (124.0, 12.8), (126.2, 8.2), (125.5, 5.8), (122.0, 6.9), (121.0, 14.2)],
    # Maritime SE Asia & New Guinea
    [(95.3, 5.5), (99.5, 3.0), (104.5, -2.5), (105.8, -5.9), (102.0, -4.0), (97.5, 1.5)],
    [(105.4, -6.1), (114.4, -7.8), (114.0, -8.7), (106.5, -7.2)],
    [(109.2, 1.6), (117.0, 6.8), (118.9, 5.2), (117.5, -1.0), (114.5, -3.7), (110.2, -3.0)],
    [(119.3, 1.0), (125.0, 1.5), (122.8, -4.8), (119.5, -5.5), (119.0, -2.0)],
    [(131.0, -1.5), (141.0, -2.6), (150.5, -10.3), (145.0, -8.2), (138.0, -8.2), (132.5, -4.0)],
    # Australia, Tasmania, New Zealand
    [
        (129.0, -14.5), (136.8, -12.2), (136.0, -15.5), (141.0, -17.5),
        (142.5, -10.7), (146.0, -18.0), (153.5, -28.0), (151.3, -33.9),
        (149.9, -37.5), (144.8, -38.4), (138.5, -35.0), (135.5, -34.8),
        (129.0, -31.8), (121.9, -33.9), (115.1, -34.3), (114.1, -22.0),
        (122.2, -18.0),
    ],
    [(144.8, -40.7), (148.3, -41.0), (147.3, -43.4), (145.4, -42.5)],
    [(172.7, -34.5), (178.5, -37.7), (175.3, -41.4), (174.0, -39.1), (174.7, -36.8)],
    [(172.8, -40.6), (174.2, -41.7), (170.5, -45.9), (166.5, -46.1), (168.5, -43.5)],
]

FONT_SEARCH_DIRS = [
    "/data/data/com.termux/files/usr/share/fonts/TTF",
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/TTF",
    "/usr/share/fonts",
    "/data/data/com.termux/files/usr/lib/python3.14/site-packages/matplotlib/mpl-data/fonts/ttf",
]

FONT_ROLE_FILES = {
    "serif_bold": "DejaVuSerif-Bold.ttf",
    "sans_bold": "DejaVuSans-Bold.ttf",
    "sans": "DejaVuSans.ttf",
    "sans_cond": "DejaVuSansCondensed.ttf",
    "sans_cond_bold": "DejaVuSansCondensed-Bold.ttf",
    "mono_bold": "DejaVuSansMono-Bold.ttf",
}

REGIONS = [
    {
        "key": "AMERICAS",
        "label": "AMERICAS",
        "range_label": "#1–#7",
        "color": "#38BDF8",
        "badge_fg": "#062033",
        "panel_tint": "#102136",
    },
    {
        "key": "EUROPE",
        "label": "EUROPE",
        "range_label": "#8–#14",
        "color": "#60A5FA",
        "badge_fg": "#071A38",
        "panel_tint": "#111F38",
    },
    {
        "key": "MENA",
        "label": "MIDDLE EAST & N. AFRICA",
        "range_label": "#15–#21",
        "color": "#FB7185",
        "badge_fg": "#3B0714",
        "panel_tint": "#261522",
    },
    {
        "key": "AFRICA",
        "label": "SUB-SAHARAN AFRICA",
        "range_label": "#22–#28",
        "color": "#FBBF24",
        "badge_fg": "#361903",
        "panel_tint": "#241D14",
    },
    {
        "key": "APAC",
        "label": "ASIA-PACIFIC",
        "range_label": "#29–#35",
        "color": "#34D399",
        "badge_fg": "#03261A",
        "panel_tint": "#0F2422",
    },
    {
        "key": "GLOBAL",
        "label": "GLOBAL / SCIENCE / MARKETS",
        "range_label": "#36–#42",
        "color": "#C084FC",
        "badge_fg": "#240A42",
        "panel_tint": "#1D1730",
    },
]

REGION_BY_KEY = {r["key"]: r for r in REGIONS}

HERO_STORIES = [
    {
        "eyebrow": "ASIA-PACIFIC SUMMIT",
        "pins": "#29",
        "title": "APEC SHENZHEN SUMMIT",
        "detail": "Xi hosts Trump, Putin & Pacific leaders; calls for open WTO trade and growth pact",
        "accent": "#34D399",
    },
    {
        "eyebrow": "SECURITY ESCALATION",
        "pins": "#9 #15 #16",
        "title": "GULF & ODESA STRIKES",
        "detail": "US hits Iran's Qeshm Island; Iran drones target Kuwait; Shaheds strike Odesa",
        "accent": "#FB7185",
    },
    {
        "eyebrow": "DEEP SPACE MILESTONE",
        "pins": "#36",
        "title": "VOYAGER 1: 1 LIGHT-DAY",
        "detail": "NASA probe reaches 25.9B km (16B mi) from Earth, humanity's farthest mark",
        "accent": "#C084FC",
    },
    {
        "eyebrow": "TECH & CLIMATE TALKS",
        "pins": "#2 #18",
        "title": "NVIDIA $115.8B & COP31",
        "detail": "AI chip revenue jumps +103% YoY as Antalya climate talks enter endgame stocktake",
        "accent": "#38BDF8",
    },
]

STORIES = [
    # AMERICAS (#1-#7)
    {
        "id": 1,
        "region": "AMERICAS",
        "title": "Alaska Senate: Peltola Wins",
        "detail": "Mary Peltola beats Dan Sullivan via RCV; Dems hold 56-44 edge",
        "lat": 61.2,
        "lon": -149.9,
    },
    {
        "id": 2,
        "region": "AMERICAS",
        "title": "Nvidia Q3 Revenue Hits $115.8B",
        "detail": "Data center sales hit $107.6B (+103% YoY); Q4 guide $130B",
        "lat": 37.4,
        "lon": -121.9,
    },
    {
        "id": 3,
        "region": "AMERICAS",
        "title": "CISA Urges Java4Shell Patching",
        "detail": "Critical OpenJDK AVX-512 RCE flaw CVE-2026-114938 hits servers",
        "lat": 38.9,
        "lon": -77.0,
    },
    {
        "id": 4,
        "region": "AMERICAS",
        "title": "NSA Internal Network Outage",
        "detail": "Classified NSANet suffers disruption; officials see no cyber link",
        "lat": 39.1,
        "lon": -76.8,
    },
    {
        "id": 5,
        "region": "AMERICAS",
        "title": "US, Mexico Lose Measles Status",
        "detail": "PAHO revokes measles-free status for US, Mexico, and Bolivia",
        "lat": 19.4,
        "lon": -99.1,
    },
    {
        "id": 6,
        "region": "AMERICAS",
        "title": "Canada-China Swap & Tariff Deal",
        "detail": "PM Mark Carney renews currency swap and cuts trade friction",
        "lat": 45.4,
        "lon": -75.7,
    },
    {
        "id": 7,
        "region": "AMERICAS",
        "title": "Darien Gap Crossings Drop 90%",
        "detail": "IOM reports plunge in Panama crossings as flows shift south",
        "lat": 8.4,
        "lon": -77.7,
    },
    # EUROPE (#8-#14)
    {
        "id": 8,
        "region": "EUROPE",
        "title": "EU Proposes EUR 45B Ukraine Loan",
        "detail": "EUR 25B defense + EUR 20B budget aid repaid via Russian funds",
        "lat": 50.8,
        "lon": 4.4,
    },
    {
        "id": 9,
        "region": "EUROPE",
        "title": "Deadly Drone Strike Hits Odesa",
        "detail": "Jet-powered Shaheds hit downtown; city declares mourning day",
        "lat": 46.5,
        "lon": 30.7,
    },
    {
        "id": 10,
        "region": "EUROPE",
        "title": "E5 Coalition Leads Peace Lineup",
        "detail": "FR, DE, UK, IT, PL + EU prep Berlin talks; Kallas excluded",
        "lat": 52.5,
        "lon": 13.4,
    },
    {
        "id": 11,
        "region": "EUROPE",
        "title": "Italy Rules Out Ukraine Troops",
        "detail": "Rome backs E5 diplomacy but refuses Coalition of Willing force",
        "lat": 41.9,
        "lon": 12.5,
    },
    {
        "id": 12,
        "region": "EUROPE",
        "title": "UK Inflation Ticks Up to 3.6%",
        "detail": "ONS Oct CPI rises on fuel costs; BoE holds rate at 4.0%",
        "lat": 51.5,
        "lon": -0.1,
    },
    {
        "id": 13,
        "region": "EUROPE",
        "title": "Ukraine Submits DOT-Chain Arms",
        "detail": "Kyiv seeks EU clearance for 1,000+ defense & FPV drone systems",
        "lat": 50.4,
        "lon": 30.5,
    },
    {
        "id": 14,
        "region": "EUROPE",
        "title": "Eurozone Inflation Hits 4.0%",
        "detail": "EU autumn forecast sees 1.4% GDP; France 3.7%, Spain 4.9% CPI",
        "lat": 50.1,
        "lon": 8.7,
    },
    # MIDDLE EAST & N. AFRICA (#15-#21)
    {
        "id": 15,
        "region": "MENA",
        "title": "US Strikes Iran's Qeshm Island",
        "detail": "Precision jets hit IRGC missile site near Strait of Hormuz",
        "lat": 26.9,
        "lon": 56.0,
    },
    {
        "id": 16,
        "region": "MENA",
        "title": "Iran Attacks Kuwait Air Base",
        "detail": "Drones target Ali Al Salem; Kuwait & Bahrain intercept threats",
        "lat": 29.3,
        "lon": 47.4,
    },
    {
        "id": 17,
        "region": "MENA",
        "title": "Tanker Struck in Strait of Hormuz",
        "detail": "ADNOC oil tanker hit leaving 1 missing; GCC condemns strikes",
        "lat": 26.4,
        "lon": 56.5,
    },
    {
        "id": 18,
        "region": "MENA",
        "title": "COP31 Launches 2nd Stocktake",
        "detail": "UN's Stiell urges action; Africa & South reject weak draft text",
        "lat": 36.9,
        "lon": 30.7,
    },
    {
        "id": 19,
        "region": "MENA",
        "title": "Israel Launches Central Gaza Thrust",
        "detail": "Tanks advance near Bureij & Nuseirat; Knesset elects Kahana",
        "lat": 31.4,
        "lon": 34.4,
    },
    {
        "id": 20,
        "region": "MENA",
        "title": "Houthis Threaten Aden; Saudi Shift",
        "detail": "Saudi names Gen. Al-Ruwaili as coalition intercepts 2 drones",
        "lat": 15.4,
        "lon": 44.2,
    },
    {
        "id": 21,
        "region": "MENA",
        "title": "IMF & Egypt Reach EFF Deal",
        "detail": "Staff agreement on 8th EFF review bolsters macro stability",
        "lat": 30.0,
        "lon": 31.2,
    },
    # SUB-SAHARAN AFRICA (#22-#28)
    {
        "id": 22,
        "region": "AFRICA",
        "title": "Nigeria Advances State Police Bill",
        "detail": "Senate sends constitutional bill to Tinubu after 36-state vote",
        "lat": 9.1,
        "lon": 7.5,
    },
    {
        "id": 23,
        "region": "AFRICA",
        "title": "Lake Chad States Agree 5km Pursuit",
        "detail": "Nigeria, Chad, Cameroon & Niger sign cross-border terror pact",
        "lat": 12.1,
        "lon": 15.0,
    },
    {
        "id": 24,
        "region": "AFRICA",
        "title": "Sudan Sentences RSF Chief to Death",
        "detail": "Court convicts Hemetti in absentia; UN cites El Obeid drone toll",
        "lat": 19.6,
        "lon": 37.2,
    },
    {
        "id": 25,
        "region": "AFRICA",
        "title": "Kenya Ruto Address & EU Data Pact",
        "detail": "Ruto touts local exam savings; Kenya-EU seal data adequacy deal",
        "lat": -1.3,
        "lon": 36.8,
    },
    {
        "id": 26,
        "region": "AFRICA",
        "title": "SA Reprimands Nigerian Envoy",
        "detail": "DIRCO rebukes Fani-Kayode; US ends SA & Rwanda AGOA Jan 2027",
        "lat": -25.7,
        "lon": 28.2,
    },
    {
        "id": 27,
        "region": "AFRICA",
        "title": "DRC Launches Ebola Vaccine Trial",
        "detail": "WHO starts Tumaini trial for Bundibugyo strain; 11,300+ cases",
        "lat": -1.7,
        "lon": 29.2,
    },
    {
        "id": 28,
        "region": "AFRICA",
        "title": "Senegal Ruling Party Expels Pres.",
        "detail": "Pastef expels Pres. Faye & 31 allies in Sonko power split",
        "lat": 14.7,
        "lon": -17.5,
    },
    # ASIA-PACIFIC (#29-#35)
    {
        "id": 29,
        "region": "APAC",
        "title": "APEC Shenzhen Opens: Xi & Trump",
        "detail": "Xi urges open WTO trade; Trump, Putin & APEC leaders gather",
        "lat": 22.5,
        "lon": 114.1,
    },
    {
        "id": 30,
        "region": "APAC",
        "title": "South Korea Seeks Peninsula Peace",
        "detail": "Pres. Lee meets Xi in Shenzhen; AI exam cheating scandal rocks",
        "lat": 37.6,
        "lon": 127.0,
    },
    {
        "id": 31,
        "region": "APAC",
        "title": "Japan Proposes 'Asian IEA' Pact",
        "detail": "PM Takaichi pitches regional oil reserve task force at ASEAN",
        "lat": 35.7,
        "lon": 139.7,
    },
    {
        "id": 32,
        "region": "APAC",
        "title": "Indonesia Inks $71.8B China Deals",
        "detail": "Pres. Prabowo secures tech & smart-city pledges after ASEAN",
        "lat": -6.2,
        "lon": 106.8,
    },
    {
        "id": 33,
        "region": "APAC",
        "title": "Malaysia Q3 GDP Grows 5.5% YoY",
        "detail": "Bank Negara reports strong tech exports and domestic demand",
        "lat": 3.1,
        "lon": 101.7,
    },
    {
        "id": 34,
        "region": "APAC",
        "title": "India Hosts Royals & H5N1 Vaccine",
        "detail": "Modi meets UK royals; Apple Maps launches; H5N1 poultry shot",
        "lat": 28.6,
        "lon": 77.2,
    },
    {
        "id": 35,
        "region": "APAC",
        "title": "Australia Starts Kids mRNA Trial",
        "detail": "World-first PaedNEO-VAX brain cancer trial; settler sanctions",
        "lat": -33.9,
        "lon": 151.2,
    },
    # GLOBAL / SCIENCE / MARKETS (#36-#42)
    {
        "id": 36,
        "region": "GLOBAL",
        "title": "Voyager 1 Reaches 1 Light-Day",
        "detail": "NASA probe hits 25.9B km (16B mi) from Earth, a historic first",
        "lat": 34.2,
        "lon": -118.2,
    },
    {
        "id": 37,
        "region": "GLOBAL",
        "title": "S&P 500 & Nasdaq Slip on Tech",
        "detail": "S&P ~7,341, Dow ~50,759, Nasdaq ~24,328 after Nvidia report",
        "lat": 40.7,
        "lon": -74.0,
    },
    {
        "id": 38,
        "region": "GLOBAL",
        "title": "Gold Drops Below $3,800/oz",
        "detail": "Bullion slides ~2% to ~$3,772-$3,786 on strong USD & Fed bets",
        "lat": 47.4,
        "lon": 8.5,
    },
    {
        "id": 39,
        "region": "GLOBAL",
        "title": "Brent Crude Slides Near $91/bbl",
        "detail": "Brent falls ~1.2% (~$91.70) & WTI ~$84.34 on rising US stocks",
        "lat": 29.8,
        "lon": -95.4,
    },
    {
        "id": 40,
        "region": "GLOBAL",
        "title": "Bitcoin Slumps Near $64,000",
        "detail": "BTC down ~49% off highs amid ETF outflows and market risk-off",
        "lat": 1.3,
        "lon": 103.8,
    },
    {
        "id": 41,
        "region": "GLOBAL",
        "title": "SpaceX & NASA Prep Artemis III",
        "detail": "Starship catch aids 2027 LEO docking test; Dragon CRS-35 holds",
        "lat": 28.5,
        "lon": -80.6,
    },
    {
        "id": 42,
        "region": "GLOBAL",
        "title": "Anthropic Advances IPO Plans",
        "detail": "AI lab pushes IPO prep as global investors weigh AI valuations",
        "lat": 37.8,
        "lon": -122.4,
    },
]

KPIS = [
    {"label": "S&P 500", "value": "7,341", "delta": "-1.0%", "accent": "#FB7185"},
    {"label": "BRENT CRUDE", "value": "$91.70", "delta": "-1.2%", "accent": "#FBBF24"},
    {"label": "GOLD SPOT", "value": "$3,780", "delta": "-2.0%", "accent": "#FBBF24"},
    {"label": "BITCOIN", "value": "$64,000", "delta": "-49% ATH", "accent": "#FB7185"},
    {"label": "NVIDIA Q3", "value": "$115.8B", "delta": "+103% YoY", "accent": "#34D399"},
    {"label": "VOYAGER 1", "value": "25.9B km", "delta": "1 Light-Day", "accent": "#C084FC"},
]


def copy_prebuilt_image() -> Path:
    """Copy pre-rendered entry.png to MAKEFUN_OUTPUT_DIR using Python stdlib only."""
    src = Path(__file__).resolve().parent / "entry.png"
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / "entry.png"
    shutil.copyfile(src, dst)
    return dst


def hex_rgb(code: str) -> tuple[int, int, int]:
    """Convert a #RRGGBB hex string into an RGB 3-tuple."""
    clean = code.lstrip("#")
    return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def blend_rgb(
    c1: tuple[int, int, int], c2: tuple[int, int, int], alpha: float
) -> tuple[int, int, int]:
    """Linearly blend two RGB tuples where alpha=1.0 selects c2."""
    inv = 1.0 - alpha
    return (
        int(round(c1[0] * inv + c2[0] * alpha)),
        int(round(c1[1] * inv + c2[1] * alpha)),
        int(round(c1[2] * inv + c2[2] * alpha)),
    )


def find_font_path(filename: str) -> str:
    """Resolve a TTF font file across Termux and standard Linux font directories."""
    for base in FONT_SEARCH_DIRS:
        candidate = Path(base) / filename
        if candidate.is_file():
            return str(candidate)
    for base in FONT_SEARCH_DIRS:
        base_path = Path(base)
        if base_path.is_dir():
            for match in base_path.rglob(filename):
                if match.is_file():
                    return str(match)
    raise FileNotFoundError(f"Font file not found: {filename}")


def make_font_loader(image_font_mod):
    """Create a cached font lookup callable keyed by (role, pixel_size)."""
    resolved_paths = {
        role: find_font_path(fname) for role, fname in FONT_ROLE_FILES.items()
    }
    cache: dict[tuple[str, int], object] = {}

    def get_font(role: str, size: int):
        key = (role, size)
        if key not in cache:
            cache[key] = image_font_mod.truetype(resolved_paths[role], size=size)
        return cache[key]

    return get_font


def fit_font_single_line(
    draw, get_font, role: str, text: str, max_w: int, start_size: int, min_size: int
):
    """Shrink font size until single-line text fits inside max_w without truncation."""
    for size in range(start_size, min_size - 1, -1):
        font = get_font(role, size)
        if draw.textlength(text, font=font) <= max_w:
            return font, size
    return get_font(role, min_size), min_size


def wrap_text_to_box(
    draw,
    get_font,
    role: str,
    text: str,
    max_w: int,
    max_h: int,
    start_size: int,
    min_size: int,
    line_gap: int = 5,
):
    """Word-wrap text and fit font size so every word renders inside max_w x max_h."""
    words = text.split()
    for size in range(start_size, min_size - 1, -1):
        font = get_font(role, size)
        ascent, descent = font.getmetrics()
        line_h = ascent + descent + line_gap
        lines: list[str] = []
        current = ""
        word_fits = True
        for word in words:
            if draw.textlength(word, font=font) > max_w:
                word_fits = False
                break
            candidate = word if not current else f"{current} {word}"
            if draw.textlength(candidate, font=font) <= max_w:
                current = candidate
            else:
                lines.append(current)
                current = word
        if not word_fits:
            continue
        if current:
            lines.append(current)
        total_h = len(lines) * line_h - line_gap if lines else 0
        if total_h <= max_h:
            return font, lines, line_h
    font = get_font(role, min_size)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + line_gap
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if draw.textlength(candidate, font=font) <= max_w or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return font, lines, line_h


def draw_centered_text(draw, cx: float, cy: float, text: str, font, fill) -> None:
    """Draw text centered optically around (cx, cy) using its true bounding box."""
    x0, y0, x1, y1 = draw.textbbox((0, 0), text, font=font)
    tx = cx - (x0 + x1) / 2.0
    ty = cy - (y0 + y1) / 2.0
    draw.text((tx, ty), text, font=font, fill=fill)


def draw_masthead(draw, get_font) -> None:
    """Render newspaper masthead banner with prominent date badge and edition bar."""
    x0, y0, x1, y1 = MARGIN_X, MASTHEAD_Y0, CANVAS_W - MARGIN_X, MASTHEAD_Y1
    draw.rounded_rectangle(
        (x0, y0, x1, y1), radius=14, fill=SURFACE_ALT, outline=BORDER_COLOR, width=2
    )
    draw.rectangle((x0 + 14, y0, x1 - 14, y0 + 6), fill=GOLD_ACCENT)

    title_font = get_font("serif_bold", 54)
    title_x = x0 + 26
    draw.text((title_x, y0 + 17), EDITION_TITLE, font=title_font, fill=TEXT_PRIMARY)
    title_w = draw.textlength(EDITION_TITLE, font=title_font)

    badge_x0, badge_y0, badge_x1, badge_y1 = x1 - 635, y0 + 18, x1 - 24, y0 + 76
    sep_x = int(round(title_x + title_w + 26))
    draw.line((sep_x, y0 + 22, sep_x, y0 + 74), fill=BORDER_COLOR, width=2)

    kicker_x = sep_x + 24
    kicker_max_w = badge_x0 - kicker_x - 20
    k1_font, _ = fit_font_single_line(
        draw, get_font, "sans_bold", "WORLD NEWS SUMMARY", kicker_max_w, 18, 13
    )
    k2_font, _ = fit_font_single_line(
        draw, get_font, "sans", "6 REGIONS • 42 VERIFIED STORIES", kicker_max_w, 16, 12
    )
    draw.text((kicker_x, y0 + 25), "WORLD NEWS SUMMARY", font=k1_font, fill=GOLD_ACCENT)
    draw.text((kicker_x, y0 + 50), "6 REGIONS • 42 VERIFIED STORIES", font=k2_font, fill=TEXT_MUTED)

    draw.rounded_rectangle(
        (badge_x0, badge_y0, badge_x1, badge_y1), radius=10, fill=GOLD_ACCENT
    )
    date_font, _ = fit_font_single_line(
        draw, get_font, "sans_bold", EDITION_DATE, badge_x1 - badge_x0 - 28, 28, 20
    )
    draw_centered_text(
        draw,
        (badge_x0 + badge_x1) / 2.0,
        (badge_y0 + badge_y1) / 2.0,
        EDITION_DATE,
        date_font,
        BG_COLOR,
    )

    draw.line((x0 + 24, y0 + 88, x1 - 24, y0 + 88), fill=BORDER_COLOR, width=2)
    sub_font, _ = fit_font_single_line(
        draw, get_font, "sans", EDITION_SUBTITLE, CONTENT_W - 52, 18, 14
    )
    draw_centered_text(
        draw,
        (x0 + x1) / 2.0,
        y0 + 104,
        EDITION_SUBTITLE,
        sub_font,
        TEXT_SECONDARY,
    )


def draw_hero_cards(draw, get_font) -> None:
    """Render the 4 top Hero Spotlight cards highlighting the day's lead stories."""
    gap = 16
    card_w = (CONTENT_W - 3 * gap) // 4
    y0, y1 = HERO_Y0, HERO_Y1
    for idx, hero in enumerate(HERO_STORIES):
        cx0 = MARGIN_X + idx * (card_w + gap)
        cx1 = (CANVAS_W - MARGIN_X) if idx == len(HERO_STORIES) - 1 else (cx0 + card_w)
        accent = hex_rgb(hero["accent"])
        card_bg = blend_rgb(SURFACE_COLOR, accent, 0.08)
        draw.rounded_rectangle(
            (cx0, y0, cx1, y1), radius=12, fill=card_bg, outline=BORDER_COLOR, width=2
        )
        draw.rectangle((cx0 + 12, y0, cx1 - 12, y0 + 6), fill=accent)

        inner_w = (cx1 - cx0) - 32
        eyebrow_font = get_font("sans_bold", 16)
        draw.text((cx0 + 16, y0 + 15), hero["eyebrow"], font=eyebrow_font, fill=accent)

        pin_font = get_font("mono_bold", 15)
        pin_txt = hero["pins"]
        pin_w = int(math.ceil(draw.textlength(pin_txt, font=pin_font))) + 18
        px1 = cx1 - 16
        px0 = px1 - pin_w
        draw.rounded_rectangle(
            (px0, y0 + 13, px1, y0 + 38),
            radius=6,
            fill=blend_rgb(BG_COLOR, accent, 0.25),
            outline=accent,
            width=1,
        )
        draw_centered_text(
            draw, (px0 + px1) / 2.0, y0 + 25.5, pin_txt, pin_font, TEXT_PRIMARY
        )

        title_font, _ = fit_font_single_line(
            draw, get_font, "sans_bold", hero["title"], inner_w, 27, 18
        )
        draw.text((cx0 + 16, y0 + 46), hero["title"], font=title_font, fill=TEXT_PRIMARY)

        detail_font, lines, line_h = wrap_text_to_box(
            draw, get_font, "sans", hero["detail"], inner_w, y1 - (y0 + 86) - 10, 21, 15, line_gap=6
        )
        ty = y0 + 86
        for line in lines:
            draw.text((cx0 + 16, ty), line, font=detail_font, fill=TEXT_SECONDARY)
            ty += line_h


def project_equirectangular(
    lat: float,
    lon: float,
    bounds: tuple[float, float, float, float],
    width: int,
    height: int,
) -> tuple[float, float]:
    """Project (lat, lon) into pixel coordinates within an equirectangular viewport."""
    lon_min, lon_max, lat_min, lat_max = bounds
    x = (lon - lon_min) / (lon_max - lon_min) * width
    y = (lat_max - lat) / (lat_max - lat_min) * height
    return (x, y)


def render_map_basemap(
    image_cls,
    image_draw_cls,
    width: int,
    height: int,
    bounds: tuple[float, float, float, float],
    lon_step: int,
    lat_step: int,
):
    """Render an equirectangular ocean basemap with lat/lon graticule and landmasses."""
    map_img = image_cls.new("RGB", (width, height), OCEAN_BG)
    mdraw = image_draw_cls.Draw(map_img)

    lon_min, lon_max, lat_min, lat_max = bounds
    first_lon = int(math.ceil(lon_min / lon_step) * lon_step)
    for lon in range(first_lon, int(lon_max) + 1, lon_step):
        x, _ = project_equirectangular(0.0, float(lon), bounds, width, height)
        col = EQUATOR_COLOR if lon == 0 else GRID_LINE_COLOR
        mdraw.line((x, 0, x, height), fill=col, width=1)

    first_lat = int(math.ceil(lat_min / lat_step) * lat_step)
    for lat in range(first_lat, int(lat_max) + 1, lat_step):
        _, y = project_equirectangular(float(lat), 0.0, bounds, width, height)
        col = EQUATOR_COLOR if lat == 0 else GRID_LINE_COLOR
        mdraw.line((0, y, width, y), fill=col, width=2 if lat == 0 else 1)

    for poly in WORLD_POLYGONS:
        pts = [
            project_equirectangular(lat, lon, bounds, width, height)
            for (lon, lat) in poly
        ]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if max(xs) < -20 or min(xs) > width + 20 or max(ys) < -20 or min(ys) > height + 20:
            continue
        mdraw.polygon(pts, fill=LAND_FILL, outline=LAND_OUTLINE)

    return map_img, mdraw


def layout_map_pins(
    stories: list[dict],
    bounds: tuple[float, float, float, float],
    width: int,
    height: int,
    badge_r: int,
) -> list[dict]:
    """Place numbered pin badges near true coordinates with collision-free offsets."""
    anchors = []
    for story in stories:
        ax, ay = project_equirectangular(
            story["lat"], story["lon"], bounds, width, height
        )
        anchors.append((story, ax, ay))

    placed: list[dict] = []
    min_badge_dist = 2.0 * badge_r + 4.0
    pad = badge_r + 6.0

    # Place dense cluster pins deterministically from center outward
    radii = [0.0, 1.75 * badge_r, 2.55 * badge_r, 3.4 * badge_r, 4.3 * badge_r, 5.2 * badge_r]
    angles = [k * (2.0 * math.pi / 16.0) for k in range(16)]

    for story, ax, ay in anchors:
        best_pos = (
            min(max(ax, pad), width - pad),
            min(max(ay, pad), height - pad),
        )
        best_score = float("inf")

        for r in radii:
            dirs = [(0.0, 0.0)] if r == 0.0 else [(math.cos(a), math.sin(a)) for a in angles]
            for dx, dy in dirs:
                cx = ax + r * dx
                cy = ay + r * dy
                if cx < pad or cx > width - pad or cy < pad or cy > height - pad:
                    continue

                score = r * 1.4
                for other in placed:
                    dist = math.hypot(cx - other["px"], cy - other["py"])
                    if dist < min_badge_dist:
                        score += 10000.0 * (min_badge_dist - dist)
                for other_story, oax, oay in anchors:
                    if other_story["id"] == story["id"]:
                        continue
                    adist = math.hypot(cx - oax, cy - oay)
                    if adist < badge_r + 5.0:
                        score += 85.0 * (badge_r + 5.0 - adist)

                if score < best_score:
                    best_score = score
                    best_pos = (cx, cy)
                    if score == 0.0:
                        break
            if best_score == 0.0:
                break

        placed.append(
            {
                "story": story,
                "ax": ax,
                "ay": ay,
                "px": best_pos[0],
                "py": best_pos[1],
            }
        )

    return placed


def draw_map_pins(
    mdraw, get_font, placements: list[dict], badge_r: int, font_size: int
) -> None:
    """Draw leader lines, true coordinate dots, and numbered region-colored pin badges."""
    pin_font = get_font("mono_bold", font_size)
    # Draw leader lines & true anchor dots first so badges sit cleanly on top
    for item in placements:
        story = item["story"]
        color = hex_rgb(REGION_BY_KEY[story["region"]]["color"])
        ax, ay, px, py = item["ax"], item["ay"], item["px"], item["py"]
        if math.hypot(px - ax, py - ay) > badge_r + 3:
            mdraw.line((ax, ay, px, py), fill=blend_rgb(color, TEXT_PRIMARY, 0.45), width=2)
            mdraw.ellipse((ax - 4, ay - 4, ax + 4, ay + 4), fill=TEXT_PRIMARY, outline=BG_COLOR, width=1)

    for item in placements:
        story = item["story"]
        reg = REGION_BY_KEY[story["region"]]
        color = hex_rgb(reg["color"])
        fg = hex_rgb(reg["badge_fg"])
        px, py = item["px"], item["py"]
        mdraw.ellipse(
            (px - badge_r - 2, py - badge_r - 2, px + badge_r + 2, py + badge_r + 2),
            fill=BG_COLOR,
        )
        mdraw.ellipse(
            (px - badge_r, py - badge_r, px + badge_r, py + badge_r),
            fill=color,
            outline=TEXT_PRIMARY,
            width=1,
        )
        draw_centered_text(mdraw, px, py, str(story["id"]), pin_font, fg)


def draw_world_map_section(base_img, draw, get_font, image_cls, image_draw_cls) -> None:
    """Render the central World Map panel, Regional Legend key, and Europe/Mideast inset."""
    # Left panel: Main Equirectangular World Map (x=32..1524, y=358..922)
    mx0, my0, mx1, my1 = MARGIN_X, MAP_Y0, 1524, MAP_Y1
    draw.rounded_rectangle(
        (mx0, my0, mx1, my1), radius=12, fill=SURFACE_ALT, outline=BORDER_COLOR, width=2
    )
    hdr_font = get_font("sans_bold", 16)
    draw.text(
        (mx0 + 16, my0 + 10),
        "WORLD NEWS ATLAS  •  42 GEOLOCATED EVENTS  (WED 18 NOV 2026)",
        font=hdr_font,
        fill=TEXT_PRIMARY,
    )
    sub_map_font = get_font("sans", 14)
    draw.text(
        (mx1 - 295, my0 + 12),
        "Equirectangular  •  1–42 Story Pins",
        font=sub_map_font,
        fill=TEXT_MUTED,
    )

    vx0, vy0, vx1, vy1 = mx0 + 8, my0 + 38, mx1 - 8, my1 - 8
    vw, vh = vx1 - vx0, vy1 - vy0
    world_img, world_draw = render_map_basemap(
        image_cls, image_draw_cls, vw, vh, WORLD_BOUNDS, lon_step=30, lat_step=30
    )

    # Highlight Europe & Mideast inset extent on the world map
    iz_x0, iz_y1 = project_equirectangular(INSET_BOUNDS[2], INSET_BOUNDS[0], WORLD_BOUNDS, vw, vh)
    iz_x1, iz_y0 = project_equirectangular(INSET_BOUNDS[3], INSET_BOUNDS[1], WORLD_BOUNDS, vw, vh)
    world_draw.rectangle(
        (iz_x0, iz_y0, iz_x1, iz_y1), outline=(176, 138, 46), width=2
    )

    world_pins = layout_map_pins(STORIES, WORLD_BOUNDS, vw, vh, badge_r=13)
    draw_map_pins(world_draw, get_font, world_pins, badge_r=13, font_size=14)
    base_img.paste(world_img, (vx0, vy0))
    draw.rectangle((vx0, vy0, vx1, vy1), outline=BORDER_COLOR, width=1)

    # Right-top panel: Regional Color Key (x=1540..2016, y=358..568)
    kx0, ky0, kx1, ky1 = 1540, MAP_Y0, CANVAS_W - MARGIN_X, 568
    draw.rounded_rectangle(
        (kx0, ky0, kx1, ky1), radius=12, fill=SURFACE_ALT, outline=BORDER_COLOR, width=2
    )
    draw.text(
        (kx0 + 16, ky0 + 10),
        "MAP KEY  •  6 REGIONS & BEATS",
        font=hdr_font,
        fill=GOLD_ACCENT,
    )
    draw.line((kx0 + 14, ky0 + 34, kx1 - 14, ky0 + 34), fill=BORDER_COLOR, width=1)

    key_font = get_font("sans_bold", 15)
    range_font = get_font("mono_bold", 15)
    row_h = (ky1 - (ky0 + 40) - 8) / len(REGIONS)
    for idx, reg in enumerate(REGIONS):
        ry = ky0 + 40 + idx * row_h + row_h / 2.0
        col = hex_rgb(reg["color"])
        draw.ellipse((kx0 + 18, ry - 8, kx0 + 34, ry + 8), fill=col, outline=TEXT_PRIMARY, width=1)
        draw.text((kx0 + 44, ry - 9), reg["label"], font=key_font, fill=TEXT_PRIMARY)
        rw = draw.textlength(reg["range_label"], font=range_font)
        draw.text((kx1 - 18 - rw, ry - 9), reg["range_label"], font=range_font, fill=col)

    # Right-bottom panel: Europe & Mideast Zoom Inset (x=1540..2016, y=580..922)
    zx0, zy0, zx1, zy1 = 1540, 580, CANVAS_W - MARGIN_X, MAP_Y1
    draw.rounded_rectangle(
        (zx0, zy0, zx1, zy1), radius=12, fill=SURFACE_ALT, outline=BORDER_COLOR, width=2
    )
    draw.text(
        (zx0 + 16, zy0 + 10),
        "EUROPE & MIDEAST ZOOM (#8–#21, #38)",
        font=hdr_font,
        fill=GOLD_ACCENT,
    )
    ivx0, ivy0, ivx1, ivy1 = zx0 + 8, zy0 + 36, zx1 - 8, zy1 - 8
    ivw, ivh = ivx1 - ivx0, ivy1 - ivy0
    inset_img, inset_draw = render_map_basemap(
        image_cls, image_draw_cls, ivw, ivh, INSET_BOUNDS, lon_step=15, lat_step=15
    )
    inset_stories = [
        s
        for s in STORIES
        if s["region"] in {"EUROPE", "MENA"} or s["id"] == 38
    ]
    inset_pins = layout_map_pins(inset_stories, INSET_BOUNDS, ivw, ivh, badge_r=14)
    draw_map_pins(inset_draw, get_font, inset_pins, badge_r=14, font_size=15)
    base_img.paste(inset_img, (ivx0, ivy0))
    draw.rectangle((ivx0, ivy0, ivx1, ivy1), outline=GOLD_ACCENT, width=2)


def draw_regional_grid(draw, get_font) -> None:
    """Render the 6 regional news panels (7 stories each = 42 total) with matching pins."""
    cols = 3
    rows = 2
    gap_x = 16
    gap_y = 16
    panel_w = (CONTENT_W - (cols - 1) * gap_x) // cols
    panel_h = (GRID_Y1 - GRID_Y0 - (rows - 1) * gap_y) // rows

    hdr_font = get_font("sans_bold", 18)
    range_font = get_font("mono_bold", 15)
    badge_font = get_font("mono_bold", 15)
    badge_r = 15

    for idx, reg in enumerate(REGIONS):
        row = idx // cols
        col = idx % cols
        px0 = MARGIN_X + col * (panel_w + gap_x)
        px1 = (CANVAS_W - MARGIN_X) if col == cols - 1 else (px0 + panel_w)
        py0 = GRID_Y0 + row * (panel_h + gap_y)
        py1 = GRID_Y1 if row == rows - 1 else (py0 + panel_h)

        accent = hex_rgb(reg["color"])
        badge_fg = hex_rgb(reg["badge_fg"])
        panel_bg = blend_rgb(SURFACE_COLOR, accent, 0.05)

        draw.rounded_rectangle(
            (px0, py0, px1, py1), radius=12, fill=panel_bg, outline=BORDER_COLOR, width=2
        )
        hdr_h = 40
        draw.rounded_rectangle(
            (px0 + 2, py0 + 2, px1 - 2, py0 + hdr_h),
            radius=10,
            fill=blend_rgb(SURFACE_ALT, accent, 0.16),
        )
        draw.rectangle((px0 + 12, py0, px1 - 12, py0 + 5), fill=accent)

        draw.text((px0 + 16, py0 + 11), reg["label"], font=hdr_font, fill=TEXT_PRIMARY)
        rw = int(math.ceil(draw.textlength(reg["range_label"], font=range_font))) + 18
        rx1 = px1 - 12
        rx0 = rx1 - rw
        draw.rounded_rectangle(
            (rx0, py0 + 9, rx1, py0 + 33), radius=6, fill=accent
        )
        draw_centered_text(
            draw, (rx0 + rx1) / 2.0, py0 + 21, reg["range_label"], range_font, badge_fg
        )

        reg_stories = [s for s in STORIES if s["region"] == reg["key"]]
        body_y0 = py0 + hdr_h + 4
        body_y1 = py1 - 6
        row_h = (body_y1 - body_y0) / len(reg_stories)
        text_x = px0 + 54
        max_text_w = px1 - text_x - 14

        for s_idx, story in enumerate(reg_stories):
            ry0 = body_y0 + s_idx * row_h
            ry_mid = ry0 + row_h / 2.0
            if s_idx > 0:
                draw.line(
                    (px0 + 14, ry0, px1 - 14, ry0),
                    fill=blend_rgb(SURFACE_COLOR, BORDER_COLOR, 0.65),
                    width=1,
                )

            bx = px0 + 29
            draw.ellipse(
                (bx - badge_r, ry_mid - badge_r, bx + badge_r, ry_mid + badge_r),
                fill=accent,
                outline=blend_rgb(accent, TEXT_PRIMARY, 0.45),
                width=1,
            )
            draw_centered_text(
                draw, bx, ry_mid, str(story["id"]), badge_font, badge_fg
            )

            title_font, _ = fit_font_single_line(
                draw, get_font, "sans_bold", story["title"], max_text_w, 20, 15
            )
            detail_font, _ = fit_font_single_line(
                draw, get_font, "sans", story["detail"], max_text_w, 16, 12
            )
            draw.text((text_x, ry0 + 6), story["title"], font=title_font, fill=TEXT_PRIMARY)
            draw.text((text_x, ry0 + 33), story["detail"], font=detail_font, fill=TEXT_SECONDARY)


def draw_kpi_strip(draw, get_font) -> None:
    """Render the 6-item bottom KPI ticker strip with key market & science figures."""
    gap = 14
    n_kpis = len(KPIS)
    card_w = (CONTENT_W - (n_kpis - 1) * gap) // n_kpis
    label_font = get_font("sans_bold", 14)
    delta_font = get_font("mono_bold", 15)

    for idx, kpi in enumerate(KPIS):
        kx0 = MARGIN_X + idx * (card_w + gap)
        kx1 = (CANVAS_W - MARGIN_X) if idx == n_kpis - 1 else (kx0 + card_w)
        ky0, ky1 = KPI_Y0, KPI_Y1
        accent = hex_rgb(kpi["accent"])
        card_bg = blend_rgb(SURFACE_ALT, accent, 0.08)

        draw.rounded_rectangle(
            (kx0, ky0, kx1, ky1), radius=10, fill=card_bg, outline=BORDER_COLOR, width=2
        )
        draw.rectangle((kx0 + 2, ky0 + 10, kx0 + 7, ky1 - 10), fill=accent)

        draw.text((kx0 + 16, ky0 + 11), kpi["label"], font=label_font, fill=TEXT_MUTED)
        dw = draw.textlength(kpi["delta"], font=delta_font)
        draw.text((kx1 - 14 - dw, ky0 + 10), kpi["delta"], font=delta_font, fill=accent)

        val_font, _ = fit_font_single_line(
            draw, get_font, "sans_bold", kpi["value"], (kx1 - kx0) - 30, 28, 18
        )
        draw.text((kx0 + 16, ky0 + 36), kpi["value"], font=val_font, fill=TEXT_PRIMARY)


def render_infographic() -> Path:
    """Render the 2x supersampled infographic and downsample to 1024x1024 RGB PNG."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    get_font = make_font_loader(ImageFont)

    draw_masthead(draw, get_font)
    draw_hero_cards(draw, get_font)
    draw_world_map_section(img, draw, get_font, Image, ImageDraw)
    draw_regional_grid(draw, get_font)
    draw_kpi_strip(draw, get_font)

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    dst = out_dir / "entry.png"
    final_img = img.resize((TARGET_SIZE, TARGET_SIZE), Image.Resampling.LANCZOS)
    final_img.save(dst, format="PNG", optimize=True)
    size_bytes = dst.stat().st_size
    if size_bytes > MAX_BYTES:
        raise ValueError(f"Generated PNG exceeds 1 MiB limit: {size_bytes} bytes")
    return dst


def main() -> int:
    render_flag = os.environ.get("MAKEFUN_RENDER", "").strip().lower()
    if render_flag in {"1", "true", "yes", "on"}:
        render_infographic()
    else:
        copy_prebuilt_image()
    return 0


if __name__ == "__main__":
    sys.exit(main())
