# 📡 ESM (Energy Saving Manager) Project Vibe Context

## 1. 프로젝트 개요 (Project Overview)
* **목적**: 이동통신(4G/5G) 네트워크의 Traffic Data(PM)와 Energy Stat Data를 분석하여, Energy Saving(ES) 적용 임계조건을 도출하고 예상 절감 에너지를 예측하는 GUI 기반 최적화 도구 개발.
* **주요 스택**: Python, Tkinter (UI), Pandas (데이터 처리), Matplotlib (시각화)
* **핵심 지표**:
  * PM: `IP Tput`, `UsedRB`, `AirMacDLByte`, `AirMacULByte`
  * Energy: `RuPowerTot`, `RuPowerCnt` (RU별 시간당 소모 전력)
  * Efficiency: Energy Efficiency (EE) = (AirMacDLByte + AirMacULByte) / Consumed [Wh]
* **버전 파일 관리**: `ESM/esm_r11.py`, `ESM/esm_r12.py`(모두 과거 버전, 더 이상 수정하지 않음)와 `ESM/esm_r13.py`(최신 개발 버전)를 함께 보관한다. 새 기능/변경은 항상 최신 버전 파일에 반영하고, 이전 버전은 롤백/비교용으로 그대로 남겨둔다. 다음 라운드부터는 `esm_r13.py`를 복제해 `esm_r14.py`로 이어간다.

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

## 5. 진행 중인 작업 및 다음 단계 (To-Do / Next Steps)
* 현재 상태: v2.3(`esm_r13.py`) - Learning Energy Curve 전면 개편 + 결과 CSV 다운로드/시각화 라벨링 + 학습데이터 2-파일 분리 + PA-shared-cell 보정 + 기울기 분산 진단(공유여부/nRB 구간별 세분화)까지 완료 (로직 End-to-End 합성 데이터 검증 완료, GUI 실행 테스트는 로컬 확인 필요).
* 확인 필요:
  1. Google Drive(`VibeCoding/ESM`) 저장 방식 — 사용자가 스킵 요청, 추후 처리 방법 논의 필요.
  2. 실제 Cell 단위/RU 단위 학습데이터 CSV의 실제 컬럼명이 `_parse_learning_cell_file()`/`_parse_learning_ru_file()`의 매핑 규칙과 맞는지, CM의 `PA-shared-cell` 컬럼명이 실제와 일치하는지 실데이터로 확인 필요.
  3. GUI 환경(tkinterdnd2 설치된 로컬 PC)에서 실제 CM 파일/Cell 단위/RU 단위 학습데이터 파일을 드래그 앤 드롭해 "학습 실행" 버튼 동작 확인 필요.
  4. **다음 결정 대기**: 실데이터로 "[r13] 공유여부별 비교"/"[r13] nRB 구간별 비교" 결과를 보고, 기울기 분산을 더 잘 설명하는 기준을 하나 채택하거나 두 기준을 조합해 더 세분화할지 결정.
  5. **Energy Dashboard 연동 보류 중**: 사용자가 실데이터로 학습 결과(Idle/PA off 보정값, Loading 기울기)의 유의미성을 먼저 검증한 뒤, `_calc_all_savings` 등 절감 예측 로직에 어떻게 반영할지 결정하기로 함 — 다음 라운드 대기.
* 다음 대기 작업: (사용자 요청 대기 중)

---
*Last Updated: 2026-07-03*
*AI Directive Status: Active (Always Read First, Always Update Post-Task)*
