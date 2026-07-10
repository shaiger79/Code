# 📡 ESM (Energy Saving Manager) Project Vibe Context

## 1. 프로젝트 개요 (Project Overview)

* **목적**: 이동통신(4G/5G) 네트워크의 Traffic Data(PM)와 Energy Stat Data를 분석하여, Energy Saving(ES) 적용 임계조건을 도출하고 예상 절감 에너지를 예측하는 GUI 기반 최적화 도구.
* **주요 스택**: Python, Tkinter(UI), Pandas(데이터 처리), Matplotlib(시각화), scikit-learn(선택적 — Learning Energy Curve의 Isotonic Regression/MSE/MAE, 미설치 시 numpy 폴백), scipy(선택적 — ExpSat 모델 `curve_fit`, 미설치 시 해당 모델만 비활성화), tkinterdnd2(선택적 — 드래그 앤 드롭), tkcalendar(선택적 — 날짜 선택기).
* **핵심 지표**: PM(`IP Tput`/`UsedRB`/`AirMacDLByte`/`AirMacULByte`), Energy(`RuPowerTot`/`RuPowerCnt`), Efficiency(EE = (AirMacDLByte+AirMacULByte)/Consumed[Wh]).

### 1-1. 버전 파일 관리 (2026-07-09 기준 재정리)

* **Base Version — `ESM/esm_r15_0.py`**: `esm_r11.py`~`esm_r16.py`(구 라운드, `esm_r15.py`/`esm_r16.py`까지)를 거쳐 안정화된 기준 버전. 더 이상 별도로 수정하지 않고, 새 라운드(Branch)의 시작점(clone 대상)으로만 사용한다. §4 참고.
* **`ESM/esm_r16_0.py`**: `esm_r15_0.py` + Deep Sleep(구현에 결함이 있었던 첫 버전)을 포함한 병행 파일. `esm_r15_0.py`와 함께 branch `esm-r0-cellru-mapping`에 이 라운드 종료 시점 상태로 보존(더 이상 수정하지 않음) — Deep Sleep은 `esm_r17.py`에서 전면 재작성됨.
* **Branch 1 / 첫 수정본 — `ESM/esm_r17.py`**: `esm_r16_0.py`를 복제해 시작(Base의 모든 기능 + 재작성된 Deep Sleep을 이미 포함). **현재 유일한 활성 개발 파일** — 새 기능/버그 수정은 모두 여기에 반영한다. §5 참고.
* **버전 관리 원칙**: 기존 라운드 파일은 절대 수정하지 않는다. 사용자가 명시적으로 "새 라운드"를 신호하면 그 시점의 최신(또는 지정한) 파일을 복제해 다음 파일을 만든다(파일명 패턴은 그때그때 사용자가 지정하는 대로 따름 — 항상 `r{N+1}`은 아니었음, 예: `esm_r15_0`/`esm_r16_0`처럼 `_0` 접미사를 쓴 전례 있음). "버전업을 더 자주"라는 요청은 새 파일을 더 자주 만들라는 뜻이 아니라 이 문서의 changelog 항목을 더 잘게 쪼개라는 뜻이었음(§5-1 이하 항목 참고).

## 2. 핵심 개발 원칙 (Core Rules & Directives)

1. **아키텍처 보존**: 4단계 상속 구조 `AppBase` → `AppEditors` → `AppDashboard` → `ESAnalyzerApp`을 유지하며 확장한다.
2. **ID 정규화 철저**: `eNB_ID`/`Sector`/`cell-num` 등 모든 식별자는 콤마 없는 순수 숫자 문자열로 변환해 매핑 오류를 차단한다(`_extract_int_id`).
3. **방어적 코딩**: DataFrame 병합/조회 시 `empty` 체크를 철저히 하고, `SettingWithCopyWarning` 방지를 위해 명시적 `.copy()`를 사용한다.
4. **[AI 지침] 컨텍스트 최우선**: 새 세션/작업 시작 전 반드시 이 `vibe_context.md`를 읽고, 주요 변경 후에는 자동으로 갱신한다(요청 여부 무관, 매 작업 전/후 필수).
5. **버그 수정 워크플로우**: 여러 파일이 동시에 활성 상태였던 라운드(예: `esm_r15_0.py`+`esm_r16_0.py`)에서는 "한쪽에 먼저 반영·검증 → 다른 쪽에 포팅"이 표준 절차였음. 지금은 `esm_r17.py` 하나만 활성 상태이므로 해당하지 않지만, 향후 다시 병행 파일이 생기면 이 절차를 재사용한다.
6. **커밋/푸시**: 검증 완료된 변경은 사용자에게 묻지 않고 자동으로 커밋·push한다(branch에 한함). PR 생성은 이 환경에 `gh` CLI가 없어 자동화하지 않음 — compare 링크만 안내.

## 3. 시스템 아키텍처 (4단계 상속 구조)

* **`AppBase`**: 공통 헬퍼(ID 정규화, 시간/날짜 필터링, UI 기본 설정, 파일 입출력 폴더/설정 저장·자동 불러오기) + 각 하위 기능의 no-op 스텁 정의.
* **`AppEditors`**: CarrierConf/SectorList/RU Spec/CIQ JSON·Excel 로드 및 Treeview CRUD 에디터.
* **`AppDashboard`**: CM/CIQ 데이터 병합(Cell-RU Mapping, 저장/자동 불러오기 포함), Energy Stat 파싱, Energy 대시보드 시각화.
* **`ESAnalyzerApp`**: Traffic Pattern Viewer + ES 임계조건 최적화(Optimizer) + 절감량 예측 + Learning Energy Curve + ES Level 시간별 시뮬레이션 + 최종 리포트. 최상위 실행 클래스.

### 3-1. 탭(Notebook) 구성

1. 📂 Data I/O & CM — Traffic/Energy Stat/CM 파일 로드(Input 폴더 자동 선택), Cell-RU Mapping 조회, Input/Output 폴더 설정.
2. ⚙️ DB Editors — CarrierConf/SectorList/RU Spec(Deep Sleep 열 포함)/CIQ 편집.
3. ✨ Optimizer — ES 임계조건 산출(Manual/Auto 운영시간), Advanced Settings(Deep Sleep on/off 포함).
4. 📊 Traffic Pattern — Interactive/Batch 트래픽 시각화.
5. ⚡ Energy Dashboard — 소모 에너지 분석, 절감 예측(Mode 1/2/3), ES Level 시간별(15분 단위) IIR 시뮬레이션.
6. 📈 Learning Energy Curve — RU HW별 loading-energy 회귀 학습(Linear/ExpSat/Isotonic 3종 모델).

## 4. Base Version 레퍼런스: `esm_r15_0.py`

`esm_r11.py`부터 여러 라운드를 거쳐 누적된 기능을 **현재 동작 기준으로** 정리한 것. 상세한 라운드별 변경 이력(버그 발견 경위, 검증 수치 등)은 git 커밋 로그와 이 문서의 이전 버전(git history)에 남아 있음 — 필요하면 `git log -- ESM/vibe_context.md` 등으로 조회.

### 4-1. Data I/O & Cell-RU Mapping

* CM(Cell-RU Mapping) Excel + CIQ 데이터를 병합해 `cm_map_df_full`(eNB_ID/cell-num/ru-board-id/ru-port-id/ru-cascade-id/Board Type/Sector/Azimuth) 생성.
* **설정/Input·Output 폴더 자동화**: 앱 폴더(스크립트/exe 위치) 하위 `Input`/`Output`이 기본값. `esm_settings.json`(앱 폴더)에 각 탭 파라미터를 수동 저장(Data I/O 탭 버튼)하고 시작 시 자동 불러오기. Input 폴더에서 Traffic/Energy Stat/CM/Cell·RU 학습데이터 파일을 파일명 키워드·CSV 헤더로 자동 선택(후보가 1개일 때만, 아니면 팝업 안내).
* **Cell-RU 매핑 저장/자동 불러오기**: CM 처리 시 `Input/CellRUMapping_<타임스탬프>.json`으로 자동 저장, 시작 시 가장 최근 파일을 자동 불러오고 불러온 경우에만 팝업 안내.
* Output 폴더: Optimizer 실행이 그 세션의 `Output/<timestamp>/` 폴더를 확정하면, 이후 Energy Dashboard/Learning 다운로드도 같은 폴더를 재사용(반복 다운로드는 `subfolder_2`, `_3`…로 자동 분리).

### 4-2. Optimizer (ES 임계조건 산출)

* SectorList의 Band별 RB 값(양수=ES 적용대상, 음수=ES 미적용/coverage 고정)과 CarrierConf(band↔cell-num 매핑, `CoveragePriority`/`ENDC_priority`/`ES capability`/`ES priority`)로 sector별 정책을 생성. Advanced Settings: `IP Tput Margin_LTE`/`Guarantee Ratio_LTE`/`Threshold RBlowutil_LTE`/`Coe_low_LTE`/`RBLow Multiplier_LTE`/`RB Threshold Margin_LTE`/`Required IP Tput Low Util_LTE`/`N_allowedEScell_LTE`(Max ES Level 상한).
* **RBlow**: 고정값이 아니라 CarrierConf `CoveragePriority`(동률 시 ES capability→ES priority) 기준으로 Coverage band를 선택(`_select_coverage_band`) — 선택된 band는 RB<0으로 강제 전환해 ES 적용대상에서 제외하고, `RBlow = coverage band nRB × RBlow Multiplier_LTE`로 계산.
* **eMTC/ENDC anchor 서비스 보장** (`_enforce_protected_band`): eMTC(`conf-emtc-switch`)·ENDC anchor(`endc-anchor-type`=='endc-anchor' & `endc-support`) 서비스가 sector에 배치되어 있는데 이미 ES 미적용(RB<0) cell이 하나도 없으면, ES 적용대상(RB>0) band 중 우선순위 기준(eMTC: `ES priority` 최대, ENDC anchor: `ENDC_priority` 최소·-1 제외)으로 하나를 골라 강제로 ES 미적용 처리. **eMTC/ENDC anchor의 on/off 속성은 CarrierConf가 아니라 병합된 CM 데이터(`cm_map_df_full`, eNodeBID+cell-num 인덱스)에 있음** — CarrierConf는 band↔cell-num 매핑과 우선순위 값만 제공. 강제 조정이 발생하면 ESM Output Result에 `Note` 컬럼으로 사유 기록.
* **ES Level 없는 sector도 SectorList 기준으로 항상 포함**: ES 적용대상 band를 하나도 못 찾아 ES Level 1조차 생성되지 않은 sector는 시뮬레이션 대상에서 자연히 제외되지만, 에너지 절감효과 결과표(시뮬레이션 기반, §4-4)에는 SectorList에 있는 한 절감 0으로 반드시 포함된다(`_get_all_sectorlist_pairs`).
* **Deep Sleep capability 열**: Optimizer Advanced Settings의 `Deep Sleep 기능 사용`이 On일 때만 ESM Output Result에 `Deep Sleep Capability` 열 추가(off면 열 자체가 없음). §4-4/§5 참고 — 실제 판정 로직은 `esm_r17.py`에서 처음 구현.

### 4-3. Traffic Pattern / DB Editors / Learning Energy Curve

* **Traffic Pattern**: eNodeBID별 Interactive/Batch 시각화, 결과는 `<Output 폴더>/TrafficPatternAnalysis/<날짜>/`에 자동 저장.
* **DB Editors**: CarrierConf/SectorList/RU Spec(신규 `Deep Sleep` 열 포함)/CIQ를 Treeview로 CRUD, Excel/CSV/JSON 불러오기·저장.
* **Learning Energy Curve**: CM + Cell 단위/RU 단위 학습데이터 2개 CSV(파일명·헤더 자동 분류)를 입력받아, RU(eNB_ID+Bid/RuPort/Cascade, `PA-shared-cell` 그룹 보정 포함) 단위로 Idle/PA off 레퍼런스 보정값과 Loading→ConsumedPower 관계를 학습. Board Type × Shared/Exclusive × Sector Group 3축 그룹으로 집계하고, Loading_traffic(비율)/Active_RB(절대) 두 축을 병행 학습. 3종 모델(Linear/ExpSat/Isotonic, R²·MSE·MAE 비교 후 `_recommend_model`로 자동 추천) + 수식(Formula) 표 + 4개 시각화 탭. 결과는 `<Output 폴더>/LearningEnergyCurve/`에 CSV 다운로드(UTF-8 BOM으로 한글 깨짐 방지).

### 4-4. Energy Dashboard / ES Level 시간별 시뮬레이션

* **평가 기간/평가 시간**(공통 필터, Energy Dashboard 상단)과 **시뮬레이션 수행 기간**(팝업별 개별 위젯, 어느 트래픽 데이터로 Rawdata를 만들지)은 서로 다른 설정 — 시뮬레이션 자체는 ES operation window를 따라 시뮬레이션 수행 기간 내내 실행되고, summary 집계(레벨별 카운트/Tput 위반 등)만 평가 기간·시간으로 한정.
* **`_run_es_level_simulation`**: (eNodeBID, Sector) 셀 단위 15분 스텝 IIR(EWMA) 기반 레벨 결정. PRB 조건은 원시 RB 단위(`RB_Threshold_L{n}` + `RB Threshold Margin_LTE`), Tput 조건은 Mbps로 환산해 비교. **ES 윈도우 진입 시점**은 무조건 Level 0으로 1스텝 대기하지 않고, 그 직전까지 연속으로 갱신되어 온 IIR 값으로 즉시 Entering 조건을 평가해 조건이 이미 충족되어 있으면 그 스텝부터 바로 Level 1로 진입한다(데이터셋의 맨 첫 행은 자기 자신의 raw 값을 기준으로 동일하게 판단).
* **절감 에너지 계산**(`_calc_es_level_simulation_savings`, Mode 2/3 기본): 레벨 k는 `Applied_ES_Level==k`(현재 최고 레벨, fallback 위험 있어 PA off만) vs `>k`(이미 지난 레벨, 조건 충족 시 Deep Sleep 가능) 구간으로 나눠 계산. `_get_all_sectorlist_pairs`로 SectorList 전체를 포함(ES Level 없는 sector는 절감 0). Mode 1(NC2 기반)은 이 SectorList 전체 포함 로직이 아직 적용되지 않음(별도 확인 대기, §6).
* **Deep Sleep**: `esm_r15_0.py`/`esm_r16_0.py`에는 결함이 있던 초기 버전만 있고(RU 공유 판정이 그 레벨 자신의 Target Cell에만 국한되어 다른 band/sector가 실제로 꺼져 있는지 확인하지 않음), 전면 재작성된 최종 버전은 `esm_r17.py`에만 있다. §5 참고.

## 5. Branch 1 / 첫 수정본: `esm_r17.py`

`esm_r16_0.py`를 복제해 시작(2026-07-09). Base(§4)의 모든 기능을 그대로 포함하며, 이 섹션에는 **`esm_r17.py`에서만** 발생한 변경만 기록한다. 향후 세부 수정은 v17.1, v17.2 …처럼 잘게 쪼개 추가한다.

* **[v17.0] (2026-07-09) Deep Sleep 기능 전면 재작성**
  * **배경**: `esm_r16_0.py`의 Deep Sleep 판정이 "그 레벨 자신의 Target Cell만" 보고 다른 band/sector가 공유 RU를 실제로 다 껐는지 확인하지 않아 과다 절감 위험이 있었음. 사용자가 정확한 스펙을 제공.
  * **1) 옵션화**: `self.deep_sleep_enabled`(Optimizer Advanced Settings, 기본 off). On일 때만 `run_analysis`가 ESM Output Result에 `Deep Sleep Capability` 열 추가(off면 열 자체가 없어 하위 로직이 열 존재 여부로 식별, 하위 호환).
  * **2) Deep Sleep Capability 판정** (`_compute_deep_sleep_capability`): RU 공유는 병합 CM 데이터의 **(ru-board-type, ru-port-id)** 조합으로 판정(ru-board-id가 없는 셀이 있을 수 있는데, 그 경우 board-type도 몰라 Deep Sleep 판정 자체가 불가능하므로 더 정밀한 'RU Path 공유'(board-id+port-id+cascade-id)는 결국 이 그룹의 부분집합 — board-type+port-id만으로 충분, 사용자 확인). 그룹이 Deep Sleep 가능하려면: (a) board-type이 RU/MMU Spec에 `Deep Sleep` 소모전력 > 0으로 등록, (b) 그룹의 모든 cell이(다른 sector라도) 실제 ES Level 1..Max ES Level 중 하나를 배정받음(ES Level 7/no-policy이거나 결과에 없는 cell이 하나라도 있으면 그룹 전체 불가), (c) 모든 cell의 연결된 band의 CarrierConf `ES priority`가 0이 아님. eNodeBID 내 unique한 숫자 그룹 id(1부터, 불가능하면 -1) 부여.
  * **3) 전이 조건·절감량 재계산** (`_calc_es_level_simulation_savings`): "현재 최고 레벨은 PA off, 그보다 낮은 레벨만 Deep Sleep" 원칙(5분 기상 지연으로 인한 fallback 우려)은 유지하되, "낮은 레벨"이라고 곧바로 적용하지 않고 그 레벨의 Deep Sleep Capability 그룹의 다른 멤버들이 **바로 이 15분 타임스탬프에 전부 꺼져 있는지**를 확인한다 — `_run_es_level_simulation`의 `timeline_df`(이전에는 버려지던 반환값)를 저장해 eNodeBID 내 Sector들을 Time 기준으로 피벗해 매 스텝 교차 확인(다른 Sector 데이터가 없으면 보수적으로 항상 미충족 처리). 조건 미충족 스텝은 PA off로 폴백. Deep Sleep이 꺼져 있으면 이 판정을 생략하고 기존 count(Level>=k) 공식과 동일(하위 호환).
  * **검증**: 교차 Sector 그룹 id 일치/ES priority==0 배제/ES Level 없는 cell 배제/HW 미지원 배제 단위 테스트. 손계산한 2-Sector 교차 시나리오(140Wh/40Wh 보너스, 70Wh/0 보너스)가 정확히 일치, 한 Sector가 그룹 내에서 잠깐 다시 켜지는 fallback 케이스로 보너스가 정확히 그만큼 줄어듦(40→30Wh)을 확인해 진짜 15분 단위 교차 동기화가 동작함을 증명. Base(§4)의 기존 회귀 테스트 전체(eMTC/ENDC anchor, 전 SectorList 포함, 윈도우 진입, Coverage band, 설정 저장, Output 폴더 통합)를 Deep Sleep off 상태로 재실행해 하위 호환 확인. `python -m py_compile` 통과.
  * **알려진 한계(확인 대기)**: `_run_es_level_simulation` 호출부 중 raw_df가 특정 eNodeBID/Sector로 미리 필터링된 경우(예: "에너지 분석 실행"에서 특정 sector만 선택 조회) 교차-Sector 판정에 필요한 다른 sector의 timeline이 아예 없어 보수적으로 "미충족" 처리되어 절감량이 실제보다 낮게 나올 수 있음 — 실사용에서 문제가 되는지 확인 필요.

* **[v17.1] (2026-07-09) 성능 최적화: Deep Sleep 코드의 반복 DataFrame 필터링/재계산 제거**
  * `_compute_deep_sleep_capability`: cell마다 매번 carrier_df를 필터링하던 것을 (sector, cell)→ES priority dict 사전 준비로 대체(O(cell수×band수) → O(band수)+O(cell수)), board-type별 Deep Sleep 지원 여부도 미리 dict화, eNodeBID별 Python 루프+반복 필터링을 관련 eNodeBID만 좁힌 뒤 단일 groupby로 대체, `iterrows()`/`apply(axis=1)`을 `zip()` 순회로 교체. 이 과정에서 `.astype(str)`이 object dtype 컬럼의 실제 NaN을 문자열로 바꿔주지 않는 pandas 특성으로 인한 버그도 발견해 `.fillna('')` 선적용으로 수정.
  * `_calc_es_level_simulation_savings`: 같은 (eNodeBID, group id)가 여러 band/level에서 반복 참조될 때 "그룹 전체 off" Series를 캐시해 재사용, `level_deltas`/`level_group` 구성도 `cell_res` 2회 순회를 1회로 통합.
  * **검증**: v17.0에서 작성한 모든 단위/통합 테스트를 재실행해 계산 결과가 최적화 전과 완전히 동일함을 확인. `python -m py_compile` 통과.

* **[v17.2] (2026-07-10) 'ES mode Type' 열 추가 + 탭 간 공유용 RU profile table(rupt) 신설**
  * **ES mode Type** (`_calc_es_mode_type`): ESM Output Result의 'ES Level' 바로 오른쪽에 추가. ES Level n의
    delta=DRBn(n)-DRBn(n-1)(N=1이면 DRBn(0)=0)을 n번째 band의 SectorList RB값(target_nrb)과 비교해
    delta>=target_nrb→"Cell-Off", 0<delta<target_nrb→"Tx Path Off", delta<=0→"none"(ES Level 7은 공란).
    **설계 노트(사용자 확인, 중요)**: 현재 drb_n이 순수 누적합이라 delta는 항상 target_nrb와 정확히 같아
    지금은 "Cell-Off"만 나오는 것이 정상 동작 — 추후 DRBn 계산에 모드별 비율(예: Tx Path Off=0.5배)이
    반영되면 이 로직이 그대로 Tx Path Off/none을 구분해낸다(현재는 그 준비 단계).
  * **RU profile table(rupt)** (`_build_ru_profile_table`, `self.ru_profile_df`): 열
    `NE ID/Cell ID/RU Model/BID/PID/CID/PA shared/CellOff/TxPathOff/DeepSleep/SuperSleep`을
    `cm_map_df_full` + `ru_spec_df_internal`로부터 구성해 앞으로 각 탭이 공유·재사용할 수 있게 함(별도
    캐싱 없이 매번 새로 빌드 — CM 재처리 시점마다 `self.ru_profile_df` 자동 갱신, RU/MMU Spec 편집 후
    최신 상태가 필요하면 `_build_ru_profile_table()`을 직접 재호출). RU Model/BID/PID/CID는 지정된 동의어
    후보군을 정규화 비교로 찾아 우선순위상 가장 앞선 유효값('-'/빈값 제외) 채택. PA shared는 cell-num과
    PA-shared-cell(다중값, -1 제외)을 union-find로 묶어 그룹 전체(중복 제거)를 기재. CellOff/TxPathOff/
    DeepSleep/SuperSleep은 RU Model을 RU/MMU Spec DB에 3단계 fallback(완전일치→마지막 글자 제외 접두어→
    첫 '-' 이전 접두어)으로 매칭해 Idle-각 상태 값을 계산, 매칭 실패 시 4열 모두 -1. RU/MMU Spec DB 편집기
    신규 행 기본 템플릿에 'Super Sleep' 열 추가(Deep Sleep 도입 때와 동일 패턴).
  * **검증**: `_calc_es_mode_type` 단위 테스트(사용자 제시 예시 포함) + `_generate_core_policy` 통합
    테스트로 열 위치 확인. `_build_ru_profile_table` 단위 테스트로 우선순위 선택/동의어 통합/PA shared
    합집합·중복제거/3단계 매칭 3케이스+실패 시 전체 -1/빈 입력 처리/신규 Spec 행 Super Sleep 포함을 확인.
    기존 Deep Sleep 회귀 테스트 전체 재실행해 영향 없음 확인. `python -m py_compile` 통과.

## 6. 진행 중인 작업 및 다음 단계 (To-Do / Next Steps)

* **다음 결정 대기**:
  1. Google Drive(`VibeCoding/ESM`) 저장 방식 — 스킵 중, 추후 논의.
  2. 실제 Cell/RU 단위 학습데이터 CSV의 컬럼명이 파서 매핑과 맞는지, CM의 `PA-shared-cell` 컬럼명이 실제와 일치하는지 실데이터 확인 필요.
  3. Learning Energy Curve 실행(드래그 앤 드롭, Formula 탭/다운로드, 3열 시각화, scipy 활성화 여부)을 실제 GUI 환경(tkinterdnd2 설치)에서 확인 필요.
  4. `Recommended Model`(자동 추천)이 실데이터에서 그룹별로 타당한지 최종 확인.
  5. `Better Axis (R² 기준)` 비교 결과로 Active_RB 축 단일화 여부 결정.
  6. Optimizer Auto Time Mode 1/2/3 중 기본값 채택 및 Initial level 최적화 여부 결정.
  7. Dual Band RU(RU HW 1개에 ru-port-id 2개) 식별/처리 방법 — 현재 Deep Sleep RU 공유 판정은 board-type+port-id 기준이라 이 이슈와 무관해졌을 가능성 있음, 재확인 필요.
  8. ES 윈도우 진입 "1 sample 미적용" 패턴이 실데이터에서 실제로 사라졌는지, Coverage band 선택이 기대대로 동작하는지(특히 band 1~2개뿐인 sector에서 eMTC/ENDC anchor와 겹쳐 ES 적용대상 0개가 되는 빈도) 확인 필요.
  9. eMTC/ENDC anchor 판정 알고리즘(우선순위 선택 기준)과 실제 CM Data의 `conf-emtc-switch`/`endc-anchor-type`/`endc-support` 값 표기가 코드의 `_TRUTHY_TOKENS` 판정과 맞는지 확인 필요.
  10. ES Level 없는 sector를 절감효과 결과표에 포함하는 로직은 시뮬레이션 기반(Mode 2/3)에만 적용됨 — NC2 기반(Mode 1)도 필요한지 결정 대기.
  11. **[v17.0, 중요]** Deep Sleep 기능을 실제로 켜서 실데이터로 검증 필요 — board-type 컬럼명 매칭, 여러 sector에 걸친 RU 공유 실제 사례와 그룹 id 결과, 그리고 위 "알려진 한계"(특정 sector로 필터된 호출부의 교차-Sector 판정 누락) 문제.
  12. Energy Dashboard 연동 보류 중: Learning Energy Curve의 Idle/PA off 보정값·채택 모델을 절감 예측에 반영할지는 별도 대기.
  13. **[v17.2]** rupt(RU profile table)는 아직 신규 인프라일 뿐 기존 탭(예: `_calculate_est_saving`, `_compute_deep_sleep_capability`, Learning Energy Curve의 RU 판정)은 여전히 각자의 inline 로직을 그대로 사용 — 언제/어떤 탭부터 rupt로 마이그레이션할지는 사용자 지시 대기(이번 라운드는 신설만 요청됨).
  14. **[v17.2]** ES mode Type이 실제로 "Tx Path Off"/"none"을 산출하려면 DRBn 계산식에 모드별 비율(예: Tx Path Off=0.5배) 반영이 필요 — 현재는 항상 "Cell-Off"만 나오는 것이 의도된 동작(사용자 확인), 비율 반영 기능은 추후 별도 요청 대기.
* **다음 대기 작업**: 사용자가 실데이터/실제 환경으로 재확인한 결과를 알려줄 예정.

---
*Last Updated: 2026-07-10*
*AI Directive Status: Active (Always Read First, Always Update Post-Task)*
