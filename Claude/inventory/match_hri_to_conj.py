"""
For each EUI_Gen folder under /userhome/youn_j/DEM/Testset/EUI_Gen/<DATE>T<HHMM>/,
find the nearest hrieuv174 L1 frame in SIDC release 7.0 by parsing
/userhome/youn_j/Dataset/files_L1.txt. Download the file if not already on
disk under /userhome/youn_j/Dataset/DEM4SO-v2/hrieuv174/YYYY/MM/DD/, then
hard-link or copy it into /userhome/youn_j/DEM/Testset/HRI174/<DATE>T<HHMM>/.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

EUI_GEN_ROOT = Path("/userhome/youn_j/DEM/Testset/EUI_Gen")
HRI_OUT_ROOT = Path("/userhome/youn_j/DEM/Testset/HRI174")
HRI_DISK_ROOT = Path("/userhome/youn_j/Dataset/DEM4SO-v2/hrieuv174")
FILE_LIST    = Path("/userhome/youn_j/Dataset/files_L1.txt")
RELEASE_URL  = "https://www.sidc.be/EUI/data/releases/202510_release_7.0"

PATTERN = re.compile(
    r"^(?P<rel>\./L1/(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2})/"
    r"solo_L1_eui-hrieuv174-image_(?P<ts>\d{8}T\d{6})\d*_V\d+\.fits)\s*$"
)


def parse_folder_tag(tag: str) -> datetime:
    return datetime.strptime(tag, "%Y%m%dT%H%M")


def index_release(date: datetime) -> list[tuple[datetime, str, str, str, str]]:
    rows = []
    day_prefix = f"./L1/{date.year:04d}/{date.month:02d}/{date.day:02d}/"
    with FILE_LIST.open() as fh:
        for line in fh:
            if not line.startswith(day_prefix):
                continue
            m = PATTERN.match(line)
            if not m:
                continue
            try:
                ts = datetime.strptime(m["ts"], "%Y%m%dT%H%M%S")
            except ValueError:
                continue
            rows.append((ts, m["y"], m["m"], m["d"], m["rel"].lstrip("./")))
    rows.sort(key=lambda r: r[0])
    return rows


def ensure_local(rel: str, y: str, m: str, d: str) -> Path:
    fname = Path(rel).name
    local = HRI_DISK_ROOT / y / m / d / fname
    if local.exists() and local.stat().st_size > 0:
        return local
    local.parent.mkdir(parents=True, exist_ok=True)
    url = f"{RELEASE_URL}/{rel}"
    print(f"  downloading {url}")
    subprocess.run(
        ["wget", "-q", "--tries=3", "--timeout=60", "-O", str(local), url],
        check=True,
    )
    return local


def link_or_copy(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return f"exists {dst}"
    try:
        os.link(src, dst)  # hard link to save disk
        return f"link   {dst}"
    except OSError:
        shutil.copy2(src, dst)
        return f"copy   {dst}"


def main() -> int:
    tags = sorted(p.name for p in EUI_GEN_ROOT.iterdir() if p.is_dir())
    if not tags:
        print(f"no EUI_Gen folders under {EUI_GEN_ROOT}", file=sys.stderr)
        return 1
    for tag in tags:
        target = parse_folder_tag(tag)
        rows = index_release(target)
        print(f"=== {tag}  target {target.isoformat()} ===")
        if not rows:
            print(f"  no hrieuv174 in release 7.0 on {target.date().isoformat()}")
            continue
        nearest = min(rows, key=lambda r: abs((r[0] - target).total_seconds()))
        ts, y, m, d, rel = nearest
        dt_min = abs((ts - target).total_seconds()) / 60.0
        print(f"  nearest hrieuv174 = {ts.isoformat()}  (delta = {dt_min:.1f} min)")
        local = ensure_local(rel, y, m, d)
        out_dir = HRI_OUT_ROOT / tag
        msg = link_or_copy(local, out_dir / local.name)
        print(f"  {msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
