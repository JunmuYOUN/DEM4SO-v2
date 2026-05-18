"""
Download AIA 94/131/171/193/211/335 lev1 frames matched to each HRI 174 timestamp
listed in hri174_download_list.csv.

For each HRI obstime t, queries JSOC `aia.lev1_euv_12s` for the 12-second window
[t-6s, t+6s] and keeps the single nearest frame per wavelength.

Files land under
  /userhome/youn_j/Dataset/DEM4SO-v2/AIA/YYYY/MM/DD/<wave3>/<filename>
where <wave3> is zero-padded (094, 131, 171, 193, 211, 335).

JSOC notify email reused from /userhome/youn_j/Code_V2/Download/auto_down_prepV240610.py.
"""
from __future__ import annotations

import csv
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import astropy.units as u
from astropy.time import Time
from sunpy.net import Fido, attrs as a

INV_CSV       = Path(__file__).resolve().parent / "hri174_download_list.csv"
PAIR_LOG      = Path(__file__).resolve().parent / "download_aia_pairs.log"
AIA_ROOT      = Path("/userhome/youn_j/Dataset/DEM4SO-v2/AIA")
JSOC_EMAIL    = "startime98@catholic.ac.kr"
WAVELENGTHS   = [94, 131, 171, 193, 211, 335]
HALF_WINDOW_S = 6           # +/- 6 s -> single 12 s cadence frame
MAX_RETRIES   = 3


def load_inventory(path: Path) -> list[dict]:
    rows = []
    with path.open() as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            rows.append(r)
    return rows


def fetch_one(t: datetime, wave: int, dest_dir: Path, log) -> str:
    """Fetch nearest AIA lev1 frame at wavelength `wave` to time `t`."""
    t0 = Time(t - timedelta(seconds=HALF_WINDOW_S))
    t1 = Time(t + timedelta(seconds=HALF_WINDOW_S))
    dest_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(dest_dir.glob(f"*_lev1.fits"))
    # Skip if a file already exists whose filename encodes a close enough time
    tag = t.strftime("%Y_%m_%dt%H_%M")  # JSOC AIA filenames include this pattern
    for f in existing:
        if tag in f.name.lower():
            return f"skip  {f}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            q = Fido.search(
                a.Time(t0, t1),
                a.jsoc.Series("aia.lev1_euv_12s"),
                a.Wavelength(wave * u.AA),
                a.jsoc.Notify(JSOC_EMAIL),
            )
            n = len(q[0]) if len(q) else 0
            if n == 0:
                return f"none  wave={wave} t={t.isoformat()} (no JSOC record)"
            # keep first row only -> nearest match (12s cadence guarantees at most 1-2)
            q = q[0][:1]
            files = Fido.fetch(q, path=str(dest_dir / "{file}"), progress=False, overwrite=False)
            if not files:
                raise RuntimeError("Fido.fetch returned no file")
            return f"ok    wave={wave} t={t.isoformat()} -> {files[0]}"
        except Exception as e:
            log.write(f"retry {attempt}/{MAX_RETRIES} wave={wave} t={t.isoformat()}  err={e}\n")
            log.flush()
            time.sleep(5 * attempt)
    return f"FAIL  wave={wave} t={t.isoformat()}"


def main() -> int:
    rows = load_inventory(INV_CSV)
    if not rows:
        print(f"empty inventory: {INV_CSV}", file=sys.stderr)
        return 1
    print(f"loaded {len(rows)} HRI rows; will fetch {len(rows)*len(WAVELENGTHS)} AIA frames")

    with PAIR_LOG.open("a") as log:
        log.write(f"\n=== run @ {datetime.utcnow().isoformat()}Z ===\n")
        ok = sk = fail = no_rec = 0
        for row in rows:
            t = datetime.strptime(row["time_utc"], "%Y-%m-%dT%H:%M:%S")
            y, mo, d = row["year"], row["month"], row["day"]
            for wave in WAVELENGTHS:
                dest = AIA_ROOT / y / mo / d / f"{wave:03d}"
                msg = fetch_one(t, wave, dest, log)
                log.write(msg + "\n")
                log.flush()
                print(msg)
                if msg.startswith("ok"):
                    ok += 1
                elif msg.startswith("skip"):
                    sk += 1
                elif msg.startswith("none"):
                    no_rec += 1
                else:
                    fail += 1
        summary = f"done. ok={ok} skip={sk} none={no_rec} fail={fail}"
        log.write(summary + "\n")
        print(summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
