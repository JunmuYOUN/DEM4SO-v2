"""
Apply the Shestov+2025 in-flight cross-calibration factor k = 1.4 to the
HRI 174 temperature response and save the result as a separate .npy.

Background (see Claude/related-paper/report-Shestov2025.md):
  Shestov+2025 jointly invert a 7-channel DEM with AIA 6 + HRI 174 over three
  conjunction dates (2020-05-30, 2022-03-07, 2023-03-29) and find that the
  observed HRI signal is consistently ~40% larger than the AIA-based DEM
  forward-model predicts. The single-value k recommended for default analysis
  is k = 1.4 (k spans 1.4-1.6 across dates and metrics).

  Application: multiply the CHIANTI-derived G_HRI(T) (already in
  hri174_response.npy) by k = 1.4 so that the response matrix used in
  demregpy.dn2dem matches the in-flight calibration.

  Carries a ~+/- 0.2 (~14%) calibration uncertainty: see report Section 5.

Outputs (next to this script, alongside the uncorrected file):
  hri174_response_k1p4.npy   shape=(81,), float64
  hri174_response_k1p4.json  metadata (k value, source, source file checksum)
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import numpy as np

K_FACTOR = 1.4

OUT_DIR  = Path(__file__).resolve().parent
SRC_NPY  = OUT_DIR / "hri174_response.npy"
LOGT_NPY = OUT_DIR / "hri174_logt.npy"
DST_NPY  = OUT_DIR / "hri174_response_k1p4.npy"
DST_META = OUT_DIR / "hri174_response_k1p4.json"


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> None:
    src = np.load(SRC_NPY)
    dst = src * K_FACTOR
    np.save(DST_NPY, dst)

    meta = {
        "k_factor":      K_FACTOR,
        "source":        SRC_NPY.name,
        "source_sha256": sha256(SRC_NPY),
        "shape":         list(dst.shape),
        "dtype":         str(dst.dtype),
        "logt_npy":      LOGT_NPY.name,
        "src_min":       float(src.min()),
        "src_max":       float(src.max()),
        "dst_min":       float(dst.min()),
        "dst_max":       float(dst.max()),
        "reference":     "Shestov et al. 2025, In-flight cross-calibration of "
                         "HRI_EUV/EUI and AIA/SDO; report-Shestov2025.md",
        "cal_uncertainty": "+/- ~14% (k spans 1.4-1.6 across 3 conjunctions)",
        "written":       datetime.utcnow().isoformat() + "Z",
    }
    DST_META.write_text(json.dumps(meta, indent=2) + "\n")

    print(f"k = {K_FACTOR}")
    print(f"src  {SRC_NPY.name}  shape={src.shape}  min={src.min():.3e}  max={src.max():.3e}")
    print(f"dst  {DST_NPY.name}  shape={dst.shape}  min={dst.min():.3e}  max={dst.max():.3e}")
    print(f"meta {DST_META.name}")


if __name__ == "__main__":
    main()
