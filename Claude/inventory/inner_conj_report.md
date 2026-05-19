# Inner-conjunction dataset — build result

생성: `/userhome/youn_j/Dataset_V2/RAW/inner_conj/<TAG>/{AIA,FSI,HRI}/`
스크립트: `Code_V3/Claude/inventory/build_inner_conj.py`
인벤토리: `/userhome/youn_j/Dataset_V2/RAW/inner_conj/inner_conj_inventory.csv` (50 rows)

## 1. 윈도우 정의

- **window**: `[conj, conj + 15 min]` (forward only, +15 min)
- **AIA 시각 보정**: `t_AIA = conj + Δt_light` — 내합 (Sun-SolO-Earth 일직선)에서 같은 태양 사건을 보려면 AIA 는 SolO 보다 `Δt_light` 만큼 *뒤* 에 봐야 함. `Δt_light` = `Earth↔SolO` 거리 / c.
- **HRI/FSI**: SolO 우주선 시각 그대로 `t_solo = conj`.

| Tag | conj (SolO frame UTC) | Δt_light [s] | t_AIA (Earth UTC) |
|---|---|---:|---|
| 20220307T0830 | 2022-03-07 08:30:00 | 247.84 | 2022-03-07 08:34:07.84 |
| 20230328T2130 | 2023-03-28 21:30:00 | 297.72 | 2023-03-28 21:34:57.72 |
| 20240320T0840 | 2024-03-20 08:40:00 | 282.74 | 2024-03-20 08:44:42.74 |
| 20250313T2030 | 2025-03-13 20:30:00 | 267.18 | 2025-03-13 20:34:27.18 |
| 20251007T1700 | 2025-10-07 17:00:00 | 250.05 | 2025-10-07 17:04:10.05 |

## 2. 다운로드 결과 (선택된 1 frame, Δt 는 각 instrument 의 target 시각 기준)

### 2.1 AIA 7ch (Δt = obstime − t_AIA, 초)

| Tag | 94 | 131 | 171 | 193 | 211 | 304 | 335 | source |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 20220307T0830 | +5.2 | +0.2 | +2.2 | +10.2 | +3.2 | +11.2 | +6.2 | fetch |
| 20230328T2130 | +3.3 | +10.3 | +12.3 | +8.3 | +1.3 | +9.3 | +4.3 | fetch |
| 20240320T0840 | +6.3 | +1.3 | +3.3 | +11.3 | +4.3 | +0.3 | +7.3 | fetch |
| 20250313T2030 | +33.8 | +40.8 | +42.8 | +38.8 | +43.8 | +39.8 | +34.8 | link (reused) |
| 20251007T1700 | +3.0 | +9.9 | +11.9 | +8.0 | +0.9 | +8.9 | +4.0 | fetch |

### 2.2 FSI 174 + 304, HRI 174 (Δt = obstime − conj, 초)

| Tag | FSI 174 | FSI 304 | HRI 174 | 비고 |
|---|---:|---:|---:|---|
| 20220307T0830 | +225.0 | +195.0 | +5.0 | HRI hard-linked from existing RAW/hrieuv174/20220307T0830/ |
| 20230328T2130 | +55.0 | +20.0 | — | HRI 없음: release 7.0 에 [21:30, 21:45] 안 frame 0 (그 날 block 은 20:30-21:29 로 종료) |
| 20240320T0840 | +55.0 | +20.0 | — | HRI skip (사용자 결정; 그 날 HRI 블록은 17:23 뿐) |
| 20250313T2030 | +55.0 | +20.0 | — | HRI 없음: 2025-03-13 release 7.0 의 HRI block 은 22:20–23:50 |
| 20251007T1700 | — | — | — | FSI/HRI 모두 없음: 2025-10-07 전체에 FSI 174/304 0건, HRI skip |

## 3. 파일 수

| Tag | AIA dir (image_lev1) | AIA dir (총 fits) | FSI | HRI |
|---|---:|---:|---:|---:|
| 20220307T0830 | 14 *(7 channel × 2 frame)* | 28 | 2 | 1 |
| 20230328T2130 | 14 | 28 | 2 | 0 |
| 20240320T0840 | 14 | 28 | 2 | 0 |
| 20250313T2030 | 7 *(1 channel × 1 frame, reused)* | 7 | 2 | 0 |
| 20251007T1700 | 14 | 28 | 0 | 0 |

> JSOC fetch 시 AIA 의 12 s 검색창이 채널별 T_REC 의 12 s cadence 경계와 겹치면서
> 채널당 2 frames 가 함께 들어왔다 (총 14 image_lev1 + 14 spikes = 28 fits). 채택된
> 1개만 inventory CSV 의 `dst_path` 에 기록돼 있고, 분석에는 그 1개만 쓰면 된다.
> 깔끔하게 1개씩만 두고 싶으면 cleanup 스크립트로 extras 만 제거 가능 (사용자 허락 필요).

## 4. 다음에 보완 권장

1. 빈 슬롯 채우기
   - 2023-03-28 HRI, 2025-03-13 HRI, 2025-10-07 FSI 는 release 7.0 자체에 없음.
     SOAR 에 추후 release 가 올라오면 같은 스크립트 재실행으로 빈 슬롯만 채워짐.
2. AIA extras 정리 (옵션)
   - 7 채널 × 1 frame 만 남기고 extras 7+14 = 21 files/tag 삭제. 4 tag 합쳐 84 files.
3. 같은 conjunction 의 다른 시점 (예: 본 분석은 conj+0 ~ conj+15min 만 다룸) 필요하면
   `WINDOW` 만 늘려 재실행.

## 5. 재현

```bash
ssh youn_j@163.180.171.99 \
  /userhome/youn_j/anaconda3/envs/younjm/bin/python \
  /userhome/youn_j/Code_V3/Claude/inventory/build_inner_conj.py
```

빈 디렉토리는 만들지 않으며, inventory CSV 가 곧 source-of-truth.
