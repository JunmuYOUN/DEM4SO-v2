"""
Build a per-minute snapshot set for the SolO observing block
2025-03-14 05:30..06:29 UTC (60 minutes, 60 tags).

Layout:
  /userhome/youn_j/Dataset_V2/RAW/inner_conj/20250314T0530-T0629/
    <YYYYMMDDThhmm>/
      AIA/   aia.lev1_euv_12s.<obstime>.<ch>.image_lev1.fits   (7 channels)
      FSI/   solo_L1_eui-fsi{174,304}-image_*.fits             (≤2 files)
      HRI/   solo_L1_eui-hrieuv174-image_*.fits                (1 file)

Strategy (to avoid 60 separate JSOC export jobs):
  * AIA — one Fido search over the whole block with a.Sample(60 s), so JSOC
    returns ~60 records per channel = 1 per minute. Fido.fetch streams them
    into a shared pool; then for each minute tag we pick the per-channel
    frame whose obstime is nearest.
  * HRI / FSI — scan files_L1.txt for the block, hard-link from
    /userhome/youn_j/Dataset_V2/RAW/{hrieuv174,fsi174,fsi304}/ if already
    on disk, else wget from SIDC release 7.0. Same nearest-per-tag logic.

Light-time correction (Earth ↔ SolO): +269.98 s @ 2025-03-14 06:00,
so AIA target = SolO obstime + 269.98 s. HRI/FSI keep SolO obstime as-is.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import astropy.units as u
from astropy.time import Time
from sunpy.net import Fido, attrs as a

# ---------------------------------------------------------------- constants
BLOCK_START   = datetime(2025, 3, 14, 5, 30)
BLOCK_END     = datetime(2025, 3, 14, 6, 29)        # inclusive (last minute)
LIGHT_TIME_S  = 269.98
OUT_BASE      = Path("/userhome/youn_j/Dataset_V2/RAW/inner_conj/20250314T0530-T0629")
POOL_DIR      = OUT_BASE / "_pool"                  # downloaded files staged here
FILE_LIST     = Path("/userhome/youn_j/Dataset_V2/RAW/files_L1.txt")
RAW_HRI       = Path("/userhome/youn_j/Dataset_V2/RAW/hrieuv174")
RAW_FSI174    = Path("/userhome/youn_j/Dataset_V2/RAW/fsi174")
RAW_FSI304    = Path("/userhome/youn_j/Dataset_V2/RAW/fsi304")
RELEASE_URL   = "https://www.sidc.be/EUI/data/releases/202510_release_7.0"
JSOC_EMAIL    = "startime98@catholic.ac.kr"
AIA_WAVES     = [94, 131, 171, 193, 211, 304, 335]

# ---------------------------------------------------------------- patterns
AIA_NAME_RE = re.compile(
    r"aia\.lev1_euv_12s\.(?P<ts>\d{4}-\d{2}-\d{2}T\d{6})Z\.(?P<ch>\d+)\.image_lev1\.fits$"
)
EUI_LINE_RE = re.compile(
    r"^\./L1/\d{4}/\d{2}/\d{2}/solo_L1_eui-(?P<prod>hrieuv174|fsi174|fsi304)-image_"
    r"(?P<ts>\d{8}T\d{6})\d*_V\d+\.fits\s*$"
)


# ---------------------------------------------------------------- helpers
def link_or_copy(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return "exists"
    try:
        os.link(src, dst)
        return "link"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


# ---------------------------------------------------------------- AIA bulk
def bulk_fetch_aia() -> list[tuple[datetime, int, Path]]:
    """One JSOC export covering [t_aia_start, t_aia_end+1min] with 60 s sample."""
    t0 = Time(BLOCK_START + timedelta(seconds=LIGHT_TIME_S))
    t1 = Time(BLOCK_END   + timedelta(seconds=LIGHT_TIME_S) + timedelta(minutes=1))
    pool = POOL_DIR / "AIA"
    pool.mkdir(parents=True, exist_ok=True)
    print(f"AIA Fido search  [{t0.iso}, {t1.iso}]  Sample(60s)")
    q = Fido.search(
        a.Time(t0, t1),
        a.jsoc.Series("aia.lev1_euv_12s"),
        a.jsoc.Notify(JSOC_EMAIL),
        a.Sample(60 * u.s),
    )
    if not len(q) or len(q[0]) == 0:
        print("  no records")
        return []
    n = len(q[0])
    print(f"  JSOC: {n} records  (expect ~7 channels x 60 min = 420)")
    files = Fido.fetch(q, path=str(pool / "{file}"), progress=False, overwrite=False)
    pool_files: list[tuple[datetime, int, Path]] = []
    for f in files:
        if "image_lev1" not in f:
            continue
        p = Path(f)
        m = AIA_NAME_RE.search(p.name)
        if not m:
            continue
        ts = datetime.strptime(m["ts"], "%Y-%m-%dT%H%M%S")
        pool_files.append((ts, int(m["ch"]), p))
    print(f"  pool: {len(pool_files)} image_lev1 files")
    return pool_files


# ---------------------------------------------------------------- EUI bulk
def index_eui_block(product: str) -> list[tuple[datetime, str]]:
    """Lines of files_L1.txt for `product` overlapping the block."""
    rows: list[tuple[datetime, str]] = []
    day_prefix = f"./L1/{BLOCK_START.year:04d}/{BLOCK_START.month:02d}/{BLOCK_START.day:02d}/"
    with FILE_LIST.open() as fh:
        for line in fh:
            if not line.startswith(day_prefix):
                continue
            m = EUI_LINE_RE.match(line)
            if not m or m["prod"] != product:
                continue
            try:
                ts = datetime.strptime(m["ts"], "%Y%m%dT%H%M%S")
            except ValueError:
                continue
            if BLOCK_START - timedelta(minutes=5) <= ts <= BLOCK_END + timedelta(minutes=15):
                rows.append((ts, line.strip().lstrip("./")))
    rows.sort()
    return rows


def bulk_fetch_eui(product: str) -> list[tuple[datetime, Path]]:
    """Hard-link from RAW/<product>/ if available, else wget into pool."""
    pool = POOL_DIR / product.upper().replace("HRIEUV174", "HRI").replace("FSI", "FSI")
    pool.mkdir(parents=True, exist_ok=True)
    # build name -> on-disk path lookup from the matching RAW pool
    raw_lookup: dict[str, Path] = {}
    raw_roots: list[Path] = []
    if product == "hrieuv174":
        raw_roots = [RAW_HRI]
    elif product == "fsi174":
        raw_roots = [RAW_FSI174]
    elif product == "fsi304":
        raw_roots = [RAW_FSI304]
    for root in raw_roots:
        for p in root.rglob(f"solo_L1_eui-{product}-image_*.fits"):
            raw_lookup[p.name] = p

    rows = index_eui_block(product)
    print(f"{product} candidates in block window: {len(rows)}")
    out: list[tuple[datetime, Path]] = []
    for ts, rel in rows:
        fname = Path(rel).name
        if fname in raw_lookup:
            src = raw_lookup[fname]
            dst = pool / fname
            link_or_copy(src, dst)
            out.append((ts, dst))
            continue
        dst = pool / fname
        if dst.exists() and dst.stat().st_size > 0:
            out.append((ts, dst))
            continue
        url = f"{RELEASE_URL}/{rel}"
        rc = subprocess.run(
            ["wget", "-q", "--tries=3", "--timeout=60", "-O", str(dst), url]
        ).returncode
        if rc == 0 and dst.exists() and dst.stat().st_size > 0:
            out.append((ts, dst))
        else:
            print(f"  FAIL {url}")
            if dst.exists() and dst.stat().st_size == 0:
                pass  # leave to user
    print(f"  pool: {len(out)}")
    return out


# ---------------------------------------------------------------- assign per tag
def assign_per_tag(aia_pool: list[tuple[datetime, int, Path]],
                   hri_pool: list[tuple[datetime, Path]],
                   fsi174_pool: list[tuple[datetime, Path]],
                   fsi304_pool: list[tuple[datetime, Path]]) -> int:
    n_minutes = int((BLOCK_END - BLOCK_START).total_seconds() / 60) + 1
    total_links = 0
    for i in range(n_minutes):
        conj = BLOCK_START + timedelta(minutes=i)
        t_aia = conj + timedelta(seconds=LIGHT_TIME_S)
        tag   = conj.strftime("%Y%m%dT%H%M")
        tag_dir = OUT_BASE / tag
        out_aia = tag_dir / "AIA"
        out_fsi = tag_dir / "FSI"
        out_hri = tag_dir / "HRI"

        # AIA per channel: nearest by abs time to t_aia
        for wave in AIA_WAVES:
            cands = [(abs((ts - t_aia).total_seconds()), ts, p)
                     for ts, ch, p in aia_pool if ch == wave]
            if not cands:
                continue
            cands.sort()
            _, ts, src = cands[0]
            link_or_copy(src, out_aia / src.name)
            total_links += 1
        # HRI: nearest by abs time to conj
        if hri_pool:
            cands = sorted((abs((ts - conj).total_seconds()), ts, p)
                           for ts, p in hri_pool)
            _, ts, src = cands[0]
            link_or_copy(src, out_hri / src.name)
            total_links += 1
        for pool_, prod in ((fsi174_pool, "fsi174"), (fsi304_pool, "fsi304")):
            if not pool_:
                continue
            cands = sorted((abs((ts - conj).total_seconds()), ts, p)
                           for ts, p in pool_)
            _, ts, src = cands[0]
            link_or_copy(src, out_fsi / src.name)
            total_links += 1
    return total_links


# ---------------------------------------------------------------- main
def main() -> int:
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    aia    = bulk_fetch_aia()
    hri    = bulk_fetch_eui("hrieuv174")
    fsi174 = bulk_fetch_eui("fsi174")
    fsi304 = bulk_fetch_eui("fsi304")
    n = assign_per_tag(aia, hri, fsi174, fsi304)
    print(f"\nlinks distributed: {n}")
    print(f"layout: {OUT_BASE}/<TAG>/{{AIA,FSI,HRI}}/")
    print(f"pool dir (sources): {POOL_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
