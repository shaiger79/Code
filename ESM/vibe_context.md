# 📡 ESM (Energy Saving Manager) Project Vibe Context

## 1. 프로젝트 개요 (Project Overview)

* **목적**: 이동통신(4G/5G) 네트워크의 Traffic Data(PM)와 Energy Stat Data를 분석하여, Energy Saving(ES) 적용 임계조건을 도출하고 예상 절감 에너지를 예측하는 GUI 기반 최적화 도구.
* **주요 스택**: Python, Tkinter(UI), Pandas(데이터 처리), Matplotlib(시각화), scikit-learn(선택적 — Learning Energy Curve의 Isotonic Regression/MSE/MAE, 미설치 시 numpy 폴백), scipy(선택적 — ExpSat 모델 `curve_fit`, 미설치 시 해당 모델만 비활성화), tkinterdnd2(선택적 — 드래그 앤 드롭), tkcalendar(선택적 — 날짜 선택기).
* **핵심 지표**: PM(`IP Tput`/`UsedRB`/`AirMacDLByte`/`AirMacULByte`), Energy(`RuPowerTot`/`RuPowerCnt`), Efficiency(EE = (AirMacDLByte+AirMacULByte)/Consumed[Wh]).

### 1-1. 버전 파일 관리 (2026-07-09 기준 재정리)

* **Base Version — `ESM/esm_r15_0.py`**: `esm_r11.py`~`esm_r16.py`(구 라운드, `esm_r15.py`/`esm_r16.py`까지)를 거쳐 안정화된 기준 버전. 더 이상 별도로 수정하지 않고, 새 라운드(Branch)의 시작점(clone 대상)으로만 사용한다. §4 참고.
* **`ESM/esm_r16_0.py`**: `esm_r15_0.py` + Deep Sleep(구현에 결함이 있었던 첫 버전)을 포함한 병행 파일. `esm_r15_0.py`와 함께 branch `esm-r0-cellru-mapping`에 이 라운드 종료 시점 상태로 보존(더 이상 수정하지 않음) — Deep Sleep은 `esm_r17.py`에서 전면 재작성됨.
* **`ESM/esm_r17.py`**: `esm_r16_0.py`를 복제해 시작(Base의 모든 기능 + 재작성된 Deep Sleep 포함). r17 라운드에서 v17.1~v17.14까지 진행 후 **v17.14 상태로 동결(보존)** — 더 이상 수정하지 않는다. §5 참고.
* **Branch 2 / 현재 활성 — `ESM/esm_r18.py`**: `esm_r17.py`를 복제해 시작(2026-07-14, r17의 모든 기능 포함). **현재 유일한 활성 개발 파일** — 새 기능/버그 수정은 모두 여기에 반영한다. r18 목표: **NR(5G) ES 정책 최적화** 기능 추가(기존 LTE 위주 로직에 NR 대응 확장). 윈도우 제목이 `(r18 · v18.0)`으로 표시되어 실행 중인 빌드를 바로 확인 가능. §5-2 참고.
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

* **[v17.3] (2026-07-10) rupt DeepSleep/SuperSleep 공식 변경(PA off 기준) + Deep Sleep 절감 음수 버그 수정 + 'Level k DS Count' 진단 열**
  * **버그**: 실 Spec 데이터로 Deep Sleep을 켜니 "Deep Sleep 추가 절감 [Wh]"이 음수로 나오는 사례 발견.
    원인은 기존 `elevated_delta`(Idle-Deep Sleep, Idle 기준)가 RU/MMU Spec에 Deep Sleep 소비전력이
    PA off보다 크게 잘못 입력된 RU Model에서 pa_off_delta보다 작아져도 클램프가 없었기 때문.
  * rupt의 DeepSleep/SuperSleep을 PA off 기준(`PA off-Deep Sleep`/`PA off-Super Sleep`, 결과 음수면 0
    clamp)으로 재정의(CellOff/TxPathOff는 Idle 기준 그대로). `_power_deltas_for_level`은 pa_off_delta만
    반환하도록 단순화하고, Deep Sleep 추가절감은 신규 `_deep_sleep_bonus_delta_for_level`이 rupt에서
    직접 가져온다 - **이번 라운드부터 rupt가 실제로 절감 계산 경로에 쓰이기 시작함**(§6의 기존 "인프라만"
    메모 갱신).
  * 신규 공유 헬퍼 `_compute_deep_sleep_eligible_steps` + `_attach_deep_sleep_ds_counts`로 Sector 요약
    표(`_run_es_level_simulation` 반환 summary_df)에 'Level k DS Count' 열 추가 - 절감 Wh 계산과 동일한
    함수를 공유해 두 표의 숫자가 항상 일치, 카운트×rupt DeepSleep 값으로 손 검산 가능.
  * **검증**: 기존 정상 데이터 시나리오(140/40, 70/0, fallback 30) 값 불변 확인(대수적으로 동일 - 클램프는
    비정상 데이터에서만 차이). PA off<Deep/Super Sleep 잘못된 스펙으로 절감/보너스가 0 clamp되고 음수가
    안 됨을 확인. DS Count가 Wh 계산의 eligible_steps와 정확히 일치함을 확인. `python -m py_compile` 통과.
  * **사용자 확인 결과 → [v17.4]에서 수정**: "하나 낮은 레벨까지만 대상"은 `Applied_ES_Level > k` 판정
    자체가 아니라, 그룹의 "전체가 꺼져있는지" 판정에 있던 실제 버그를 가리키는 코멘트였음.

* **[v17.4] (2026-07-10) Deep Sleep 그룹 판정 버그 수정: 그룹 멤버가 '지금 이 순간의 현재 최고 레벨'이면 그룹 전체 Deep Sleep 불가**
  * **사용자 예시**: 현재 ES Level 4가 적용 중, Level 1~3의 Target Cell은 이미 꺼져 있음(Deep Sleep
    후보). Level 2,3의 Deep Sleep Capability=3, Level 1의 Deep Sleep Capability=6, **Level 4(현재 최고
    레벨) 자신도 Deep Sleep Capability=6** — 이 경우 gid=3인 Level 2,3만 Deep Sleep 가능하고 gid=6인
    Level 1은 불가능(공유 RU가 Level 4의 fallback 위험에 묶여 있으므로).
  * **버그**: `_group_all_off_series`가 멤버 `(sector, off_level)`마다 `Applied_ES_Level >= off_level`을
    검사했는데, `>=`는 "그 sector가 지금 정확히 그 레벨"(=그 멤버가 바로 지금의 현재 최고 레벨)인
    경우도 "안전하게 꺼짐"으로 잘못 통과시켰음 — 위 예시에서 Level 4 멤버가 이 조건을 만족해버려
    그룹 gid=6이 잘못 "전체 꺼짐"으로 판정되고 Level 1에 부당하게 보너스가 붙고 있었음.
  * **수정**: `>=` → `>`(엄격 초과)로 변경 — `passed_k = sector_level > k`와 동일한 기준으로 통일. 부작용
    (의도된 정상 동작): 어떤 sector의 특정 레벨이 그 sector의 영구적 최상위(ceiling)라면, 그 레벨을
    공유하는 그룹은 그 sector가 ES 활성인 한 영원히 Deep Sleep 불가(물리적으로 올바름).
  * **영향 범위**: [v17.3]에서 `_compute_deep_sleep_eligible_steps` 하나를 'Level k DS Count'와 절감 Wh
    계산이 공유하도록 미리 리팩터해둔 덕분에, 이 함수 하나만 고치면 두 곳 모두에 자동 반영됨.
  * **검증**: 사용자 예시를 그대로 재현하는 단위 테스트(단일 sector, Level 1~4, gid 6/3/3/6) 추가 —
    Level 1 eligible_steps==0(항상), Level 2·3==4, Level 4==0(자기 자신), 절감 Wh 300/보너스 80(Level
    2+3분만)이 손계산과 일치 확인. 기존 cross-sector 테스트는 "공유 레벨이 어느 sector의 영구 ceiling도
    아닌" 시나리오로 재설계해 140Wh/40Wh 보너스가 여전히 정상 동작함을 재확인. `python -m py_compile` 통과.

* **[v17.5] (2026-07-10) 절감 에너지 계산을 "ES Level 단위"→"물리 RU(BID/PID/CID)+PA shared 단위"로 전면 재작성 + Deep Sleep 보너스 중복계산(그룹당 여러 번 합산) 버그 수정**
  * **배경(사용자 요청)**: RU 소비전력은 BID/PID/CID로 측정되고, rupt의 'PA shared'는 같은 PA를 공유하는
    cell 전체 집합이므로, 그 집합의 **모든** cell이 동시에 off일 때만 그 RU가 실제로 PA off 이득을
    실현한다. 예전 계산은 레벨 하나의 Target Cell Num이 CarrierConf 설정만으로 PA 공유를 이미 다
    반영했다고 가정했는데, 이제는 rupt의 실제 PA shared 데이터로 직접 검증한다.
  * **CellOff 재계산**(`_calc_cell_off_savings_by_ru`, Deep Sleep 옵션과 무관하게 항상 동작): rupt를
    (NE ID,BID,PID,CID)로 묶고, 같은 물리 RU에 서로 다른 PA shared 그룹이 N개 있으면(Dual Band RU 등)
    CellOff 전력차를 N분의 1씩 배분(사용자 요청, 중복 계상 방지). 적격 스텝은 그룹의 모든 멤버가
    자기 off_level **이상**(fallback 위험 없는 base CellOff라 `>=`, Deep Sleep의 `>`와 다름)일 때.
  * **Deep Sleep 보너스 재계산**(`_calc_deep_sleep_bonus_by_group`, 버그 수정): 같은 Deep Sleep
    Capability 그룹 인덱스를 여러 ES Level이 공유해도 그룹당 **정확히 1회만** 계산 - 예전에는 레벨마다
    따로 계산해 합산해서 그 그룹을 공유하는 레벨 수만큼 부풀려졌음(사용자가 직접 지적, 확인). CellOff와
    달리 N분의 1 분할은 적용하지 않음(그룹 인덱스 기준 1회, 물리 RU가 여러 개면 합산해서 1회 적용).
  * **Cross-sector 귀속**: 그룹 멤버가 여러 Sector에 걸치면 절감량을 관련 Sector에 균등 분배(사용자 확인).
  * **제거**: `_power_deltas_for_level` 삭제, `_build_level_wide_by_enb`/`_members_all_off_series`
    (strict 플래그로 CellOff `>=`/Deep Sleep `>` 통일) 공용 헬퍼로 대체.
  * **검증**: test_ru_centric_savings.py 신규(옛 test_deep_sleep_savings.py 대체) - 단일 cell 기본
    CellOff, 같은 Sector PA-shared 2 cell(모두 off일 때만 절감), cross-sector 균등분배(25/25), 같은
    RU N=2 분할(30Wh, 안 나누면 60Wh), gid 6/3/3/6 복합 시나리오(150Wh=CellOff 110+DS보너스 40, 그룹당
    1회), 잘못된 Spec으로도 음수 안 됨(end-to-end) 확인. 기존 Deep Sleep capability/rupt/ES mode Type
    회귀 테스트 전체 재실행해 영향 없음 확인. `python -m py_compile` 통과.

* **[v17.6] (2026-07-10) 전체 코드 리뷰(정독) - 버그 6건 수정 + 최적화 1건 (판단 4건은 사용자 인터뷰로 확정)**
  * **[중요] Coe_paoff 누락(v17.5 회귀)**: rupt 기반 절감 계산에서 실측 보정계수 Coe_paoff가 조용히
    빠져 NC2 경로와 불일치 → rupt 열은 순수 Spec 값 유지, 절감 Wh 계산 시 신규 `_rupt_model_coe_map`
    (3단계 매칭, 미매칭 1.0)을 CellOff/Deep Sleep 양쪽에 곱함(사용자 확인).
  * **[중요] RU 에너지 매칭에 eNB_ID 누락**: `_sector_total_energy_wh`/`_calc_all_savings`가 RU 번호
    (Bid/RuPort/Cascade)만으로 Energy Stat을 매칭해 같은 번호의 다른 사이트 RU 에너지가 합산됐음 →
    eNB_ID를 키에 포함. 동시에 `_sector_energy_wh_map`으로 벡터화(sector×RU 재스캔 → groupby+merge 1회).
  * **PA-shared 유령 cell(사용자 확인: 표기 포함+절감 차단)**: CM에 행이 없는 참조 cell을 rupt PA
    shared에 포함(스펙 '합집합')하고 절감 판정은 자동 차단(보수적). 토큰 파싱도 정규식 숫자 추출로
    강화("(120)" 등 수용).
  * **수동 모드 Rawdata 24h(사용자 확인)**: 수동 ES 시간 모드에서 트래픽을 미리 시간 필터해 Rawdata가
    ES 시간만 담기던 것 수정 - 정책 학습은 기존과 동일(ES 시간만), Rawdata는 auto 모드처럼 24시간
    전체(여러 날 윈도우 이어붙음/진입 재판정 누락으로 인한 과대 절감 해소).
  * **'에너지 분석 실행' overlay(사용자 확인)**: 특정 eNodeBID/Sector 선택 시에도 시뮬레이션은 전체
    sector로 돌리고 표시만 선택 행 합산으로 변경 - cross-sector 판정 정상화(v17.0 '알려진 한계' 이
    화면에서는 해소) + 절감률 분모를 선택 부분 실제 소모(total_wh)로 통일.
  * **자잘한 결함**: `_load_auto_jsons` CWD 의존(앱 폴더 기준으로), `_filter_cm_tree` 빈 DataFrame 가드.
  * **검증**: 신규 test_r17_fixes.py(Coe 2배/절반 일관성, 유령 cell 표기+차단, eNB 분리 200/1998Wh,
    수동 모드 run_analysis 스모크 - 24h Rawdata + 윈도우 0~5시 + 정책 불변) + 기존 회귀 전체 통과.

* **[v17.7] (2026-07-10) GUI 색감/편의성 개선 (사용자 요청)**
  * **팔레트/스타일**: 더 밝은 배경(#F3F7FD), 탭은 선택 시 흰 카드+파란 글자, Treeview 파스텔 블루
    헤더/행높이 26px/파란 선택색, 입력창 포커스 파란 테두리, 버튼 hover/pressed 반응, 스크롤바까지
    통일. 창 제목 "ESM — Energy Saving Manager (r17)", minsize 1000x720.
  * **모든 표 공통 마감**(`_finalize_tree`): 줄무늬(zebra) + 열 너비 자동 조정(고정 100~140px로 긴
    헤더가 잘리던 불편 해소) + **헤더 클릭 정렬을 모든 표로 확대**(숫자 인식, 재클릭 역순, in-place라
    편집기 표의 iid↔index 매핑 유지 - 기존 _sort_cm_tree 대체).
  * **휠 스크롤 확대**(`_enable_canvas_mousewheel` 공용화): 일괄 저장 팝업/행 편집 팝업에도 적용.
  * **자잘한 UX**: 고급 설정 ▼/▲ 상태 반영, NaN 표시 'nan'→'N/A' 통일, 행 편집 팝업 배경 통일.
  * **검증**: 신규 test_gui_polish.py(제목/minsize/스타일/zebra/자동 너비/정렬/iid 매핑/토글/빈 CM
    가드) + 기존 회귀 전체 통과. 계산 로직 무변경.

* **[v17.8] (2026-07-10) 사용자 버그 리포트 2건 대응**
  * **[중요] 절감 에너지 전부 0 회귀 수정**: `_rupt_match_ru_spec_row`만 대소문자를 구분해(다른 모든
    Spec 조회는 `.lower()`), CM board-type과 Spec DB의 케이스가 다르면 rupt CellOff 등이 전부 -1 →
    v17.5부터 모든 sector 절감 0. 3단계 매칭 전부 대소문자 무시로 수정.
  * **"Max ES Level=1인데 ES Level 1 행 없음" 가시화**: 임계값 탐색 실패(대표 원인: 그 운영시간 DL
    트래픽 없음 → SP=0 → alpha=0 → 예측 Tput 항상 0)로 band가 ES7로 편입되는 기존 설계 동작 -
    이제 ES7 행 Note에 탈락 band와 alpha를 기록(run_analysis Note 병합도 덮어쓰기→합치기로 수정).
  * **절감 효과 표 '비고' 열 신설**: 절감 0 sector의 사유(RU Model 미매칭/PA 공유 cell off 불명/
    timeline 없음/동시 off 스텝 0회/정책 없음)를 자동 표기 - 실데이터 디버깅용.
  * **검증**: test_bug_report_fixes.py(케이스 불일치 3단계 매칭+70Wh 복원, 비고 3종, alpha=0 Note,
    정상 케이스 무회귀) + 기존 회귀 전체 통과.

* **[v17.9] (2026-07-10) 대소문자 감사 후속 - Learning 탭 ref_lookup 수정**
  * board-type/RU Model↔Spec DB 대조 경로를 전수 감사. `_calculate_est_saving`/`_calc_all_savings`/
    `_compute_deep_sleep_capability`/`_rupt_match_ru_spec_row`는 이미 `.lower()` 일관됐고, Learning
    Energy Curve 탭의 `ref_lookup`(Board Type별 Idle/PA off 레퍼런스)만 원본 케이스로 조회하고 있었음.
  * CM 'AAU-Q' vs Spec 'aau-q'처럼 케이스가 다르면 Idle/PA off Reference가 NaN → Delta/Coe 보정 컬럼
    전부 깨짐. 키 생성·조회 양쪽을 `.strip().lower()`로 통일(first-wins). 이로써 5개 경로 전부 일관.
  * **검증**: test_learning_case_insensitive.py(케이스 불일치 합성데이터 end-to-end, Idle Ref=111/
    PAoff Ref=55 정상 매칭) + 기존 회귀 전체(9종) 통과.

* **[v17.10] (2026-07-13) RU Model↔Spec DB '스마트 매칭' 개편 (`_rupt_match_ru_spec_row`)**
  * **배경**: 사용자 보고 - ES 성능 이득(절감율) 계산 시 CM의 RU Model이 대소문자/'-' 이후 접미어 표기
    차이로 RU/MMU Spec DB의 board-type과 매칭에 실패해 절감율이 계산되지 않는 경우가 있었음. 대소문자
    무시([v17.8])만으로는 '660' vs '66d' 같은 접미어 차이를 못 잡았고, 후보가 여럿일 때 DataFrame 순서상
    첫 행을 무작정 고르던 문제도 있었음.
  * **매칭 규칙(신규)**: (1) 대소문자 무시 완전일치('RF4431t-660'=='rf4431t-660'). (2) 완전일치가 없으면
    '-' 이전 head(모델 family)가 같은 행들을 '동일 모델'로 보고, 그중 **전체 모델명**('660'만이 아니라
    'rf4431t-660' 전체, head 포함) 우선순위가 가장 높은 행 선택 - 앞자리부터 문자 단위 비교: **숫자>문자**,
    **숫자끼리는 큰 값**, **문자끼리는 큰 코드** 우선(예: DB에 'rf4431t-660'/'rf4431t-66d'/'rf4431t-600'이면
    660, '66d'/'60d'면 66d 선택). (3) 그래도 없으면 head로 시작하는 첫 값(방어적 fallback). head가 다른
    family('aau-999' 등)는 tail 숫자가 커도 후보에서 제외되어 섞이지 않음.
  * **구현**: 신규 헬퍼 `_ru_model_priority_key`(전체 모델명→우선순위 튜플 리스트, max()로 선택). 후보
    선택은 위치(reset_index+iloc) 기반이라 Spec DB 중복 index에도 안전. 이 함수를 쓰는 모든 경로
    (`_rupt_model_coe_map` 등)가 단일 수정점으로 함께 개선됨.
  * **설계 선택(확인 필요)**: 완전일치가 존재하면 그것을 우선한다 - CM이 정확히 'rf4431t-66d'이고 DB에도
    '66d'가 있으면 660이 아니라 66d를 반환(실데이터 표기 존중). '완전일치보다도 항상 660 우선'을 원하면 재논의.
  * **검증**: 신규 test_ru_match.py(scratchpad) - 대소문자 완전일치 / 660 vs 66d→660 / 66d vs 60d→66d(순서
    무관) / head 불일치→None / 완전일치 우선 / 빈 입력 등 8케이스 전부 통과. `python -m py_compile` 통과.
    (※ 실데이터 GUI 검증은 로컬 PC에서 추가 확인 권장.)

* **[v17.11] (2026-07-13) 버그 수정: Spec 값 열 조회 정규화 - 'PA Off' 표기 차이로 CellOff=-1 되던 문제**
  * **증상**: 실데이터에서 CM 'rf4431-660'이 Spec 'RF4431-660'과 매칭엔 성공(대소문자 무시)하는데도 "RU
    Model 미매칭(CellOff=-1)"이 뜨고 절감율이 0.
  * **원인**: board-type 열은 정규화(`_rupt_norm_key`)로 찾으면서, 값을 읽는 `_rupt_power_state_values`는
    'Idle'/'PA off'를 하드코딩 이름으로 조회 → Spec 열이 'PA Off'(대문자 O)/'idle'/'Idle '(공백) 등이면
    값이 NaN→CellOff=-1. 매칭은 됐는데 값만 못 읽는 비대칭 버그(진짜 미매칭 아님).
  * **수정**: `_rupt_power_state_values`가 spec_row 열을 `_rupt_norm_key`로 정규화해 조회(board-type과 동일
    규칙). 진단 메시지도 '미매칭 또는 Idle/PA off 값 누락'으로 정정.
  * **검증**: repro_celloff.py - 'PA Off'/'idle'/'Idle ' 모두 CellOff 정상(41.406) + 정규표기·매칭 회귀
    18케이스 무회귀. `python -m py_compile` 통과.
  * **공식 확정(2026-07-13 사용자)**: CellOff 이득 = `Idle − PA off` 유지(Idle·PA off는 각 상태의 절대
    소비전력). 따라서 Spec의 Idle 열에 값이 있어야 CellOff가 계산됨 - Idle이 비면 CellOff=-1로 남는 것이
    정상 동작(데이터 문제).

* **[v17.12] (2026-07-13) 버그 수정: Energy Dashboard eNodeBID/Sector 필터 기본값 'All' 복원**
  * eNodeBID(및 Sector) 콤보박스가 CM 데이터 로드 전에는 빈칸으로 표시되던 문제 - 콤보 생성 시점에
    `values=['All']`+`current(0)`으로 기본값을 초기화(예전 동작 복원). CM 처리 시 `['All']+enbs/secs`로
    재채움되는 로직은 그대로. `py_compile` 통과 + Tk 콤보 기본값이 'All'로 나오는지 확인.

* **[v17.13] (2026-07-13) 가독성 개선: 결과 Treeview 열 너비 확대 + Note/비고 열 좌측정렬**
  * 사용자 요청 - 결과 창 열 간격이 너무 좁고, 특히 Note/비고처럼 내용이 긴 열이 좁게 잘려 불편.
  * `_finalize_tree`(모든 결과표 공통 마감) 열 너비 로직 개선: 일반 열 90~480px(가운데), 내용이 긴 열
    ~760px, Note/비고/remark/사유 등 긴 텍스트 열은 ~1600px + **좌측 정렬**(측정 상위 60→80행). 가로
    스크롤바가 있어 넓어져도 무방(사용자 확인).
  * 검증: py_compile + Tk 실측(비고 열 847px/anchor=w, 일반 열 90~136px/center 확인).

* **[v17.14] (2026-07-13) 기능 개선: ES 정책 없는 sector도 Intermediate Data에 rawdata로 포함**
  * **배경**: ES 운영시간 자동 최적화 시 유효 ES 윈도우가 하나도 없어 ES 정책이 생성되지 않는 sector는
    `inter`가 비어 Intermediate Data에서 통째로 빠졌음. 사용자 요청: ES 정책 유무와 무관하게 Intermediate에
    데이터가 있어야 rawdata로 미동작 원인을 분석하기 쉽다.
  * **수정(`run_analysis`)**: sector별 `inter`가 비면 그 sector의 rawdata(24h 전체, ES_Window_Index=0)를
    `ES_Policy='None (no ES window)'`로 표시해 intermediate_data_list에 추가. inter_df의 정책 sector 행은
    ES_Policy를 'Applied (ES window)'로 채워 구분.
  * **한계**: 모든 sector가 no-policy면 output_results가 비어 결과 창 자체가 안 뜨는 게이트는 유지(사용자
    보고는 '몇몇 sector' 케이스). 필요 시 별도 처리 - To-Do 21.
  * **검증**: 스키마 상이한 정책 inter/no-policy raw concat 시 ES_Policy 라벨 정확·두 sector 모두 포함 확인.
    `python -m py_compile` 통과. (실데이터 GUI 확인 권장.)

## 5-2. Branch 2 / 새 라운드: `esm_r18.py` (NR ES 정책 최적화)

* **[라운드 전환] (2026-07-14)** 사용자 지시로 `esm_r17.py`를 복제해 `esm_r18.py`를 생성. 이 시점부터
  `esm_r18.py`가 유일한 활성 개발 파일이며, `esm_r17.py`는 v17.14 상태로 동결(보존)한다. 모듈 docstring
  타이틀을 `ESM_r18`로, 윈도우 제목을 `ESM — Energy Saving Manager (r18 · v18.0)`으로 변경(어느 파일/빌드를
  실행 중인지 제목으로 즉시 식별 가능 - 그동안 옛 Google Drive 백업본을 실행해 수정이 반영 안 된 것처럼 보이던
  혼동 방지). 기능 변경은 없음(순수 복제 + 타이틀).
* **r18 목표**: NR(5G)에 대한 ES 정책 최적화 기능 추가. 현재 Optimizer/시뮬레이션 로직은 LTE 위주
  (`_LTE` 접미 파라미터, band 처리, RB 계산 등)이며, NR 대응을 어떻게 확장할지는 사용자와 상세 스펙 협의 예정.
* 신규 변경은 v18.1, v18.2 …로 이 섹션에 기록한다.

## 6. 진행 중인 작업 및 다음 단계 (To-Do / Next Steps)

* **다음 결정 대기**:
  1. Google Drive(`VibeCoding/ESM`) 저장 방식 — 스킵 중, 추후 논의.
  2. 실제 Cell/RU 단위 학습데이터 CSV의 컬럼명이 파서 매핑과 맞는지, CM의 `PA-shared-cell` 컬럼명이 실제와 일치하는지 실데이터 확인 필요.
  3. Learning Energy Curve 실행(드래그 앤 드롭, Formula 탭/다운로드, 3열 시각화, scipy 활성화 여부)을 실제 GUI 환경(tkinterdnd2 설치)에서 확인 필요.
  4. `Recommended Model`(자동 추천)이 실데이터에서 그룹별로 타당한지 최종 확인.
  5. `Better Axis (R² 기준)` 비교 결과로 Active_RB 축 단일화 여부 결정.
  6. Optimizer Auto Time Mode 1/2/3 중 기본값 채택 및 Initial level 최적화 여부 결정.
  7. **[v17.5에서 CellOff 부분 해결]** Dual Band RU(RU HW 1개에 서로 다른 PA shared 그룹 여럿) — CellOff 절감 계산은 [v17.5]에서 같은 BID/PID/CID에 PA shared 그룹이 N개면 N분의 1로 나누도록 반영됨. Deep Sleep Capability 그룹핑 자체(`_compute_deep_sleep_capability`, board-type+port-id 기준)는 여전히 미변경 — 실사례로 재확인 필요.
  8. ES 윈도우 진입 "1 sample 미적용" 패턴이 실데이터에서 실제로 사라졌는지, Coverage band 선택이 기대대로 동작하는지(특히 band 1~2개뿐인 sector에서 eMTC/ENDC anchor와 겹쳐 ES 적용대상 0개가 되는 빈도) 확인 필요.
  9. eMTC/ENDC anchor 판정 알고리즘(우선순위 선택 기준)과 실제 CM Data의 `conf-emtc-switch`/`endc-anchor-type`/`endc-support` 값 표기가 코드의 `_TRUTHY_TOKENS` 판정과 맞는지 확인 필요.
  10. ES Level 없는 sector를 절감효과 결과표에 포함하는 로직은 시뮬레이션 기반(Mode 2/3)에만 적용됨 — NC2 기반(Mode 1)도 필요한지 결정 대기.
  11. **[v17.0, 중요 / v17.6에서 일부 해소]** Deep Sleep 기능을 실제로 켜서 실데이터로 검증 필요 — board-type 컬럼명 매칭, 여러 sector에 걸친 RU 공유 실제 사례와 그룹 id 결과. "알려진 한계"(특정 sector로 필터된 호출부의 교차-Sector 판정 누락)는 '에너지 분석 실행' overlay에 한해 [v17.6]에서 해소(항상 전체 sector 시뮬레이션 후 선택부만 추출) — 다른 호출부는 애초에 필터하지 않아 해당 없음.
  12. Energy Dashboard 연동 보류 중: Learning Energy Curve의 Idle/PA off 보정값·채택 모델을 절감 예측에 반영할지는 별도 대기.
  13. **[v17.2, v17.3/v17.5에서 갱신]** rupt(RU profile table)는 [v17.5]부터 ES Level 시뮬레이션의 절감 Wh 계산(CellOff+Deep Sleep 모두) 핵심 데이터 소스가 되었지만, 다른 탭(`_calculate_est_saving`=Optimizer의 Est. Saving 열, Learning Energy Curve의 RU 판정)은 여전히 각자의 inline 로직을 그대로 사용 — 나머지 탭도 언제 rupt로 마이그레이션할지는 사용자 지시 대기.
  14. **[v17.2]** ES mode Type이 실제로 "Tx Path Off"/"none"을 산출하려면 DRBn 계산식에 모드별 비율(예: Tx Path Off=0.5배) 반영이 필요 — 현재는 항상 "Cell-Off"만 나오는 것이 의도된 동작(사용자 확인), 비율 반영 기능은 추후 별도 요청 대기.
  15. **[v17.3, 중요]** Deep Sleep 음수 절감 버그의 근본 원인은 RU/MMU Spec DB에 특정 RU Model의 Deep Sleep(또는 Super Sleep) 소비전력이 PA off보다 크게 입력된 데이터 문제일 가능성이 높음 — 0-clamp로 증상은 막았지만, 실제 Spec DB에서 어떤 RU Model이 그런지 사용자가 직접 확인·정정 필요(코드가 자동으로 찾아 알려주진 않음). 'Level k DS Count' 진단 열로 카운트를 확인한 뒤에도 절감량이 기대와 다르면 이 가능성부터 점검 권장.
  16. **[v17.3에서 제기 → v17.4에서 해결]** "하나 낮은 레벨까지만 대상" 문의는 실제로는 그룹 판정의 `>=`/`>` 버그를 가리킨 것으로 확인되어 [v17.4]에서 수정 완료(esm_r17.py [v17.4] 항목 참고).
  17. **[v17.5, 중요]** CellOff/Deep Sleep 절감이 이제 rupt의 실제 'PA shared'/'BID'/'PID'/'CID' 값에 크게 의존하므로, 실제 CM 데이터에서 이 값들이 올바르게 채워지는지(특히 PA-shared-cell 원본 컬럼명이 실제 Excel과 일치하는지, Dual Band RU 케이스가 실데이터에 실제로 존재하는지) 실데이터로 검증 필요.
  18. **[v17.5]** Cross-sector 그룹의 절감량을 관련 Sector에 "균등 분배"하기로 결정했는데, 이는 각 Sector의 개별 절감량이 실제 물리적 기여도가 아니라 대표값 성격이라는 뜻 — 전체 합계는 정확하지만 Sector별 순위/비교가 필요한 용도라면 이 점을 유의해야 함(사용자에게 이미 설명함, 추가 확인 불필요하나 리포트 사용 시 참고).
  19. **[v17.10]** RU Model 스마트 매칭의 '완전일치 우선' 설계를 실데이터로 확인 - CM이 typo 접미어
      (예: '66d')를 그대로 담고 있는데 DB에도 같은 typo 행이 있는 경우, 정식 표기('660')로 강제 매핑할지
      아니면 현재처럼 완전일치를 존중할지 사용자 결정 대기.
  20. **[v17.11, 확정]** CellOff 이득 공식은 `Idle − PA off`로 확정(2026-07-13 사용자). 값 열 조회 정규화
      버그는 [v17.11]에서 해결. 남은 것은 데이터 점검뿐 — Spec의 `Idle` 열이 실제로 채워져 있어야 CellOff가
      계산됨(비면 CellOff=-1이 정상). RF4431-660/LTE 행에 Idle 값이 있는지 실데이터로 확인 권장.
  21. **[v17.14]** 모든 sector가 ES 정책 없음(no-policy)이면 output_results가 비어 결과 창이 아예 안 뜨는
      게이트(`if output_results:`)가 남아 있음 - 이 경우에도 Intermediate(rawdata)만이라도 보여줄지 결정 필요
      (out_df 빈 경우 정렬 KeyError 방지 등 처리 동반).
  22. **[r18, 주요 목표]** NR(5G) ES 정책 최적화 기능 추가 - 사용자와 스펙 협의 필요: NR의 ES 대상 단위
      (SSB/beam/cell?), NR 트래픽/전력 지표, LTE와 공통화할 부분과 NR 전용 로직 분리 범위 등.
* **[개발 환경] 프로젝트 분리**: ESM은 `shaiger79/Code` 리포의 **ESM 전용 브랜치 `esm-r0-cellru-mapping`**
  (ESM/·README.md만 존재, trafficgen 등 타 프로젝트 파일 없음)에서 진행하며 `main`과 병합하지 않는다
  (2026-07-13 사용자 결정). trafficgen과의 혼입은 main에서만 발생하므로 이 브랜치를 유지하는 것으로 분리 달성.
* **다음 대기 작업**: 사용자가 실데이터/실제 환경으로 재확인한 결과를 알려줄 예정.

---
*Last Updated: 2026-07-13*
*AI Directive Status: Active (Always Read First, Always Update Post-Task)*
