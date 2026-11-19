# news-image-20261118-172830

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Asw1999/news-image-20261118-172830/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Asw1999/news-image-20261118-172830/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

World news summary infographic for **Wednesday, 18 November 2026**, built for the [make.fun news-image-20261118 bounty](https://make.fun/bounty/news-image-20261118).

## Overview

`main.py` outputs a 1024x1024 PNG (`entry.png`) presenting an editorial newspaper broadsheet of **42 verified single-topic world news stories** from Wednesday, 18 November 2026 across six regions (Asia-Pacific, Middle East, Europe, Africa, Americas, and Global & Oceania). It features a full-width cream broadsheet masthead and proportional colored region count ribbon, 13 custom pastel vector story illustrations with bottom caption strips and wire attributions, a `THE DAY IN NUMBERS` 7-metric summary strip, a collision-free `WHERE IT HAPPENED` map with hairline leader lines, a 29-story brief directory (`#14–#42`), and a `DATE CHECK` verification strip.

## Run

Deterministic sandbox mode (Python 3 stdlib only, copies pre-rendered `entry.png`):

```bash
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Re-render from source (requires Pillow):

```bash
MAKEFUN_RENDER=1 MAKEFUN_OUTPUT_DIR=. python3 main.py
```
