# ENSO charts — handoff notes

Last updated: 4 October 2026. Latest data in hand: **JAS 2026**.

## Get the data from the ascii files, not the web tables

| Index | URL |
|---|---|
| RONI | `https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt` |
| ONI  | `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` |

Both named in [NWS PNS 26-05](https://www.weather.gov/media/notification/pdf_2026/pns26-05_Relative_ONI.pdf).

**Do not scrape the HTML tables.** Three traps found on 18 Sep 2026:

1. `.../analysis_monitoring/enso/roni/` served a **cached ERSSTv5 copy**
   truncated at MAM 2026, twice on separate days. Its header still cited
   ERSSTv5 / Huang et al. 2017 while the live page was already v6.
2. `.../analysis_monitoring/enso/oni/v6/` and `/v5/` both return a
   **redirect loop** and cannot be fetched at all.
3. `.../data/indices/` (the directory) also loops — the individual
   `.txt` files fetch fine, the listing does not.

The ascii files were current (through JJA 2026) when everything else was stale.

Sanity check after fetching: round to tenths and compare a couple of rows
against whatever the web table shows. `enso_chart.py` uses round-half-toward-
+infinity, which is what reproduces CPC's published values (−0.75 → −0.7,
0.65 → 0.7). Plain round-half-away-from-zero does not.

## Which version

CPC moved both indices to **ERSSTv6** on 10 Aug 2026 (NCEI discontinued
ERSSTv5). v6 shifted the whole historical record, not just recent months —
e.g. RONI DJF 1950 is −1.2 on v6 vs −1.5 on v5. Anything built before that
date is on the retired series. Per PNS 26-05, RONI is now the official index
for ENSO monitoring; ONI continues as a secondary reference.

## Update cadence

Page updates by the 5th of each month. A season needs its last month
complete, so **ASO posts around 5 November** (JAS was already in the ascii
files on 4 October, a day ahead of that). CPC may revise values for up
to two months after first posting, so re-download the whole file each time
rather than appending one value. At the 4 Oct update the earlier 2026
values (DJF through JJA) were unchanged in both files.

The container resets between sessions: upload `enso_chart.py` and this file,
fetch both ascii files fresh, and run. The ascii snapshots saved alongside
are three-column (SEAS YR ANOM); the live ONI file has a fourth TOTAL column,
which the parser ignores.

## Rebuilding

    python3 enso_chart.py --data RONI.ascii.txt --index RONI --out roni.png
    python3 enso_chart.py --data oni.ascii.txt  --index ONI --top 7 --out oni.png

Panel B switches the current year's label from a floating tag to a right-edge
leader line automatically once that ENSO year runs all the way to FMA.

## Event selection — read this before re-running

The `≥ +2.0 °C` rule does not survive the version change intact:

* **RONI v5** — seven events: 1957-58, 1965-66, 1972-73, 1982-83, 1991-92,
  1997-98, 2015-16.
* **RONI v6** — six. 1957-58 drops to +1.9. And the cut is fragile: at full
  hundredths only four clear it, because 1965-66 sits at 1.99 and 1972-73 at
  1.97 and both round up in the published table. Expect reshuffling.
* **ONI v6** — only three clear +2.0 (1982-83, 1997-98, 2015-16), so the ONI
  chart uses `--top 7` instead. That set is the RONI seven with 1991-92 out
  and 2023-24 in.

## Where 2026 stands (as of JAS)

* RONI v6 JAS **+1.69**, second-highest JAS in the record behind 1997 (+1.84),
  ahead of 2015 (+1.54) and 1965 (+1.49). JJA was +1.36, also second.
* ONI v6 JAS **+2.16**, the **highest JAS in the 77-year record**, above 1997
  (+1.79) and 2015 (+1.73). JJA was +1.80, also the highest. The two indices
  disagree because ONI carries the tropical-mean warming that RONI subtracts out.
* Event sets unchanged: RONI six at the +2.0 cut (1965-66, 1972-73, 1982-83,
  1991-92, 1997-98, 2015-16); ONI seven strongest (RONI six minus 1991-92,
  plus 1957-58 and 2023-24).
* Caveat worth keeping: the strong events spread widely between JAS and NDJ,
  so a high September value constrains the winter peak less than it looks.
