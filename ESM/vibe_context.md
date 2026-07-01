# 📡 ESM (Energy Saving Manager) Project Vibe Context

## 1. 프로젝트 개요 (Project Overview)
* **목적**: 이동통신(4G/5G) 네트워크의 Traffic Data(PM)와 Energy Stat Data를 분석하여, Energy Saving(ES) 적용 임계조건을 도출하고 예상 절감 에너지를 예측하는 GUI 기반 최적화 도구 개발.
* **주요 스택**: Python, Tkinter (UI), Pandas (데이터 처리), Matplotlib (시각화)
* **핵심 지표**:
  * PM: `IP Tput`, `UsedRB`, `AirMacDLByte`, `AirMacULByte`
  * Energy: `RuPowerTot`, `RuPowerCnt` (RU별 시간당 소모 전력)
  * Efficiency: Energy Efficiency (EE) = (AirMacDLByte + AirMacULByte) / Consumed [Wh]

## 2. 핵심 개발 원칙 (Core Rules & Directives)
1. **아키텍처 보존**: 객체지향형 5단계 상속 구조(`AppBase` -> `AppEditors` -> `AppTraffic` -> `AppDashboard` -> `ESAnalyzerApp`)를 절대 훼손하지 않고 확장한다. (※ 실제 코드 상으로는 `AppTraffic`이 별도 클래스로 분리되어 있지 않고 `ESAnalyzerApp`에 트래픽 패턴 뷰어 메서드가 포함된 4단계 상속: `AppBase` -> `AppEditors` -> `AppDashboard` -> `ESAnalyzerApp` 구조로 실동작 중. 아래 3항 참조.)
2. **ID 정규화 철저**: `eNB_ID`, `Sector`, `cell-num` 등 모든 식별자는 콤마(,)가 없는 순수 문자열 형태의 숫자(Natural Number)로 변환하여 매핑 오류를 원천 차단한다. (`_extract_int_id` 활용)
3. **방어적 코딩**: Pandas DataFrame 병합/조회 시 빈 데이터 예외 처리(`empty` 체크)를 철저히 하고, `SettingWithCopyWarning` 방지를 위해 명시적 `.copy()`를 사용한다.
4. **[AI 지침] 컨텍스트 최우선**: AI는 새로운 세션이나 작업 시작 전 반드시 본 `vibe_context.md`를 읽고 맥락을 동기화해야 하며, 주요 기능 변경/추가 시 본 문서를 자동 업데이트하여 사용자에게 제공해야 한다. (요청 여부와 무관하게 매 작업 전/후 필수 수행)

## 3. 시스템 아키텍처 (실제 코드 기준 4단계 상속 구조)
* **`AppBase`**: 공통 헬퍼(ID 정규화, 시간/날짜 필터링, UI 기본 설정) + 각 하위 기능의 no-op 스텁(`pass`) 정의.
* **`AppEditors`**: Carrier, Sector, RU Spec, CIQ JSON/Excel 설정 로드 및 UI 에디터(Treeview CRUD).
* **`AppDashboard`**: CM/CIQ 데이터 병합(Cell-RU Mapping), Energy Stat 파싱(`_parse_energy_stat_raw` 원본 파서 + `_parse_energy_stat` 날짜/시간 필터 래퍼), Energy 대시보드 시각화(Gamma 고급설정 포함).
* **`ESAnalyzerApp`**: Traffic Pattern Viewer(Interactive/Batch) + ES 임계조건 최적화 알고리즘(Optimizer) + 절감량 예측(EE 포함) + **Learning Energy Curve**(RU HW별 loading-energy 회귀 학습) + 최종 Treeview 리포트, 최상위 실행 클래스(`if __name__ == "__main__": app = ESAnalyzerApp()`).

### 3-1. 탭(Notebook) 구성
1. 📂 Data I/O & CM — Traffic/Energy Stat/CM 파일 로드, Cell-RU Mapping & Azimuth 조회
2. ⚙️ DB Editors — CarrierConf/SectorList/RU Spec/CIQ 편집
3. ✨ Optimizer — ES 임계조건 산출 (Manual/Auto 운영시간)
4. 📊 Traffic Pattern — Interactive/Batch 트래픽 시각화
5. ⚡ Energy Dashboard — 소모 에너지 분석, 절감 예측 팝업(Gamma)
6. **📈 Learning Energy Curve (신규, v1.5)** — 아래 4항 참조

## 4. 최근 작업 히스토리 및 주요 업데이트 (History)
* **[v1.0] 기본 프레임워크 구축**: 상속 구조 완성, Traffic 및 Energy 데이터 병합/시각화 기능 구현.
* **[v1.1] 예상 에너지 절감률 추가 및 EE 로직 구현**:
  * 전체 eNodeBID에 대한 `Total Consumed`, `Total Expected`, `Total Saving` 요약 행 추가.
  * Traffic Data(`AirMacDLByte` + `AirMacULByte`) 기반 **Energy Efficiency (EE)** 계산 및 Improvement[%] 로직 추가.
* **[v1.2] ES 상세 내역 확장 및 Gamma 보정**:
  * UI에 Advanced Settings를 추가하여 `Gamma`(기본값 0.7, 0.001단위) 설정 기능 구현.
  * `Effective Nc2 * Gamma`로 보정된 값을 이용한 에너지 절감량 정밀 산출.
  * Target Cell에 연결된 `Board Type` 식별 및 해당 RU(bid, portid, cascade)의 시간단위 소모 에너지 합산(`Target RU Consumed [Wh]`) 기능 구현.
* **[v1.3] 안정성 패치 (Bug Fixes)**:
  * 부모 프레임 계층 충돌로 인한 Advanced Settings UI 숨김/표출 버그 해결 (`before` 속성 제거).
  * Groupby 연산 시 `Total_Traffic_Byte` 컬럼 누락으로 인한 `KeyError` 해결.
  * `AppBase._filter_date_time` 내 Pandas `SettingWithCopyWarning` 해결 (명시적 `.copy()` 및 `inplace=True` 제거).
* **[v1.4] (2026-07-01) GitHub 프로젝트화 및 치명적 실행 버그 2건 긴급 수정**:
  * **[Bug #1 - SyntaxError] `AppDashboard` 클래스 docstring과 `def _build_energy_ui(self):` 선언이 한 줄에 붙어있어 `esm_r11.py`가 아예 실행조차 되지 않는 상태였음(`python -m py_compile` 즉시 실패). 두 문장을 별도 줄로 분리하여 해결.
  * **[Bug #2 - 치명적 구조 버그] `class ESAnalyzerApp(AppDashboard):`가 파일 내에 두 번 선언되어 있었음(기존 라인 935, 1237 부근). Python은 같은 이름의 class 선언을 만나면 이전 정의를 그대로 덮어쓰므로, 두 번째 `class ESAnalyzerApp` 선언 이후의 메서드들만 최종 클래스에 남고, 첫 번째 선언부에 있던 `_toggle_view_mode`, `load_enodebids`, `open_traffic_pattern_popup`, `_prep_traffic_data_for_patterns`, `_get_metric_configs`, `_render_interactive_graph`, `_batch_generate_patterns` 7개 메서드는 전부 유실되어 `AppBase`의 빈 `pass` 스텁으로 대체됨. 그 결과 **"📊 Traffic Pattern" 탭의 모든 버튼(eNodeBID 로드, Interactive Viewer Show, 전체 일괄 저장 팝업)이 클릭해도 아무 동작도 하지 않는 상태**였음. 중복된 `class ESAnalyzerApp(AppDashboard):` 선언부(및 잘못된 안내 주석)를 제거하여 하나의 클래스로 병합, 총 21개 메서드가 정상적으로 하나의 `ESAnalyzerApp`에 귀속되도록 수정. AST 파싱으로 병합 전/후 메서드 목록을 비교 검증함.
  * 위 2건 수정 후 `python -m py_compile` 정상 통과 확인. (GUI 환경(Tkinter Display)이 없는 서버 세션이라 실제 창 구동 테스트는 미실시 — 로컬 PC에서 실행 확인 필요.)
  * 프로젝트를 GitHub 저장소(`shaiger79/Code`) 내 `ESM/` 폴더로 구조화하여 커밋. (GitHub 세션 권한이 `shaiger79/Code` 리포지토리로 한정되어 있어, 별도의 신규 "ESM" 리포지토리는 생성하지 않고 기존 지정 리포지토리 내 프로젝트 폴더로 구성함.)
  * Google Drive(`VibeCoding/ESM`) 동기화는 현재 세션에 Google Drive 연동 도구가 제공되지 않아 미수행 — 사용자가 "일단 스킵"으로 확인, 추후 별도 처리 예정.

* **[v1.5] (2026-07-01) 신규 기능: 📈 Learning Energy Curve 탭 추가**
  * **목적**: 상용망 통계(Cell Unavailable Time + RU Power + Traffic)를 이용해 RU HW(Board Type)별 "loading에 따른 에너지 소모량"을 1차 함수(기울기/절편)로 학습하고, Cell OFF 시 예상 에너지 절감량을 추론하는 기능.
  * **신규 입력**: Cell Unavailable Time Data (CSV) — `cellunavailableTimeDown`[sec] 컬럼 기반. Traffic/Energy Stat/CM 데이터는 기존 'Data I/O & CM' 탭에서 로드한 것을 그대로 재사용.
  * **동작 시나리오 구현**:
    1. CM(Cell-RU Mapping) 데이터에서 `ru-board-id/ru-port-id/ru-cascade-id`(RU index) + `Board Type` 식별.
    2. Cell Unavailable Time(`cellunavailableTimeDown`)을 시간(Hourly) 단위로 합산 → `Down_Ratio`(=다운초/3600) 계산 → 사용자가 지정한 임계비율(기본 0.9) 이상이면 해당 Cell-시간을 `OFF`, 미만이면 `ON`으로 판정.
    3. 하나의 RU(Cascade)에 매핑된 여러 Cell의 상태를 종합해 RU 단위 시간별 상태(`ON`/`OFF`/`MIXED`)를 산출하고, `MIXED`(일부만 OFF)는 학습에서 제외.
    4. RU 단위 시간별 소모 에너지(Energy Stat의 `RuPowerTot/RuPowerCnt` 합산)와 Loading(Traffic의 `AirMacDLByte+AirMacULByte` 합, 또는 `UsedRB` 평균 — UI 콤보박스로 선택 가능)을 결합.
    5. **RU(bid/portid/cascade) 단위로 개별 회귀 학습** → Train(80%) : Validation(10%) : Test(10%)로 랜덤 분할(seed=42 고정) 후 Train 데이터로 1차 선형회귀(`np.polyfit` 기울기/절편) 학습, Val/Test로 R² 검증. RU 단위로 쪼개어 학습하면 동일 HW 내에서도 RU 개수만큼 학습 데이터가 늘어나는 효과가 있음.
    6. Cell OFF 시 예상 절감량 = (Cell ON 시간대 평균 소모 에너지) − (Cell OFF 시간대 평균 소모 에너지), RU 단위로 산출.
    7. 같은 `Board Type`(HW 종류)을 가진 RU들의 결과(기울기/절편/OFF 절감량)를 평균 내어 "해당 HW의 평균 성능"으로 요약.
  * **결과물**: RU 단위 상세 결과 Treeview, HW(Board Type) 평균 성능 Treeview, 시각화(Board Type별 Loading-Energy 산점도+평균 회귀선, Cell ON/OFF 평균 에너지 비교 막대그래프, Board Type별 평균 기울기/평균 OFF 절감량 막대그래프) — 스크롤 가능한 Canvas에 표시.
  * **리팩터링**: 기존 `_parse_energy_stat`을 `_parse_energy_stat_raw`(순수 파싱) + `_parse_energy_stat`(Energy Dashboard 날짜/시간 필터 적용, 기존 동작 100% 동일 유지)로 분리해 Learning Energy Curve 탭이 Energy Dashboard의 UI 필터 상태에 영향받지 않고 전체 기간 데이터로 학습하도록 함.
  * **부수적으로 발견/수정한 버그**: `_parse_energy_stat`(現 `_parse_energy_stat_raw`)의 컬럼 매핑에서 `cl.startswith('time')` 조건이 `TIMESTAMP`(소문자 `timestamp`도 `time`으로 시작)까지 잘못 가로채어 `Time` 컬럼으로 바꿔버리는 바람에, 실제 컬럼명이 `TIMESTAMP` 하나로 합쳐진 원본 데이터에서는 날짜/시간 파싱이 실패하던 잠재 버그를 발견. `timestamp`/`datetime`은 먼저 `TIMESTAMP`로 매핑하고, `Time`은 정확히 `time`인 경우에만 매핑하도록 수정(`_parse_energy_stat_raw`, 신규 `_parse_cell_unavail_stat` 양쪽 모두 적용).
  * **검증**: 이 서버 세션에는 pandas/tkinter가 설치되어 있지 않아 실제 GUI 구동 테스트는 불가. 대신 임시 가상환경에 pandas/numpy를 설치하고, 실제 코드와 동일한 컬럼 정규화·병합·회귀 로직을 재현한 스크립트를 작성해 알려진 정답값(true slope/intercept/off-saving)을 가진 합성 데이터로 End-to-End 검증 완료 — 추정된 기울기·절편·OFF 절감량이 시뮬레이션에 설정한 참값과 근사 일치함을 확인함. (실제 GUI 동작 및 실데이터 컬럼명 호환성은 로컬 PC에서 추가 확인 필요.)

## 5. 진행 중인 작업 및 다음 단계 (To-Do / Next Steps)
* 현재 상태: v1.5 - Learning Energy Curve 탭 신규 구현 완료 (로직 End-to-End 합성 데이터 검증 완료, GUI 실행 테스트는 로컬 확인 필요).
* 확인 필요:
  1. Google Drive(`VibeCoding/ESM`) 저장 방식 — 사용자가 이번 세션엔 스킵 요청, 추후 처리 방법 논의 필요.
  2. 실제 Cell Unavailable Time CSV의 실제 컬럼명(예: `cellunavailableTimeDown`, `NE unique id`, `Date`/`Time` 등)이 파서의 컬럼 매핑 규칙과 맞는지 실데이터로 확인 필요.
  3. GUI 환경에서 실제 파일로 "학습 실행" 버튼 동작 확인 (로컬 PC 필요).
* 다음 대기 작업: (사용자 요청 대기 중)

---
*Last Updated: 2026-07-01*
*AI Directive Status: Active (Always Read First, Always Update Post-Task)*
