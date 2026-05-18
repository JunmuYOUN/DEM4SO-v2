"""
Build Claude/inventory/data_distribution.md summarizing what HRI 174 and AIA
data we have on disk for the four target conjunctions.

Reads:
  * Claude/inventory/hri174_download_list.csv   (HRI inventory)
  * /userhome/youn_j/Dataset/DEM4SO-v2/hrieuv174/...   (HRI files on disk)
  * /userhome/youn_j/Dataset/DEM4SO-v2/AIA/...          (AIA files on disk)
  * Claude/inventory/download_aia_pairs.log     (per-fetch status)
"""
from __future__ import annotations

import csv
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

ROOT     = Path("/userhome/youn_j/Dataset/DEM4SO-v2")
INV_CSV  = Path("/userhome/youn_j/Code_V3/Claude/inventory/hri174_download_list.csv")
PAIR_LOG = Path("/userhome/youn_j/Code_V3/Claude/inventory/download_aia_pairs.log")
OUT_MD   = Path("/userhome/youn_j/Code_V3/Claude/inventory/data_distribution.md")

CONJ_TIMES = {
    "2022-03-07T0833": datetime(2022, 3,  7,  8, 33),
    "2023-03-28T2130": datetime(2023, 3, 28, 21, 30),
    "2024-03-20T0840": datetime(2024, 3, 20,  8, 40),
    "2025-10-07T1700": datetime(2025, 10, 7, 17,  0),
}
WAVES = [94, 131, 171, 193, 211, 335]


def human_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def main() -> None:
    # 1) read HRI inventory
    rows = list(csv.DictReader(INV_CSV.open()))
    per_conj_dates: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        per_conj_dates[r["conj"]].append(r)

    # 2) HRI on-disk file counts per (year, month, day)
    hri_disk: dict[tuple[str, str, str], list[Path]] = defaultdict(list)
    for p in (ROOT / "hrieuv174").rglob("solo_L1_eui-hrieuv174-image_*.fits"):
        y, m, d = p.parts[-4], p.parts[-3], p.parts[-2]
        hri_disk[(y, m, d)].append(p)

    # 3) AIA on-disk per (year, month, day, wave): only image_lev1 (drop spikes)
    aia_disk: dict[tuple[str, str, str, int], list[Path]] = defaultdict(list)
    aia_size_total = 0
    aia_spike_count = 0
    for p in (ROOT / "AIA").rglob("*.image_lev1.fits"):
        try:
            y, m, d, ch_str = p.parts[-5], p.parts[-4], p.parts[-3], p.parts[-2]
            ch = int(ch_str)
        except (ValueError, IndexError):
            continue
        aia_disk[(y, m, d, ch)].append(p)
        aia_size_total += p.stat().st_size
    for p in (ROOT / "AIA").rglob("*.spikes.fits"):
        aia_spike_count += 1
        aia_size_total += p.stat().st_size

    hri_size_total = sum(p.stat().st_size for v in hri_disk.values() for p in v)

    # 4) "none" records from the log (queries where JSOC returned no row)
    none_pat = re.compile(r"^none\s+wave=(\d+)\s+t=(\S+)")
    nones: list[tuple[int, str]] = []
    if PAIR_LOG.exists():
        for line in PAIR_LOG.read_text().splitlines():
            m = none_pat.match(line)
            if m:
                nones.append((int(m.group(1)), m.group(2)))

    # ============== render markdown =====================================
    lines: list[str] = []
    lines.append("# DEM4SO-v2 — Data Distribution")
    lines.append("")
    lines.append(f"Last refreshed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')} ")
    lines.append("Root: `/userhome/youn_j/Dataset/DEM4SO-v2/`")
    lines.append("")
    lines.append("## 1. 전체 요약")
    lines.append("")
    lines.append("| 자료 | 파일 수 | 디스크 사용량 |")
    lines.append("|---|---:|---:|")
    n_hri = sum(len(v) for v in hri_disk.values())
    n_aia = sum(len(v) for v in aia_disk.values())
    lines.append(f"| HRI 174 L1 (image)               | {n_hri:>4d} | {human_bytes(hri_size_total)} |")
    lines.append(f"| AIA lev1 (image_lev1.fits)       | {n_aia:>4d} | (포함) |")
    lines.append(f"| AIA spikes (spikes.fits, 부산물) | {aia_spike_count:>4d} | (포함) |")
    lines.append(f"| **AIA 합계**                     | **{n_aia + aia_spike_count}** | **{human_bytes(aia_size_total)}** |")
    lines.append("")
    lines.append("> AIA 한 query (±6 s, 12 s cadence) 당 image+spikes 한 쌍이 정상이지만, ")
    lines.append("> ±6 s 안에 두 frame 이 잡히는 경우가 있어 결과 갯수가 query 수 (120) 보다 큼.")
    lines.append("> 분석에선 image_lev1.fits 중 HRI 시각에 가장 가까운 1장만 쓰면 된다.")
    lines.append("")

    lines.append("## 2. Conjunction × 날짜별 HRI 174 분포")
    lines.append("")
    lines.append("HRI 175 L1 (image) — conjunction 시각 ±7 일 안에서 *날짜당 첫 frame 1개* 만 다운로드. ")
    lines.append("AIA pair 컬럼은 그 시각에 매칭된 AIA 6채널 중 실제로 받은 채널 수.")
    lines.append("")
    lines.append("| Conjunction (UTC) | 날짜 (UTC) | HRI obstime | HRI file | AIA pair (ch / 6) |")
    lines.append("|---|---|---|---|---:|")
    for conj_tag, conj_dt in CONJ_TIMES.items():
        records = sorted(per_conj_dates.get(conj_tag, []), key=lambda r: r["time_utc"])
        if not records:
            lines.append(f"| {conj_tag} | — | — | (없음) | 0 / 6 |")
            continue
        for r in records:
            y, m, d = r["year"], r["month"], r["day"]
            ts      = r["time_utc"]
            hri_ok  = (y, m, d) in hri_disk and bool(hri_disk[(y, m, d)])
            hri_mark = "✓" if hri_ok else "✗"
            pair_n  = sum(1 for ch in WAVES if aia_disk.get((y, m, d, ch)))
            lines.append(f"| {conj_tag} | {y}-{m}-{d} | {ts[11:]} | {hri_mark} | {pair_n} / 6 |")
        lines.append("|  | **총** | | "
                     f"{sum(1 for r in records if (r['year'],r['month'],r['day']) in hri_disk)} files | "
                     f"— |")
    lines.append("")

    lines.append("## 3. 채널별 AIA 파일 수 (date × wave)")
    lines.append("")
    header = "| 날짜 (UTC) | " + " | ".join(f"{w:03d}" for w in WAVES) + " | 합 |"
    lines.append(header)
    lines.append("|" + "---|" * (len(WAVES) + 2))
    grand = {w: 0 for w in WAVES}
    dates = sorted({(r["year"], r["month"], r["day"]) for r in rows})
    for (y, m, d) in dates:
        row_counts = [len(aia_disk.get((y, m, d, w), [])) for w in WAVES]
        for w, n in zip(WAVES, row_counts):
            grand[w] += n
        lines.append(f"| {y}-{m}-{d} | " + " | ".join(f"{n}" for n in row_counts) +
                     f" | {sum(row_counts)} |")
    lines.append("| **합** | " + " | ".join(f"**{grand[w]}**" for w in WAVES) +
                 f" | **{sum(grand.values())}** |")
    lines.append("")

    lines.append("## 4. 결측 (JSOC `none`)")
    lines.append("")
    if nones:
        lines.append("`download_aia_pairs.log` 에서 JSOC 가 해당 시각/채널에 대해 record 를 반환하지 않은 케이스 — ")
        lines.append("주로 12 s cadence series 의 quality flag 누락 또는 데이터 갭으로 추정.")
        lines.append("")
        lines.append("| Wavelength | HRI time (UTC) |")
        lines.append("|---:|---|")
        for w, t in sorted(nones):
            lines.append(f"| {w} | {t} |")
    else:
        lines.append("없음.")
    lines.append("")

    lines.append("## 5. 디렉토리 트리 (요약)")
    lines.append("")
    lines.append("```")
    lines.append("/userhome/youn_j/Dataset/DEM4SO-v2/")
    lines.append("├── hrieuv174/<YYYY>/<MM>/<DD>/solo_L1_eui-hrieuv174-image_*.fits")
    lines.append("└── AIA/<YYYY>/<MM>/<DD>/<wave3>/aia.lev1_euv_12s.*.image_lev1.fits")
    lines.append("                                          (+ same name .spikes.fits)")
    lines.append("```")
    lines.append("")
    lines.append("- HRI L1 파일은 ~4 MB / frame, AIA lev1 (image+spikes) 한 쌍 ~10 MB.")
    lines.append("- 분석 입력은 `image_lev1.fits` 만 사용; spikes 는 calibration 만 필요시 참고.")
    lines.append("")
    lines.append("## 6. 출처")
    lines.append("")
    lines.append("- HRI 174 L1: SIDC EUI release 7.0 (`https://www.sidc.be/EUI/data/releases/202510_release_7.0`)")
    lines.append("  2025-10-07 윈도우는 release 7.0 + SOAR 모두 2025-09-30 21:59 UTC 한 시점만 보유.")
    lines.append("- AIA lev1: JSOC series `aia.lev1_euv_12s`, JSOC notify email `startime98@catholic.ac.kr`,")
    lines.append("  HRI obstime ± 6 s 윈도우에서 최근접 frame.")
    lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_MD}  ({OUT_MD.stat().st_size} B)")


if __name__ == "__main__":
    main()
