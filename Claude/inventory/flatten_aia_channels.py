"""
Flatten /userhome/youn_j/Dataset/DEM4SO-v2/AIA/<TAG>/<ch>/<file>
into       /userhome/youn_j/Dataset/DEM4SO-v2/AIA/<TAG>/<file>

The wavelength is already embedded in the filename
(`aia.lev1_euv_12s.YYYY-MM-DDThhmmssZ.<ch>.image_lev1.fits` etc.)
so no information is lost.

Uses os.rename (same filesystem). Leaves now-empty <ch> directories
for explicit cleanup later (rmdir requires permission).
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT    = Path("/userhome/youn_j/Dataset/DEM4SO-v2/AIA")
TAG_RE  = re.compile(r"^\d{8}T\d{4}$")
CH_RE   = re.compile(r"^\d{3}$")


def main() -> int:
    moved = ok = collisions = 0
    for tag_dir in sorted(ROOT.iterdir()):
        if not (tag_dir.is_dir() and TAG_RE.match(tag_dir.name)):
            continue
        for ch_dir in sorted(tag_dir.iterdir()):
            if not (ch_dir.is_dir() and CH_RE.match(ch_dir.name)):
                continue
            for src in sorted(ch_dir.glob("*.fits")):
                dst = tag_dir / src.name
                if dst.exists():
                    print(f"exists {dst} (left {src})")
                    collisions += 1
                    continue
                os.rename(src, dst)
                moved += 1
    print(f"done. moved={moved} collisions={collisions}")
    # report leftover empty channel dirs
    empties = [p for p in ROOT.rglob("*") if p.is_dir() and CH_RE.match(p.name)
               and not any(p.iterdir())]
    if empties:
        print(f"\n{len(empties)} empty <ch> dirs left (cleanup needs permission):")
        for p in sorted(empties)[:10]:
            print(f"  {p}")
        if len(empties) > 10:
            print(f"  ... +{len(empties) - 10} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
