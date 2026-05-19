"""
Walk /userhome/youn_j/Dataset/DEM4SO-v2/hrieuv174/<TAG>/*.fits and re-derive
the canonical TAG from each filename's embedded obstime
(YYYYMMDDThhmmss). If a file is in the wrong TAG folder, move it.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path("/userhome/youn_j/Dataset/DEM4SO-v2/hrieuv174")
TAG_RE = re.compile(r"^\d{8}T\d{4}$")
FNAME_RE = re.compile(
    r"solo_L1_eui-hrieuv174-image_(?P<ts>\d{8}T\d{4})\d*_V\d+\.fits"
)


def main() -> int:
    moved = ok = 0
    for tag_dir in sorted(ROOT.iterdir()):
        if not (tag_dir.is_dir() and TAG_RE.match(tag_dir.name)):
            continue
        for src in sorted(tag_dir.glob("solo_L1_eui-hrieuv174-image_*.fits")):
            m = FNAME_RE.match(src.name)
            if not m:
                print(f"skip   {src} (no parseable timestamp)")
                continue
            wanted_tag = m["ts"]                       # YYYYMMDDThhmm
            if wanted_tag == tag_dir.name:
                ok += 1
                continue
            dst_dir = ROOT / wanted_tag
            dst_dir.mkdir(parents=True, exist_ok=True)
            dst = dst_dir / src.name
            if dst.exists():
                print(f"exists {dst} (left {src})")
                continue
            os.rename(src, dst)
            print(f"moved  {src.name}  {tag_dir.name} -> {wanted_tag}")
            moved += 1
    print(f"done. moved={moved} ok={ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
