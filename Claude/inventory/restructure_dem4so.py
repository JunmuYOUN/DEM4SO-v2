"""
Re-layout /userhome/youn_j/Dataset/DEM4SO-v2/ from per-date hierarchy
(<Y>/<M>/<D>/...) into per-obstime tag (<YYYYMMDDTHHMM>/...) matching the
/userhome/youn_j/DEM/Testset/ convention.

Source layout:
  hrieuv174/<Y>/<M>/<D>/solo_L1_eui-hrieuv174-image_*.fits
  AIA/<Y>/<M>/<D>/<ch>/aia.lev1_euv_12s.*.{image_lev1,spikes}.fits

New layout:
  hrieuv174/<TAG>/solo_L1_eui-hrieuv174-image_*.fits
  AIA/<TAG>/<ch>/aia.lev1_euv_12s.*.{image_lev1,spikes}.fits

where TAG = obstime.strftime("%Y%m%dT%H%M") is derived **from each FITS
filename's own timestamp**, so multiple files sharing a (Y, M, D) directory
land in distinct tag folders.

For AIA, the tag of the AIA file follows the matched HRI obstime read from
Claude/inventory/hri174_download_list.csv (one HRI obstime per (Y, M, D)).
If a (Y, M, D) ever holds AIAs for multiple HRI obstimes, extend this
mapping accordingly.

Uses os.rename (same filesystem). Empty <Y>/<M>/<D> trees are left for the
user to remove explicitly later (rmdir requires permission).
"""
from __future__ import annotations

import csv
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT     = Path("/userhome/youn_j/Dataset/DEM4SO-v2")
INV_CSV  = Path("/userhome/youn_j/Code_V3/Claude/inventory/hri174_download_list.csv")
CHANNELS = ["094", "131", "171", "193", "211", "335"]
LOG_PATH = Path("/userhome/youn_j/Code_V3/Claude/inventory/restructure.log")
HRI_FNAME_RE = re.compile(
    r"solo_L1_eui-hrieuv174-image_(?P<ts>\d{8}T\d{4})\d*_V\d+\.fits"
)


def safe_move(src: Path, dst: Path) -> str:
    if not src.exists():
        return f"miss   {src}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return f"exists {dst}"
    os.rename(src, dst)
    return f"moved  {src} -> {dst}"


def main() -> int:
    rows = list(csv.DictReader(INV_CSV.open()))
    if not rows:
        print(f"empty inventory: {INV_CSV}", file=sys.stderr)
        return 1
    log: list[str] = []
    n_hri = n_aia = 0
    for r in rows:
        t   = datetime.fromisoformat(r["time_utc"])
        tag = t.strftime("%Y%m%dT%H%M")
        y, m, d = r["year"], r["month"], r["day"]

        # --- HRI: tag derived from each file's own timestamp -------------
        hri_src_dir = ROOT / "hrieuv174" / y / m / d
        if hri_src_dir.is_dir():
            for src in sorted(hri_src_dir.glob("solo_L1_eui-hrieuv174-image_*.fits")):
                fm = HRI_FNAME_RE.match(src.name)
                file_tag = fm["ts"] if fm else tag
                dst = ROOT / "hrieuv174" / file_tag / src.name
                msg = safe_move(src, dst)
                log.append(msg)
                if msg.startswith("moved"):
                    n_hri += 1

        # --- AIA per channel ----------------------------------------------
        for ch in CHANNELS:
            aia_src_dir = ROOT / "AIA" / y / m / d / ch
            if not aia_src_dir.is_dir():
                continue
            for src in sorted(aia_src_dir.glob("aia.lev1_euv_12s.*.fits")):
                dst = ROOT / "AIA" / tag / ch / src.name
                msg = safe_move(src, dst)
                log.append(msg)
                if msg.startswith("moved"):
                    n_aia += 1

    LOG_PATH.write_text("\n".join(log) + "\n")
    print(f"moved {n_hri} HRI files, {n_aia} AIA files")
    print(f"log -> {LOG_PATH}")

    # report empty source dirs left behind (rmdir is user's call)
    empties: list[Path] = []
    for base in ("hrieuv174", "AIA"):
        for p in (ROOT / base).rglob("*"):
            if p.is_dir() and not any(p.iterdir()):
                empties.append(p)
    if empties:
        print(f"\n{len(empties)} empty directories left (not removed):")
        for p in sorted(empties)[:20]:
            print(f"  {p}")
        if len(empties) > 20:
            print(f"  ... and {len(empties) - 20} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
