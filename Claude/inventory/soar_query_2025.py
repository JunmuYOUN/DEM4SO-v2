"""
Query SOAR for HRI EUV 174 L1 within +/-1 week of 2025-10-07T17:00 UTC.

Writes results next to this script and (if any rows are returned) appends a
matching block to hri174_download_list.csv plus emits soar_download_list.csv
that the bash downloader can also consume.
"""
from __future__ import annotations

from pathlib import Path

from astropy.time import Time
from sunpy.net import Fido, attrs as a
import sunpy_soar  # noqa: F401  (registers SOAR client)

CENTER  = Time("2025-10-07T17:00")
WINDOW_DAYS = 7
OUT_DIR = Path(__file__).resolve().parent

def main() -> None:
    t_start = CENTER - WINDOW_DAYS * 1.0   # days
    t_stop  = CENTER + WINDOW_DAYS * 1.0
    # Note: in sunpy_soar, the SOOP/Instrument attributes are stored under a.soar
    # so we use a.Instrument and a.Level for cross-archive compatibility.
    print(f"querying SOAR: hrieuv174 L1, {t_start.iso} .. {t_stop.iso}")
    results = Fido.search(
        a.Time(t_start, t_stop),
        a.Instrument("EUI"),
        a.Level(1),
        a.soar.Product("eui-hrieuv174-image"),
    )
    print(results)

    table = results[0] if len(results) else None
    out_txt = OUT_DIR / "soar_query_2025-10-07.txt"
    out_csv = OUT_DIR / "soar_query_2025-10-07.csv"
    with out_txt.open("w") as fh:
        fh.write(str(results))
    if table is not None and len(table) > 0:
        # Try to coerce to a tidy CSV with the most useful columns
        cols = [c for c in ("Start Time", "End Time", "Instrument", "Level",
                            "Data product", "Filesize", "Data item ID") if c in table.colnames]
        if cols:
            table[cols].write(out_csv, format="csv", overwrite=True)
        else:
            table.write(out_csv, format="csv", overwrite=True)
        print(f"wrote {len(table)} rows -> {out_csv}")
    else:
        out_csv.write_text("# no rows returned\n")
        print("no rows returned")


if __name__ == "__main__":
    main()
