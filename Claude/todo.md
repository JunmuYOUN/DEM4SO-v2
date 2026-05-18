# DEM4SO-v2 Research Plan

> Question: *AIA(또는 AIA-like-EUI) 6채널 DEM에 HRI 174를 한 채널 추가했을 때
> 소규모 구조 (campfire, nanoflare 등) 위치에서 DEM 결과가 얼마나 달라지며,
> 달라진다면 그 원인은 무엇인가?*

**역할 분담 (2026-05-18 사용자 추가 지침)**

* **AIA / AIA-like-EUI** — *background*. 큰 FOV로 corona의 광역 온도 구조
  (active region 전체, network, supergranular cell 등) 를 받쳐주는 역할.
  HRI 격자에 reproject 되어 7채널 DEM의 "넓은 영역" 컨텍스트를 제공한다.
* **HRI 174** — *fine-scale probe*. 같은 격자에서 ~100 km 분해능으로 campfire
  (수 Mm, 수 분 lifetime), nanoflare 후보 (서브-Mm, 수십 초) 등을 분해한다.
  DEM 결과 평가 ROI는 **이러한 작은 구조 중심**으로 선정한다.

`AIA-like-EUI(174+304→6ch) + HRI174` 합성 7채널 DEM은 **Phase 5**에서 별도 트랙으로
다루며, 우선 **AIA 진본 6ch vs (AIA 6ch + HRI174 = 7ch)** 차이를 정량화한다.

작성 코드는 전부 `/userhome/youn_j/Code_V3/Claude/` 아래에 저장한다.

---

## 0. 기준 자료 / 배경

* 기존 DEM 코드 베이스: `/userhome/youn_j/DEM/DEM_study/DEM_2024_11/`
  특히 `DEM_areaV5_240529_TEST.ipynb` (2026-03 기준 최신 수정).
* DEM solver: `demregpy.dn2dem` (Hannah & Kontar 2012 regularized inversion).
* 기존 응답함수: `/userhome/youn_j/DEM/HRI/Paper/`
  * `resp_concat_AIA.npy` — AIA 6채널 (94/131/171/193/211/335)
  * `resp_concat_EUI_factor0.6.npy` — 합성 EUI 6채널 (94/131/**174**/193/211/335)
  * `resp_concat_FSI_factor0.{5,6,7}_rev1.npy` — FSI 6채널 (Phase 5에서 사용)
  * temperature grid: `tresp_logt = np.linspace(4, 8, 81)`, `T_bins = 10**arange(4,8,0.1)` (40개)
* Reference 논문: Youn et al., *Can we properly determine DEM from Solar Orbiter/EUI/FSI
  with deep learning?* — Phase 5에서 reference로 사용.
* Conjunction 후보 (Conj_front, Solar Orbiter ↔ SDO 정렬):
  * 2022-03-07 08:33  (separation ≈ TBD)
  * 2023-03-28 21:30
  * 2024-03-20 08:40
  * 2025-10-07 17:00  (이 시기 hrieuv174는 SIDC L1 release 7.0 기준 3개만 있음 — 다른 데이터셋 필요)

---

## Phase 1. 환경 정비 & 데이터 인벤토리

목표: 7채널 DEM을 돌릴 수 있는 환경, 데이터, 응답함수가 모두 손에 잡히는 상태를 만든다.

- [ ] **1-1. 패키지 환경 점검**
  * `demregpy`, `aiapy`, `sunpy>=5.x`, `reproject`, `astropy>=6` 버전 확인.
  * 산출물: `Claude/env/check_env.py` — import 후 버전 print.
- [ ] **1-2. 데이터 인벤토리 스크립트**
  * 4 conjunction × ±1 week 윈도우 안의 (a) AIA 6ch, (b) HRI 174, (c) HRI Lyα,
    (d) FSI 174/304 파일을 모아 CSV로 저장.
  * 산출물: `Claude/inventory/inventory_around_conj.py` →
    `Claude/inventory/conj_window_inventory.csv` (excluded from git via .gitignore for .csv? — 일단 추적).
- [ ] **1-3. SO–SDO separation 계산**
  * `sunpy.coordinates.get_horizons_coord` 로 4 conjunction과 추가 후보일자에 대해
    SO–Sun–SDO 각도를 계산하고 표로 정리 (5°/10°/15°/20°/25°/30° 부근 후보 추출).
  * 산출물: `Claude/inventory/separation_angle.py`, `separation_table.csv`.
- [ ] **1-4. 응답함수 시각화**
  * `resp_concat_AIA.npy` 와 EUI 174 (resp_concat_EUI_factor0.6.npy 의 index 2) 를
    같은 logT 축에서 plot — 7채널의 sensitivity 겹침/공백 영역 확인.
  * 산출물: `Claude/responses/plot_response.py`, figure.

질문/결정 포인트:
* HRI174 응답을 합성-EUI factor 0.6 그대로 쓸지, factor 0.5/0.7 sensitivity까지 함께
  실험할지 → Phase 2 일정 영향. 기본은 0.6 으로 fix, 부록 분석에서 sweep.

---

## Phase 2. 7채널 DEM 파이프라인 (AIA 6 + HRI 174)

목표: HRI FOV ROI 한 장면에 대해 AIA-only(6ch) vs AIA+HRI174(7ch) DEM 을 동일 픽셀
격자에서 비교하는 *재현 가능한 함수형* 파이프라인 완성.

- [ ] **2-1. 데이터 로더**
  * `Claude/pipeline/io_loaders.py`
    * `load_aia_set(time, channels)` → `Sequence[sunpy.map.Map]`
      * `aiapy.calibrate.update_pointing` + `register` + `correct_degradation`.
    * `load_hri174(file)` → calibrated `sunpy.map.Map` (L2 권장; L1이면 dark/flat 적용).
- [ ] **2-2. HRI FOV 추출 → AIA reproject**
  * `Claude/pipeline/coregister.py`
    * `crop_hri_fov(hri_map)` → HRI FOV bounding box.
    * `reproject_aia_to_hri(aia_map, hri_map)` → `aia_map.reproject_to(hri_map.wcs)`.
    * **선택**: differential rotation을 HRI obstime 기준으로 AIA에 적용 (Phase 4에서 sweep).
    * 결과 6장의 AIA + 1장의 HRI174 모두 동일한 (ny_HRI, nx_HRI) 픽셀 그리드.
- [ ] **2-3. 노이즈 모델 & 응답행렬 준비**
  * `Claude/pipeline/dem_setup.py`
    * `build_data_edata(maps_7ch)` — 기존 `setting()` 일반화 (npix는 HRI 격자 기준 1).
    * `build_tresp_7ch()` — AIA 6채널 response + HRI174 response 를 (81, 7) 행렬로 stack.
    * 디스크 캐시: `Claude/responses/tresp_AIA6_HRI174.npy`.
- [ ] **2-4. DEM 호출 wrapper**
  * `Claude/pipeline/dem_run.py`
    * `run_dem(data, edata, tresp, kind={"AIA6","AIA6+HRI174"})` →
      `dem, edem, elogt, chisq, dn_reg, mlogt`.
- [ ] **2-5. 비교/저장**
  * `Claude/pipeline/compare.py`
    * pixel-wise DEM 차이 통계 (median ratio per logT, χ² 분포, peak T shift,
      EM 적분 차이) — **HRI 격자 전체 + 작은-구조 마스크 안쪽** 두 가지로 따로 집계.
    * 저장: `outputs/<date>/<roi>/dem_aia6.npz`, `dem_aia7.npz`, `compare.json`.
- [ ] **2-6. Small-structure 마스크 / ROI 추출기**
  * `Claude/pipeline/feature_mask.py`
    * `find_campfire_candidates(hri_map)` — HRI 174에서 unsharp / running-difference
      기반으로 작은 (≲ 5 Mm) brightening detection. 우선 단순 threshold +
      connected-component 로 시작 (Berghmans+ 2021 식 정의 참고).
    * `roi_around(coord, half_size_pix)` — 그 후보 주변 (예: 64×64 픽셀) 잘라내
      Phase 2-5 비교의 입력으로 쓴다.
- [ ] **2-7. 1개 conjunction (2022-03-07) 으로 end-to-end smoke test**
  * 산출물: `Claude/notebooks/2022-03-07_smoke.ipynb` — pipeline 함수를 호출만 하는
    가벼운 노트북. ROI 1개 (campfire 후보 1개), figure 4장
    (HRI input, AIA reproject input, DEM AIA6, DEM AIA7, diff @ campfire 위치).

---

## Phase 3. Separation-angle 의존성 연구

목표: SO–SDO separation 각도가 (AIA+HRI174) DEM 의 AIA-only 대비 차이에 어떻게
영향을 주는지 정량화.

- [ ] **3-1. 케이스 리스트 확정**
  * 4 conjunction (≈0°) + Phase 1-3 표에서 separation ≈ 5/10/15/20/25/30° 각 1–2일씩
    선정 → 총 10–12 케이스.
  * 산출물: `Claude/study_separation/cases.yaml`.
- [ ] **3-2. 일괄 실행**
  * `Claude/study_separation/run_all.py` → 각 케이스에서 **HRI 174 frame 안의
    campfire 후보 N개** 를 자동 추출 (Phase 2-6 마스크) 한 뒤, 그 ROI에서
    AIA-only DEM 과 AIA+HRI174 DEM 을 모두 돌린다.
  * 비교 baseline: 같은 conjunction 안의 quiet 영역 (HRI 의 low-variance 패치)
    에서의 DEM 차이.
  * 산출물: `outputs/separation/<sep_deg>/<date>/<campfire_id>/...`.
- [ ] **3-3. 분석/시각화**
  * separation vs (campfire 위치 DEM peak T shift, EM 차이, χ² 차이) scatter,
    quiet 영역의 동일 지표와 함께 plot — separation이 quiet에는 영향이 적고
    small-feature 에는 크게 영향을 주는지 본다.
  * 산출물: `Claude/study_separation/analyze.ipynb`, `Claude/study_separation/figs/`.

가설 / 메모:
* HRI는 ~100 km 분해능에서 campfire/nanoflare 의 hot kernel 을 분리해낸다.
  AIA-only 는 그 kernel 을 ~440 km/px 빔에 평균하여 hot tail 을 *희석* 시키므로,
  AIA+HRI 의 DEM 은 같은 위치에서 더 높은 logT (≳ 6.4) 의 component 를 더 잘
  살릴 가능성이 있다.
* separation 이 커지면 LOS 가 달라져 동일 구조라도 column emission 이 달라짐 →
  AIA+HRI 가 본질적으로 *다른* plasma column 을 보게 되므로 small-feature
  DEM 차이가 더 커질 것. quiet 영역은 LOS 적분이 두꺼워서 상대적으로 둔감.
* "*같은 픽셀*" 비교는 reproject 가 동일 위치를 가정하므로, separation 이 커질수록
  reproject 자체의 모호성이 증가 → 그 효과도 함께 보고할 것.

---

## Phase 4. Time-offset 의존성 연구

목표: EUI(=HRI174) 시각 t에 대해 AIA를 t + Δt (Δt ∈ {-60, -30, 0, +30, +60} min) 으로
가져왔을 때 7ch DEM 이 어떻게 변하는지.

- [ ] **4-1. 1 conjunction 픽스 (가장 데이터 풍부: 2022-03-07 ; 2024-03-20 은 HRI block 단 1개)**
- [ ] **4-2. 동일 campfire ROI 3종 × Δt 5종 = 15 케이스**
  * `Claude/study_time_offset/run_offset.py`.
  * campfire 의 lifetime 이 보통 5–60 분 사이라는 점이 핵심 — Δt = ±30, ±60 분이면
    같은 frame 안의 campfire 가 *AIA 쪽에서는 이미 사라졌거나 아직 안 떴을* 가능성이
    높다. 이 효과가 DEM 의 hot-tail 에 어떻게 들어오는지 본다.
- [ ] **4-3. 결과 figure**
  * Δt vs DEM 차이 통계 (Phase 3 와 같은 metric).
  * **campfire 위치** vs **quiet 위치** 의 차이 분리 — quiet 은 시간 변화가 작아
    Δt 에 둔감해야 하고, campfire 는 Δt 가 커질수록 hot component 가 사라지는
    방향으로 차이가 커져야 한다는 예측.
* 산출물: `Claude/study_time_offset/analyze.ipynb`.

---

## Phase 5. (Follow-up) AIA-like-EUI(174+304→6ch) + HRI174 DEM

Phase 1–4 결과 정리 *이후* 진행. 이 단계는 별도 phase로 분리해 effect를 섞지 않는다.

- [ ] **5-1. EUI 174+304 → AIA 6ch 합성 모델 확보**
  * 기존 STIX-GOES V1–V4 와 같은 흐름의 image-to-image 모델 (이미 학습된 weight가
    있는지 먼저 확인; 없으면 별도 학습은 본 plan의 scope 밖으로 정의).
- [ ] **5-2. 합성 6ch + HRI174 = 7ch DEM**
  * Phase 2 파이프라인 재사용. `tresp` 만 합성-EUI factor 0.6 + HRI174로 교체.
- [ ] **5-3. (AIA+HRI174) vs (AIA-like-EUI+HRI174) 비교**
  * 동일 logT bin에서 DEM 비율, peak shift, EM 적분 차이.
  * 기대: 합성 모델 noise / channel cross-talk 효과를 분리할 수 있어야 함.
* 의미: AIA가 직접 볼 수 없는 conjunction-off 시점에도 합성-EUI 가 background 역할을
  대신 해줄 수 있는지 검증 — 즉 *HRI 만의 시점에서도* DEM 이 가능한지의 토대.

---

## Phase 6. 보고서/figure 정리

- [ ] Phase 2/3/4 결과를 묶은 internal report (`Claude/report/` 하위).
- [ ] Reference 논문(Wright et al.) 결과와의 정성 비교.
- [ ] 다음 단계 (논문 draft / supervisor 보고) 의 골격.

---

## 파일 트리 (계획)

```
Code_V3/Claude/
├── todo.md                        ← 이 파일
├── env/
│   └── check_env.py
├── inventory/
│   ├── inventory_around_conj.py
│   ├── separation_angle.py
│   ├── conj_window_inventory.csv
│   └── separation_table.csv
├── responses/
│   ├── plot_response.py
│   └── tresp_AIA6_HRI174.npy
├── pipeline/
│   ├── io_loaders.py
│   ├── coregister.py
│   ├── dem_setup.py
│   ├── dem_run.py
│   ├── feature_mask.py            ← campfire/nanoflare 후보 검출
│   └── compare.py
├── notebooks/
│   └── 2022-03-07_smoke.ipynb
├── study_separation/
│   ├── cases.yaml
│   ├── run_all.py
│   └── analyze.ipynb
├── study_time_offset/
│   ├── run_offset.py
│   └── analyze.ipynb
└── report/
    └── ...
```

---

## 진행 메모 / 의사결정 로그

* 2026-05-18 : repo 초기화, 본 plan 작성. 다음 작업은 Phase 1-1, 1-2.
* 2026-05-18 : Phase 1-2 (HRI L1 inventory ±1 week 1/day) + SOAR 쿼리 + AIA pair
  다운로드 시작. 합성 plan 변경 — *AIA / AIA-like-EUI 는 background, HRI 는 작은
  구조 (campfire, nanoflare) 의 fine-scale probe* 로 역할 분담. Phase 2-6
  small-structure 마스크 단계 추가, Phase 3/4 의 ROI 선정 기준을 campfire 중심으로
  바꿈.
