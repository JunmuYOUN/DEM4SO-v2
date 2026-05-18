"""
Build a download inventory of HRI 174 L1 files for the four target conjunctions.

Selection rule (per user direction 2026-05-18, supersedes earlier +/-2h plan):
  * channel : hrieuv174 (image), L1
  * window  : conjunction date +/- 7 days
  * cadence : at most one frame per UTC day (the earliest frame on that date wins).
              Time-of-day is irrelevant; AIA pairs will be matched to the chosen
              HRI obstime later.

Inputs
------
* /userhome/youn_j/Dataset/files_L1.txt   (SIDC release 7.0 file listing)

Outputs (next to this script)
-----------------------------
* hri174_download_list.csv  columns: conj, time_utc, year, month, day, relpath, url
* hri174_download_list.summary.txt  per-conjunction counts

The CSV is consumed by download_hri174.sh.
"""
from __future__ import annotations

import csv
import re
from datetime import datetime, timedelta
from pathlib import Path

FILE_LIST    = Path("/userhome/youn_j/Dataset/files_L1.txt")
RELEASE_URL  = "https://www.sidc.be/EUI/data/releases/202510_release_7.0"
WINDOW       = timedelta(days=7)
OUT_DIR      = Path(__file__).resolve().parent
CSV_PATH     = OUT_DIR / "hri174_download_list.csv"
SUMMARY_PATH = OUT_DIR / "hri174_download_list.summary.txt"

CONJUNCTIONS = {
    "2022-03-07T0833": datetime(2022, 3,  7,  8, 33),
    "2023-03-28T2130": datetime(2023, 3, 28, 21, 30),
    "2024-03-20T0840": datetime(2024, 3, 20,  8, 40),
    "2025-10-07T1700": datetime(2025, 10, 7, 17,  0),
}

# Match HRI 174 image (not dark/cal) and capture timestamp + relative path
PATTERN = re.compile(
    r"^(?P<rel>\./L1/(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2})/"
    r"solo_L1_eui-hrieuv174-image_(?P<ts>\d{8}T\d{6})\d*_V\d+\.fits)\s*$"
)


def main() -> None:
    windows = {tag: (c - WINDOW, c + WINDOW) for tag, c in CONJUNCTIONS.items()}
    # per-conjunction: date-bucket -> earliest matching (datetime, relpath)
    buckets: dict[str, dict[datetime, tuple[datetime, str, str, str, str]]] = {
        tag: {} for tag in CONJUNCTIONS
    }

    with FILE_LIST.open() as fh:
        for line in fh:
            m = PATTERN.match(line)
            if not m:
                continue
            try:
                ts = datetime.strptime(m["ts"], "%Y%m%dT%H%M%S")
            except ValueError:
                continue
            for tag, (lo, hi) in windows.items():
                if not (lo <= ts <= hi):
                    continue
                day = ts.replace(hour=0, minute=0, second=0, microsecond=0)
                existing = buckets[tag].get(day)
                if existing is not None and existing[0] <= ts:
                    continue  # we already have an earlier frame on this date
                buckets[tag][day] = (ts, m["y"], m["m"], m["d"], m["rel"].lstrip("./"))

    rows: list[dict[str, str]] = []
    for tag in CONJUNCTIONS:
        for minute in sorted(buckets[tag]):
            ts, y, mo, d, rel = buckets[tag][minute]
            rows.append({
                "conj":     tag,
                "time_utc": ts.strftime("%Y-%m-%dT%H:%M:%S"),
                "year":     y,
                "month":    mo,
                "day":      d,
                "relpath":  rel,
                "url":      f"{RELEASE_URL}/{rel}",
            })

    fieldnames = list(rows[0].keys()) if rows else \
        ["conj","time_utc","year","month","day","relpath","url"]
    with CSV_PATH.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    lines = []
    total = 0
    for tag, conj in CONJUNCTIONS.items():
        lo, hi = conj - WINDOW, conj + WINDOW
        n = len(buckets[tag])
        total += n
        lines.append(f"{tag}  window [{lo:%Y-%m-%d %H:%M} .. {hi:%Y-%m-%d %H:%M}]  files={n}")
    lines.append("-" * 60)
    lines.append(f"TOTAL  files={total}")
    summary = "\n".join(lines) + "\n"
    SUMMARY_PATH.write_text(summary)
    print(summary)
    print(f"wrote {CSV_PATH}")


if __name__ == "__main__":
    main()
