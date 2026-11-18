# news-image-20261118-172830

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Asw1999/news-image-20261118-172830/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Asw1999/news-image-20261118-172830/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

World news summary infographic for **Wednesday, 18 November 2026**, built for the [make.fun news-image-20261118 bounty](https://make.fun/bounty/news-image-20261118).

## Overview

`main.py` outputs a 1024x1024 RGB PNG (`entry.png`) presenting an editorial newspaper broadsheet of **45 verified world news stories** from Wednesday, 18 November 2026 across all six continents and beats (Americas, Europe, Middle East, Africa, Asia-Pacific, and Global & Science). It combines 13 custom flat-vector story illustrations with wire attributions, a light-mode equirectangular `WHERE IT HAPPENED` map, a 4-metric `BY THE NUMBERS` panel, and a 32-story brief directory.

## Run

Deterministic sandbox mode (Python 3 stdlib only, copies pre-rendered `entry.png`):

```bash
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Re-render from source (requires Pillow):

```bash
MAKEFUN_RENDER=1 MAKEFUN_OUTPUT_DIR=. python3 main.py
```
