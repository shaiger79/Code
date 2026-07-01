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
* **`AppDashboard`**: CM/CIQ 데이터 병합(Cell-RU Mapping), Energy Stat 파싱, Energy 대시보드 시각화(Gamma 고급설정 포함).
* **`ESAnalyzerApp`**: Traffic Pattern Viewer(Interactive/Batch) + ES 임계조건 최적화 알고리즘(Optimizer) + 절감량 예측(EE 포함) + 최종 Treeview 리포트, 최상위 실행 클래스(`if __name__ == "__main__": app = ESAnalyzerApp()`).

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
  * Google Drive(`VibeCoding/ESM`) 동기화는 현재 세션에 Google Drive 연동 도구가 제공되지 않아 미수행 — 사용자 확인/대안 필요.

## 5. 진행 중인 작업 및 다음 단계 (To-Do / Next Steps)
* 현재 상태: v1.4 - 치명적 실행 버그 2건 수정 완료, GitHub(`ESM/` 폴더) 커밋 완료.
* 확인 필요:
  1. Google Drive(`VibeCoding/ESM`) 저장 방식 (연동 도구 부재로 사용자 확인 필요).
  2. GitHub 리포지토리 구성 방식 확정 (`shaiger79/Code` 내 `ESM/` 폴더 vs 별도 신규 리포지토리).
* 다음 대기 작업: (사용자 요청 대기 중 - 새로운 분석 조건, 파일 병합 기능 고도화, 또는 UI 개선 등)

---
*Last Updated: 2026-07-01*
*AI Directive Status: Active (Always Read First, Always Update Post-Task)*
