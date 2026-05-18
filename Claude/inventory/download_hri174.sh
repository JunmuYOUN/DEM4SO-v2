#!/usr/bin/env bash
# Download HRI 174 L1 files listed in hri174_download_list.csv.
#
# Preserves the SIDC tree under DEST_ROOT and skips files that already exist
# (wget -nc). Runs PARALLEL streams.
#
# Usage:  bash download_hri174.sh  [PARALLEL]   (default PARALLEL=4)

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CSV="${SCRIPT_DIR}/hri174_download_list.csv"
DEST_ROOT="/userhome/youn_j/Dataset/DEM4SO-v2/hrieuv174"
PARALLEL="${1:-4}"
LOG="${SCRIPT_DIR}/download_hri174.log"

if [[ ! -f "$CSV" ]]; then
    echo "missing $CSV (run build_hri_inventory.py first)" >&2
    exit 1
fi

mkdir -p "$DEST_ROOT"
: > "$LOG"

# CSV columns: conj,time_utc,year,month,day,relpath,url
tail -n +2 "$CSV" | tr -d '\r' | awk -F, '{print $3","$4","$5","$6","$7}' \
| xargs -P "$PARALLEL" -I {} bash -c '
    IFS=, read -r year month day rel url <<<"{}"
    fname="$(basename "$rel")"
    out_dir="'"$DEST_ROOT"'/${year}/${month}/${day}"
    out_file="${out_dir}/${fname}"
    mkdir -p "$out_dir"
    if [[ -s "$out_file" ]]; then
        echo "skip  $out_file" >> "'"$LOG"'"
        exit 0
    fi
    if wget -q --tries=3 --timeout=60 -O "$out_file.part" "$url"; then
        mv "$out_file.part" "$out_file"
        echo "ok    $out_file ($(stat -c%s "$out_file") B)" >> "'"$LOG"'"
    else
        rm -f "$out_file.part"
        echo "FAIL  $url" >> "'"$LOG"'"
    fi
'

ok_n=$(grep -c '^ok '   "$LOG" || true)
sk_n=$(grep -c '^skip ' "$LOG" || true)
fl_n=$(grep -c '^FAIL ' "$LOG" || true)
echo "done. ok=$ok_n skip=$sk_n fail=$fl_n  (log: $LOG)"
