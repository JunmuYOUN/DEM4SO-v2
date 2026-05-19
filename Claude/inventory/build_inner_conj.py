"""
Build /userhome/youn_j/Dataset_V2/RAW/inner_conj/<TAG>/{AIA,FSI,HRI}/
holding the *earliest* AIA 7ch / FSI 174+304 / HRI 174 frame in the
window [conj, conj+15min] for each inner conjunction time in
/userhome/youn_j/Dataset_V2/conjunction.md.

Reuse-first: scan RAW/AIA, RAW/hrieuv174, RAW/fsi174, RAW/fsi304, and
RAW/20250313T2030 for files whose filename obstime falls in the window.
Hard-link matches into inner_conj/. If a slot is still empty, fall back
to a SIDC release-7.0 download (EUI) or a JSOC Fido fetch (AIA).

HRI is skipped for 2024-03-20 and 2025-10-07 per user (no HRI obs near
conj on those days).
"""
from __future__ import annotations

import csv
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
RAW_ROOT      = Path("/userhome/youn_j/Dataset_V2/RAW")
OUT_ROOT      = RAW_ROOT / "inner_conj"
INV_CSV       = OUT_ROOT / "inner_conj_inventory.csv"
FILE_LIST     = RAW_ROOT / "files_L1.txt"
RELEASE_URL   = "https://www.sidc.be/EUI/data/releases/202510_release_7.0"
JSOC_EMAIL    = "startime98@catholic.ac.kr"
WINDOW        = timedelta(minutes=15)
AIA_WAVES     = [94, 131, 171, 193, 211, 304, 335]

# Conjunction tag -> (datetime, want_hri?, Earth-SolO light-time [s])
# Light times from /userhome/youn_j/Dataset_V2/conjunction.md.
# For inner conjunctions (SolO between Earth and Sun), the same solar event
# arrives at AIA `light_time_s` seconds AFTER it arrives at SolO, so AIA
# obstime to match an SolO obstime of `conj` is `conj + light_time_s`.
CONJUNCTIONS: list[tuple[str, datetime, bool, float]] = [
    ("20220307T0830", datetime(2022, 3,  7,  8, 30), True,  247.84),
    ("20230328T2130", datetime(2023, 3, 28, 21, 30), True,  297.72),
    ("20240320T0840", datetime(2024, 3, 20,  8, 40), False, 282.74),  # no HRI near conj
    ("20250313T2030", datetime(2025, 3, 13, 20, 30), True,  267.18),
    ("20251007T1700", datetime(2025, 10, 7, 17,  0), False, 250.05),  # no HRI near conj
    # Extra user-requested 3-instrument combos (not strict inner conjunctions
    # but near enough that the light-time correction is essentially constant).
    ("20230328T2100", datetime(2023, 3, 28, 21,  0), True,  297.57),
]

# ---------------------------------------------------------------- patterns
EUI_OBS_RE = re.compile(
    r"solo_L1_eui-(?P<prod>hrieuv174|fsi174|fsi304)-image_(?P<ts>\d{8}T\d{6})\d*_V\d+\.fits$"
)
AIA_OBS_RE = re.compile(
    r"aia\.lev1_euv_12s\.(?P<ts>\d{4}-\d{2}-\d{2}T\d{6})Z\.(?P<ch>\d+)\.image_lev1\.fits$"
)
RELEASE_LINE = re.compile(
    r"^\./L1/\d{4}/\d{2}/\d{2}/solo_L1_eui-(?P<prod>hrieuv174|fsi174|fsi304)-image_"
    r"(?P<ts>\d{8}T\d{6})\d*_V\d+\.fits\s*$"
)


def parse_eui_obstime(name: str) -> datetime | None:
    m = EUI_OBS_RE.search(name)
    if not m:
        return None
    return datetime.strptime(m["ts"], "%Y%m%dT%H%M%S")


def parse_aia(name: str) -> tuple[datetime, int] | None:
    m = AIA_OBS_RE.search(name)
    if not m:
        return None
    ts = datetime.strptime(m["ts"], "%Y-%m-%dT%H%M%S")
    return ts, int(m["ch"])


# ---------------------------------------------------------------- reuse scan
def scan_local_eui(product: str) -> list[tuple[datetime, Path]]:
    """All on-disk EUI <product> frames anywhere under RAW_ROOT."""
    out = []
    for p in RAW_ROOT.rglob(f"solo_L1_eui-{product}-image_*.fits"):
        ts = parse_eui_obstime(p.name)
        if ts is not None:
            out.append((ts, p))
    return out


def scan_local_aia() -> list[tuple[datetime, int, Path]]:
    out = []
    for p in RAW_ROOT.rglob("aia.lev1_euv_12s.*.image_lev1.fits"):
        parsed = parse_aia(p.name)
        if parsed is not None:
            ts, ch = parsed
            out.append((ts, ch, p))
    return out


# ---------------------------------------------------------------- release index
def index_release(product: str, conj: datetime) -> list[tuple[datetime, str]]:
    """Lines of files_L1.txt for the given product on conj's UTC date."""
    day_prefix = f"./L1/{conj.year:04d}/{conj.month:02d}/{conj.day:02d}/"
    out = []
    with FILE_LIST.open() as fh:
        for line in fh:
            if not line.startswith(day_prefix):
                continue
            m = RELEASE_LINE.match(line)
            if not m or m["prod"] != product:
                continue
            try:
                ts = datetime.strptime(m["ts"], "%Y%m%dT%H%M%S")
            except ValueError:
                continue
            out.append((ts, line.strip().lstrip("./")))
    out.sort(key=lambda r: r[0])
    return out


# ---------------------------------------------------------------- helpers
def link_or_copy(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        return f"exists {dst}"
    try:
        os.link(src, dst)
        return f"link"
    except OSError:
        shutil.copy2(src, dst)
        return f"copy"


def download_eui(rel: str, dst: Path) -> bool:
    dst.parent.mkdir(parents=True, exist_ok=True)
    url = f"{RELEASE_URL}/{rel}"
    print(f"    GET {url}")
    rc = subprocess.run(
        ["wget", "-q", "--tries=3", "--timeout=60", "-O", str(dst), url]
    ).returncode
    if rc != 0 and dst.exists() and dst.stat().st_size == 0:
        dst.unlink()
    return rc == 0 and dst.exists() and dst.stat().st_size > 0


def fetch_aia_all_channels(t_aia: datetime, dst_dir: Path) -> list[Path]:
    """Fetch one nearest frame per EUV channel for ALL 7 channels in one go.

    Walks [t_aia, t_aia+WINDOW] in 12 s windows. `aia.lev1_euv_12s` holds
    all 7 channels at 12 s cadence so a 12 s window yields exactly one frame
    per channel (7 records). The first window that returns >=7 records is
    fetched; any extras (rare; happens when JSOC straddles boundary) are
    left on disk and the caller picks the earliest per channel.
    """
    deadline = t_aia + WINDOW
    step = timedelta(seconds=12)
    t = t_aia
    while t < deadline:
        t_end = min(t + step, deadline)
        try:
            q = Fido.search(
                a.Time(Time(t), Time(t_end)),
                a.jsoc.Series("aia.lev1_euv_12s"),
                a.jsoc.Notify(JSOC_EMAIL),
            )
        except Exception as e:
            print(f"    aia search err t={t.isoformat()}: {e}")
            t = t_end
            continue
        n = len(q[0]) if len(q) else 0
        if n >= 7:
            print(f"    JSOC: {n} records in [{t.isoformat()}, {t_end.isoformat()}]")
            try:
                files = Fido.fetch(q, path=str(dst_dir / "{file}"),
                                   progress=False, overwrite=False)
            except Exception as e:
                print(f"    aia fetch err: {e}")
                t = t_end
                continue
            return [Path(f) for f in files if "image_lev1" in f]
        t = t_end
    return []


# ---------------------------------------------------------------- per-conj
def process_conjunction(tag: str, conj: datetime, want_hri: bool,
                        light_time_s: float,
                        eui_index: dict[str, list[tuple[datetime, Path]]],
                        aia_index: list[tuple[datetime, int, Path]],
                        log: list[dict]) -> None:
    t_aia = conj + timedelta(seconds=light_time_s)
    print(f"=== {tag}  conj {conj.isoformat()}  "
          f"AIA target {t_aia.isoformat()}  (+{light_time_s:.1f}s light)  +{WINDOW} ===")
    out_aia = OUT_ROOT / tag / "AIA"
    out_fsi = OUT_ROOT / tag / "FSI"
    out_hri = OUT_ROOT / tag / "HRI"

    # ------ AIA: nearest 1 frame per channel in [t_aia, t_aia+15min] ----
    # Local reuse: pick earliest per channel from any RAW location.
    chosen: dict[int, tuple[datetime, Path, str]] = {}
    for ts, ch, p in aia_index:
        if ch not in AIA_WAVES or not (t_aia <= ts <= t_aia + WINDOW):
            continue
        prev = chosen.get(ch)
        if prev is None or ts < prev[0]:
            chosen[ch] = (ts, p, "reuse")
    # Missing channels: one JSOC search for all 7, then filter
    missing = [w for w in AIA_WAVES if w not in chosen]
    if missing:
        print(f"  AIA missing {missing} -> 1 JSOC search for all 7 channels")
        fetched = fetch_aia_all_channels(t_aia, out_aia)
        for f in fetched:
            parsed = parse_aia(f.name)
            if parsed is None:
                continue
            ts, ch = parsed
            if ch not in AIA_WAVES or not (t_aia <= ts <= t_aia + WINDOW):
                continue
            prev = chosen.get(ch)
            if prev is None or ts < prev[0]:
                chosen[ch] = (ts, f, "fetch")
            aia_index.append((ts, ch, f))

    for wave in AIA_WAVES:
        if wave not in chosen:
            print(f"  AIA {wave:>3d}  none in window")
            log.append({"tag": tag, "instrument": f"AIA{wave:03d}",
                        "obstime": "", "delta_s": "",
                        "source": "miss", "src_path": "",
                        "dst_path": ""})
            continue
        ts, src, how = chosen[wave]
        dt = (ts - t_aia).total_seconds()
        if how == "reuse":
            dst = out_aia / src.name
            verb = link_or_copy(src, dst)
            print(f"  AIA {wave:>3d}  {verb:6s}  Δt=+{dt:6.1f}s (from t_aia)  {src.name}")
            log.append({"tag": tag, "instrument": f"AIA{wave:03d}",
                        "obstime": ts.isoformat(), "delta_s": f"{dt:.1f}",
                        "source": verb, "src_path": str(src),
                        "dst_path": str(dst)})
        else:
            print(f"  AIA {wave:>3d}  fetch   Δt=+{dt:6.1f}s (from t_aia)  {src.name}")
            log.append({"tag": tag, "instrument": f"AIA{wave:03d}",
                        "obstime": ts.isoformat(), "delta_s": f"{dt:.1f}",
                        "source": "fetch", "src_path": "JSOC",
                        "dst_path": str(src)})

    # ------ FSI 174 / 304 ------------------------------------------------
    for prod in ("fsi174", "fsi304"):
        cands = [(ts, p) for ts, p in eui_index[prod]
                 if conj <= ts <= conj + WINDOW]
        cands.sort(key=lambda r: r[0])
        if cands:
            ts, src = cands[0]
            dst = out_fsi / src.name
            verb = link_or_copy(src, dst)
            dt   = (ts - conj).total_seconds()
            print(f"  {prod}  {verb:6s}  Δt=+{dt:6.1f}s  {src.name}")
            log.append({"tag": tag, "instrument": prod,
                        "obstime": ts.isoformat(), "delta_s": f"{dt:.1f}",
                        "source": verb, "src_path": str(src),
                        "dst_path": str(dst)})
            continue
        # fallback: SIDC release
        rels = [(ts, rel) for ts, rel in index_release(prod, conj)
                if conj <= ts <= conj + WINDOW]
        if rels:
            ts, rel = rels[0]
            dst = out_fsi / Path(rel).name
            if download_eui(rel, dst):
                dt = (ts - conj).total_seconds()
                print(f"  {prod}  fetch   Δt=+{dt:6.1f}s  {dst.name}")
                log.append({"tag": tag, "instrument": prod,
                            "obstime": ts.isoformat(), "delta_s": f"{dt:.1f}",
                            "source": "fetch", "src_path": rel,
                            "dst_path": str(dst)})
                # also pin to RAW/<prod>/ for future reuse
                pin = RAW_ROOT / prod / dst.name
                if not pin.exists():
                    try: os.link(dst, pin)
                    except OSError: shutil.copy2(dst, pin)
                eui_index[prod].append((ts, pin if pin.exists() else dst))
                continue
        print(f"  {prod}  none in window")
        log.append({"tag": tag, "instrument": prod,
                    "obstime": "", "delta_s": "",
                    "source": "miss", "src_path": "",
                    "dst_path": ""})

    # ------ HRI 174 ------------------------------------------------------
    if not want_hri:
        print(f"  HRI174  skipped (user-decided: no HRI near conj on this day)")
        log.append({"tag": tag, "instrument": "hrieuv174",
                    "obstime": "", "delta_s": "",
                    "source": "skip_per_plan", "src_path": "",
                    "dst_path": ""})
        return

    cands = [(ts, p) for ts, p in eui_index["hrieuv174"]
             if conj <= ts <= conj + WINDOW]
    cands.sort(key=lambda r: r[0])
    if cands:
        ts, src = cands[0]
        dst = out_hri / src.name
        verb = link_or_copy(src, dst)
        dt   = (ts - conj).total_seconds()
        print(f"  HRI174  {verb:6s}  Δt=+{dt:6.1f}s  {src.name}")
        log.append({"tag": tag, "instrument": "hrieuv174",
                    "obstime": ts.isoformat(), "delta_s": f"{dt:.1f}",
                    "source": verb, "src_path": str(src),
                    "dst_path": str(dst)})
        return
    # SIDC fallback
    rels = [(ts, rel) for ts, rel in index_release("hrieuv174", conj)
            if conj <= ts <= conj + WINDOW]
    if rels:
        ts, rel = rels[0]
        dst = out_hri / Path(rel).name
        if download_eui(rel, dst):
            dt = (ts - conj).total_seconds()
            print(f"  HRI174  fetch   Δt=+{dt:6.1f}s  {dst.name}")
            log.append({"tag": tag, "instrument": "hrieuv174",
                        "obstime": ts.isoformat(), "delta_s": f"{dt:.1f}",
                        "source": "fetch", "src_path": rel,
                        "dst_path": str(dst)})
            pin = RAW_ROOT / "hrieuv174" / ts.strftime("%Y%m%dT%H%M") / dst.name
            if not pin.exists():
                pin.parent.mkdir(parents=True, exist_ok=True)
                try: os.link(dst, pin)
                except OSError: shutil.copy2(dst, pin)
            eui_index["hrieuv174"].append((ts, pin if pin.exists() else dst))
            return
    print(f"  HRI174  none in window")
    log.append({"tag": tag, "instrument": "hrieuv174",
                "obstime": "", "delta_s": "",
                "source": "miss", "src_path": "",
                "dst_path": ""})


# ---------------------------------------------------------------- main
def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    print("indexing local EUI ...")
    eui_index = {
        "hrieuv174": scan_local_eui("hrieuv174"),
        "fsi174":    scan_local_eui("fsi174"),
        "fsi304":    scan_local_eui("fsi304"),
    }
    print(f"  hrieuv174={len(eui_index['hrieuv174'])} "
          f"fsi174={len(eui_index['fsi174'])} "
          f"fsi304={len(eui_index['fsi304'])}")
    print("indexing local AIA ...")
    aia_index = scan_local_aia()
    print(f"  AIA={len(aia_index)}")

    log: list[dict] = []
    for tag, conj, want_hri, light_s in CONJUNCTIONS:
        process_conjunction(tag, conj, want_hri, light_s,
                            eui_index, aia_index, log)

    fields = ["tag", "instrument", "obstime", "delta_s",
              "source", "src_path", "dst_path"]
    with INV_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(log)
    print(f"\nwrote {INV_CSV}  ({len(log)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
