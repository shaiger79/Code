# 🧭 TrafficGen Vibe Context (연속성 컨텍스트)

> **이 파일의 목적**: 어떤 세션/사람이 이어받아도 **작업의 연속성**을 유지하기 위한 살아있는 로그다.
> ESM 프로젝트의 `ESM/vibe_context.md`와 같은 역할을 TrafficGen에서 수행한다.
>
> **[AI 필수 지침 — 매 작업 전/후]**
> 1. **작업 시작 전**: 반드시 `TrafficGen/MASTER_PROMPT.md`(프로젝트 헌장)와 이 파일을 먼저 읽고,
>    확립된 맥락·결정 안에서 작업한다.
> 2. **작업 종료 후**: 진행한 사항(무엇을/왜/어떻게, 검증 결과, 다음 대기)을 이 파일에 갱신한다
>    (사용자 요청 여부와 무관, 항상).
> 3. **버전 파일 규칙**: 활성 개발 파일은 `trafficgen_rN.py`. 사용자가 "새 라운드"를 신호하면 그 시점
>    최신 파일을 복제해 다음 번호를 만든다. 기존 라운드 파일은 수정하지 않는다(ESM 관례 준용).
> 4. **커밋/머지**: 검증된 변경은 지정 브랜치 `claude/wireless-network-kpi-docs-yjm6y4`에 커밋·푸시하고,
>    git을 통해 코드 머지로 하나의 프로젝트를 완성해 간다.
> 5. **저장소 정합**: 자매 프로젝트 `ESM/`(에너지 절감 분석)과 `LBM`(로드밸런싱, 예정)이 본 툴의 출력을
>    소비한다. 출력 스키마·식별자 규칙은 ESM 호환을 최우선으로 유지한다.

*Last Updated: 2026-07-11*

---

## 1. 확정된 주요 결정 (Decisions)

* **정체성**: 상용망(4G LTE + 5G NR) **트래픽/KPI Generator**. 데이터 애널리스트의 알고리즘 개발(에너지
  세이빙·로드밸런싱 등) 토대가 되는 합성 raw data 생성. 폴더 `TrafficGen/`에서 관리.
* **RAT 범위**: **LTE + NR 오버레이(둘 다)**. 현행 상용망이 NSA(ENDC)로 운용 중임을 반영.
  * **ENDC / NSA(Non-Standalone)**: E-UTRA(LTE) + NR **Dual Connectivity**. 마스터 노드는 LTE(제어),
    데이터는 주로 NR(SCG)로 받는 구조. LTE와 NR을 동시에 쓰는 사용자 존재.
  * **SA(Standalone)**: NR 단독(제어+트래픽)도 최근 상용화 → 사용자 분산 시나리오에 포함 가능.
* **첫 시스템(초기 구축 대상)**: **단일 사이트(1 site) 오버레이**
  * LTE 시스템 1개 = **멀티캐리어(커버리지 오버랩) 3 캐리어(=3 셀)**.
  * NR 시스템 1개 = **3 캐리어(=3 셀)**.
  * 즉 한 사이트에 총 6개 셀(LTE×3 + NR×3)이 지리적으로 겹쳐(overlay) 존재.
* **KPI 집계 레벨(4단계)**:
  1. **Cell KPI** — 각 셀 단위.
  2. **LTE Sector KPI** — 커버리지 오버랩된 LTE 셀 3개 aggregation.
  3. **NR Sector KPI** — NR 셀 3개 aggregation.
  4. **LTE+NR Total KPI** — 전체 통합 품질/수준 비교.
* **출력**: ESM 호환 CSV(`utf-8-sig`). PM(Traffic)/Energy/Topology(CM) 3계열. ESM·LBM 연동용 다운로드 지원.
* **UI**: **GUI 필수**(사용자 요구). Tkinter + Matplotlib. 시각화(시계열/CDF/히스토그램) + KPI 테이블
  비교 + CSV 다운로드. (ESM과 동일 스택으로 상호운용성 확보.)
* **생성 충실도**: 초기엔 **경량 통계/규칙 + 인과관계 모델**로 시작(§MASTER_PROMPT §5). 이후 필요 시
  물리 큐잉/스케줄러 기반으로 고도화.
* **향후 활용 맥락(설계 시 염두)**: 에너지 세이빙(셀 off 시 트래픽 오프로딩으로 지표 유지),
  로드밸런싱(과밀 셀 → 타 셀/RAT로 유저 분산: NR→LTE 오프로딩, DC 해제 시 LTE anchor만 서비스 등).
  → 생성 모델은 **사이트 수요를 캐리어/RAT로 분배(steering) 가능한 구조**로 두어 이런 실험을 지원한다.

## 2. 기술 스택 / 실행 환경 메모

* Python 3.11, numpy/pandas/matplotlib. GUI는 tkinter(로컬 실행 필요).
* **개발 컨테이너에는 tkinter 미설치** → GUI는 로컬에서 실행. 코드는 tkinter 없이도 import/`py_compile`
  되도록 방어(엔진과 GUI 분리, 조건부 base class). **엔진/집계/Export/플로팅은 headless로 검증한다.**
* 검증 관례: `python -m py_compile` + headless 생성 스모크(샘플 CSV/PNG 산출 + 인과관계 sanity check).

## 3. 진행 이력 (Changelog)

* **[r1] (2026-07-11) ENDC/DC·SA Steering 명시적 구현 — `trafficgen_r1.py` (현재 유일 활성 개발 파일)**
  * `trafficgen_r0.py`를 복제해 시작. r0의 기능 전부 유지 + steering 계층 추가. (PR #30 머지 후 main에서
    브랜치 재시작하여 진행.)
  * **핵심 변경 — 사이트 수요 라우팅**: 이전엔 셀별 독립 offered load 였으나, 이제 사이트 전체 수요(Mbps,
    `site_peak_dl_mbps`)를 사용자 클래스(Legacy-LTE / ENDC(NSA) / NR-SA)로 나눠 steering 정책대로
    LTE 풀 / NR 풀로 라우팅 후 캐리어 용량비로 분배(`_route_demand`). 트래픽 보존(옮긴 만큼 목적지 부하↑).
  * **`SteeringConfig` 레버**: 캐리어 on/off(`lte_enabled`/`nr_enabled`, off 셀은 sleep 전력=p_idle×0.12,
    트래픽 0), `endc_split_nr`(ENDC 데이터 NR(SCG) 비중), `dc_release`(ENDC 전부 LTE anchor),
    `nr_to_lte_offload`(로드밸런싱 강제 이전), `sa_fallback_to_lte`(NR 전면 off 시 SA 폴백). 프리셋:
    baseline/nr_off/nr_all_off/dc_release/offload.
  * **엔진**: `_generate_cell`이 이제 배정 수요(Mbps)+enabled 를 받아 offered=배정÷용량(>1이면 혼잡),
    유저수는 offered 비례(수요 0이면 유저 0), 나머지 인과 체인은 r0 동일.
  * **GUI**: Config 탭에 Steering 패널(프리셋/site peak/ENDC split/DC release/offload/셀 on-off 체크) 추가,
    `_current_steering()`로 Generate 에 반영. `run_scenario()`/`run_headless_demo()`는 baseline vs nr_off 비교.
  * **검증**: `py_compile` 통과 + headless 시나리오 비교 —
    (1) NR-off 총에너지 절감 551.7→485.3 kWh, (2) 남은 NR 캐리어 부하 상승, (3) offload 시 LTE_util↑·NR_util↓,
    (4) dc_release 시 LTE_util 38.6→75.1 상승, (5) 꺼진 셀 DL=0·sleep 전력 확인. (대용량 NR→소용량 LTE
    오프로딩 시 LTE 혼잡으로 총 전달량↓ 하는 트레이드오프도 데이터로 재현됨.)

* **[r0] (2026-07-10) TrafficGen v0 최초 구현 — 단일 사이트 LTE×3 + NR×3 오버레이 생성기 + GUI**
  * 파일: `TrafficGen/trafficgen_r0.py` (r1으로 대체됨 — 이후 수정 없음, 라운드 보존).
  * **토폴로지**: `build_default_topology()` — LTE 3캐리어(B1/2100, B3/1800, B7/2600, 각 20MHz/100RB)
    + NR 3캐리어(n78 100MHz/273RB ×2, n78 소역폭 1). 셀별 용량/에너지/유저 파라미터 부여.
  * **생성 엔진**(`TrafficGenEngine`): 15분 ROP 시계열. 일주기(diurnal, 점심/저녁 피크+주말 감쇠) 수요 →
    셀별 인과 체인: offered load → UsedRB/PRB Util(포화 클리핑) → Traffic Volume(DL/UL bytes) →
    IP Tput(활성 유저수↑ → 사용자당 처짐↓) → RU 에너지(P_idle + (P_max−P_idle)·util) →
    Failure(혼잡 제곱 가중). 시드 고정 재현성.
  * **집계**(`aggregate_kpis`): Cell / LTE Sector / NR Sector / Total 4레벨. Volume·RB·Energy·Users·Fail
    합산, PRB Util = ΣUsedRB/ΣnRB, IP Tput = 볼륨가중 평균(사용자 체감 대표값).
  * **Export**(`export_esm_csv`): PM(Traffic)/Energy Stat/Topology(CM) 3개 CSV, `utf-8-sig`, ESM 식별자
    규칙(콤마 없는 숫자 문자열).
  * **시각화**(`plot_kpi`): 시계열 / CDF / 히스토그램 (Axes 주입식 → GUI·headless 공용).
  * **GUI**(`TrafficGenApp`, Tkinter): Config / Generate / Visualize / Compare / Export 5탭. tkinter
    없으면 base=object로 대체되어 import 안전.
  * **검증**: `python -m py_compile` 통과. headless 스모크(7일×6셀 생성)로 인과관계 확인 —
    (a) 피크시간 PRB Util·에너지 동반 상승, (b) 활성 유저수↑ 구간 IP Tput 하락, (c) NR 셀이 LTE보다
    바이트/에너지 크게 소모, (d) 집계 합산 일관성, (e) 3개 CSV + CDF PNG 산출. (상세 수치는 커밋 로그.)

## 4. 다음 단계 / 대기 (To-Do)

1. **GUI 실환경 확인**: 사용자 로컬(tkinter 설치)에서 5탭 동작·시각화·다운로드 확인 필요(컨테이너 미검증).
2. ~~**ENDC/DC·SA steering**~~ ✅ [r1] 구현 완료(`SteeringConfig`, `_route_demand`). 후속: steering
   파라미터를 시간대별로 변화(스케줄/이벤트)시키는 동적 정책, 사용자 클래스 비율의 지역/시간 변동.
3. **멀티 사이트 확장**: 현재 1 사이트. 다중 사이트/섹터(방위각)로 확장.
4. **ESM round-trip 검증**: 생성 CSV를 실제 ESM에 로드해 파싱·분석되는지 왕복 확인(컬럼명 최종 정합).
5. **정답(ground truth) 라벨 출력 여부**: 이상/이벤트 주입 및 숨은 파라미터 동시 출력(애널리스트 검증용) — 사용자 확정 대기.
6. **KPI 세부 확정**: Failure 세부(RRC/E-RAB/Drop/HO) 컬럼명, Active/Connected 구분, RuPowerTot/Cnt의
   ESM 파싱 의미 정합.

---
*AI Directive Status: Active (Always Read MASTER_PROMPT + this file First, Always Update Post-Task)*
