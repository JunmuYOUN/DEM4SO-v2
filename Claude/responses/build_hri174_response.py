"""
Build HRI 174 temperature-response array from the CHIANTI synthetic G(T,n) table.

Source FITS  : /userhome/youn_j/DEM/HRI/gof_hri_174_sun_coronal_2021_chianti.abund_chianti.ioneq_synthetic.fits
Header notes : NAXIS=(81, 11), Values = (NH/Ne)*G(Ne,Te)*Ne^2/(4*pi),
               81 logT samples over T = 1e4..1e8 K, 11 log10(Ne) samples over 1e8..1e18 cm^-3,
               UNITS = [DN.m^-1.s^-1].
Recipe (from /userhome/youn_j/DEM/HRI/Temp_Resp_231222.ipynb):
    data174_HRI = fits.open(fp)[0].data        # shape (11, 81)
    resp = data174_HRI[1] * 1e-8               # density-index 1, unit -> [DN cm^5 s^-1 px^-1]
    xarr = np.linspace(4, 8, 81)               # logT axis (matches existing tresp_logt)

Output       : <repo>/Claude/responses/hri174_response.npy   shape=(81,), float64
               <repo>/Claude/responses/hri174_logt.npy       shape=(81,), float64
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from astropy.io import fits

FITS_PATH = Path(
    "/userhome/youn_j/DEM/HRI/"
    "gof_hri_174_sun_coronal_2021_chianti.abund_chianti.ioneq_synthetic.fits"
)
OUT_DIR  = Path(__file__).resolve().parent
DENSITY_INDEX = 1   # row in the (11, 81) array, matching prior usage
UNIT_FACTOR   = 1e-8


def main() -> None:
    with fits.open(FITS_PATH) as hdul:
        data = np.asarray(hdul[0].data, dtype=np.float64)   # (11, 81)
        if data.shape != (11, 81):
            raise RuntimeError(f"unexpected FITS shape {data.shape}, expected (11, 81)")

    resp = data[DENSITY_INDEX] * UNIT_FACTOR                # (81,)
    logt = np.linspace(4.0, 8.0, 81)                        # (81,)

    out_resp = OUT_DIR / "hri174_response.npy"
    out_logt = OUT_DIR / "hri174_logt.npy"
    np.save(out_resp, resp)
    np.save(out_logt, logt)

    print(f"saved {out_resp}  shape={resp.shape}  min={resp.min():.3e}  max={resp.max():.3e}")
    print(f"saved {out_logt}  shape={logt.shape}  range=[{logt[0]}, {logt[-1]}]")


if __name__ == "__main__":
    main()
