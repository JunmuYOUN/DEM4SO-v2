"""
Compute Earth <-> Solar Orbiter light travel time at the listed Conj_front times.
Uses the same toolset as Code_V2/Check_image/inst_location_plot_V2_250904.ipynb
(sunpy.coordinates.get_horizons_coord + get_body_heliographic_stonyhurst).
"""
from __future__ import annotations

from datetime import datetime

import astropy.units as u
from astropy.constants import c
from astropy.time import Time
from sunpy.coordinates import (
    get_body_heliographic_stonyhurst,
    get_horizons_coord,
)

TIMES = [
    "2022-03-07T08:30",
    "2023-03-28T21:30",
    "2024-03-20T08:40",
    "2025-03-13T20:30",
    "2025-10-07T17:00",
]


def light_time(t_iso: str) -> tuple[float, float, float]:
    t = Time(t_iso)
    # Both returned in HeliographicStonyhurst -> .cartesian shares the same
    # Sun-centred frame, so the simple vector difference is the Earth-SolO
    # baseline.
    solo  = get_horizons_coord("Solar Orbiter",
                               {"start": t, "stop": t + 1 * u.min, "step": "1min"})[0]
    earth = get_body_heliographic_stonyhurst("Earth", t)
    delta = solo.cartesian - earth.cartesian
    d_km  = delta.norm().to(u.km).value
    d_au  = (d_km * u.km).to(u.AU).value
    ltime = (d_km * u.km / c).to(u.s).value
    return d_au, d_km, ltime


def main() -> None:
    print(f"{'time (UTC)':<22s}  {'distance [AU]':>14s}  {'distance [km]':>16s}  "
          f"{'light time [s]':>15s}  {'light time [m:s]':>17s}")
    print("-" * 92)
    for t_iso in TIMES:
        d_au, d_km, lts = light_time(t_iso)
        mm, ss = divmod(lts, 60)
        print(f"{t_iso:<22s}  {d_au:14.6f}  {d_km:16.0f}  "
              f"{lts:15.3f}  {int(mm):>3d}:{ss:06.3f}")


if __name__ == "__main__":
    main()
