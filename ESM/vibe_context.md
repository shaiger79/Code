# 📡 ESM (Energy Saving Manager) Project Vibe Context

## 1. 프로젝트 개요 (Project Overview)
* **목적**: 이동통신(4G/5G) 네트워크의 Traffic Data(PM)와 Energy Stat Data를 분석하여, Energy Saving(ES) 적용 임계조건을 도출하고 예상 절감 에너지를 예측하는 GUI 기반 최적화 도구 개발.
* **주요 스택**: Python, Tkinter (UI), Pandas (데이터 처리), Matplotlib (시각화), scikit-learn(선택적 — Learning Energy Curve의 Isotonic Regression/MSE/MAE 계산에 사용, 미설치 시 numpy로 직접 구현한 폴백으로 자동 대체), scipy(선택적 — Learning Energy Curve의 지수포화 ExpSat 모델 `curve_fit`에 사용, 미설치 시 해당 모델만 비활성화)
* **핵심 지표**:
  * PM: `IP Tput`, `UsedRB`, `AirMacDLByte`, `AirMacULByte`
  * Energy: `RuPowerTot`, `RuPowerCnt` (RU별 시간당 소모 전력)
  * Efficiency: Energy Efficiency (EE) = (AirMacDLByte + AirMacULByte) / Consumed [Wh]
* **버전 파일 관리**: `ESM/esm_r11.py`, `ESM/esm_r12.py`, `ESM/esm_r13.py`(모두 과거 버전, 더 이상 수정하지 않음)와 `ESM/esm_r14.py`(최신 개발 버전)를 함께 보관한다. 새 기능/변경은 항상 최신 버전 파일에 반영하고, 이전 버전은 롤백/비교용으로 그대로 남겨둔다. 다음 라운드부터는 `esm_r14.py`를 복제해 `esm_r15.py`로 이어간다.

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
    - Loading_traffic vs Consumed Power 산점도에 학습된 Energy Curve 수식을 텍스트 박스로 직접 표시: `P ≈ {절편} + {기울기} × Loading_traffic, R²(Val)={값}`.
    - Idle/PA off Reference vs 실측 보정값 막대 위에 실제 수치(W) 라벨 표시.
    - 하단 요약의 Board Type별 평균 기울기 막대, Idle/PA off 보정폭(Delta) 막대에도 수치 라벨 표시(양수/음수 모두 라벨 위치 자동 조정).
  * **Energy Dashboard 연동은 보류**: 사용자 확인 결과, 학습 결과의 유의미성(실데이터 검증)을 먼저 확인한 뒤 적용 방법을 결정하기로 함 — 이번 라운드에는 연동하지 않음.
  * **검증**: matplotlib을 설치한 임시 가상환경에서 Agg(헤드리스) 백엔드로 신규 라벨/수식 텍스트 렌더링 로직만 별도 재현해 실행 — NaN 값이 섞인 Board Type(레퍼런스 데이터 일부 누락 케이스), 양/음수가 혼재된 Delta 막대 등 엣지 케이스에서도 예외 없이 렌더링됨을 확인.

* **[v2.2 / esm_r12.py] (2026-07-03) 학습데이터 2-파일 분리 + PA-shared-cell 기반 RU path 보정**
  * **학습데이터 파일 2개로 분리**: 실제 데이터는 집계 단위(index)가 서로 달라 파일이 1개가 아니라 2개임을 확인 — 반영.
    - **Cell 단위 학습데이터** (`self.learn_cell_file`): `Ne unique id` + `Cnum` 기준. `Cellunavailabletimedown s`(초), `UsedRB`, `UsedRB_t`, `nRB`.
    - **RU 단위 학습데이터** (`self.learn_ru_file`): `Ne unique id` + `Bid`/`RuPort`/`Cascade` 기준. `Consumed Power`.
    - 두 파일 모두 CSV 헤더를 보고 자동 분류하는 `_classify_learning_files_drop()`을 추가해, 두 입력창 중 어디에 드롭하든(한 번에 2개를 같이 드롭해도) 알맞은 변수에 채워지도록 구현. `_bind_widget_drop()`도 다중 파일 드롭(`on_drop(paths: list)`)을 지원하도록 확장. "📁 두 파일 한번에 선택" 버튼으로 파일 대화상자에서도 2개를 한 번에 선택 가능.
    - 이에 따라 Consumed Power는 더 이상 Cell 단위로 평균 낼 필요 없이(원래부터 RU path 단위로 이미 집계되어 있으므로) RU path + 시간 기준으로 바로 병합하도록 단순화(`_parse_learning_ru_file` → `ru_power_hourly` → 직접 merge). Cell off(초)/Loading_traffic/Loading_total만 여전히 "동일 RU path를 공유하는 Cell들의 평균/비율의 합"으로 집계.
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
    - **마우스 스크롤 미작동 수정**: 임베드된 matplotlib 캔버스 위에서는 `canvas.bind()`만으로 휠 이벤트가 잡히지 않는 문제 — 스크롤 컨테이너(`plot_outer`)의 `<Enter>`/`<Leave>` 이벤트에서 `bind_all`/`unbind_all`로 마우스 휠 핸들러를 그때그때 등록/해제하는 방식으로 교체(Linux `Button-4`/`Button-5`, Windows/Mac `<MouseWheel>`의 `event.delta` 모두 처리).
    - **창 크기에 따른 그래프 크기 자동 조정**: `self.learning_plot_canvas`의 실제 픽셀 폭을 읽어 그림 폭(inch)을 동적으로 계산하는 `_get_plot_fig_width_inches()`를 추가하고, `<Configure>` 리사이즈 이벤트를 300ms 디바운스(`self.after`)해 학습을 다시 돌리지 않고 마지막 결과(`self.learn_hw_df`/`self.learn_pooled_active_points`)로 그래프만 다시 그리는 `_redraw_learning_plots_if_ready()`를 추가.
    - **그래프 간격/겹침 개선**: `plt.tight_layout()` → `constrained_layout=True` + `fig.set_constrained_layout_pads(w_pad=0.35, h_pad=0.55, hspace=0.18, wspace=0.14)`로 교체, 행당 높이를 4.6→5.8인치로 확대, 그래프 제목을 2줄로 나누고 폰트 크기를 10으로 낮춰 라벨 겹침을 줄임.
  * **② 로그모델 → 지수포화(Exponential Saturation) 모델 교체**: `Consumed Power = a − b·exp(−k·Loading_traffic)` (scipy `curve_fit`으로 비선형 최소자승 적합, 초기값은 데이터 범위 기반으로 자동 추정, 파라미터에 물리적으로 타당한 bounds 설정). RU 전력증폭기가 부하 증가에 따라 증가폭이 점점 줄고 특정 최대치(포화 전력)로 수렴하는 특성을 로그모델보다 물리적으로 더 정확히 표현. `HAS_SCIPY` 플래그(tkinterdnd2/tkcalendar/sklearn과 동일한 패턴)를 신규 추가해 scipy 미설치 환경에서도 앱이 깨지지 않고 해당 모델만 비활성화되도록 구성(`_fit_exp_saturation()`이 `None`을 반환하면 그 RU/그룹은 ExpSat 결과 없이 나머지 2종 모델로만 비교). 컬럼명 전체를 `Log *` → `ExpSat *`(a/b/k, R2/MSE/MAE Val/Test)로 교체하고 `_recommend_model` 기본 순서도 `('Linear', 'ExpSat', 'Isotonic')`로 변경.
  * **③ Sector 내 Cell수 그룹핑 추가**: CM의 `cell-num`(Cnum)을 10으로 나눈 나머지를 Sector로 정의(`Sector = Cnum % 10`)하고, 같은 `eNB_ID`+`Sector` 내 서로 다른 Cell 개수를 `Sector_Cell_Count`로 계산. RU path에 연결된 Cell(들)이 속한 Sector의 Cell수를 대표값(최빈값)으로 삼아 `Sector Group`(예: `3Cell/Sector`, `1Cell/Sector`) 레이블을 부여하고, 기존 `Board Type × Shared/Exclusive` 2축 그룹핑에 `Sector Group`을 세 번째 축으로 추가(`hw_df = ru_df.groupby(['Board Type', 'Shared', 'Sector Group'])`). 예: 같은 RU HW의 Shared RU라도 Sector 내 Cell이 3개인 대상만 모아 학습한 결과와 1개인 대상만 모아 학습한 결과를 분리해서 비교 가능. 시각화(`_render_learning_plots`)도 3-tuple 그룹 순회로 갱신, 그래프 제목/하단 요약 라벨에 Sector Group 포함.
  * **④ 한글 폰트 커밋 검토/보완**: 사용자가 직접 커밋한 `plt.rcParams['font.family'] = 'Malgun Gothic'`은 Windows 전용 폰트만 지정하고 `axes.unicode_minus` 설정이 빠져 있어, macOS/Linux 환경에서는 한글이 깨지고 음수 부호(-)도 깨질 위험이 있었음 → `_KOREAN_FONT_CANDIDATES`(Malgun Gothic/AppleGothic/NanumGothic/Noto Sans CJK KR/Noto Sans KR) 리스트로 교체해 `matplotlib.font_manager`에서 실제 설치된 폰트를 확인 후 우선순위대로 선택하고, 하나도 없으면 경고 로그만 남기고 넘어가도록(크래시 방지) 수정. `axes.unicode_minus = False`도 함께 추가.
  * **검증**: 임시 가상환경(scipy/sklearn/numpy/pandas 설치)에서 4가지 모두 로직 단위 검증 — (a) 참값이 지수포화 곡선인 합성 데이터에서 `curve_fit`이 실제 a/b/k 값을 15% 오차 이내로 정확히 복원하고 R²(Val)가 Linear(0.76)보다 크게 높음(0.996)을 확인, (b) 참값이 순수 선형인 데이터에서는 여전히 Linear가 추천됨(오컴의 면도날 규칙 유지 확인), (c) 데이터가 3개 미만이거나 상수인 퇴화 케이스에서 `_fit_exp_saturation`이 예외 없이 `None`을 반환함을 확인, (d) `Cnum % 10` 기준 Sector 그룹핑이 3-Cell/1-Cell Sector를 정확히 구분하고 `Board Type × Shared × Sector Group` 3축 groupby가 그룹을 올바르게 분리 유지함을 확인. matplotlib UI 변경(스크롤/리사이즈/간격)은 앞선 라운드에서 이미 matplotlib 3.11 환경으로 렌더링 검증 완료된 패턴을 그대로 재사용.

* **[v2.7 / esm_r14.py] (2026-07-06) Linear/ExpSat 모델을 "수식(Formula)" 표로 정리 + 다운로드, Sector Group 일반화 방향 논의**
  * **배경**: 사용자가 시각화(그래프)로만 보던 Learning Energy Curve 결과를, loading 값만 넣으면 바로 ConsumedPower를 계산할 수 있는 "사용 가능한" 형태(수식/표)로 가져가고 싶다고 요청. 또한 Sector Group(1Cell/Sector vs 3Cell/Sector 등)에 따라 결과가 갈리는 문제를 더 일반적인 형태로 개선할 아이디어를 요청(사용자 제안: UsedRB당 소모전력 지표, 또는 nRB에 대한 함수로 표현).
  * **버전 분기**: 핵심 개발 원칙(2항)에 따라 `esm_r13.py`(과거 버전, 더 이상 수정 안 함)를 그대로 복제해 `esm_r14.py`(신규 최신 개발 버전)로 시작. 이번 라운드부터 모든 변경은 `esm_r14.py`에만 반영.
  * **Energy Curve 수식(Formula) 표 추가** (사용자 요청 1번):
    - 신규 `_build_formula_df(hw_df)`: HW(Board Type × Shared × Sector Group) 요약(`hw_df`)의 Linear/ExpSat 계수를, `ConsumedPower = 절편 + 기울기 × Loading_traffic`(Linear) / `ConsumedPower = a − b × exp(−k × Loading_traffic)`(ExpSat) 형태의 텍스트 수식 문자열로 변환한 `self.learn_formula_df`를 생성. Board Type/Shared/Sector Group/RU Count/Recommended Model과 함께 R²·MSE·MAE(Val), 원본 계수(Slope/Intercept, a/b/k)도 그대로 포함해 사람이 읽는 수식과 프로그램적으로 재사용 가능한 계수를 한 표에서 모두 제공.
    - Isotonic은 계수가 없는 비모수(non-parametric) 모델이라 닫힌 형태 수식으로 표현할 수 없으므로 이 표에는 포함하지 않고, 해당 그룹의 `Recommended Model`이 Isotonic이면 `Note` 컬럼에 "수식 없음 — RU 단위 상세 결과/시각화의 곡선 참고" 안내만 표시.
    - Learning Energy Curve 결과 탭에 " 📐 Energy Curve 수식(Formula) " 탭을 신규 추가(RU 단위 상세 / HW 요약 / **수식(Formula)** / 시각화, 총 4개 탭)하고, `Loading_traffic = ΣUsedRB_t/ΣnRB` 정의를 안내 문구로 표시. "💾 Energy Curve 수식(Formula) CSV 다운로드" 버튼 추가.
  * **Sector Group 일반화 — Active_RB(절대 활성 RB) 축 병행 진단 추가** (사용자 요청 2번, 사용자가 "지금 병행 진단 추가"를 선택해 바로 구현):
    - 현재 `Loading_traffic`은 RU path에 연결된 총 nRB로 나눈 **비율(0~1)** 이라, 셀 1개짜리 RU path와 3개짜리(3Cell/Sector) RU path가 같은 Loading_traffic 값이어도 실제로 구동되는 절대 RB 개수(및 PA/캐리어 개수)는 서로 다름 — 이 절대 규모 차이가 Sector Group별 기울기/ExpSat 곡선이 갈리는 주된 원인으로 추정.
    - 사용자 제안 ① "UsedRB당 소모전력"은 Loading이 0에 가까울 때 분모가 0에 가까워져 값이 발산하므로 회귀의 x/y축으로는 채택하지 않음(향후 별도 효율 KPI로는 유효할 수 있음, 이번 라운드에는 미구현).
    - 사용자 제안 ② "nRB에 대한 함수로 표현"을 채택 — 비율(`Loading_traffic`) 외에 **`Active_RB`(=ΣUsedRB_t, 나누기 전 절대 활성 RB 수)** 를 두 번째 회귀 입력 축으로 신규 추가하고, 기존 축(비율)은 그대로 유지한 채 두 축을 **나란히 병행 학습**하도록 구현(v2.3→v2.4의 "공유여부 vs nRB구간" 진단과 동일한 패턴).
    - **구현 상세**: 기존 per-RU 학습 로직(Linear/ExpSat/Isotonic 3종 모델 적합 + 지표 계산)을 신규 헬퍼 `_fit_three_models(x_train,y_train,x_val,y_val,x_test,y_test)`로 추출해, `Loading_traffic`(비율)과 `Active_RB`(절대, `ru_loading_hourly['Active_RB'] = UsedRB_t_sum`) 양쪽에 **동일한 Train/Val/Test 분할**을 재사용해 공정 비교. RU 단위 결과(`ru_df`)에 `RB Linear/ExpSat/Isotonic *`, `RB Recommended Model` 컬럼을 추가하고, HW 요약(`hw_df`)에도 동일하게 `RB Avg *` 컬럼과 `RB Recommended Model`을 추가. 그룹별로 두 축 중 어느 쪽 최고 R²(Val)가 더 높은지 비교하는 `Best R2 (Loading_traffic 비율)` / `Best R2 (Active_RB 절대)` / `Better Axis (R² 기준)`(차이 ≤0.02면 "유사") 컬럼을 신규 추가해, 실데이터에서 어느 축이 Sector Group 차이를 더 잘 흡수하는지 한눈에 판단할 수 있게 함.
    - **수식 표 확장**: `_build_formula_df`에 `Linear/ExpSat Formula (Active_RB)` 컬럼과 `Better Axis` 컬럼을 추가해, 두 축의 수식을 한 표에서 비교 가능.
    - **시각화 확장**: 기존 산점도+3모델 그리기 로직을 `_plot_axis_models()` 공용 헬퍼로 추출해 두 축(비율/절대)에 재사용. 그룹당 그래프 배치를 2열→3열(① Loading_traffic 산점도 ② Active_RB 산점도 ③ Idle/PA off 막대)로 확장하고, 하단 요약도 R²비교 막대를 축별로 하나씩(비율/절대) 나란히 표시.
    - **다음 단계**: 실데이터로 학습을 돌려 `Better Axis` 컬럼과 두 산점도(비율 vs 절대)를 비교해, Active_RB 축이 Sector Group 차이를 뚜렷하게 줄여준다면 다음 라운드(`esm_r15.py`)에서 Sector Group을 그룹핑 축에서 제거하고 Active_RB 기반 단일 커브로 정리하는 것을 검토.
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

## 5. 진행 중인 작업 및 다음 단계 (To-Do / Next Steps)
* 현재 상태: v2.9(`esm_r14.py`) - Data I/O & CM 탭 드래그 앤 드롭 파일 분류(Traffic vs Energy Stat) 버그 수정 완료. 이전 v2.8에서 CSV 다운로드 인코딩(`utf-8-sig`) 버그를 수정했고, v2.7에서 Learning Energy Curve의 Linear/ExpSat 모델을 "수식(Formula)" 표(+CSV 다운로드)로 정리했고, Sector Group 일반화를 위해 `Active_RB`(절대 활성 RB) 축을 기존 `Loading_traffic`(비율) 축과 나란히 병행 학습/시각화/수식화하는 진단 기능까지 구현 완료(로직 End-to-End 합성 데이터 검증 완료, GUI 실행 테스트는 로컬 확인 필요).
* 확인 필요:
  1. Google Drive(`VibeCoding/ESM`) 저장 방식 — 사용자가 스킵 요청, 추후 처리 방법 논의 필요.
  2. 실제 Cell 단위/RU 단위 학습데이터 CSV의 실제 컬럼명이 `_parse_learning_cell_file()`/`_parse_learning_ru_file()`의 매핑 규칙과 맞는지, CM의 `PA-shared-cell` 컬럼명이 실제와 일치하는지 실데이터로 확인 필요.
  3. GUI 환경(tkinterdnd2 설치된 로컬 PC)에서 실제 CM 파일/Cell 단위/RU 단위 학습데이터 파일을 드래그 앤 드롭해 "학습 실행" 버튼 동작 확인 필요, 특히 신규 "수식(Formula)" 탭/다운로드, 3열로 넓어진 시각화 탭(가로 스크롤 필요할 수 있음)과 scipy 설치 여부(ExpSat 모델 활성화 조건) 함께 확인 필요.
  4. **다음 결정 대기(기존)**: 실데이터로 학습 실행 후 `Recommended Model`(자동 추천)과 그래프 모양을 함께 보고 사용자가 최종 확인 — 그룹(Board Type×공유여부×Sector Group)마다 추천 모델이 다르게 나올 수 있으므로 그대로 채택할지, 특정 그룹은 수동으로 다른 모델을 지정할지 결정.
  5. **다음 결정 대기(v2.7)**: 실데이터로 `Better Axis (R² 기준)` 컬럼과 두 산점도(Loading_traffic 비율 vs Active_RB 절대)를 비교 — Active_RB 축이 Sector Group별 차이를 뚜렷하게 줄여준다면, 다음 라운드(`esm_r15.py`)에서 Sector Group을 그룹핑 축에서 제거하고 Active_RB 기반 단일 커브로 결과를 단순화할지 결정. 반대로 차이가 없거나 Active_RB 축도 여전히 Sector Group별로 갈린다면 Sector Group 축을 유지하고 다른 원인(예: Board Type 내 세부 HW 리비전 차이 등)을 살펴봐야 함.
  6. **Energy Dashboard 연동 보류 중**: 사용자가 실데이터로 학습 결과(Idle/PA off 보정값, 채택된 Energy Curve 모델)의 유의미성을 먼저 검증한 뒤, `_calc_all_savings` 등 절감 예측 로직에 어떻게 반영할지 결정하기로 함 — 다음 라운드 대기.
* 다음 대기 작업: (사용자 요청 대기 중 — 실데이터로 Better Axis 비교 결과를 보고 Sector Group 축 유지/대체 여부 확정 시 `esm_r15.py`에서 반영)

---
*Last Updated: 2026-07-06*
*AI Directive Status: Active (Always Read First, Always Update Post-Task)*
