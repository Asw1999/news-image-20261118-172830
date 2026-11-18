# news-image-20261118-172830

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Asw1999/news-image-20261118-172830/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Asw1999/news-image-20261118-172830/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

World news summary infographic for **Wednesday, 18 November 2026**, built for the [make.fun news-image-20261118 bounty](https://make.fun/bounty/news-image-20261118).

## Overview

`main.py` outputs a 1024x1024 RGB PNG (`entry.png`) synthesizing 42 verified world news stories from Wednesday, 18 November 2026 across six regions and beats (Americas, Europe, Middle East & North Africa, Sub-Saharan Africa, Asia-Pacific, and Global / Science / Markets), complete with a 4-card Hero Spotlight, a numbered equirectangular world news map, regional story cards, and a 6-metric market & milestone KPI ticker.

## Run

Deterministic sandbox mode (Python 3 stdlib only, copies pre-rendered `entry.png`):

```bash
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Re-render from source (requires Pillow):

```bash
MAKEFUN_RENDER=1 MAKEFUN_OUTPUT_DIR=. python3 main.py
```
