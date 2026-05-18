# Shestov et al. 2025 — 종합 분석 보고서

**논문**: *In-flight cross-calibration of HRI_EUV/EUI and AIA/SDO*
**저자**: S. V. Shestov, A. N. Zhukov, F. Auchère, D. Berghmans, J. Loicq
**저널**: A&A 699, A7 (2025) · **DOI**: [10.1051/0004-6361/202452444](https://doi.org/10.1051/0004-6361/202452444)
**Bibcode**: [2025A&A...699A...7S](https://ui.adsabs.harvard.edu/abs/2025A&A...699A...7S/abstract)
**접수일**: 2024-10-01 · **승인일**: 2025-04-11

본 보고서는 PDF를 다운로드받아 6개 섹션을 병렬로 한국어 번역·분석한 결과를 통합한 것이다. 각 섹션의 상세 요약은 `section_0X_summary.md` 에 별도 저장되어 있다.

---

## TL;DR (3-Bullet 요약)

- **핵심 결과**: AIA 6 채널 + HRI_EUV 1 채널 = **7 채널 동시 DEM 역산** 을 수행한 결과, **실제 HRI_EUV 신호가 AIA-기반 DEM 시뮬레이션 예측보다 ~40% 큼**. 보정 계수 `k = 1.4–1.6` 이 3개 관측일(2020-05-30, 2022-03-07, 2023-03-29) 모두에서 일관되게 best-match.
- **물리적 의미**: HRI_EUV 를 DEM 인풋에 포함하면 **log T ≈ 6.0 (1 MK warm plasma)** 영역의 EM 만 의미 있게 수정됨. 2 MK 이상 hot loop EM 은 변화 없음.
- **DEM4SO 시사점**: EUI/HRI_EUV 의 모든 정량 분석은 **±40% systematic calibration uncertainty 를 동반 보고**해야 하며, 1 MK 영역 결론은 7 채널 DEM 에 의존해야 한다.

---

## Section 1: Abstract + Introduction

### Abstract 핵심
- **Context**: HRI_EUV 는 174 Å 부근 5 Å passband, 0.5″ 각분해능
- **Aim**: HRI_EUV ↔ AIA radiometric cross-calibration
- **Method**: 7 채널 (AIA 6 + HRI 1) DEM 역산, 실제 vs 시뮬 영상 비교
- **Result**: 실제 HRI 가 시뮬 대비 ~40% 큼
- **Conclusion**: 어느 기기 책임인지는 단정 불가; DEM 분석에 이 차이를 반영해야 함; HRI 포함 시 1 MK warm plasma 수정. "Golden reference" 전략 제안.

### Introduction의 핵심 가설
> 여러 기기를 동시에 사용한 DEM 역산에서 G_j(T) 오차는 예측 신호 I_j 의 체계적 불일치로 나타난다. 따라서 다중 기기 DEM 일관성 비교로 G_j(T) 정합성과 in-orbit degradation 을 동시에 진단할 수 있다.

### 핵심 수식
- **등온 모델**: `I_j = G_j(T_0) · EM_{T_0}`  (Eq. 1)
- **다온도 모델**: `I_j = ∫_{T_min}^{T_max} G_j(T) · DEM(T) dT`  (Eq. 2)
- **응답함수**: `G_j(T) = ∫ s_T(λ) · R_j(λ) dλ`
- **보정 계수**: `G̃_j(T) = k · G_j(T)`

### 선행 연구 (cross-calibration 직계)
| 인용 | 기여 |
|------|------|
| Boerner+2014 | AIA ↔ EVE/EIS 상호보정 (방법론 직계) |
| Hock & Eparvier 2008 | SOHO/EIT ↔ TIMED/SEE 절대 보정 |
| Shestov+2014 | 1저자의 SPIRIT ↔ EIT cross-cal 선례 |
| Raftery+2013 | AIA/SWAP/EIT/EUVI 171 Å 다기기 비교 |
| Zhukov+2021 | EUI HRI + AIA 스테레오스코피 (cross-cal 동기) |

---

## Section 2: Observations

### HRI_EUV 사양
- 광학: Off-axis Cassegrain, f = **4187 mm**
- 검출기: 10 μm CMOS APS, **0.5″/pixel**
- 입사구경: ∅ 47.4 mm
- Multilayer: Al/Mo/SiC, 174 Å peak, **FWHM ≈ 5 Å**
- 필터: entrance Al foil + filter wheel (open + 2× Al + occulting slot)
- 사용 데이터: **EUI Data Release 6.0** (Kraaikamp+2023, DOI 10.24414/z818-4163), Level-2, `FILTER='Aluminium_174_2'`
- 지상 보정: Gissot+2023

### AIA 사양
- 광학: Cassegrain, f = 4.125 m, ∅ 20 cm split primary
- 검출기: 12 μm back-side CCD, **0.6″/pixel**
- FWHM ≈ 10 Å (HRI 의 2배)
- 사용 채널: **94, 131, 171, 193, 211, 335 Å**
- 데이터: SolarSoft `aia_prep` Level-1.5
- Degradation: `aia_bp_get_corrections()` 로 G_j(T) 단계에서 보정

### 관측 데이터셋
| 날짜 | SolO–Earth 분리각 | 비고 |
|------|------------------|------|
| **2020-05-30** ~14:58 UT | **31.3°** (큰 분리각) | HRI 캠프파이어 캠페인 (Berghmans+2021), 시차 잔존 |
| **2022-03-07** | **3.0°** | 시차 최소 |
| **2023-03-29** | **2.8°** | 약 3년 시계열 → degradation 검출 가능 |

### Spectral response 차이 (Fig. 2)
- **AIA 171 Å 가 더 좁음**: Fe IX 171 Å 중심, **Al 필터의 L-edge** 가 peak 근처를 잘라냄
- **HRI_EUV 가 더 넓음**: Fe IX + Fe X (174 Å) 인접 라인 기여 포함
- 결과: G(T) 형태와 peak 위치가 미세하게 다름 → cross-cal 의 핵심 차이점

---

## Section 3: DEM 방법론 (가장 중요한 섹션)

### DEM 알고리즘 핵심
| 항목 | 내용 |
|------|------|
| DEM 코드 | **Cheung et al. (2015)** — SolarSoft 내장 sparse-basis 방법 |
| DEM 형태 | Piece-wise step function, bin 별 적분 EM 추정 |
| Temperature grid | log T = **5.6–6.62**, Δlog T = 0.06, **17 bins** (0.4–4.2 MK) |
| Basis | Delta 1개 + Gaussian 2개 (σ = 0.1, 0.2) |
| 정규화 | Sparse / basis-pursuit + EM ≥ 0 제약 |
| Forward model | `I_j = Σ_i G_j(T_i) · EM_{T_i}` (Eq. 3) |
| 방정식 수 | AIA-only: **6** / Joint: **7** |
| 풀이 방식 | **Per-pixel** (per-structure 아님) |

### 데이터 전처리 핵심 결정
1. **`aia_get_response()` 미사용** — 분광 모델 차이로 인한 채널별 50% 변동 회피. AIA + HRI 모두 **CHIANTI 직접 호출** (`sun_coronal_2021_chianti` abundance, n_e = 10⁹ cm⁻³, λ ∈ 10–1000 Å) 로 동일 조건 G_j(T) 계산.
2. **AIA degradation 계수**: `aia_bp_get_corrections()`, 2020–2023 상수:
   - 94 / 131 / 171 / 193 / 211 / 335 Å → **0.9 / 0.51 / 0.74 / 0.49 / 0.40 / 0.17**
3. **WCS 재투영**: Thompson 2006/2010 루틴, FITS 헤더 `DSUN_OBS, HGLN_OBS, HGLT_OBS, WCSNAME, CRPIX/VAL/DELT` 사용
4. **시간 정렬**: HRI 의 `EARTH_DATE` 키워드로 광행거리 보정 후 AIA 최근접 프레임 선택
5. **수동 co-alignment**: HRI `CRVAL` **5–10 arcsec** 수정, AIA 211 Å **2 픽셀 shift** 추가

### Cross-calibration 계수 k
- **정의**: DEM 으로 재현한 HRI 시뮬과 실제 HRI 의 절대 신호 비.
- **적용**: 시뮬 신호에 k 곱 (Section 4) 또는 실제 신호를 k 로 나눔 (Section 5) — 수학적 동등.
- **본 섹션 보고값**: HRI_EUV **k = 1.7**, AIA 171 Å **k = 5.5**.

### 강점과 한계
**강점**: 응답함수 일관 계산, per-pixel DEM map, 다중 vantage point 통합
**한계**: 정렬 오차 민감(수동 shift 필요), k 값 > 1 자체가 미해결 절대보정 문제, log T < 5.6 천이영역 제외, background subtraction 미명시

---

## Section 4: AIA-only DEM

### 절차
1. AIA 6 채널로 DEM 역산 (1024×1024 px @ 2020-05-30)
2. G_HRI(T) 곱 → HRI 시뮬 영상 합성
3. HRI 픽셀 격자로 재투영
4. 실제 HRI와 시각+히스토그램 비교, 정규화 계수 k 결정 (Fig. 5, 6)

### 결과: k 의 시간 변화
| 날짜 | best k | 해석 |
|------|--------|------|
| 2020-05-30 | **1.7** | HRI 초기 과민감성 |
| 2022-03-07 | **1.2** | 부분 열화 |
| 2023-03-29 | **1.0** | 정상화? |

→ **AIA-only 관점**: HRI 가 약 20%/2년 점진적 열화로 보이며, AIA degradation 률과 부합.

### 잔존 차이
- 시뮬이 **대비가 더 높음** (어두운 픽셀 더 어둡고 많음)
- 밝은 루프 영역에서 AIA 171 재투영 vs 시뮬 차이 → 174 Å이 171 Å보다 약간 더 뜨거운 플라스마에 민감
- HRI 픽셀 ≈ 200 km vs AIA 픽셀 ≈ 441 km @ 0.55 au — 미세 구조 재현 불가

---

## Section 5: HRI + AIA 동시 DEM (메인 결과)

### 핵심 변화점
Section 4가 "AIA-only DEM → HRI 시뮬" 방향이었다면, Section 5는 **HRI 를 직접 인풋으로 추가한 7 채널 DEM**. HRI 실제 신호를 k 로 **나눈 후** 역산 (수학적으로 등가).

### k-scan 결과: **3개 날짜 모두 k = 1.4–1.6 으로 일관**

| 날짜 | 분리각 | Sect. 4 (AIA-only) k | **Sect. 5 (joint DEM) k** |
|------|--------|---------------------|---------------------------|
| 2020-05-30 | 31.3° | 1.7 | **1.4–1.6** |
| 2022-03-07 | 3.0° | 1.2 | **1.4–1.6** |
| 2023-03-29 | 2.8° | 1.0 | **1.4** |

> **Section 4 vs Section 5 의 긴장 관계**: AIA-only 는 단조감소하지만 joint DEM 은 ~1.4-1.6 으로 일정. 2023년에 가장 크게 갈라짐. 저자들은 이 차이를 **flag 만 하고 결론은 유보**.

### "40% larger" 의 출처
- 3개 독립 관측일 모두 k ≈ 1.4–1.6 → 실제 HRI 가 시뮬보다 ~40% 큼
- **두 가지 통계적 진단**으로 검증:
  1. 1D 히스토그램 매칭 (전 FOV)
  2. 2D 히스토그램 — Pearson r 최대화 + off-diagonal spread 최소화 + DEM 비수렴 픽셀(black pixel) 최소화
- best k = 1.4–1.6 에서 세 지표 모두 동시 최적

### DEM(T) 의 변화 (Fig. 16, Discussion에서 인용)
- HRI 추가 시 **log T ≈ 6.0 (1 MK warm plasma) 의 EM 만 의미 있게 수정**
- log T ≥ 6.2 (≥ 1.6 MK) 영역 EM 은 거의 동일
- 더 차가운(T < 0.6 MK) 또는 더 뜨거운(T > 3 MK) bin 도 거의 변화 없음
- **이유**: HRI_EUV 의 G(T) peak 가 정확히 log T ≈ 6.0 부근

### Resolution Robustness
2× 또는 4× downsampling 해도 결과 동일 → 분해능 의존성 없음.

---

## Section 6: Discussion & Conclusions

### 주요 결론
1. **40% 불일치 확인** (k ≈ 1.4–1.6)
2. **그러나 절대보정학적으로는 "매우 좋은" 일치** — G(T) 변환 사슬의 복잡성 감안 시
3. **DEM 분석에는 반드시 보정 필요**
4. **어느 기기의 책임인지는 단정 불가** — HRI vs AIA 둘 다 자체 모델 견고
5. **HRI 추가의 주된 효과 = 1 MK warm plasma EM 의 수정**
6. **k 의 시간 변화 가설은 미결** — 21개 일자 분석에도 활동도·시점 변동으로 결정적 결론 불가
7. **"Golden reference" EUV 보정 표준 제안** — TSI 복사계 cross-cal 모델을 EUVI/SWAP/SUVI/EIT 로 확장
8. **방법론의 일반화 가능성** — 큰 FOV 영역 비교 방식의 우월성

### 40% 차이의 원인 (저자들의 분류)
**(A) Peak value error (광학 처리량 과소평가)**
- HRI: 필터 메쉬 그림자, degradation 불확실성
- AIA: 동일 유형 가능하지만 SolarSoft+AIA팀 확인으로 신뢰도 ↑

**(B) Shape error (분광 모델 / 스펙트럼 감도)**
- CHIANTI 누락 라인
- 분광 처리량 측정 오차
- 단, HRI passband 인 171 Å 부근은 잘 연구되어 원자데이터 문제 가능성 낮음

→ 소거법적으로 **peak value error 쪽 가능성 더 높음**.

### 추가 검증
- **다른 abundance set** (`sun_coronal_1992_feldman_ext`) 사용 시 결과 크게 안 변함 (Appendix D)
- T_min 등 inversion 매개변수 변경 시에도 robust

---

## DEM4SO 연구 적용 종합 권장사항

### 단계별 워크플로
1. **데이터 준비**
   - SDO/AIA Level-1.5 (`aia_prep`) 6 채널
   - SolO/EUI HRI_EUV Level-2 (EUI DR 6.0 또는 최신)
   - FITS 헤더 `DSUN_OBS, HGLN_OBS, HGLT_OBS, EARTH_DATE, CRPIX, CRVAL, CRDELT` 확인

2. **응답함수 자체 계산**
   - SolarSoft `aia_get_response()` 우회, CHIANTI 직접 호출
   - 동일 조건: λ ∈ 10–1000 Å, n_e = 10⁹ cm⁻³, abundance = `sun_coronal_2021_chianti`
   - AIA degradation: `aia_bp_get_corrections()` 적용 (위 표의 6개 계수)

3. **DEM 인버전 셋업**
   - Cheung+2015 sparse-basis 알고리즘
   - log T = 5.6–6.62, 17 bins, Δlog T = 0.06
   - Basis: δ + 2× Gaussian (σ = 0.1, 0.2)

4. **시간 정렬 & 재투영**
   - HRI `EARTH_DATE` 로 AIA 매칭
   - SunPy `reproject_interp` 또는 SSW WCS 루틴
   - 수동 잔여 shift: HRI `CRVAL` ±10 arcsec, AIA 211 Å ±2 px 보정

5. **k-스캔 및 보정 적용**
   - k ∈ [1.0, 2.0] 격자, Δk = 0.2
   - 진단: 1D 히스토그램 + 2D 히스토그램 (Pearson r) + 비수렴 픽셀 비율
   - **Default 권장 k = 1.4** (3개 시점 평균, joint-DEM 기준)
   - 관측 일자에 따라 보간 가능 (2020: 1.6 → 2022: 1.4 → 2023: 1.4)

6. **결과 보고 시 시스템 오차 명시**
   - **모든 DEM4SO 산출물에 ±40% 절대보정 systematic uncertainty 동반 표기**
   - 통계 노이즈와 별도로 calibration error bar 운영
   - log T ≈ 6.0 (1 MK) bin 에는 추가 "low-confidence" 등급 부여

7. **Cross-validation**
   - AIA-only 6 채널 DEM vs Joint 7 채널 DEM 동시 계산
   - 두 결과 차이를 systematic uncertainty proxy 로 사용
   - abundance 2종 이상 (Feldman vs Asplund vs Schmelz) 교차 검증
   - T_min 등 인버전 매개변수 robustness 테스트

### 절대 사용하지 말아야 할 보정
- **Section 4 의 AIA-only k 값 (1.7/1.2/1.0) 단독 사용 금지**
- 이는 HRI를 인버전 제약에 포함하지 않은 less-self-consistent 값
- 반드시 **Section 5 의 joint-DEM k (1.4–1.6)** 사용

### 신뢰할 수 있는 영역 / 주의할 영역
| 영역 | 신뢰도 | 비고 |
|------|--------|------|
| log T ≥ 6.2 (≥ 1.6 MK) hot loop EM | **HIGH** | HRI 포함/제외 무관, 6-AIA만으로 충분 |
| log T ≈ 6.0 (1 MK warm plasma) EM | **MEDIUM** | HRI 인풋에 가장 민감, 7-채널 필수 |
| log T < 5.6 (< 0.4 MK) TR/chromosphere | **LOW** | DEM 그리드 밖, HRI 정보 부족 |
| log T > 6.62 (> 4.2 MK) very hot | **LOW** | DEM 그리드 밖 |
| 절대 EM 정량값 (모든 T) | **MEDIUM** | ±40% systematic offset |
| 상대 EM 변화 (시간/공간) | **HIGH** | k는 안정적이므로 차이는 신뢰 가능 |

---

## 보존 파일

| 파일 | 내용 |
|------|------|
| `shestov2025.pdf` | A&A 원본 PDF (6 pages + appendices, 19.8 MB) |
| `shestov2025.html` | A&A 원본 HTML |
| `shestov2025_flow.txt` | PDF 추출 텍스트 (paragraph flow) |
| `sections/00_frontmatter_intro.txt` ~ `08_appendices.txt` | 섹션별 분할 |
| `section_01_summary.md` ~ `section_06_summary.md` | 섹션별 상세 분석 (한국어) |
| `report-Shestov2025.md` | **본 통합 보고서** |

---

## 인용 (BibTeX)

```bibtex
@article{Shestov2025,
  author = {Shestov, S. V. and Zhukov, A. N. and Auch\`ere, F. and Berghmans, D. and Loicq, J.},
  title = {In-flight cross-calibration of HRI{\_}EUV/EUI and AIA/SDO},
  journal = {Astronomy \& Astrophysics},
  volume = {699},
  pages = {A7},
  year = {2025},
  doi = {10.1051/0004-6361/202452444}
}
```

---

*보고서 생성: 2026-05-19 · D:\\Claude-research\\DEM4SO-research\\Shestov2025\\report-Shestov2025.md · 6개 섹션 병렬 분석 통합*
