"""
Retry the AIA records that came back as `none` in download_aia_pairs.log,
this time with a wider +/-30 s window. Appends results back to the same log
so the next data_distribution.md run sees them.

Re-uses download_aia_pairs.fetch_one with a per-call window override via a
small wrapper.
"""
from __future__ import annotations

import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import astropy.units as u
from astropy.time import Time
from sunpy.net import Fido, attrs as a

LOG     = Path("/userhome/youn_j/Code_V3/Claude/inventory/download_aia_pairs.log")
AIA_ROOT = Path("/userhome/youn_j/Dataset/DEM4SO-v2/AIA")
JSOC_EMAIL = "startime98@catholic.ac.kr"
HALF_WINDOW_S = 30


def parse_nones(log: Path) -> list[tuple[int, datetime]]:
    pat = re.compile(r"^none\s+wave=(\d+)\s+t=(\S+)")
    seen: set[tuple[int, str]] = set()
    rows: list[tuple[int, datetime]] = []
    for line in log.read_text().splitlines():
        m = pat.match(line)
        if not m:
            continue
        key = (int(m.group(1)), m.group(2))
        if key in seen:
            continue
        seen.add(key)
        rows.append((int(m.group(1)), datetime.fromisoformat(m.group(2))))
    return rows


def fetch(wave: int, t: datetime, log) -> str:
    t0 = Time(t - timedelta(seconds=HALF_WINDOW_S))
    t1 = Time(t + timedelta(seconds=HALF_WINDOW_S))
    y, mo, d = f"{t.year:04d}", f"{t.month:02d}", f"{t.day:02d}"
    dest = AIA_ROOT / y / mo / d / f"{wave:03d}"
    dest.mkdir(parents=True, exist_ok=True)
    try:
        q = Fido.search(
            a.Time(t0, t1),
            a.jsoc.Series("aia.lev1_euv_12s"),
            a.Wavelength(wave * u.AA),
            a.jsoc.Notify(JSOC_EMAIL),
        )
        if not len(q) or len(q[0]) == 0:
            return f"none  wave={wave} t={t.isoformat()} (still no record at +/-30s)"
        q = q[0][:1]
        files = Fido.fetch(q, path=str(dest / "{file}"), progress=False, overwrite=False)
        if not files:
            return f"FAIL  wave={wave} t={t.isoformat()} (fetch returned empty)"
        return f"ok    wave={wave} t={t.isoformat()} -> {files[0]}  [retry +/-30s]"
    except Exception as e:
        return f"FAIL  wave={wave} t={t.isoformat()}  err={e}"


def main() -> int:
    nones = parse_nones(LOG)
    if not nones:
        print("no `none` entries to retry")
        return 0
    print(f"retrying {len(nones)} entries with +/-{HALF_WINDOW_S}s window")
    with LOG.open("a") as log:
        log.write(f"\n=== retry +/-{HALF_WINDOW_S}s @ {datetime.utcnow().isoformat()}Z ===\n")
        ok = fail = none = 0
        for wave, t in nones:
            msg = fetch(wave, t, log)
            log.write(msg + "\n")
            log.flush()
            print(msg)
            if msg.startswith("ok"):
                ok += 1
            elif msg.startswith("none"):
                none += 1
            else:
                fail += 1
            time.sleep(2)
        summary = f"retry done. ok={ok} none={none} fail={fail}"
        log.write(summary + "\n")
        print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
