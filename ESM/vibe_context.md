# 📡 ESM (Energy Saving Manager) Project Vibe Context

## 1. 프로젝트 개요 (Project Overview)

* **목적**: 이동통신(4G/5G) 네트워크의 Traffic Data(PM)와 Energy Stat Data를 분석하여, Energy Saving(ES) 적용 임계조건을 도출하고 예상 절감 에너지를 예측하는 GUI 기반 최적화 도구 개발.
* **주요 스택**: Python, Tkinter (UI), Pandas (데이터 처리), Matplotlib (시각화), scikit-learn(선택적 — Learning Energy Curve의 Isotonic Regression/MSE/MAE 계산에 사용, 미설치 시 numpy로 직접 구현한 폴백으로 자동 대체), scipy(선택적 — Learning Energy Curve의 지수포화 ExpSat 모델 `curve_fit`에 사용, 미설치 시 해당 모델만 비활성화)
* **핵심 지표**:
  * PM: `IP Tput`, `UsedRB`, `AirMacDLByte`, `AirMacULByte`
  * Energy: `RuPowerTot`, `RuPowerCnt` (RU별 시간당 소모 전력)
  * Efficiency: Energy Efficiency (EE) = (AirMacDLByte + AirMacULByte) / Consumed [Wh]
* **버전 파일 관리**: `ESM/esm_r11.py` ~ `ESM/esm_r15.py`(모두 과거 버전, 더 이상 수정하지 않음)와 `ESM/esm_r16.py`(최신 개발 버전)를 함께 보관한다. 새 기능/변경은 항상 최신 버전 파일에 반영하고, 이전 버전은 롤백/비교용으로 그대로 남겨둔다. 다음 라운드부터는 `esm_r16.py`를 복제해 `esm_r17.py`로 이어간다.

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
5. ⚡ Energy Dashboard — 소모 에너지 분석, 절감 예측 팝업(Gamma), **ES Level 시간별(15분 단위) IIR 시뮬레이션 팝업(v4.0/esm_r15.py 신규)**
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

* **[v2.0 / esm_r12.py] (2026-07-01) Learning Energy Curve 전면 개편 — Idle/PA off 레퍼런스 보정 + 드래그 앤 드롭 입력**
  * **파일**: `ESM/esm_r11.py`는 그대로 보존(수정 안 함), 이번 변경은 새로 만든 `ESM/esm_r12.py`에만 반영.
  * **입력 단순화 + 드래그 앤 드롭**: 기존 r11의 3개 파일(Traffic/Energy Stat/Cell Unavailable) 기반 설계를 폐기하고, **CM(Cell-RU Mapping) + 통합 학습데이터 CSV 1개**로 단순화. 두 입력 모두 Learning Energy Curve 탭 안의 Entry 위젯에 파일을 직접 드래그 앤 드롭할 수 있도록 `AppBase._bind_widget_drop()` 헬퍼를 추가(tkinterdnd2 기반, 위젯 단위 `drop_target_register`). CM 파일을 드롭하면 `_process_cm_ciq_data()`가 자동 실행됨. tkinterdnd2 미설치 환경에서는 기존 '찾기' 버튼으로 자동 대체.
  * **통합 학습데이터 스키마**: 한 행 = 한 Cell(`Ne unique id` + `Cnum`) × 시간. 컬럼: `Cellunavailabletimedown s`(초), `UsedRB`(총 사용 자원량), `UsedRB_t`(데이터 전송에 사용된 자원량), `nRB`(Cell에 할당된 총 자원량), `Consumed Power`. `_parse_learning_traindata()` 신규 파서로 처리.
  * **RU 단위 집계 로직** (요청하신 시나리오 그대로 구현):
    1. CM 정보로 Cell(`Cnum`) → RU path(`Bid`/`RuPort`/`Cascade`) 식별.
    2. 동일 `Ne unique id` 내에서 같은 RU path를 공유하는 여러 Cell의 값을 RU 단위로 통합: **Consumed Power·Cell off(초)는 산술 평균**, **Loading_traffic = ΣUsedRB_t / ΣnRB**, **Loading_total = ΣUsedRB / ΣnRB** (모두 셀 간 비율의 합으로 계산).
    3. Cell off 판정(Down 비율 ≥ 임계값, 기본 0.9)으로 RU-시간을 `PA off 구간`(OFF)과 `ON 구간`으로 분리하고, ON 구간을 다시 `Loading_traffic ≈ 0`(Idle 구간)과 `Loading_traffic > 0`(Active 구간)으로 세분.
  * **3가지 학습/보정 결과** (RU 단위로 개별 산출 후, 같은 Board Type의 RU끼리 평균 → "해당 HW의 평균 성능"):
    1. **Idle 보정**: Idle 구간 Consumed Power 실측 평균값을 산출하고, RU/MMU Spec 에디터(RU HW DB)의 `Idle` 레퍼런스(Lab test)와 비교해 Delta(실측-Ref) 및 보정 계수(실측/Ref)를 계산.
    2. **PA off 보정**: OFF 구간 Consumed Power 실측 평균값을 RU HW DB의 `PA off` 레퍼런스와 비교해 동일하게 Delta/보정 계수 산출.
    3. **Loading에 따른 소비전력 모델링**: Active 구간 데이터를 Train 8 : Val 1 : Test 1로 분할(seed 고정)하여 `Consumed Power = 기울기 × Loading_traffic + 절편` 1차 회귀 학습, R²(Val/Test)로 검증.
  * **치명적 버그 수정 (r11에도 있던 문제, r12에서 최초로 발견/수정)**: r11의 Learning Energy Curve는 RU를 `ru-board-id/ru-port-id/ru-cascade-id`만으로 식별하고 **`eNB_ID`(Ne unique id)를 키에서 빠뜨렸음**. Bid/RuPort/Cascade 번호는 eNB(사이트) 내부에서만 유일하므로, 서로 다른 사이트의 RU가 우연히 같은 번호 조합을 쓰면 서로 다른 물리 RU가 하나로 잘못 합쳐질 위험이 있었음. r12에서는 `ru_path_keys = ['eNB_ID'] + [ru-board-id, ru-port-id, ru-cascade-id]`로 전 구간(CM 매핑, RU 단위 집계, 회귀 학습 loop)을 통일해 수정. (r11 파일 자체는 과거 버전 보존 차원에서 수정하지 않음 — 사용법에서 r11의 Learning Energy Curve 탭은 이 문제를 인지하고 사용할 것.)
  * **시각화 개편**: Board Type별로 (a) Loading_traffic-Consumed Power 산점도 + 평균 회귀선 + 실측 Idle 평균선, (b) Idle/PA off Reference vs 실측 보정값 막대 비교를 표시하고, 하단 요약으로 (c) Board Type별 평균 기울기 막대, (d) Board Type별 Idle/PA off 보정폭(Delta) 막대를 추가.
  * **활용처**: 여기서 학습된 Idle/PA off 보정값과 Loading 기울기는 Energy Dashboard의 절감 예측 정확도를 높이는 데 사용할 수 있음(사용자 요청사항, 다음 라운드에 Energy Dashboard 연동 검토 필요).
  * **검증**: 이번에도 이 서버 세션엔 pandas/tkinter가 없어 GUI 구동은 불가. 임시 가상환경에 pandas/numpy를 설치하고 실제 코드와 동일한 로직을 재현한 스크립트로, 두 개의 서로 다른 eNB가 **일부러 동일한 Bid/RuPort/Cascade 번호(1/1/0)를 사용**하도록 합성 데이터를 만들어 검증 — RU가 올바르게 분리되어 유지됨을 확인(위 eNB_ID 버그 수정 검증)하고, 각 RU의 학습된 Slope/Intercept/Idle Measured/Idle Delta/PAoff Measured/PAoff Delta 값이 시뮬레이션에 설정한 참값과 근사 일치함을 확인함.

* **[v2.1 / esm_r12.py] (2026-07-01) Learning Energy Curve 결과 다운로드 + 시각화에 예측값/모델식 명시**
  * **CSV 다운로드 버튼 추가**: 학습 실행 버튼 아래에 "💾 RU 단위 상세 결과 CSV 다운로드"와 "💾 HW(Board Type) 요약 CSV 다운로드" 버튼을 추가(`_download_learn_result`). `self.learn_ru_df`/`self.learn_hw_df`를 그대로 CSV로 저장하며, 학습 실행 전에는 경고 메시지 표시.
  * **시각화에 예측값/모델식 명시**: 기존엔 그래프만 있고 수치가 눈에 잘 안 보였음 → 개선:
    * Loading_traffic vs Consumed Power 산점도에 학습된 Energy Curve 수식을 텍스트 박스로 직접 표시: `P ≈ {절편} + {기울기} × Loading_traffic, R²(Val)={값}`.
    * Idle/PA off Reference vs 실측 보정값 막대 위에 실제 수치(W) 라벨 표시.
    * 하단 요약의 Board Type별 평균 기울기 막대, Idle/PA off 보정폭(Delta) 막대에도 수치 라벨 표시(양수/음수 모두 라벨 위치 자동 조정).
  * **Energy Dashboard 연동은 보류**: 사용자 확인 결과, 학습 결과의 유의미성(실데이터 검증)을 먼저 확인한 뒤 적용 방법을 결정하기로 함 — 이번 라운드에는 연동하지 않음.
  * **검증**: matplotlib을 설치한 임시 가상환경에서 Agg(헤드리스) 백엔드로 신규 라벨/수식 텍스트 렌더링 로직만 별도 재현해 실행 — NaN 값이 섞인 Board Type(레퍼런스 데이터 일부 누락 케이스), 양/음수가 혼재된 Delta 막대 등 엣지 케이스에서도 예외 없이 렌더링됨을 확인.

* **[v2.2 / esm_r12.py] (2026-07-03) 학습데이터 2-파일 분리 + PA-shared-cell 기반 RU path 보정**
  * **학습데이터 파일 2개로 분리**: 실제 데이터는 집계 단위(index)가 서로 달라 파일이 1개가 아니라 2개임을 확인 — 반영.
    * **Cell 단위 학습데이터** (`self.learn_cell_file`): `Ne unique id` + `Cnum` 기준. `Cellunavailabletimedown s`(초), `UsedRB`, `UsedRB_t`, `nRB`.
    * **RU 단위 학습데이터** (`self.learn_ru_file`): `Ne unique id` + `Bid`/`RuPort`/`Cascade` 기준. `Consumed Power`.
    * 두 파일 모두 CSV 헤더를 보고 자동 분류하는 `_classify_learning_files_drop()`을 추가해, 두 입력창 중 어디에 드롭하든(한 번에 2개를 같이 드롭해도) 알맞은 변수에 채워지도록 구현. `_bind_widget_drop()`도 다중 파일 드롭(`on_drop(paths: list)`)을 지원하도록 확장. "📁 두 파일 한번에 선택" 버튼으로 파일 대화상자에서도 2개를 한 번에 선택 가능.
    * 이에 따라 Consumed Power는 더 이상 Cell 단위로 평균 낼 필요 없이(원래부터 RU path 단위로 이미 집계되어 있으므로) RU path + 시간 기준으로 바로 병합하도록 단순화(`_parse_learning_ru_file` → `ru_power_hourly` → 직접 merge). Cell off(초)/Loading_traffic/Loading_total만 여전히 "동일 RU path를 공유하는 Cell들의 평균/비율의 합"으로 집계.
  * **컬럼 매핑 확인**: `Ne unique id`는 `"ENB_1001"`처럼 접두어가 붙어도 기존 `_extract_int_id`(정규식으로 숫자만 추출)가 그대로 처리 가능함을 확인(추가 수정 불필요). `Cnum`=CM의 `cell-num`, `Bid/RuPort/Cascade`=CM의 `ru-board-id/ru-port-id/ru-cascade-id`, RU HW 종류는 CM의 `ru-board-type` 컬럼(정규화 시 `ruboardtype`으로 매칭되어 기존 로직이 이미 지원).
  * **PA-shared-cell 기반 RU path 보정 (신규 `_resolve_pa_shared_ru_paths`)**: CM에 있는 `PA-shared-cell` 컬럼은 해당 Cell이 다른 어떤 Cell과 PA(RU path)를 공유하는지 알려줌(`-1`이면 공유하는 Cell 없음). Union-Find로 PA를 공유하는 Cell들을 하나의 그룹으로 묶고, 그룹 내에서 Bid/RuPort/Cascade가 채워진 값을 대표값으로 삼아 그룹 전체에 적용 — 이렇게 하면 자기 자신의 Bid/RuPort/Cascade가 비어 있는 Cell(다른 Cell과 PA를 공유하기 때문에 별도 RU path가 없는 경우)도 올바른 RU path로 귀속되어 Loading 집계에서 누락되지 않음.
  * **검증**: 임시 가상환경에서, 한 eNB 안에 Cell 2개(20010은 자체 Bid/RuPort/Cascade=(5,1,0) 보유, 20011은 CM에 Bid/RuPort/Cascade가 비어 있고 `PA-shared-cell=20010`으로 20010과 공유) 시나리오를 합성 데이터로 만들어 검증 — PA-shared-cell 해석 후 두 Cell이 동일 RU path로 정확히 병합됨을 assert로 확인했고, Cell 파일(Loading/Cell off)과 RU 파일(Consumed Power)이 올바르게 merge되어 학습된 Slope/Intercept/Idle/PAoff 값이 설정한 참값과 근사 일치함을 확인함.

* **[v2.3 / esm_r13.py] (2026-07-03) 기울기(Slope) 분산 원인 진단용 세분화 분석 추가**
  * **배경**: 사용자가 실데이터로 학습을 돌려보니 같은 Board Type(RU HW) 안에서도 기울기가 RU마다 크게 갈리는 경우가 많다고 확인 — 원인 후보 2가지를 제시하고, 아직 어느 쪽이 맞는지 결론이 안 나서 우선 둘 다 분석/시각화해 비교할 수 있게 해달라는 요청.
  * **1) RU path 공유(Shared) vs 단독(Exclusive) 비교**: CM(`cm_by_cell`)에서 RU path(eNB_ID+Bid/RuPort/Cascade)별로 매핑된 Cell 개수를 세어, 2개 이상이면 `Shared (공유)`, 1개면 `Exclusive (단독)`으로 분류. Board Type × Shared 조합으로 그룹핑해 평균 기울기/절편/R² 등을 별도 집계(`hw_shared_df`, 신규 트리뷰 탭 "[r13] 공유여부별 비교").
  * **2) RU path 총 nRB 구간별 비교**: RU path에 실제 연결된 총 nRB(공유 시 여러 Cell의 nRB 합산값, `ru_dataset`의 `nRB_sum` 중앙값)를 RU별로 산출(`Total_nRB`)하고, Board Type별로 분위수 기반 구간(최대 3구간, 구간을 나눌 만큼 값이 다양하지 않으면 'All' 하나로)으로 나누어 평균 기울기 등을 집계(`hw_nrb_df`, 신규 `_assign_nrb_buckets()`, 신규 트리뷰 탭 "[r13] nRB 구간별 비교").
  * **시각화 추가**: 기존 Board Type별 요약 막대 아래에 한 행을 추가 — (a) RU별 (Total_nRB, Slope) 산점도(Board Type별 색상, 공유여부별 마커 모양 구분)로 기울기 분산이 nRB 규모나 공유여부와 관련 있는지 한눈에 확인 가능, (b) Board Type별 공유 vs 단독 평균 기울기 그룹 막대.
  * **결과물 다운로드**: "💾 공유여부별 비교 CSV 다운로드", "💾 nRB 구간별 비교 CSV 다운로드" 버튼 추가.
  * **검증**: 임시 가상환경에서, 같은 Board Type(TypeD)에 RU 3개(A: 단독·nRB=100·true slope=20, B: 단독·nRB=100·true slope=20, C: 2개 Cell이 공유·합산 nRB=200·true slope=40)를 합성해 검증 — 기존 방식대로 Board Type 하나로 뭉뚱그려 평균 내면 26.65로 어느 쪽 실제 값과도 다르게 왜곡되지만, r13의 공유여부별 분리 집계는 Exclusive=20.00(참값 일치), Shared=39.95(참값 40 근접)로 정확히 분리해 보여줌을 확인 — 이번에 추가한 세분화 분석이 실제로 "기울기가 여러 개로 갈리는" 원인을 진단하는 데 유효함을 검증함.
  * **주의**: 아직 사용자가 실데이터로 두 가지 방식(공유여부 vs nRB 구간) 중 어느 쪽이 더 설명력이 좋은지 판단 전 단계 — 다음 라운드에서 결과를 보고 하나로 확정하거나 두 기준을 조합하는 방향으로 더 세분화할 수 있음.

* **[v2.3.1 / esm_r13.py] (2026-07-03) 핫픽스: `module 'matplotlib.cm' has no attribute 'get_cmap'`**
  * **원인**: 사용자 로컬 환경의 matplotlib 버전(3.9+, 실제 확인된 버전 3.11)에서 `matplotlib.cm.get_cmap`(= `plt.cm.get_cmap`)이 완전히 제거됨. 코드 내 2곳(`_generate_core_policy`의 ES 산점도 색상 - Optimizer 탭, 원래 r11부터 있던 코드; r13에서 신규 추가한 `_render_learning_plots`의 Total_nRB vs Slope 진단 산점도)에서 이 API를 사용하고 있어 실행 시 즉시 오류 발생.
  * **수정**: `AppBase`에 `_get_qual_cmap(name, n)` 헬퍼를 추가 — 신형 API(`plt.colormaps[name].resampled(n)`, matplotlib 3.6+)를 우선 시도하고, 실패 시 구형 API(`plt.cm.get_cmap`)로 자동 폴백하여 신/구 matplotlib 버전 모두에서 동작하도록 함. 기존 2곳의 호출을 모두 이 헬퍼로 교체.
  * **검증**: 실제 오류를 재현한 matplotlib 3.11.0 가상환경에서 신형 API 경로가 정상 동작하고 기존과 동일하게 정수 인덱스로 색상을 얻을 수 있음을 확인.

* **[v2.4 / esm_r13.py] (2026-07-03) nRB 구간 분석 제거, 공유여부(Shared) 기준으로 결과 전면 재구성 + 3종 Energy Curve 모델링**
  * **배경**: v2.3에서 만든 두 진단(공유여부 vs nRB 구간) 중, 사용자가 **공유여부(Shared/Exclusive) 결과만 사용하기로 결정** — nRB 구간 분석은 제거하고, 대신 다른 모든 결과(HW 요약, Idle/PA off 보정값, Energy Curve 등)도 전부 공유여부 기준으로 나누어 보여달라는 요청. 또한 loading에 따른 Consumed Power 추정을 1차 함수 하나로만 하지 말고, 정확도를 위해 커브피팅 난이도가 다른 3종 모델을 그래프에 함께 그려서 눈으로 비교해 고를 수 있게 해달라는 요청.
  * **nRB 구간 분석 완전 제거**: `_assign_nrb_buckets()`, `Total_nRB`/`nRB_Bucket` 컬럼, `learn_hw_nrb_df`, "[r13] nRB 구간별 비교" 탭/다운로드 버튼을 모두 삭제.
  * **공유여부(Shared)가 결과 전체의 기본 축이 됨**: 기존에는 `hw_df`가 Board Type만으로 집계되고 `hw_shared_df`가 별도 진단표였는데, 이제 `hw_df` 자체를 `groupby(['Board Type', 'Shared'])`로 집계 — Idle/PA off 측정값·레퍼런스·Delta·보정계수, 3종 모델의 계수/R² 등 모든 요약 항목이 Board Type × 공유여부 단위로 나온다. 별도의 "공유여부별 비교" 탭은 이제 메인 HW 요약 탭 자체이므로 삭제(탭 2개 → RU 단위 상세 / HW(Board Type×공유여부) 요약 / 시각화, 총 3개로 정리).
  * **Loading → Consumed Power 3종 모델링** (모두 동일한 Train 8 : Val 1 : Test 1 분할로 공정 비교):
    1. **① 간단(선형)**: 기존 1차 회귀(`np.polyfit(...,1)`) — `Linear Slope`/`Linear Intercept`/`Linear R2_Val`/`Linear R2_Test`.
    2. **② 중간(2차 다항식)**: `np.polyfit(...,2)` — `Quad a2`/`Quad a1`/`Quad a0`/`Quad R2_Val`/`Quad R2_Test`. 완만한 곡률(예: 부하가 커질수록 증가폭이 커지거나 작아지는 패턴)을 반영.
    3. **③ 복잡/정확(Isotonic Regression, PAVA)**: 신규 `_pava_isotonic_fit()`(Pool Adjacent Violators Algorithm, numpy만으로 구현) + `_isotonic_predict()`(구간 밖은 양 끝값 고정한 선형보간). "Loading이 늘어날수록 소비전력이 줄어들 수 없다"는 물리적 제약을 그대로 반영하는 완전 비모수(non-parametric) 모델이라 다항식처럼 차수를 정하거나 오버피팅(Runge 현상)을 걱정할 필요 없이 가장 유연하게 실제 곡선 형태를 따라간다. sklearn 등 외부 ML 라이브러리를 새로 추가하지 않기 위해 numpy만으로 직접 구현(현장 PC의 pip 설치 제약을 고려한 선택).
    4. RU 단위 개별 학습은 기존처럼 유지(데이터량 증가 효과)하고, 그룹(HW×공유여부) 대표값은 선형/2차는 RU별 계수의 평균, Isotonic은 그룹 내 전체 RU의 Active 샘플을 모아 한 번에 재적합(비모수 모델은 계수 평균이 의미가 없으므로).
  * **시각화**: Board Type × 공유여부 조합마다 한 행씩, 왼쪽엔 산점도 위에 3종 모델 곡선을 함께 그려 R²(Val)와 함께 표시(①점선/②일점쇄선/③실선으로 구분), 오른쪽엔 기존 Idle/PA off 예측값 막대. 하단 요약에 (a) 그룹별 3종 모델 R²(Val) 비교 막대(어떤 모델이 어떤 그룹에서 더 잘 맞는지 한눈에 비교), (b) 그룹별 Idle/PA off 보정폭 막대.
  * **검증**: 임시 가상환경에서, (a) 실제로 곡선형(포화 곡선, Idle+Amp*(1-exp(-k·Loading))) 관계를 갖는 합성 데이터에서 선형 R²=0.83인 반면 2차=0.98, Isotonic=0.99로 유의미하게 개선됨을 확인(모델 복잡도가 실제로 정확도를 높여준다는 것을 검증), (b) 실제로 선형인 데이터에서는 3종 모두 비슷하게(~0.96~0.97) 잘 맞아 복잡한 모델이 불이익을 주지 않음을 확인, (c) 공유여부만으로 그룹핑되고 nRB 관련 컬럼이 전혀 남아있지 않음을 확인.

* **[v2.5 / esm_r13.py] (2026-07-03) 2차 다항식 → 로그스케일 모델 교체, MSE/MAE 지표 추가, sklearn 기반 "간단하지만 성능 좋은 모델" 추천 기능**
  * **배경**: 사용자 피드백 — 2차 다항식은(비단조/과도한 곡률 위험 등으로) 실사용이 어려워 보임, Isotonic은 특정 예외 케이스를 빼면 대체로 좋아 보임 → 2차 대신 로그스케일 모델을 요청. 또한 R² 외에 MSE/MAE도 함께 고려해서 모델을 추천해달라는 요청, 그리고 이제 sklearn을 사용해도 되니 간단하면서도 성능 좋은 모델을 찾아달라는 요청.
  * **② 중간 모델을 2차 다항식 → 로그스케일로 교체**: `Consumed Power = a + b·ln(Loading_traffic + ε)` (ε=1e-3, `np.polyfit`으로 로그변환된 x에 대해 1차 회귀). 부하가 커질수록 증가폭이 점점 완만해지는(체감) 물리적으로 흔한 패턴을 2개 파라미터로 안정적으로 표현하며, 2차 다항식과 달리 비단조(위로 볼록 후 감소)로 튈 위험이 없음. 컬럼: `Log a [W]`/`Log b [W]`/`Log R2_Val`/`Log R2_Test`/`Log MSE_Val`/`Log MSE_Test`/`Log MAE_Val`/`Log MAE_Test`.
  * **MSE/MAE 지표 추가**: 3종 모델(Linear/Log/Isotonic) 모두 R² 외에 MSE(평균제곱오차)·MAE(평균절대오차)를 Val/Test 양쪽에 대해 계산해 RU 단위 상세 결과·HW 요약 표에 모두 반영. sklearn이 설치되어 있으면 `sklearn.metrics.mean_squared_error`/`mean_absolute_error`를 쓰고(신규 `_regression_metrics()`), 없으면 numpy로 직접 계산하는 폴백으로 자동 전환.
  * **sklearn 채택**: 이제 sklearn 사용이 허용되어, Isotonic Regression은 자체 구현한 PAVA 대신 `sklearn.isotonic.IsotonicRegression(increasing=True, out_of_bounds='clip')`을 우선 사용(동률 처리·경계값 클리핑이 더 안정적)하도록 `_fit_isotonic()`을 추가. tkinterdnd2/tkcalendar와 동일한 패턴으로 `HAS_SKLEARN` 플래그를 두어, sklearn이 없는 환경에서는 기존 자체 구현(PAVA)·수동 MSE/MAE 계산으로 자동 폴백해 기능이 그대로 동작한다(현장 PC에 sklearn이 없어도 앱이 깨지지 않음).
  * **"간단하지만 성능 좋은 모델" 추천 기능 (신규 `_recommend_model()`)**: RU 단위·HW(Board Type×공유여부) 그룹 단위 모두에 `Recommended Model` 컬럼을 추가. 로직: Validation R²가 가장 높은 모델을 기준으로, 복잡도가 낮은 순서(Linear → Log → Isotonic)로 훑어서 최고 R²와 0.02 이내 차이가 나는 가장 간단한 모델을 채택(오컴의 면도날 — Isotonic이 아주 근소하게만 더 좋다면 굳이 안 씀). 모든 모델의 R²가 0 이하면 "N/A(적합도 낮음)"으로 표시.
  * **시각화**: 그래프 범례에 각 모델의 R²와 MSE를 함께 표시하고, 추천된 모델은 굵은 선(★ 표시)으로 강조. 그래프 제목에도 "— 추천: {모델명}"을 표시. 하단 요약 R² 비교 막대그래프에는 그룹별로 추천된 모델 위치에 ★ 표시를 얹어 한눈에 확인 가능.
  * **검증**: sklearn을 설치한 임시 가상환경에서 3가지 서로 다른 참값 형태(① 로그형 체감곡선 → Log 추천, ② 순수 선형 → Linear 추천(단순함 우선 규칙 확인), ③ 계단형(선형·로그 어느 쪽도 잘 안 맞는 형태) → Isotonic 추천)로 각각 합성 데이터를 만들어 추천 로직이 실제 곡선 형태에 맞게 정확히 동작함을 확인함.

*(아래 v2.6까지는 `esm_r13.py` 기준, v2.7부터는 새로 분기한 `esm_r14.py` 기준)*

* **[v2.6 / esm_r13.py] (2026-07-03) 시각화 UI 개선 + 로그모델 → 지수포화(ExpSat) 모델 교체 + Sector 내 Cell수 그룹핑 추가 + 한글 폰트 커밋 검토**
  * **배경**: 사용자가 한 턴에 4가지를 동시에 요청 — ① 시각화 탭 마우스 스크롤 미작동/그래프 크기 고정/간격 협소/라벨 겹침 UI 문제, ② 로그스케일 모델 제외하고 더 나은(복잡해도 무방한) 모델 추가, ③ Sector(=Cnum%10) 내 Cell수를 기준으로 한 세 번째 학습 그룹핑 축 추가(예: 3-Cell Sector끼리만 모아 학습 vs 1-Cell Sector끼리만 모아 학습), ④ 사용자가 직접 커밋한 한글 폰트 설정 코드 리뷰 및 보완.
  * **① 시각화 UI 개선**:
    * **마우스 스크롤 미작동 수정**: 임베드된 matplotlib 캔버스 위에서는 `canvas.bind()`만으로 휠 이벤트가 잡히지 않는 문제 — 스크롤 컨테이너(`plot_outer`)의 `<Enter>`/`<Leave>` 이벤트에서 `bind_all`/`unbind_all`로 마우스 휠 핸들러를 그때그때 등록/해제하는 방식으로 교체(Linux `Button-4`/`Button-5`, Windows/Mac `<MouseWheel>`의 `event.delta` 모두 처리).
    * **창 크기에 따른 그래프 크기 자동 조정**: `self.learning_plot_canvas`의 실제 픽셀 폭을 읽어 그림 폭(inch)을 동적으로 계산하는 `_get_plot_fig_width_inches()`를 추가하고, `<Configure>` 리사이즈 이벤트를 300ms 디바운스(`self.after`)해 학습을 다시 돌리지 않고 마지막 결과(`self.learn_hw_df`/`self.learn_pooled_active_points`)로 그래프만 다시 그리는 `_redraw_learning_plots_if_ready()`를 추가.
    * **그래프 간격/겹침 개선**: `plt.tight_layout()` → `constrained_layout=True` + `fig.set_constrained_layout_pads(w_pad=0.35, h_pad=0.55, hspace=0.18, wspace=0.14)`로 교체, 행당 높이를 4.6→5.8인치로 확대, 그래프 제목을 2줄로 나누고 폰트 크기를 10으로 낮춰 라벨 겹침을 줄임.
  * **② 로그모델 → 지수포화(Exponential Saturation) 모델 교체**: `Consumed Power = a − b·exp(−k·Loading_traffic)` (scipy `curve_fit`으로 비선형 최소자승 적합, 초기값은 데이터 범위 기반으로 자동 추정, 파라미터에 물리적으로 타당한 bounds 설정). RU 전력증폭기가 부하 증가에 따라 증가폭이 점점 줄고 특정 최대치(포화 전력)로 수렴하는 특성을 로그모델보다 물리적으로 더 정확히 표현. `HAS_SCIPY` 플래그(tkinterdnd2/tkcalendar/sklearn과 동일한 패턴)를 신규 추가해 scipy 미설치 환경에서도 앱이 깨지지 않고 해당 모델만 비활성화되도록 구성(`_fit_exp_saturation()`이 `None`을 반환하면 그 RU/그룹은 ExpSat 결과 없이 나머지 2종 모델로만 비교). 컬럼명 전체를 `Log *` → `ExpSat *`(a/b/k, R2/MSE/MAE Val/Test)로 교체하고 `_recommend_model` 기본 순서도 `('Linear', 'ExpSat', 'Isotonic')`로 변경.
  * **③ Sector 내 Cell수 그룹핑 추가**: CM의 `cell-num`(Cnum)을 10으로 나눈 나머지를 Sector로 정의(`Sector = Cnum % 10`)하고, 같은 `eNB_ID`+`Sector` 내 서로 다른 Cell 개수를 `Sector_Cell_Count`로 계산. RU path에 연결된 Cell(들)이 속한 Sector의 Cell수를 대표값(최빈값)으로 삼아 `Sector Group`(예: `3Cell/Sector`, `1Cell/Sector`) 레이블을 부여하고, 기존 `Board Type × Shared/Exclusive` 2축 그룹핑에 `Sector Group`을 세 번째 축으로 추가(`hw_df = ru_df.groupby(['Board Type', 'Shared', 'Sector Group'])`). 예: 같은 RU HW의 Shared RU라도 Sector 내 Cell이 3개인 대상만 모아 학습한 결과와 1개인 대상만 모아 학습한 결과를 분리해서 비교 가능. 시각화(`_render_learning_plots`)도 3-tuple 그룹 순회로 갱신, 그래프 제목/하단 요약 라벨에 Sector Group 포함.
  * **④ 한글 폰트 커밋 검토/보완**: 사용자가 직접 커밋한 `plt.rcParams['font.family'] = 'Malgun Gothic'`은 Windows 전용 폰트만 지정하고 `axes.unicode_minus` 설정이 빠져 있어, macOS/Linux 환경에서는 한글이 깨지고 음수 부호(-)도 깨질 위험이 있었음 → `_KOREAN_FONT_CANDIDATES`(Malgun Gothic/AppleGothic/NanumGothic/Noto Sans CJK KR/Noto Sans KR) 리스트로 교체해 `matplotlib.font_manager`에서 실제 설치된 폰트를 확인 후 우선순위대로 선택하고, 하나도 없으면 경고 로그만 남기고 넘어가도록(크래시 방지) 수정. `axes.unicode_minus = False`도 함께 추가.
  * **검증**: 임시 가상환경(scipy/sklearn/numpy/pandas 설치)에서 4가지 모두 로직 단위 검증 — (a) 참값이 지수포화 곡선인 합성 데이터에서 `curve_fit`이 실제 a/b/k 값을 15% 오차 이내로 정확히 복원하고 R²(Val)가 Linear(0.76)보다 크게 높음(0.996)을 확인, (b) 참값이 순수 선형인 데이터에서는 여전히 Linear가 추천됨(오컴의 면도날 규칙 유지 확인), (c) 데이터가 3개 미만이거나 상수인 퇴화 케이스에서 `_fit_exp_saturation`이 예외 없이 `None`을 반환함을 확인, (d) `Cnum % 10` 기준 Sector 그룹핑이 3-Cell/1-Cell Sector를 정확히 구분하고 `Board Type × Shared × Sector Group` 3축 groupby가 그룹을 올바르게 분리 유지함을 확인. matplotlib UI 변경(스크롤/리사이즈/간격)은 앞선 라운드에서 이미 matplotlib 3.11 환경으로 렌더링 검증 완료된 패턴을 그대로 재사용.

* **[v2.7 / esm_r14.py] (2026-07-06) Linear/ExpSat 모델을 "수식(Formula)" 표로 정리 + 다운로드, Sector Group 일반화 방향 논의**
  * **배경**: 사용자가 시각화(그래프)로만 보던 Learning Energy Curve 결과를, loading 값만 넣으면 바로 ConsumedPower를 계산할 수 있는 "사용 가능한" 형태(수식/표)로 가져가고 싶다고 요청. 또한 Sector Group(1Cell/Sector vs 3Cell/Sector 등)에 따라 결과가 갈리는 문제를 더 일반적인 형태로 개선할 아이디어를 요청(사용자 제안: UsedRB당 소모전력 지표, 또는 nRB에 대한 함수로 표현).
  * **버전 분기**: 핵심 개발 원칙(2항)에 따라 `esm_r13.py`(과거 버전, 더 이상 수정 안 함)를 그대로 복제해 `esm_r14.py`(신규 최신 개발 버전)로 시작. 이번 라운드부터 모든 변경은 `esm_r14.py`에만 반영.
  * **Energy Curve 수식(Formula) 표 추가** (사용자 요청 1번):
    * 신규 `_build_formula_df(hw_df)`: HW(Board Type × Shared × Sector Group) 요약(`hw_df`)의 Linear/ExpSat 계수를, `ConsumedPower = 절편 + 기울기 × Loading_traffic`(Linear) / `ConsumedPower = a − b × exp(−k × Loading_traffic)`(ExpSat) 형태의 텍스트 수식 문자열로 변환한 `self.learn_formula_df`를 생성. Board Type/Shared/Sector Group/RU Count/Recommended Model과 함께 R²·MSE·MAE(Val), 원본 계수(Slope/Intercept, a/b/k)도 그대로 포함해 사람이 읽는 수식과 프로그램적으로 재사용 가능한 계수를 한 표에서 모두 제공.
    * Isotonic은 계수가 없는 비모수(non-parametric) 모델이라 닫힌 형태 수식으로 표현할 수 없으므로 이 표에는 포함하지 않고, 해당 그룹의 `Recommended Model`이 Isotonic이면 `Note` 컬럼에 "수식 없음 — RU 단위 상세 결과/시각화의 곡선 참고" 안내만 표시.
    * Learning Energy Curve 결과 탭에 " 📐 Energy Curve 수식(Formula) " 탭을 신규 추가(RU 단위 상세 / HW 요약 / **수식(Formula)** / 시각화, 총 4개 탭)하고, `Loading_traffic = ΣUsedRB_t/ΣnRB` 정의를 안내 문구로 표시. "💾 Energy Curve 수식(Formula) CSV 다운로드" 버튼 추가.
  * **Sector Group 일반화 — Active_RB(절대 활성 RB) 축 병행 진단 추가** (사용자 요청 2번, 사용자가 "지금 병행 진단 추가"를 선택해 바로 구현):
    * 현재 `Loading_traffic`은 RU path에 연결된 총 nRB로 나눈 **비율(0~1)** 이라, 셀 1개짜리 RU path와 3개짜리(3Cell/Sector) RU path가 같은 Loading_traffic 값이어도 실제로 구동되는 절대 RB 개수(및 PA/캐리어 개수)는 서로 다름 — 이 절대 규모 차이가 Sector Group별 기울기/ExpSat 곡선이 갈리는 주된 원인으로 추정.
    * 사용자 제안 ① "UsedRB당 소모전력"은 Loading이 0에 가까울 때 분모가 0에 가까워져 값이 발산하므로 회귀의 x/y축으로는 채택하지 않음(향후 별도 효율 KPI로는 유효할 수 있음, 이번 라운드에는 미구현).
    * 사용자 제안 ② "nRB에 대한 함수로 표현"을 채택 — 비율(`Loading_traffic`) 외에 **`Active_RB`(=ΣUsedRB_t, 나누기 전 절대 활성 RB 수)** 를 두 번째 회귀 입력 축으로 신규 추가하고, 기존 축(비율)은 그대로 유지한 채 두 축을 **나란히 병행 학습**하도록 구현(v2.3→v2.4의 "공유여부 vs nRB구간" 진단과 동일한 패턴).
    * **구현 상세**: 기존 per-RU 학습 로직(Linear/ExpSat/Isotonic 3종 모델 적합 + 지표 계산)을 신규 헬퍼 `_fit_three_models(x_train,y_train,x_val,y_val,x_test,y_test)`로 추출해, `Loading_traffic`(비율)과 `Active_RB`(절대, `ru_loading_hourly['Active_RB'] = UsedRB_t_sum`) 양쪽에 **동일한 Train/Val/Test 분할**을 재사용해 공정 비교. RU 단위 결과(`ru_df`)에 `RB Linear/ExpSat/Isotonic *`, `RB Recommended Model` 컬럼을 추가하고, HW 요약(`hw_df`)에도 동일하게 `RB Avg *` 컬럼과 `RB Recommended Model`을 추가. 그룹별로 두 축 중 어느 쪽 최고 R²(Val)가 더 높은지 비교하는 `Best R2 (Loading_traffic 비율)` / `Best R2 (Active_RB 절대)` / `Better Axis (R² 기준)`(차이 ≤0.02면 "유사") 컬럼을 신규 추가해, 실데이터에서 어느 축이 Sector Group 차이를 더 잘 흡수하는지 한눈에 판단할 수 있게 함.
    * **수식 표 확장**: `_build_formula_df`에 `Linear/ExpSat Formula (Active_RB)` 컬럼과 `Better Axis` 컬럼을 추가해, 두 축의 수식을 한 표에서 비교 가능.
    * **시각화 확장**: 기존 산점도+3모델 그리기 로직을 `_plot_axis_models()` 공용 헬퍼로 추출해 두 축(비율/절대)에 재사용. 그룹당 그래프 배치를 2열→3열(① Loading_traffic 산점도 ② Active_RB 산점도 ③ Idle/PA off 막대)로 확장하고, 하단 요약도 R²비교 막대를 축별로 하나씩(비율/절대) 나란히 표시.
    * **다음 단계**: 실데이터로 학습을 돌려 `Better Axis` 컬럼과 두 산점도(비율 vs 절대)를 비교해, Active_RB 축이 Sector Group 차이를 뚜렷하게 줄여준다면 다음 라운드(`esm_r15.py`)에서 Sector Group을 그룹핑 축에서 제거하고 Active_RB 기반 단일 커브로 정리하는 것을 검토.
  * **검증**: pandas/numpy만 설치된 환경(scipy/sklearn 미설치, `HAS_SCIPY=False`/`HAS_SKLEARN=False` 상태)에서 (a) `_build_formula_df`를 합성 `hw_df`(양/음의 기울기, ExpSat 계수 NaN 케이스, Isotonic 추천 케이스 포함)로 단위 테스트해 수식 문자열 포맷·부호 처리·N/A 처리·Note 안내가 모두 올바름을 확인, (b) 실제 GUI 앱(`ESAnalyzerApp`)을 기동해 신규 "수식(Formula)" 탭/Treeview가 정상 생성됨을 확인, (c) CM(단독 RU path 1개, nRB_sum=100 + 공유 RU path 1개, nRB_sum=200, 참값 slope=50/intercept=110)과 Cell/RU 단위 학습데이터를 합성해 `_run_energy_curve_learning()`을 실제로 실행 — 복원된 Linear 계수(비율 축 slope≈50.2/49.6, intercept≈109.8/110.0)가 참값과 근접했고, **비율 축과 Active_RB 축의 계수가 수학적으로 정확히 일치**함을 확인(`RB Linear Slope × nRB_sum` = 비율 축 slope, 두 RU path 모두 오차 0.01 이내), `learn_formula_df`의 두 축 수식 문자열이 각 계수와 일치함을 확인(scipy 미설치라 ExpSat 결과는 예상대로 N/A로 표시됨), (d) 시각화 렌더링(matplotlib 3.10, 3열×(그룹수+1)행 그리드)이 예외 없이 완료되고 캔버스 위젯이 정상 생성됨을 확인 — 렌더링 과정에서 컬럼명 접두어 순서 버그(`Avg RB ...` vs `RB Avg ...`) 1건을 발견해 즉시 수정함. GUI 드래그앤드롭/실데이터 컬럼명 호환은 이전 라운드와 동일하게 로컬 PC 확인 필요.

* **[v2.8 / esm_r14.py] (2026-07-06) 버그 수정: CSV 다운로드 시 한글/특수문자 깨짐(엑셀 인코딩 오인식)**
  * **배경**: 사용자가 Energy Curve 수식(Formula) CSV를 다운로드해 열어보니 `-` 기호와 한글 내용이 깨져 보인다고 보고. 사용자는 "저장 폰트"를 맑은 고딕 같은 일반 폰트로 바꿔달라고 표현했지만, CSV는 폰트 정보를 갖지 않는 순수 텍스트 파일이라 실제 원인은 폰트가 아니라 **인코딩**이었음.
  * **원인**: 모든 `to_csv()` 호출이 인코딩을 지정하지 않아 BOM 없는 UTF-8로 저장됨. Excel은 BOM이 없는 CSV를 열 때 파일 내용을 UTF-8이 아니라 OS의 로컬 코드페이지(한국어 Windows 기준 CP949/EUC-KR)로 오인식하므로, UTF-8로 인코딩된 한글과 일부 특수문자(수식 문자열의 `×`, 음수 부호 등)가 깨져 보임.
  * **수정**: `_download_learn_result`(RU 상세/HW 요약/**Formula** CSV 다운로드 공용 함수), `_download_energy_intermediate`, Sector 결과 CSV 저장(`save_csv`), 최종 결과 파일 저장(`save_files`, `ESMOutput_Result*.csv` 3종) 등 파일 내 모든 `to_csv()` 호출에 `encoding='utf-8-sig'`(UTF-8 + BOM)를 추가 — Excel이 BOM을 보고 UTF-8임을 올바르게 인식해 한글/특수문자가 정상 표시됨.
  * **검증**: 로컬 PC 실행 환경에서 실제로 Excel/메모장으로 열어 한글·`×`·`-` 표시를 확인하는 것을 권장(이 세션에는 Excel 실행 환경이 없어 코드 레벨 수정만 확인).

* **[v2.9 / esm_r14.py] (2026-07-06) 버그 수정: Data I/O & CM 탭 드래그 앤 드롭 시 Traffic Data가 Energy Stat Data로 오분류**
  * **배경**: 사용자가 "Data I/O & CM" 탭에 CSV를 드래그 앤 드롭하면 Traffic Data 파일도 항상 Energy Stat Data 입력란에 채워지는 오류를 보고. 두 파일 모두 확장자가 `.csv`라 `handle_file_drop`이 파일명 키워드만으로 구분하는데, 기존 Energy Stat 판정 키워드 목록(`['energy', 'stat', 'power', 'pm', 'ru']`)의 `'stat'`/`'pm'`이 너무 포괄적이어서(PM=Performance Monitoring으로 흔히 불리는 Traffic 파일명에도 자주 포함) Traffic 파일까지 Energy Stat으로 잘못 분류되고 있었음.
  * **수정**: `AppBase.handle_file_drop`을 두 개의 명확한 키워드 세트로 교체 — 파일명에 `'energy'`/`'power'`/`'ru'`가 있으면 Energy Stat Data, `'traffic'`/`'sector'`/`'group'`이 있으면 Traffic Data로 분류(둘 다 매치되거나 둘 다 매치 안 되면 기존과 동일하게 Traffic Data로 기본 처리).
  * **검증**: 분류 로직만 별도로 추출해 `PM_Traffic_*.csv`(→Traffic), `RU_Power_Stat_*.csv`(→Energy), `Sector_Group_Traffic.csv`(→Traffic), `EnergyStat.csv`/`RUPowerData.csv`(→Energy), 키워드 없는 파일명(→Traffic, 기존 기본값 유지) 등 대표 케이스로 단위 테스트해 의도대로 분류됨을 확인.

* **[v3.0 / esm_r14.py] (2026-07-06) Optimizer 기능 확장: Advanced Settings 파라미터 추가 + ESM Output Result 열 재구성 + Energy Dashboard용 24시간 Rawdata**
  * **배경**: 사용자가 Optimizer 결과(ESM Output Result)의 RB/PRB 임계값 표현을 더 세밀하게(진입/이탈 히스테리시스) 다듬고, Energy Dashboard가 하루 24시간 전체를 놓고 절감량을 계산할 수 있도록 ES 윈도우 밖 시간까지 포함한 원본 데이터를 만들어달라고 요청. 4가지를 한 번에 요청: (1) Advanced Settings 파라미터 3개 추가, (2) 기존 파라미터 이름에 "_LTE" 태그, (3) ESM Output Result 열 구성 변경, (4) Energy Dashboard용 24시간 Rawdata 추가.
  * **(1) Advanced Settings 신규 파라미터 3개** (`_build_main_ui`, 모두 configurable):
    * `RB Threshold Margin_LTE`(기본값 15) — Leaving Th_PRB 계산에 바로 사용(아래 (3) 참조).
    * `Required IP Tput Low Util_LTE`(기본값 1), `N_allowedEScell_LTE`(기본값 6) — 이번 라운드에는 설정값만 추가하고 계산 로직에는 아직 연결하지 않음(사용자 요청 문구가 "코드 수정이 다 끝나면 신규 기능에 대해 요청할게"였기 때문에, 이 두 파라미터의 구체적 활용 방식은 다음 라운드 요청을 기다리는 중).
  * **(2) 기존 파라미터 라벨에 "_LTE" 태그 추가**: 최소보장 목표 IP Tput/IP Tput Margin/Guarantee Ratio/Threshold RBlowutil/Coe_low/RBLow Multiplier 6개 라벨에 "_LTE" 접미사 추가(향후 NR 등 다른 RAT 파라미터와 구분하기 위한 태그, 내부 변수명(`self.tput_threshold` 등)은 변경하지 않고 UI 라벨 텍스트만 수정).
  * **(3) ESM Output Result 열 재구성**: 'PRBusage Threshold' 한 열을 4개 열로 확장(신규 `_build_th_cols` 헬퍼, `_generate_core_policy` 내 5곳 모두 적용):
    * `Entering Th_PRB` = RBThreshold/total_rb*100 (기존 PRBusage Threshold와 동일한 계산).
    * `Leaving Th_PRB` = (RBThreshold + RB Threshold Margin_LTE)/total_rb/0.01 — Entering보다 더 높은 RB 사용률에서 ES를 벗어나도록 하는 히스테리시스 여유분.
    * `Entering Th_Tput` = 최소보장 목표 IP Tput_LTE + IP Tput Margin_LTE (기존에 이미 `t_target`으로 계산되던 값).
    * `Leaving Th_Tput` = 최소보장 목표 IP Tput_LTE.
    * ES Level 7(정책 없음, RBThreshold=-1)이거나 total_rb=0이면 4개 모두 -1로 '해당 없음' 표시(기존 -1 컨벤션 유지).
  * **(4) Energy Dashboard용 24시간 Rawdata 신규 추가** (신규 `_build_window_rawdata`): 기존 Optimizer의 "Intermediate Data"는 ES 운영시간 윈도우로 필터링된 시간만 포함했는데, Energy Dashboard가 하루 전체(윈도우 밖 시간 포함)를 봐야 하므로 필터링 이전의 전체 `group`을 기반으로 새 데이터셋을 만듦:
    * `Time` 다음 열에 `ES_Window_Index`를 추가 — 해당 시간이 속한 ES operation window를 식별(자동 모드는 카테고리 번호 1(Low Util)/2(ES Level2)/3(ES Level1)를 그대로 사용, 수동 모드는 윈도우가 하나뿐이라 항상 1, 어떤 윈도우에도 속하지 않는 시간(No ES 시간대 등)은 0).
    * `Alpha`/`DRB_L{n}`/`RB_Threshold_L{n}`을 해당 윈도우에서 학습된 값으로 채움(윈도우가 다르면 값도 다름 — 사용자가 기대한 대로 윈도우별로 다른 DRB_L/RB Threshold가 적용됨). 윈도우 밖 시간은 ES 정책이 없으므로 NaN.
    * `_do_manual_mode`/`_do_auto_mode`가 이제 `(results, intermediates, raw_df)` 3-tuple을 반환하도록 변경, `run_analysis`에서 취합해 `self.latest_optimizer_rawdata`에 보관.
    * **Optimizer 탭에는 표시하지 않음**(사용자 요청) — `show_results_window`의 트리뷰 탭 구성(ESM Output Result/Intermediate Data/Auto Time Eval O/X)은 그대로 유지하고, raw_df는 "💾 최종 결과 파일(CSV) 저장" 클릭 시 `ESMOutput_RawData_EnergyDashboard.csv`로만 함께 저장.
    * Energy Dashboard 쪽 코드에서 향후 "Rawdata"라고 언급되면 이 `self.latest_optimizer_rawdata`(=`ESMOutput_RawData_EnergyDashboard.csv`)를 가리키는 것으로 이해하고 작업하기로 함.
  * **검증**: pandas/numpy만으로 `_build_th_cols`/`_build_window_rawdata`를 가짜 self(간단한 `.get()` 속성만 가진 객체)로 단위 테스트 — Entering/Leaving Th_PRB·Th_Tput 계산값이 손계산과 일치하고 ES Level 7의 -1 처리가 정확함을 확인했고, 2개 윈도우(0~3시=Cat1, 20~23시=Cat3)로 구성한 24시간 합성 데이터에서 `ES_Window_Index`/`Alpha`/`DRB_L{n}`/`RB_Threshold_L{n}`이 각 윈도우 안에서는 그 윈도우의 값으로, 윈도우 밖(4~19시)에서는 0/NaN으로 정확히 채워짐을 확인. `python -m py_compile` 통과. GUI 실행(Advanced Settings 새 항목 표출, 실제 트래픽 데이터로 ESM Output Result의 4개 신규 열/저장되는 RawData CSV 확인)은 로컬 PC에서 추가 확인 필요.
  * **사용자 확인 요청 사항**: 사용자가 "맞게 동작하는 거지? 확인해줘"라고 명시적으로 질문한 부분 — (a) `ES_Window_Index`를 자동 모드 카테고리 번호(1/2/3)로, 수동 모드는 항상 1로 정한 것이 맞는지 → **사용자가 "맞음, 이대로 사용" 확정**. (b) 윈도우 밖 시간의 DRB_L/RB_Threshold_L을 NaN(정책 없음)으로 둔 것 → 별도 이견 없이 유지. (c) `Required IP Tput Low Util_LTE`/`N_allowedEScell_LTE` 활용 방식 → 아래 v3.1에서 확정.

* **[v3.1 / esm_r14.py] (2026-07-06) 후속 확인: Required IP Tput Low Util_LTE / N_allowedEScell_LTE 계산 로직 연결**
  * **배경**: v3.0에서 두 파라미터를 설정값만 추가하고 계산에 연결하지 않았던 것에 대해 사용자가 구체적 활용 방식을 알려줌.
  * **Required IP Tput Low Util_LTE**: Low Util 윈도우(`is_low_util=True`)의 Entering/Leaving Th_Tput은 일반 ES Level과 달리 최소보장 목표 IP Tput_LTE가 아니라 이 파라미터를 기준으로 계산 — Entering Th_Tput = Required IP Tput Low Util_LTE + IP Tput Margin_LTE, Leaving Th_Tput = Required IP Tput Low Util_LTE. `_build_th_cols`에 `is_low_util` 인자를 추가해 분기 처리(일반 ES Level 호출부는 그대로, Low Util 분기의 두 호출부 중 성공 케이스에 `is_low_util=True` 전달; ES Level 7(-1) 케이스는 어차피 4열 모두 -1로 조기 반환되어 플래그가 결과에 영향 없음).
  * **N_allowedEScell_LTE**: "Max ES Level 상한" 파라미터로 확정 — 셀에 실제 할당 가능한 ES level(양수 밴드 개수, `max_n`)이 이 값보다 크면 `max_n = min(max_n, N_allowedEScell_LTE)`로 낮춤(`run_analysis`에서 `max_n` 산출 직후 적용). 예: 밴드가 6개라 원래 6레벨까지 나올 수 있어도 N_allowedEScell_LTE=4면 ES Level은 최대 4까지만 산출.
  * **검증**: 가짜 self로 `_build_th_cols(..., is_low_util=True)`가 Required IP Tput Low Util_LTE(1.0)+IP Tput Margin_LTE(1.0)=2.0(Entering)/1.0(Leaving)을 반환하고 `is_low_util=False`(기본값)는 기존 t_target/tput_threshold 기준을 그대로 반환함을 확인. 실제 GUI 앱으로 양수 밴드 3개(B1/B2/B3)를 가진 셀에 `N_allowedEScell_LTE=2`를 설정해 `run_analysis()`를 실행 — 결과의 `Max ES Level`이 3이 아닌 2로 나오고 `ES Level` 값도 {1,2}만 존재(3이 산출되지 않음)함을 확인.

*(v3.1까지는 `esm_r14.py` 기준, v4.0부터는 새로 분기한 `esm_r15.py` 기준)*

* **[v4.0 / esm_r15.py] (2026-07-06) Energy Dashboard 신규 기능: ES Level 시간별(15분 단위) IIR 시뮬레이션**
  * **배경**: 기존 에너지 절감 예측(`_calc_all_savings`)은 분포 특성(Nc2, 시간대별 누적 카운트) 기반 추정이라 "시간의 흐름에 따라 ES level이 실제로 어떻게 변하는지"를 반영하지 못해 오차가 있음 — 사용자가 정확도를 높이기 위해 시간 흐름에 따라 ES 적용 조건을 실제로 시뮬레이션하는 기능을 요청. 버전 분기 원칙(1항)에 따라 `esm_r14.py`를 복제해 `esm_r15.py`로 시작(이번 라운드부터 모든 변경은 `esm_r15.py`에만 반영). `esm_r14.py`에 있던 관련 코드 주석의 "[r15]" 태그는 실제로는 `esm_r14.py`에서 작업했던 것이라 "[r14]"로 정정.
  * **신규 Advanced Settings**: `IIR Filter Coefficient Tput_LTE`/`IIR Filter Coefficient PRB_LTE`(둘 다 기본값 0.25) 추가 — cmIPTput/UsedRB_t_adj를 15분마다 지수평활(EWMA)해 순간적인 튐으로 ES level이 매 스텝 널뛰는 것을 방지.
  * **Rawdata 재사용/재생성 로직** (신규 `_get_cell_window_defs` + `_build_rawdata_for_period`): Energy Dashboard에 새 "⏱ ES Level 시간별 시뮬레이션" 버튼(팝업)을 추가하고, 팝업 안에서 시뮬레이션 대상 기간(날짜 범위)을 지정할 수 있게 함.
    * Optimizer 실행 시 사용한 기간을 `run_analysis`에서 `self.latest_optimizer_period = (start_date, end_date, exclude_dates_str)`로 기록해두고, 시뮬레이션 기간이 이와 완전히 같으면(시작일=종료일=제외 날짜 모두 동일) `self.latest_optimizer_rawdata`를 그대로 재사용.
    * 다르면 **Optimizer를 재실행하지 않고** 트래픽 데이터만 새로 읽어, 이미 도출된 ES 윈도우/레벨 정의(어느 시간이 어느 윈도우인지는 `self.latest_optimizer_rawdata`의 시간→`ES_Window_Index` 매핑에서, 레벨별 DRBn/RBThreshold/Entering·Leaving Th_PRB·Th_Tput은 `self.latest_optimizer_results`에서 각각 복원)를 그대로 적용해 새 Rawdata를 생성. 이렇게 하면 Optimizer 결과물(ES level 대상 target cell, DRB 등)을 재사용하면서도 다른 기간의 실제 트래픽에 대한 Rawdata를 얻을 수 있음.
  * **Rawdata 스키마 확장**(`_build_window_rawdata` 수정): 기존 `DRB_L{n}`/`RB_Threshold_L{n}`/`Alpha`에 더해, 레벨별 `Entering/Leaving Th_PRB_L{n}`·`Th_Tput_L{n}`(ESM Output Result와 동일 값)과 그 시점 raw 트래픽 기준 `Pred_IPTput_Mbps_L{n}`/`Raw_RB_Margin_L{n}`(Low Util 윈도우도 Alpha=1로 동일 공식 적용)을 모든 레벨에 열로 추가 — 시뮬레이션이 매 스텝 다음 레벨의 임계값/예측치를 열 조회만으로 즉시 얻을 수 있게 함.
  * **핵심 시뮬레이션 엔진**(신규 `_run_es_level_simulation`): (eNodeBID, Sector) 셀 단위로 15분 스텝마다—
    1. ES_Window_Index==0(운영 윈도우 밖)이거나 직전 스텝과 윈도우가 바뀌면 Level을 Initial level(0, 하드코딩 — 추후 최적화 기능으로 발전 예정)로 재시작하고 IIR만 raw 값으로 계속 갱신(레벨 결정 로직은 건너뜀).
    2. 같은 윈도우 안이면: **감소** — `cmIPTput_iir(n) < Leaving Th_Tput(Curr)` 또는 `UsedRB_t_adj_iir(n) > Leaving Th_PRB(Curr)`면 `Next=max(Curr-1,0)`(Tput 조건으로 감소한 경우는 IP Tput 불만족으로 별도 누적) → 아니면 **증가** — `Pred_IPTput_Mbps_L(Curr+1)`(raw, 그 시점 원본 UsedRB_t_adj/SP 기준)이 `Entering Th_Tput(Curr+1)` 이상이고 `UsedRB_t_adj_iir(n)`이 `Entering Th_PRB(Curr+1)` 이하면 `Next=min(Curr+1,max_n)` → 아니면 **유지**.
    3. 결정된 Next 레벨에 따라 다음 스텝의 cmIPTput 입력을 갱신 — Next=0이면 raw 그대로, Next>0이면 `max(raw_cmIPTput*(1-DRB_L(Next)/(total_rb-raw_UsedRB)),0)`로 보정(전력 절감의 반사실적 효과 반영, UsedRB_t_adj는 항상 raw 사용) — 이 값이 다음 IIR 입력이 됨.
  * **결과물**: 셀별 요약(레벨 0..max_n 누적 스텝 카운트, IP Tput 불만족 누적 카운트, 총/ES 활성 스텝 수)과 15분 단위 상세 타임라인(Applied_ES_Level/cmIPTput_IIR/UsedRB_t_adj_IIR/cmIPTput_Simulated/Tput_Violation)을 팝업 표 + CSV(요약+타임라인 2개 파일) 다운로드로 제공. **Watt-hour 절감량 환산은 이번 라운드에는 미구현** — 사용자가 이 시뮬레이션 결과(레벨 궤적, 불만족 발생 빈도)의 타당성을 먼저 확인한 뒤 다음 라운드에 반영 여부/방법을 결정하기로 함.
  * **사용자 확인 완료 사항**(구현 전 3가지 질문 → 모두 "권장안대로" 확정): (a) `Pred_IPTput_Mbps_L(Curr+1)` 계산은 raw(비-IIR) UsedRB_t_adj/SP 사용. (b) "동일 기간" 판정은 시작일/종료일/제외 날짜 모두 일치. (c) 결과는 Energy Dashboard의 새 버튼+팝업으로 표시(기존 "Energy Saving Prediction" 팝업과는 별도).
  * **검증**: `_run_es_level_simulation`을 가짜 self(iir 계수만 있는 객체)와 손으로 설계한 6-스텝 합성 Rawdata(윈도우 내내 유리한 조건→0→1→2 증가, PRB Leaving 조건으로 2→1 감소, Tput Leaving 조건으로 1→0 감소(Tput_Violation 플래그 확인), 마지막 스텝은 윈도우 이탈로 0 유지)로 단위 테스트해 레벨 궤적 `[0,1,2,1,0,0]`과 IIR 값이 손계산과 소수점까지 정확히 일치함을 확인. 실제 GUI 앱으로 3일치 15분 단위 합성 트래픽에 Optimizer를 실행한 뒤, Optimizer와 동일 기간을 넣으면 `reused=True`로 기존 Rawdata를 그대로 반환하고, 다른 날짜(Optimizer 실행에 없던 3일차)를 넣으면 `reused=False`로 Optimizer를 재실행하지 않고 트래픽만 다시 읽어 15분 간격(하루 96행) Rawdata를 새로 만들며 `ES_Window_Index`/`DRB_L`/`Entering Th_PRB` 등이 기존 학습된 윈도우 정의와 정확히 일치함을 확인 — 이 Rawdata로 시뮬레이션까지 오류 없이 실행됨을 확인. `python -m py_compile` 통과.

* **[v4.1 / esm_r15.py] (2026-07-07) ES Level 시뮬레이션 → 절감 에너지[Wh] 환산 + Advanced Settings 위치 버그 수정**
  * **배경**: v4.0에서 IIR 필터 계수를 Optimizer 탭 Advanced Settings에 추가했는데, 이 파라미터는 Energy Dashboard 전용 기능(ES Level 시뮬레이션)에서만 쓰이다 보니 사용자가 Energy Dashboard 쪽 Advanced Settings에서 찾다가 못 찾음(버그로 보고) — Energy Dashboard의 Advanced Settings(`energy_adv_frame`, 기존 Gamma 설정 위치)로 이동. 또한 v4.0에서는 ES Level별 누적 카운트만 보여주고 실제 Watt-hour 절감량 환산은 미구현이었는데, 이를 구현해달라는 요청.
  * **Advanced Settings 위치 수정**: IIR Filter Coefficient Tput_LTE/PRB_LTE를 Optimizer 탭에서 제거하고 Energy Dashboard 탭의 Advanced Settings로 이동(내부 변수 `self.iir_coef_tput_lte`/`self.iir_coef_prb_lte`는 그대로 재사용, UI 위젯 위치만 변경).
  * **신규 Gamma2**: Energy Dashboard Advanced Settings에 `Gamma2`(기본값 0.7, 기존 Nc2 기반 방식의 `Gamma`와 동일한 스핀박스 스타일) 추가 — ES Level 시뮬레이션 기반 절감 에너지 추정치에 곱하는 보정 계수.
  * **절감 에너지 계산 로직** (신규 `_calc_es_level_simulation_savings` + 헬퍼 `_power_delta_for_cells`/`_parse_energy_stat_for_range`/`_sector_total_energy_wh`): ESM Output Result의 레벨별 `Target Cell Num`(그 레벨에서 새로 꺼지는 고유 셀)과 CM 매핑으로 찾은 RU HW의 Idle-PAoff 전력차를 결합. 레벨 k의 셀은 `Applied_ES_Level >= k`인 모든 시뮬레이션 스텝 동안 계속 꺼져 있으므로(DRBn이 누적합인 것과 동일한 논리, 기존 `_calc_all_savings`의 cum_nc2 누적 방식과 수학적으로 동일한 원리) — 절감 에너지 = Σ_k [ power_delta(레벨 k 고유 대상 셀) × count(Level>=k, 시뮬레이션 요약의 `Level {L} Count`로 계산) × 0.25h ] × Gamma2.
  * **Sector별 소모 대비 절감률**: Energy Stat 데이터를 (Energy Dashboard 탭의 날짜 위젯과 무관하게) 시뮬레이션이 지정한 기간으로 직접 필터링(`_parse_energy_stat_for_range`)하고, CM의 `Sector`열(cell-num%10)로 해당 Sector에 속한 모든 RU path를 찾아 총 소모 에너지를 합산(`_sector_total_energy_wh`, 공유 RU 중복 방지를 위해 RU path 기준 dedupe). ES Level 시뮬레이션 팝업에 "에너지 절감 효과 (Sector별)" 탭을 신규 추가해 Sector별 **소모에너지[Wh] / 절감에너지[Wh] / 절감률(%) / Tput Violation Count / Tput Violation Ratio**(=위반 스텝수/ES Active Steps)를 표로 보여주고, 마지막 행에 전체 사이트 합계를 추가. CSV 다운로드에도 `_EnergySaving.csv`로 함께 포함.
  * **검증**: `_calc_es_level_simulation_savings`를 가짜 self(3개 RU를 가진 Sector, 레벨1/2 각각 고유 대상 셀 1개씩, RU HW Idle-PAoff 전력차 60W, 레벨별 카운트 0/30/50, Energy Stat 24시간치 합성 데이터)로 단위 테스트 — 절감 에너지 1365.0Wh(=60W×80스텝×0.25h + 60W×50스텝×0.25h, Gamma2=0.7 적용), 소모 에너지 7200.0Wh(3개 RU×24시간×100Wh), 절감률 18.96%, Tput Violation Ratio 0.0625가 모두 손계산과 정확히 일치함을 확인. 실제 GUI 앱에서 ES Level 시뮬레이션 팝업이 3개 탭(Sector 요약/에너지 절감 효과/상세 타임라인) 구성으로 오류 없이 열림을 확인.

* **[v4.2 / esm_r15.py] (2026-07-07) Energy Dashboard 필터 통합("평가 기간/평가 시간") + 절감효과 예측 Mode 1/2/3 + 평가 시간 한정 카운트**
  * **배경**: 사용자가 Energy Dashboard를 정리해달라며 4가지 요청 — (1) 날짜/시간 필터를 "평가 기간/평가 시간"으로 개명하고 Energy Dashboard 전체가 공통으로 참조, (2) 에너지 분석 실행에 절감효과 시각화 추가, (3) 에너지 절감효과 예측 버튼이 NC2/시뮬레이션/둘다(Mode 1/2/3, 기본 2)를 지원하고 Mode 3에서 비교표 제공, (4) 시뮬레이션은 24시간 내내 ES 윈도우를 따라 계속 수행하되 결과에 집계되는 레벨별 카운트/Tput 위반은 평가 시간으로만 한정.
  * **(1) 필터 통합**: "날짜 범위"/"시간" 라벨을 "평가 기간"/"평가 시간"으로 개명. `_predict_energy_saving_popup`의 자체 시간 필터(`pred_hours_var`)와 ES Level 시뮬레이션 팝업의 자체 날짜 범위 위젯을 모두 제거하고, 신규 `_get_eval_date_range()`/`_parse_eval_hours()` 헬퍼로 Energy Dashboard 상단의 공통 필터를 모든 기능이 함께 참조하도록 통일.
  * **(2) 에너지 분석 실행에 절감 효과 추가**: `_analyze_energy_stat`에서 대상 eNodeBID/Sector·평가 기간/평가 시간에 대해 ES Level 시뮬레이션 기반 절감 에너지를 계산해 상단 요약 라벨에 "예상 절감 에너지" 표시, 기존 3개 그래프(누적 추이/시간대별/요일별) 아래에 소모/절감/절감 후 예상 소모 3-bar 비교 그래프를 4번째로 추가.
  * **(3) 절감효과 예측 Mode 1/2/3**: Energy Dashboard Advanced Settings에 `절감효과 예측 Mode`(기본값 2) 신규 추가. `_predict_energy_saving_popup`을 모드에 따라 탭을 동적으로 구성하는 단일 진입점으로 재구성 — Mode 1(NC2 기반)은 기존 3개 탭만, Mode 2(시뮬레이션 기반, 기본값)는 "Sector별 절감 효과" 탭만, Mode 3(둘 다)은 위 모든 탭 + 신규 `_build_mode_comparison_df`로 만든 "Mode 비교(NC2 vs 시뮬레이션)" 탭까지 표시. CSV 다운로드는 현재 모드에 해당하는 표만 저장.
  * **(4) 평가 시간 한정 카운트**: `_run_es_level_simulation`에 `eval_hours` 인자 추가 — 시뮬레이션 자체(레벨 결정+IIR)는 ES operation window 정의를 따라 24시간 전체 항상 수행(윈도우가 0~5시면 평가 시간과 무관하게 그 5시간 내내 정책 적용)하되, summary_df의 "레벨별 누적 카운트"/"Tput 불만족 카운트"/"ES Active Steps"/"Total Steps"만 평가 시간에 속하는 스텝으로 한정. timeline_df에 `In_Eval_Hours` 열 추가. `_parse_energy_stat_for_range`/`_calc_es_level_simulation_savings`에도 `eval_hours`를 전달해 소모 에너지 계산도 동일하게 한정.
  * **검증**: 기존 6-스텝 합성 Rawdata(레벨 궤적 `[0,1,2,1,0,0]`)를 `eval_hours=[0]`으로 재실행 — 전체 궤적은 그대로 유지된 채(윈도우는 계속 시뮬레이션됨) summary만 앞 4스텝(0시)으로 한정되어 Total Steps=4/ES Active Steps=4/Tput Violation Count=1/Level 0,1,2 Count=1,2,1로 정확히 집계됨을 확인. 실제 GUI 앱으로 Optimizer 실행 후 Mode 1/2/3 팝업, ES Level 시뮬레이션 팝업, 절감 효과 시각화가 추가된 `_analyze_energy_stat`이 모두 오류 없이 실행됨을 확인.

* **[v4.3 / esm_r15.py] (2026-07-07) 절감 에너지 단위(Wh) 재확인/명시 + Energy Dashboard·Learning Energy Curve 결과도 Output 폴더 자동 저장**
  * **배경**: 사용자가 두 가지를 요청 — (1) ES Level 시뮬레이션의 절감량 계산 시 15분 단위 count 기반 값(전력)과 실제 에너지 단위(Wh)가 다르므로 count를 시간(hour, count/4)으로 환산해야 한다는 주의사항, (2) Energy Dashboard/Learning tlabnergy Curve의 다운로드 결과도 Optimizer처럼 파일 대화상자 없이 `Output` 폴더에 자동 저장.
  * **단위 확인**: `_calc_es_level_simulation_savings`를 재점검한 결과 이미 `power_delta(W) × count(15분 스텝수) × 0.25(h/step) × Gamma2`로 count를 시간으로 환산한 뒤 Watt와 곱해 Wh를 산출하고 있었음(기존 `_calculate_est_saving`의 `/4.0`과 동일한 관례) — 계산 로직 자체는 이미 올바르게 되어 있었음. 다만 결과 표에서 이 환산이 바로 보이지 않아서, `_run_es_level_simulation`의 summary_df에 `Level {L} Count` 옆에 시간 환산값 `Level {L} Hours`(=count×0.25)를 나란히 추가해 결과 CSV만 봐도 단위 환산이 명확히 드러나도록 함(계산 결과 자체는 변경 없음, 표시만 추가).
  * **Output 폴더 자동 저장**: Optimizer의 "최종 결과 파일 저장"과 동일하게 신규 `_make_output_dir(subfolder)` 헬퍼로 `Output/<timestamp>/<subfolder>/`를 만들어 파일 대화상자 없이 자동 저장하도록 변경 — `_download_energy_intermediate`(`EnergyDashboard/`), `_predict_energy_saving_popup`의 CSV 다운로드(`EnergySavingPrediction/`, 모드에 따라 NC2_Sector.csv/Simulation_Sector.csv/Comparison.csv 중 해당 파일만), ES Level 시뮬레이션 팝업의 CSV 다운로드(`ESLevelSimulation/`, Summary/EnergySaving/Timeline 3종), `_download_learn_result`(Learning Energy Curve RU 상세/HW 요약/Formula 3버튼 공용, `LearningEnergyCurve/`).
  * **검증**: 기존 절감 에너지 단위 테스트(3개 RU, 레벨1/2, 전력차 60W, 카운트 80/50, Gamma2=0.7)에 `Level {L} Hours` 컬럼을 포함한 summary_df로 재실행 — 절감 에너지 1365.0Wh로 기존과 동일함을 재확인(표시용 컬럼 추가가 계산에 영향 없음 확인). `_download_learn_result`를 실제로 호출해 `Output/<timestamp>/LearningEnergyCurve/<파일명>`에 정확히 저장되는 것을 파일시스템에서 직접 확인.

*(v4.3까지는 `esm_r15.py` 기준, v5.0부터는 새로 분기한 `esm_r16.py` 기준)*

* **[v5.0 / esm_r16.py] (2026-07-07) 신규 기능: Deep Sleep**
  * **배경**: RU HW가 완전히 shutdown되면 Idle→PA off보다 더 깊은 저전력 상태인 Deep Sleep으로 진입 가능한 경우가 있어, ES Level 시뮬레이션의 절감 에너지 계산에 이를 반영해달라는 요청. Deep Sleep은 기상(wake-up) 시간이 5분이라 ES fallback(레벨 감소) 시 즉각적인 Tput 보장이 불가능해지므로 3가지 조건을 모두 만족해야 적용 가능. 버전 분기 원칙(1항)에 따라 `esm_r15.py`를 복제해 `esm_r16.py`로 시작.
  * **조건 1(HW 지원 여부)**: RU/MMU Spec DB Editor에 신규 `Deep Sleep` 열 추가(Deep Sleep 상태의 Consumed Power[W]) — 값이 0보다 크면 해당 RU HW(board-type)가 Deep Sleep을 지원, 아니면(0/공란) PA off만 적용(기존과 동일). `_add_editor_row('ru_spec')`의 신규 행 기본 컬럼 템플릿에도 `Deep Sleep` 추가.
  * **조건 2(RU HW의 모든 RU path shutdown)**: RU HW(물리 RU)를 `ru-board-id + ru-cascade-id`로 식별(신규 `_power_deltas_for_level`에서 `ru-port-id`를 그룹핑 키에서 제외) — 지금까지는 RU path(`ru-board-id+ru-port-id+ru-cascade-id`) 단위로만 RU를 식별했는데, 물리적으로 하나의 RU HW가 여러 RU path(포트)를 가질 수 있어(Dual Band RU) Deep Sleep은 그 RU HW의 모든 RU path가 꺼져야 적용 가능. 이번 라운드는 **Single Band RU만 가정**(물리 RU 1개=RU path 1개)하므로 이 식별만으로 충분하고, ES Level의 Target Cell Num이 이미 PA-shared-cell 해석을 거쳐 그 RU path에 연결된 모든 Cell을 포함하도록 구성되어 있어 "모든 RU path shutdown" 조건이 레벨 단위로 자동 충족됨(추가 검증 로직 불필요). Dual Band RU(포트 2개) 지원은 사용자가 추후 방법을 알려줄 예정 — 다음 라운드 대기.
  * **조건 3(최고 레벨 제외)**: 현재 적용된 ES level(Curr) 자신의 몫으로 꺼진 RU는 Deep Sleep 대상에서 제외(언제든 한 단계 감소(fallback)로 즉시 재점등이 필요할 수 있어 5분 기상 시간을 감당 못 함). Deep Sleep은 Curr보다 낮은 레벨(1..Curr-1)의 RU에만 적용 가능.
  * **구현**: 시뮬레이션의 레벨 결정 로직(`_run_es_level_simulation`)은 전혀 변경하지 않음 — Deep Sleep은 이미 꺼져 있는 RU를 얼마나 더 깊게 재우는지의 "에너지 계산" 문제일 뿐 트래픽/레벨 전환 판단에는 영향을 주지 않기 때문. `_power_delta_for_cells`를 `_power_deltas_for_level`로 교체 — 레벨별로 `(pa_off_delta, elevated_delta)`를 함께 계산(elevated_delta는 RU HW가 Deep Sleep을 지원하면 Idle-DeepSleep전력 기준, 아니면 pa_off_delta와 동일). `_calc_es_level_simulation_savings`의 절감 에너지 계산을 `Σ_k [ pa_off_delta(k)×count(Level==k)×0.25h + elevated_delta(k)×count(Level>k)×0.25h ] × Gamma2`로 변경(Deep Sleep 미지원 HW는 elevated_delta==pa_off_delta이므로 기존 count(Level>=k) 공식과 완전히 동일하게 귀결 — 하위 호환 보장). 결과 표에 `중 Deep Sleep 추가 절감 [Wh]` 열을 추가.
  * **동작 확인(사용자 제시 예시로 검증)**: "Curr=3, 레벨1/2는 Deep Sleep 지원 RU, 레벨3은 현재 최고 레벨" 시나리오(카운트 Level1=5/Level2=8/Level3=77)로 계산 — 레벨1/2는 `count(Level>k)` 몫(각각 85, 77스텝)에 Deep Sleep 전력차가 적용되고, 레벨3은 `count(Level==3)` 몫(77스텝, `count(Level>3)`는 항상 0)에 PA off 전력차만 적용됨을 확인 — "레벨2로 fallback하면 레벨2의 Deep Sleep이 즉시 Cell off로 전환되고 레벨3의 RU는 완전히 켜진다"는 시나리오가 매 15분 스텝마다 그 순간의 Applied_ES_Level 값을 기준으로 count_eq_k/count_gt_k를 판정하는 방식으로 자연히 성립됨을 확인(전용 상태 추적 로직 없이도 집계 공식만으로 시나리오가 성립).
  * **검증**: (a) 위 예시 시나리오에서 절감 에너지 3496.5Wh(Gamma2=0.7 적용 후), Deep Sleep 추가 절감분 850.5Wh가 손계산과 정확히 일치함을 확인, (b) Deep Sleep 미지원 기존 r15 테스트 케이스를 그대로 재실행해 절감 에너지 1365.0Wh/소모 에너지 7200.0Wh/절감률 18.96%/Deep Sleep 추가 절감 0.0Wh로 r15와 완전히 동일한 결과가 나옴을 확인(하위 호환 검증). 실제 GUI 앱으로 RU/MMU Spec 에디터의 '행 추가'가 `Deep Sleep` 열을 포함해 생성됨을 확인하고, Optimizer 실행 → Deep Sleep 지원 RU/MMU Spec 구성 → ES Level 시뮬레이션 → 절감 에너지 계산까지 전체 파이프라인이 오류 없이 동작함을 확인.

* **[v5.1 / esm_r16.py, 동일 수정을 esm_r15.py에도 적용] (2026-07-07) 버그 수정: "시뮬레이션 수행 기간"이 "평가 기간"에 강제 통합되어 있던 문제**
  * **배경**: v4.2에서 날짜/시간 필터를 "평가 기간/평가 시간"으로 통합하면서, ES Level 시뮬레이션 팝업/절감효과 예측(Mode 2·3)이 "어느 트래픽 데이터를 Rawdata로 만들어 시뮬레이션을 돌릴지"(시뮬레이션 수행 기간)까지 실수로 "평가 기간"과 같은 값으로 강제 통합해버림 — 원래 이 둘은 별개 개념인데 하나로 묶여, 실제 ES operation 시간과 평가 시간이 다른 경우(예: 실제 0~7시 운영, 평가는 0~4시만) 시뮬레이션이 제대로 동작하지 못하는 문제가 있었음. 사용자가 "Sector별로 ES level 적용 시간이 다른데 절감에너지량이 똑같이 나온다"는 버그도 함께 보고.
  * **수정**: `_open_es_level_simulation_popup`과 `_predict_energy_saving_popup`(Mode 2/3)에 팝업 자체의 "시뮬레이션 수행 기간" 날짜 범위 위젯을 별도로 복원 — 이 값이 `_build_rawdata_for_period`(Rawdata 생성/재사용 판단)에 전달되고, Energy Dashboard 상단의 공통 "평가 기간/평가 시간"은 오직 결과 집계·소모 에너지 비교에만 사용. `_run_es_level_simulation`에 `eval_start_date`/`eval_end_date`를 추가해 시뮬레이션은 시뮬레이션 수행 기간 전체에 대해 항상 실행하고, summary_df 집계만 평가 기간(날짜)+평가 시간(시간)으로 한정(기존에는 시간만 한정 가능했음). 표시용 열도 `In_Eval_Hours` → `In_Eval_Window`로 개명(날짜+시간 조건을 모두 반영).
  * **"Sector별 절감에너지 동일" 버그 조사**: `_calc_es_level_simulation_savings`/`_run_es_level_simulation`을 서로 다른 레벨-시간 분포를 가진 2개 Sector로 직접 단위 테스트 — 각각 52.5Wh/0.0Wh로 카운트에 비례해 정확히 다르게 나와 집계 공식 자체는 정상임을 확인. 위 기간 통합 버그가 원인일 가능성이 높다고 판단(원하는 평가 기간이 보유한 트래픽 데이터 범위와 맞지 않으면 Rawdata 재생성이 실패해 이전 결과가 표에 남아있는 것처럼 보일 수 있었음) — 이번 수정으로 시뮬레이션 수행 기간을 트래픽 데이터가 있는 범위로 별도 지정할 수 있게 되어 해결될 것으로 예상. 재현 시 CM Data/RU-MMU Spec의 board-type 매핑 누락으로 전력차가 0으로 조용히 귀결되는 경우가 있는지도 확인 필요.
  * **적용 범위**: 사용자 요청에 따라 동일한 수정(시뮬레이션 수행 기간 분리 + 버그 조사)을 `esm_r15.py`에도 그대로 반영(r15에는 Deep Sleep 기능이 없으므로 그 부분은 제외하고 이 수정만 포팅).
  * **검증**: 팝업 2개 모두 새 "시뮬레이션 수행 기간" 위젯이 포함되어 오류 없이 열리고, 트래픽 미설정 시 경고만 표시하고 예외 없이 종료됨을 확인. `python -m py_compile` 통과(양쪽 파일 모두).

* **[v5.2 / esm_r15.py 우선 반영 후 esm_r16.py에 포팅 완료] (2026-07-07) 버그 수정: IpThruThpDLTime<=0/NaN 행 통째 제외로 인한 15분 연속성 붕괴 + 특정 Sector ES 적용 0회 문제**
  * **배경**: 사용자가 시뮬레이션 상세 타임라인을 직접 검토하다가, IIR을 손으로 재현해도 Entering 조건(Tput/UsedRB_t)이 만족되는 것처럼 보이는데 실제 시뮬레이션은 특정 Sector에서 레벨 적용 횟수가 0으로 나오는 것을 발견 — 이상하다고 보고. 사용자가 "r15에 먼저 반영하고, 고친 뒤 r16에 반영"하라고 순서를 지정.
  * **원인**: `run_analysis`/`_build_rawdata_for_period` 양쪽 모두 `IpThruThpDLTime > 0`을 만족 못하는 행(트래픽 통계가 0초/NaN으로 잡힌 구간)을 valid_mask에서 통째로 제외하고 있었음 — 이러면 15분 간격의 연속 스텝이라는 시뮬레이션의 기본 가정이 깨져서, 결측 구간이 많은 Sector는 윈도우 진입마다 Initial level(0)로 재시작하는 로직과 맞물려 레벨이 오를 기회 자체가 거의 사라져 "적용 횟수 0"으로 보였을 것으로 추정.
  * **수정**: valid_mask에서 `IpThruThpDLTime > 0` 조건을 제거해 그런 행도 더 이상 통째로 버리지 않고 유지(15분 간격 연속성 보존)하되, `cmIPTput`만 그 행에서 NaN으로 계산되도록 함(SP/InitEstIPTput은 IpThruThpDLTime과 무관하므로 영향 없음). `_run_es_level_simulation`에 예외 처리 추가: 그 스텝의 rawdata `cmIPTput`이 NaN이면(윈도우 진입/이탈 판정 포함) 레벨 결정을 보류하고 이전 스텝의 ES level/IIR 상태를 그대로 승계(freeze-forward) — "그 시간은 그냥 이전 ES level을 승계해야 한다"는 사용자 지시 그대로 반영.
  * **검증**: 6-스텝 합성 데이터의 3번째 스텝에 `cmIPTput=NaN`을 주입한 단위 테스트에서 레벨/IIR이 정확히 이전 스텝 값을 승계하고 이후 스텝은 승계된 상태를 기반으로 다시 정상적으로 레벨 결정이 이어짐을 확인. 실제 GUI 앱으로 트래픽의 약 6%(17/288행, ES 운영 시간대 집중) 행에 IpThruThpDLTime=0/NaN을 주입해 실행 — 이전이면 해당 행들이 사라져 24행 중 18행만 남았을 것이 수정 후 24행 모두 유지되고 그중 6행만 cmIPTput=NaN으로 정확히 표시됨을 확인.
  * **적용 순서**: 사용자 지시대로 `esm_r15.py`에 먼저 반영·검증한 뒤, 동일한 수정(valid_mask 변경 2곳 + `_run_es_level_simulation` 예외 처리)을 `esm_r16.py`에도 그대로 포팅 완료 — 두 파일 모두 동일한 합성 테스트로 결과 일치 확인(Deep Sleep 로직과는 독립적이라 상호작용 없음).

* **[v5.3 / esm_r15.py 우선 반영 후 esm_r16.py에 포팅 완료] (2026-07-08) 버그 수정: ES Level 시뮬레이션의 PRB/Tput 조건 단위 불일치로 특정 Sector에서 ES level이 전혀 적용되지 않던 문제**
  * **배경**: v5.2로도 문제가 해결되지 않자, 사용자가 실제 raw data 한 행(eNodeBID 210993 Sector 2: UsedRB_t_adj=25, total_rb=650, cmIPTput=32855.07, Pred_IPTput_Mbps_L1=12.306, Entering Th_Tput=7, Entering Th_PRB_L1=10.92%)을 손으로 계산해 두 Entering 조건을 모두 만족하는 것 같은데 ES Level 1이 전혀 적용되지 않는다고 매우 구체적으로 보고. "혹시 Th 조건을 PRB usage(%)가 아니라 UsedRB(원시 RB)로 비교한다면 ESM output의 RB Threshold/RB Margin을 쓰면 된다"와 "Tput 단위 mismatch도 확인해달라"는 정확한 힌트까지 제공.
  * **원인 1(PRB 단위 불일치, 진짜 근본 원인)**: `_run_es_level_simulation`이 PRB 조건에 `Entering/Leaving Th_PRB_L{n}` 열(ESM Output Result와 동일하게 %, 0~100 스케일)을 그대로 사용했는데, 비교 대상인 `UsedRB_t_adj_iir`는 원시 RB 개수(0~total_rb 스케일, 예시에서는 0~650) — 25(원시 RB)와 10.92(%)를 그냥 비교하면 25 > 10.92라 "이미 초과"로 오판되어, 실제로는 25/650=3.8%로 10.92%보다 훨씬 작아 조건을 만족해야 했던 상황에서도 PRB 조건이 거의 항상 실패해 ES level이 오르지 못하고 있었음.
  * **원인 2(Tput 단위 불일치)**: rawdata의 `cmIPTput`은 `(IpThruThpVoDLByte/IpThruThpDLTime)*8000` 공식상 kbps 스케일(예: 32855.07kbps=32.86Mbps)인데 `Entering/Leaving Th_Tput`은 Mbps 스케일(예: 6~7) — Leaving(감소) 조건에서 kbps 스케일 cmIPTput_iir과 Mbps 스케일 임계값을 그대로 비교하면 cmIPTput이 항상 훨씬 크게 나와 "Tput 불만족으로 인한 감소"가 거의 발생하지 않는 문제(Entering 조건의 `Pred_IPTput_Mbps_L{n}`은 원래부터 Mbps라 문제 없었음).
  * **수정**: PRB 조건은 %(Entering/Leaving Th_PRB_L{n}) 대신 원시 RB 단위인 `RB_Threshold_L{n}`(이미 rawdata에 존재, ESM Output Result의 RBThreshold와 동일값)과 `RB Threshold Margin_LTE`를 그대로 사용(Entering: `UsedRB_t_adj_iir <= RB_Threshold_L{n}`, Leaving: `UsedRB_t_adj_iir > RB_Threshold_L{n} + RB Threshold Margin_LTE`). Tput 조건은 rawdata의 `cmIPTput`을 시뮬레이션 내부 로컬 변수에서만 1000으로 나눠 Mbps로 환산해 비교(원본 rawdata `cmIPTput` 열 자체는 Optimizer의 alpha 회귀 등에 그대로 쓰이므로 변경하지 않음).
  * **검증**: 사용자가 제시한 실제 수치를 그대로 입력해 단위 테스트 — 수정 전 로직대로면 PRB 조건이 25>10.92로 오판되어 진입 실패했을 것이, 수정 후 1번째 스텝에서 정확히 ES Level 1로 진입하고 `cmIPTput_IIR`도 32.86(Mbps)로 사람이 계산한 값과 일치함을 확인.
  * **적용 순서**: 사용자 지시대로 `esm_r15.py`에 먼저 반영·검증한 뒤, 동일한 수정(cmIPTput /1000 Mbps 환산 + PRB 조건을 `RB_Threshold_L{n}`/`RB Threshold Margin_LTE` 기반으로 교체)을 `esm_r16.py`에도 그대로 포팅 완료(Deep Sleep 로직과는 독립적이라 상호작용 없음, `python -m py_compile` 양쪽 파일 모두 통과 확인). 포팅 당시 `esm_r16.py` 모듈 상단 changelog 문단(`[r16-후속2]`)을 빠뜨렸던 것을 이번(v5.4) 작업 중 발견해 함께 보완.

* **[v5.4 / esm_r16.py 전용, 새 편의 기능이라 esm_r15.py에는 포팅하지 않음(Deep Sleep과 동일한 전례)] (2026-07-09) 기능 추가: 파일 입출력 폴더/파라미터 초기값 자동 저장·불러오기 + Input 폴더 파일 자동 선택**
  * **배경**: 사용자가 앱을 실행할 때마다 Input/Output 폴더나 각 탭 파라미터를 다시 설정하고, Traffic/Energy Stat/CM/학습데이터 파일을 드래그 앤 드롭이나 '찾기'로 매번 다시 선택하는 게 번거롭다고 요청. 조건: Input/Output 폴더 기본값은 앱이 위치한 폴더 내부의 Input/Output 폴더로, 설정 파일이 없으면 기존 하드코딩 초기값 사용, 자동 저장은 하지 말고 필요할 때만 수동으로 저장, Input 폴더의 파일도 파일명/헤더 규칙으로 자동 선택하고 실패 시 팝업으로 안내.
  * **구현**: `_app_dir()`(스크립트 또는 exe가 위치한 폴더) 기준으로 `input_dir`/`output_dir` 기본값을 `<앱 폴더>/Input`, `<앱 폴더>/Output`으로 설정. 앱 폴더의 `esm_settings.json`이 있으면 `_load_app_settings()`가 그 값과 `_SETTINGS_PARAM_NAMES`(Optimizer/Advanced Settings/Energy Dashboard/Learning 탭의 주요 파라미터, 파일 경로는 제외)를 덮어씀 - 파일이 없으면 기존 초기값 그대로. 저장은 Data I/O 탭의 "현재 설정을 기본값으로 저장" 버튼(`_save_app_settings()`)에서만 수동으로 발생. `_auto_select_input_files()`가 앱 구동 시 Input 폴더를 스캔해 CM Data(확장자), Traffic/Energy Stat Data(기존 `handle_file_drop`과 동일한 파일명 키워드 규칙), Cell/RU 단위 학습데이터(기존 `_classify_learning_files_drop`과 동일한 CSV 헤더 컬럼 시그니처, 공통 로직은 `_sniff_learning_csv_kind`로 분리)를 자동으로 채워줌 - 항목별 후보가 정확히 1개일 때만 자동 선택하고, 0개/2개 이상이면 자동 선택하지 않고 팝업 하나로 모아서 안내. `_make_output_dir`/`run_analysis`/Traffic Pattern 저장 로직의 출력 폴더 기준도 `os.getcwd()`에서 `self.output_dir`로 통일.
  * **검증**: 임시 폴더에 실제 스키마를 반영한 샘플 파일(CM 확장자, Traffic/Energy Stat CSV - Energy Stat은 실제 컬럼명인 `RuPowerTot`/`RuPowerCnt` 사용, Cell/RU 학습데이터 CSV)을 두고 `ESAnalyzerApp`을 실제로 생성해 5개 파일이 모두 정확히 자동 선택되고 경고 팝업이 뜨지 않음을 확인. 파라미터를 바꾸고 저장한 뒤 새 인스턴스를 생성해 Input/Output 폴더와 파라미터가 정확히 재로딩됨을 확인. CM 파일 후보를 2개로 만들었을 때는 자동 선택하지 않고 정확히 그 항목만 안내 팝업에 포함됨을 확인. `python -m py_compile` 통과.
  * **적용 범위**: 최초 반영은 `esm_r16.py`에만(Deep Sleep과 같은 전례로 판단) — 이후 v5.6에서 사용자가 "r16의 차별화 포인트는 Deep Sleep뿐"이라며 `esm_r15.py`에도 포팅 요청, 반영 완료. Input 폴더가 아직 없으면(사용자가 아직 Input 폴더를 만들지 않은 경우) 경고 팝업만 띄우고 정상 구동.

* **[v5.5 / esm_r16.py 전용] (2026-07-09) 기능 개선: Optimizer와 Energy Dashboard/Learning 결과를 같은 Output 타임스탬프 폴더로 통합 + 같은 종류의 결과를 반복 다운로드해도 서로 덮어쓰지 않도록 폴더 분리**
  * **배경**: ES Policy Optimizer 실행 후 Energy Dashboard(에너지 분석/절감효과 예측/ES Level 시뮬레이션)를 이어서 쓰는 게 정상적인 순차 워크플로우인데, `run_analysis`(Optimizer)와 `_make_output_dir`(Energy Dashboard/Learning 다운로드 공용)이 각자 새 타임스탬프를 만들어 결과가 서로 다른 `Output/<timestamp>/` 폴더에 흩어지는 문제를 사용자가 지적. 또한 Energy Dashboard에서 조합(eNodeBID/Sector/시뮬레이션 조건 등)을 바꿔가며 같은 종류의 결과를 반복 다운로드하면 같은 폴더의 같은 파일명에 매번 덮어써지는 문제도 함께 요청 — 해결 방식은 파일명에 index를 붙이거나 폴더 이름을 다르게 하거나 둘 중 편한 쪽으로 일임.
  * **수정**: `self.latest_run_timestamp`를 신설해 `run_analysis` 실행 시점의 타임스탬프를 기록하고, `_make_output_dir`은 자체적으로 새 타임스탬프를 만들지 않고 이 값을 재사용(Optimizer 미실행 시 첫 호출이 새로 만들고 이후 호출들이 그대로 따름) — Optimizer -> Energy Dashboard/Learning 순서로 이어지는 한 세션의 모든 결과가 하나의 `Output/<timestamp>/` 폴더에 모임. 폴더 충돌은 파일명 index 대신 폴더 이름을 다르게 하는 방식을 선택 — 같은 타임스탬프 폴더 안에서 subfolder(예: `ESLevelSimulation`)가 이미 있으면 `ESLevelSimulation_2`, `_3`…으로 자동으로 새 폴더를 만듦(다운로드 하나가 여러 파일을 한 번에 저장하는 경우가 있어 폴더 단위 분리가 더 간단·일관적).
  * **검증**: `latest_run_timestamp`를 미리 지정한 상태에서 여러 subfolder로 `_make_output_dir`을 호출해 모두 같은 타임스탬프 폴더 아래 생성됨을 확인. 같은 subfolder를 반복 호출하면 `_2`, `_3`으로 이어지며 서로 다른 폴더가 만들어짐을 확인. Optimizer 미실행 상태에서는 첫 호출이 새 타임스탬프를 만들고 이후 호출들이 그 값을 재사용함을 확인. `python -m py_compile` 통과.
  * **적용 범위**: 최초 반영은 `esm_r16.py`에만 — 이후 v5.6에서 `esm_r15.py`에도 함께 포팅 완료(아래 참고).

* **[v5.6 / esm_r15.py로 포팅] (2026-07-09) v5.4·v5.5 편의 기능을 esm_r15.py에도 동일하게 반영**
  * **배경**: 사용자가 "r_15에도 이번 편의기능들을 적용해줘. r_16의 차별화 포인트는 Deep sleep 반영이니까 말야"라고 요청 — v5.4(설정 저장/자동 불러오기 + Input 폴더 파일 자동 선택)와 v5.5(Optimizer/Energy Dashboard Output 폴더 통합 + 반복 다운로드 폴더 분리)는 Deep Sleep과 무관한 범용 편의 기능이므로, esm_r16.py만의 차별화 요소(Deep Sleep)와 분리해 두 파일 모두에 반영해야 한다는 취지.
  * **수정**: esm_r16.py의 `_SETTINGS_PARAM_NAMES`, `input_dir`/`output_dir`/`latest_run_timestamp` 상태 변수, `_app_dir`/`_settings_path`/`_load_app_settings`/`_save_app_settings`/`_browse_dir`/`_sniff_learning_csv_kind`/`_auto_select_input_files` 메서드, Data I/O 탭의 Input/Output 폴더 UI + 저장 버튼, `_make_output_dir`의 타임스탬프 재사용·폴더 분리 로직, `run_analysis`의 `latest_run_timestamp` 기록, `_classify_learning_files_drop`의 `_sniff_learning_csv_kind` 재사용 리팩터링을 코드 그대로 `esm_r15.py`에 포팅(Deep Sleep 관련 코드는 esm_r15.py에 애초에 없으므로 그 부분만 자연히 제외됨).
  * **검증**: esm_r16.py에서 쓴 것과 동일한 두 벌의 테스트(Input 폴더 자동 선택 5종 + 설정 저장/재로딩 + CM 파일 후보 2개 시 안내, `_make_output_dir` 타임스탬프 공유 + 반복 호출 시 `_2`/`_3` 폴더 분리)를 esm_r15.py를 대상으로 재실행해 모두 동일하게 통과함을 확인. `python -m py_compile` 통과.
  * **적용 범위**: `esm_r15.py` + `esm_r16.py` 모두. 이제 두 파일의 유일한 기능 차이는 Deep Sleep(esm_r16.py 전용)뿐.

## 4-1. 새 라운드: esm_r15_0.py / esm_r16_0.py (branch `esm-r0-cellru-mapping`)

* **[라운드 전환] (2026-07-09)** 사용자 지시로 새 브랜치 `esm-r0-cellru-mapping`을 만들고 `esm_r15.py`→`esm_r15_0.py`, `esm_r16.py`→`esm_r16_0.py`로 파일명을 변경(순수 rename + 모듈 docstring 타이틀/출처 한 줄만 수정, 기능 변경 없음). 이 시점부터의 신규 작업은 `esm_r15_0.py`/`esm_r16_0.py`에 반영하고, `esm_r15.py`/`esm_r16.py`는 이전 라운드 상태로 그대로 둔다(브랜치 `new-version`에 보존).

* **[v5.7 / esm_r15_0.py 우선 반영 후 esm_r16_0.py에 포팅 완료] (2026-07-09) 기능 추가: Cell-RU 매핑 저장/자동 불러오기 + eMTC/ENDC anchor 서비스 보장을 위한 ES 적용대상 band 강제 조정**
  * **배경**: 새 라운드에서 사용자가 두 가지 기능을 요청. (1) Data I/O 탭에서 생성하는 Cell-RU 매핑 정보(`cm_map_df_full`)를 파일로 저장해 Input 폴더에 두고, 앱 구동 시 자동으로(동일 이름이 여러 개면 타임스탬프 기준 최신 것) 불러오면서 불러온 경우에만 팝업으로 안내. (2) Optimizer가 ES 정책을 생성할 때 eMTC 서비스와 ENDC anchor 서비스가 각각 최소 하나의 cell에서는 항상 유지되도록(ES 미적용) 보장하는 규칙 — SectorList+CarrierConf로 추출한 cell-num 중 해당 서비스가 켜진 cell이 있는데 이미 RB<0(ES 미적용)인 것이 하나도 없으면, RB>0(ES 적용대상)이고 서비스가 켜진 band 중 우선순위 기준(eMTC: ES priority가 가장 큰 것, ENDC anchor: ENDC_priority가 가장 작은 것 중 -1 제외)으로 하나를 골라 강제로 ES capability 0으로 간주하고, ESM Output에 Note로 기록.
  * **구현**: `_save_cellru_mapping_file()`/`_auto_load_cellru_mapping()`(파일명 `CellRUMapping_<%Y%m%d_%H%M%S>.json`, Input 폴더, 문자열 정렬=시간순 정렬 활용), `run_analysis`에 삽입된 공통 헬퍼 `_enforce_protected_band()`(+`_is_emtc_enabled`/`_is_endc_anchor_enabled`/`_lookup_cell_attr`). eMTC/ENDC anchor 속성(`conf-emtc-switch`/`endc-anchor-type`/`endc-support`)이 CarrierConf(band당 한 행)에 있는지 CM Data/Cell-RU Mapping(cell-num당 한 행)에 있는지 확실치 않아, CarrierConf 행을 먼저 보고 없으면 `cm_map_df_full`에서 (eNodeBID, cell-num)으로 찾는 이중 조회로 방어적으로 구현 — **실데이터로 확인 후 필요하면 한쪽으로 단순화 필요(확인 필요 목록에 추가)**. band 매칭은 기존 `_get_target_cells_str`와 동일하게 SectorList의 Band 컬럼명(예: "B1")을 그대로 사용(기존 DSS 매칭의 'B' 접두어 제거 방식과는 다른 컨벤션 - Target Cell Num 추출이 이미 이 방식으로 동작 중이라 그에 맞춤).
  * **검증**: `_enforce_protected_band` 단위 테스트로 미배치/이미 보장됨/강제 조정 필요(eMTC·ENDC anchor 각각)/CarrierConf 미보유 시 cm_map_df_full 폴백까지 모두 확인. 합성 데이터로 `run_analysis`를 실제 실행해 강제 제외된 cell이 ES Level 1에서 빠지고 ES Level 7(항상 켜짐)에 포함되며 Note가 정확히 기록됨을 확인. Cell-RU 매핑은 저장 후 재시작 시 가장 최근 파일이 자동 로딩되고, 매핑 파일이 없으면 팝업이 뜨지 않음을 확인. `python -m py_compile` 통과.
  * **적용 순서**: 사용자 지시대로 `esm_r15_0.py`에 먼저 반영·검증한 뒤, 동일한 수정(Cell-RU 매핑 저장/자동 불러오기 + `_enforce_protected_band` 등 eMTC/ENDC anchor 보장 로직)을 `esm_r16_0.py`에도 그대로 포팅 완료(Deep Sleep 로직과는 독립적이라 상호작용 없음). 기존 v5.4/v5.5 회귀 테스트도 재실행해 부작용 없음을 확인. `python -m py_compile` 양쪽 파일 모두 통과.

* **[v5.8 / esm_r15_0.py 우선 반영 후 esm_r16_0.py에 포팅 완료] (2026-07-09) 단순화: eMTC/ENDC anchor 속성 조회를 cm_map_df_full 단일 조회로 단순화**
  * **배경**: v5.7에서 남겨둔 확인 필요 사항(`conf-emtc-switch`/`endc-anchor-type`/`endc-support`가 CarrierConf/CM Data 중 어디에 있는지)을 사용자가 확인: "conf-emtc-switch/endc-anchor-type/endc-support는 병합된 CM데이터에 있어. eNodeBID, cell-num, Sector 열(인덱스)을 가지고 있어서, SectorList와 CarrierConf를 이용하면, 각 cell-num-Band를 연결할 수 있고, band별 priority 값들도 연결할 수 있어." — 즉 이 세 속성은 CM Data(`cm_map_df_full`, eNodeBID+cell-num 인덱스)에만 있고, CarrierConf는 band<->cell-num 매핑과 ES priority/ENDC_priority 값만 제공.
  * **수정**: `_lookup_cell_attr`/`_is_emtc_enabled`/`_is_endc_anchor_enabled`에서 CarrierConf 조회 분기(방어적 이중 조회)를 제거하고 `cm_map_df_full`(eNodeBID+cell-num)만 조회하도록 단순화. band<->cell-num 매핑과 priority 조회(carrier_df 기반)는 그대로 유지.
  * **검증**: 새 데이터 모델(conf-emtc-switch 등은 cm_map_df_full에, ES priority/ENDC_priority는 carrier_df에)에 맞춰 단위 테스트를 다시 작성해 재실행 - 서비스 미배치/이미 보장됨/강제 조정(eMTC·ENDC anchor)/anchor-type 불일치·support=False 케이스 모두 통과. `run_analysis` 합성 데이터 통합 테스트도 갱신해 재확인. `python -m py_compile` 양쪽 파일 모두 통과.
  * **적용 순서**: `esm_r15_0.py`에 먼저 반영 후 `esm_r16_0.py`에 동일 포팅.

* **[v5.9 / esm_r15_0.py 우선 반영 후 esm_r16_0.py에 포팅 완료] (2026-07-09) 기능 개선: ES Level이 아예 생성되지 않은 sector도 에너지 절감효과 결과표에 포함(절감 0)**
  * **배경**: 사용자 요청 — "ES 적용대상 cell/band를 찾지 못해, ES level 1도 생성되지 않은 경우, 시뮬레이션을 수행 필요는 없어. 다만 시뮬레이션 기반으로 Energy Saving 이득을 계산하니까, 에너지 절감효과 등을 계산할 때는 ES level이 없더라도 Sectorlist에 있는 sector들을 모두 포함하도록 코드를 수정해줘." eMTC/ENDC anchor 강제 조정(v5.7) 등으로 ES 적용대상 band가 하나도 남지 않으면 ES Level 1 자체가 생성되지 않고, `_run_es_level_simulation`도 그 sector를 건너뛰는 게 맞지만(시뮬레이션은 실제로 불필요), `_calc_es_level_simulation_savings`가 그 결과(summary_df)만 순회해 그런 sector가 절감효과 결과표에서 통째로 사라지는 문제가 있었음.
  * **수정**: 새 헬퍼 `_get_all_sectorlist_pairs()`(현재 Target Cat_ID의 SectorList 전체 (eNodeBID, Sector) 쌍)를 추가. `_calc_es_level_simulation_savings`는 summary_df에 있는 sector는 기존과 동일하게 계산하고, SectorList에는 있지만 summary_df에 없는 sector는 소모 에너지(Energy Stat 기반, ES 정책과 무관)만 채우고 절감에너지=0(esm_r16_0.py는 Deep Sleep 추가 절감 컬럼도 0)인 행을 추가. summary_df가 완전히 비어 있어도(모든 sector가 ES Level 없음) 빈 표 대신 SectorList 전체를 0-절감 행으로 채운 표를 반환하도록 변경. 전체 합계 행은 기존 로직을 그대로 재사용(모든 행의 합이라 자동 반영).
  * **적용 범위**: 시뮬레이션 기반 계산(`_calc_es_level_simulation_savings`, Advanced Settings 기본값인 Mode 2/3에서 사용)에만 적용 — NC2 기반(`_calc_all_savings`, Mode 1)은 ES Level별 상세 행(Target Cell Num/Board Type 등) 구조라 의미 있는 0-행을 만들기 어렵고, 사용자 요청도 "시뮬레이션 기반" 계산을 명시적으로 지목해 이번에는 다루지 않음.
  * **검증**: SectorList에 3개 sector(1개는 ES 정책 있음, 2개는 ES 적용대상 band 없음)를 두고 호출 - 정책 없는 2개 sector도 절감에너지 0, 소모 에너지는 정상값으로 나타나고 전체 합계도 3개 sector 소모량을 모두 반영함을 확인. summary_df를 완전히 비워도 SectorList 3개 sector가 모두 0-절감 행으로 채워진 표를 반환함을 확인(빈 DataFrame이 아님). 양쪽 파일 모두 동일하게 통과. `python -m py_compile` 통과.
  * **적용 순서**: `esm_r15_0.py`에 먼저 반영·검증 후 `esm_r16_0.py`에 동일 포팅.

## 5. 진행 중인 작업 및 다음 단계 (To-Do / Next Steps)

* 현재 상태: v5.9(`esm_r15_0.py` + `esm_r16_0.py` 모두 반영 완료) - ES 적용대상 cell/band를 찾지 못해 ES Level이 아예 생성되지 않은 sector도 에너지 절감효과 결과표(시뮬레이션 기반)에 절감 0으로 포함되도록 수정. 이전 v5.8에서 eMTC/ENDC anchor 속성(`conf-emtc-switch`/`endc-anchor-type`/`endc-support`) 조회처가 CM Data(`cm_map_df_full`)로 확정되어 v5.7의 CarrierConf 폴백 조회를 제거·단순화했고, v5.7에서 Cell-RU 매핑 저장/자동 불러오기 기능과 eMTC/ENDC anchor 서비스 보장을 위한 ES 적용대상 band 강제 조정 규칙을 새 라운드(esm-r0-cellru-mapping 브랜치)의 두 파일 모두에 추가했고, v5.6(`esm_r15.py`+`esm_r16.py`, 구 라운드)에서 설정 자동 저장/불러오기 + Input 폴더 파일 자동 선택 + Output 폴더 통합 편의 기능을 양쪽 파일 모두에 반영하며 구 라운드를 마무리했고, v5.3에서 ES Level 시뮬레이션의 PRB/Tput 단위 불일치를 수정했고, v5.0(`esm_r16.py`)에서 Deep Sleep 기능을 신규 추가하며 여기까지 도달.
* 확인 필요:
  1. Google Drive(`VibeCoding/ESM`) 저장 방식 — 사용자가 스킵 요청, 추후 처리 방법 논의 필요.
  2. 실제 Cell 단위/RU 단위 학습데이터 CSV의 실제 컬럼명이 `_parse_learning_cell_file()`/`_parse_learning_ru_file()`의 매핑 규칙과 맞는지, CM의 `PA-shared-cell` 컬럼명이 실제와 일치하는지 실데이터로 확인 필요.
  3. GUI 환경(tkinterdnd2 설치된 로컬 PC)에서 실제 CM 파일/Cell 단위/RU 단위 학습데이터 파일을 드래그 앤 드롭해 "학습 실행" 버튼 동작 확인 필요, 특히 신규 "수식(Formula)" 탭/다운로드, 3열로 넓어진 시각화 탭(가로 스크롤 필요할 수 있음)과 scipy 설치 여부(ExpSat 모델 활성화 조건) 함께 확인 필요.
  4. **다음 결정 대기(기존)**: 실데이터로 학습 실행 후 `Recommended Model`(자동 추천)과 그래프 모양을 함께 보고 사용자가 최종 확인 — 그룹(Board Type×공유여부×Sector Group)마다 추천 모델이 다르게 나올 수 있으므로 그대로 채택할지, 특정 그룹은 수동으로 다른 모델을 지정할지 결정.
  5. **다음 결정 대기(v2.7)**: 실데이터로 `Better Axis (R² 기준)` 컬럼과 두 산점도(Loading_traffic 비율 vs Active_RB 절대)를 비교 — Active_RB 축이 Sector Group별 차이를 뚜렷하게 줄여준다면, 다음 라운드에서 Sector Group을 그룹핑 축에서 제거하고 Active_RB 기반 단일 커브로 결과를 단순화할지 결정.
  6. **다음 결정 대기(v4.2)**: 사용자가 실제 데이터로 Mode 1/2/3 비교 결과를 검토한 뒤 — (a) 최종적으로 어느 모드를 기본으로 채택할지, (b) Initial level을 0이 아닌 값으로 최적화하는 기능을 다음 라운드에 결정.
  7. **다음 결정 대기(v5.0)**: 사용자가 Dual Band RU(RU HW 1개에 ru-port-id 2개)를 어떻게 식별/처리할지 방법을 알려줄 예정 — 현재는 Single Band RU만 지원.
  8. **다음 결정 대기(v5.3)**: 사용자가 실데이터로 재확인해 다른 Sector들도 이제 ES level이 정상적으로 적용되는지 검증 필요(esm_r15.py/esm_r16.py 양쪽 모두).
  9. **다음 결정 대기(v5.4)**: 사용자가 실제 로컬 PC에서 `esm_r15.py`/`esm_r16.py`를 실행해 Input 폴더 자동 선택(파일명/헤더 규칙)과 `esm_settings.json` 저장/불러오기가 실제 CM/Traffic/Energy Stat/학습데이터 파일로도 의도대로 동작하는지, 안내 팝업 문구가 실제 상황에 적절한지 확인 필요.
  10. **다음 결정 대기(v5.5)**: 사용자가 실제로 Optimizer 실행 -> Energy Dashboard 사용 순서로 이어서 써보고, 결과가 정말 같은 `Output/<timestamp>/` 폴더에 모이는지, 반복 다운로드 시 생기는 `_2`/`_3` 폴더 분리 방식이 실사용에 괜찮은지(선호하면 파일명 index 방식으로 바꿀 수도 있음) 확인 필요(esm_r15.py/esm_r16.py 양쪽 모두).
  11. **Energy Dashboard 연동 보류 중(기존)**: Learning Energy Curve 학습 결과(Idle/PA off 보정값, 채택된 Energy Curve 모델)를 절감 예측 로직에 반영할지는 별도로 대기 중.
  12. **다음 결정 대기(v5.8)**: eMTC/ENDC anchor 판정 알고리즘(eMTC: `ES priority`가 가장 큰 band 선택, ENDC anchor: `ENDC_priority`가 가장 작은 band 선택·-1 제외)을 사용자가 실데이터로 재검증 필요 — 데이터 소스(cm_map_df_full)는 확정되었으나 실제 CM Data의 `conf-emtc-switch`/`endc-anchor-type`/`endc-support` 값 표기(Enable/Disable, True/False 등)가 코드의 `_TRUTHY_TOKENS` 판정과 맞는지 확인 필요.
  13. **다음 결정 대기(v5.9)**: ES Level 없는 sector를 절감효과 결과표에 포함하는 수정은 시뮬레이션 기반 계산(`_calc_es_level_simulation_savings`, Mode 2/3)에만 적용했음 — NC2 기반(`_calc_all_savings`, Mode 1)도 동일하게 다뤄야 하는지 사용자 확인 필요(요청 시 ES Level별 상세 행 구조를 어떻게 0-표시할지 별도 설계 필요).
* 다음 대기 작업: (사용자가 실데이터/실제 환경으로 재확인한 결과를 알려줄 예정)

---
*Last Updated: 2026-07-09*
*AI Directive Status: Active (Always Read First, Always Update Post-Task)*
