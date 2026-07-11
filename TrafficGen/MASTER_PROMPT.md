# 📡 TrafficGen — 상용망 무선 네트워크 KPI(Traffic) Generator 마스터 프롬프트

> **문서 성격**: 이 파일은 "상용망(4G LTE / 5G NR) 기지국 성능 KPI 생성 툴"을 바이브코딩으로
> 만들기 위한 **마스터 프롬프트(프로젝트 헌장 + AI 컨텍스트)** 이다. 새 세션/작업 시작 전 반드시
> 먼저 읽고, 주요 변경 후에는 이 문서를 갱신한다.
>
> **자매 프로젝트**: 같은 저장소의 `ESM/`(Energy Saving Manager)은 상용망의 PM(Traffic)·Energy·CM
> 데이터를 **입력으로 소비**해 에너지 절감을 분석하는 툴이다. 본 TrafficGen은 그 **입력 데이터를 인공적으로
> 생성(모사)** 하는 반대 방향의 툴이다. 따라서 **생성 결과의 스키마·의미는 ESM이 읽는 데이터와
> 최대한 호환**되어야 한다(§6 데이터 모델 참조).

*Status: v0.2 — 첫 시스템 스펙 확정 + TrafficGen r0 구현 착수 (2026-07-10)*

> **연속성 규칙**: 작업 전 이 문서와 `TrafficGen/vibe_context.md`를 먼저 읽고, 작업 후 `vibe_context.md`를
> 갱신한다(진행 이력·다음 대기). 활성 개발 파일은 `trafficgen_rN.py`.

---

## 1. 프로젝트 개요 (Overview)

* **한 줄 정의**: 전 세계 상용망(미국/한국/캐나다 등)에 존재하는 여러 기지국이 만들어내는 시간대별
  **성능 KPI(Performance Metric / Performance KPI)** 를 규칙·확률 기반으로 **생성(합성)** 하는 툴.
* **목적**: 여기서 생성한 KPI 데이터를 **데이터 애널리스트가 알고리즘(정책/최적화/예측 모델)을 개발할 때
  기본 토대(학습·검증용 raw data)로** 사용한다. 즉 결과물은 "분석·알고리즘 개발이 가능한 현실감 있는
  네트워크 KPI 데이터셋"이다.
* **왜 생성이 필요한가**: 실 상용망 데이터는 확보·보안·규모 제약이 크므로, RAN 동작 원리(3GPP)에
  부합하는 **인과관계가 살아있는 합성 데이터**를 만들어 알고리즘 개발/실험을 자유롭게 하기 위함.
* **핵심 요구**: 단순 난수가 아니라, **KPI 간의 물리적 인과관계**(트래픽↑ → 자원 사용↑ → 에너지↑,
  사용자수↑ → 사용자당 처짐 → 체감 품질↓ 등)가 반영된 데이터여야 한다(§5).

---

## 2. 배경 지식: RAN / 4G·5G 구조 (요약 학습)

### 2-1. 무선 접속망(RAN, Radio Access Network) 개념
* **RAN**: 단말(UE)과 코어망 사이의 무선 구간. 4G는 **E-UTRAN**(기지국 = **eNB**), 5G는 **NG-RAN**
  (기지국 = **gNB**)으로 부른다.
* **기지국 물리 구성(중요, 에너지·자원의 단위)**:
  * **BBU/DU (Baseband/Distributed Unit)**: 신호 처리.
  * **RU (Radio Unit) / RRH**: 안테나단에서 실제 전파를 **방사(radiation)** 하는 장비. **소모 에너지의
    핵심 원천** — 전력증폭기(PA)가 트래픽 부하에 비례해 큰 전력을 소모한다. 본 툴의 에너지 KPI는 이 RU
    소모전력을 모사한다.
* **셀(Cell) / 섹터(Sector) / 캐리어(Carrier/Band)**:
  * 한 기지국은 보통 여러 **섹터**(방위각으로 분할, 예: 3섹터 120°씩)로 커버리지를 나눈다.
  * 각 섹터에는 여러 **밴드/캐리어(주파수)** 의 **셀**이 있다. KPI는 **셀(cell) 단위**로 측정·집계되는
    것이 기본이며, 섹터/기지국 단위로 rollup 한다.
* **식별자 체계(ESM과 정합)**: `eNB_ID`(기지국) → `Sector` → `cell-num`(셀). RU는 `ru-board-id`/
  `ru-port-id`/`ru-cascade-id`(BID/PID/CID)로 식별. 여러 셀이 하나의 PA/RU path를 공유할 수 있다
  (`PA-shared-cell`).

### 2-2. 무선 자원(Resource Block, RB/PRB)
* **RB(Resource Block)**: 주파수-시간 자원의 최소 스케줄링 단위. 1 RB = **주파수축 12개 부반송파
  (subcarrier)**. 셀이 가진 총 RB 수(`nRB`)는 대역폭에 비례(예: LTE 20MHz ≈ 100 RB).
* **스케줄러**: 매 TTI(전송 시간 단위, LTE 1ms)마다 접속 단말들에게 RB를 나눠준다. **사용자가 많으면
  한 사람당 돌아가는 RB/기회가 줄어(퐁당퐁당 스케줄링) 전송 지연이 커지고 체감 속도가 떨어진다.**
* **PRB Utilization(자원 사용률)**: `UsedRB / nRB × 100 [%]`. 셀 혼잡도의 대표 지표.

### 2-3. 시간 단위
* 상용망 PM은 보통 **ROP(Result Output Period)** 단위로 집계 — 통상 **15분**(3GPP 관례). ESM도 15분
  스텝을 사용한다. 본 툴의 기본 시간 해상도도 **15분**을 채택(설정 가능).

---

## 3. 규격 근거 (3GPP)

* **근간 사이트**: [3GPP.org](https://www.3gpp.org) 규격을 참조해 RAN 동작·용어·KPI 정의를 학습·정렬한다.
* **시스템 규격(사용자 지정)**:
  * **TS 36 시리즈** = **4G LTE / E-UTRA(N)** 시스템 규격.
  * **TS 38 시리즈** = **5G NR / NG-RAN** 시스템 규격.
* **KPI/PM 정의 관련(정합 시 참고할 보조 규격)**:
  * LTE 성능측정: **TS 32.425**(E-UTRAN PM), KPI 정의 **TS 32.450 / 32.451**.
  * 5G 성능측정: **TS 28.552**(5G PM), 종단 KPI **TS 28.554**.
  * → 본 툴의 KPI 이름/정의는 위 규격의 개념(IP Throughput, PRB utilization, RRC/E-RAB 성공·실패 등)을
    따르되, **컬럼명은 ESM 호환**(§6)을 최우선으로 한다.
* **AI 학습 지침**: 세부 정의가 모호할 때는 위 규격의 정의를 기준으로 삼고, ESM 컬럼과 충돌하면
  사용자에게 확인한다.

---

## 4. 생성 대상 핵심 KPI 정의 (Core KPIs)

> 아래는 사용자가 지정한 "개발 주요 KPI"를 규격/ESM 용어로 정리한 것이다. 모든 KPI는 **(기지국, 셀,
> 시간) 단위 시계열**로 생성된다.

| # | KPI (범주) | 의미 | 대표 컬럼(ESM 호환) | 단위 |
|---|---|---|---|---|
| 1 | **Traffic Volume (전송량)** | 공중 인터페이스로 전송된 데이터량(DL/UL) | `AirMacDLByte`, `AirMacULByte` | Byte |
| 2 | **Resource Usage (자원 사용량)** | 사용된 RB 수 / 총 RB / 사용률 | `UsedRB`, `nRB`, (PRB Util %) | RB, % |
| 3 | **Energy (소모 에너지)** | RU가 소모한 전력/에너지 | `RuPowerTot`, `RuPowerCnt` | Wh, count |
| 4 | **User Perceived Throughput (체감 품질)** | 사용자 체감 속도 = 전송량 ÷ 전송소요시간 | `IP Tput` | Mbps |
| 5 | **Failure Volume (실패 볼륨)** | 접속/세션/호 실패 건수 | (신규, §4-5) | count |
| 6 | **Active Users (사용자 수)** | 접속/활성 단말 수 (체감 품질의 원인 변수) | (신규, §4-6) | count |

### 4-1. Traffic Volume — `AirMacDLByte` / `AirMacULByte`
* 정의: 해당 15분 구간에 그 셀이 공중 인터페이스(MAC 계층)에서 실제 전송한 **DL/UL 바이트 총량**.
* 성격: **수요(offered load)** 를 대표하는 1차 동인. 다른 대부분 KPI(자원/에너지/실패/체감)의 원인 변수.
* 패턴: **일주기(diurnal)** — 낮 피크/새벽 저점, 요일/지역 특성, 사이트 유형(도심/주거/교외) 반영.

### 4-2. Resource Usage — `UsedRB`, `nRB`, PRB Utilization
* `nRB`: 셀의 총 가용 RB(대역폭·numerology로 결정, 셀 정적 속성).
* `UsedRB`: 그 구간 실제 사용된 평균 RB 수. **트래픽 볼륨 ÷ 스펙트럼 효율(MCS/무선품질)** 로 결정.
* **PRB Utilization[%] = UsedRB / nRB × 100**. 상한 100%(포화). 포화 접근 시 지연·실패 급증.

### 4-3. Energy — `RuPowerTot` / `RuPowerCnt`
* 개념 모델: **RU 소모전력 = 정적(baseline/idle) + 동적(부하 비례)**.
  * `P(t) = P_idle + (P_max − P_idle) × load_factor`, 여기서 `load_factor ≈ PRB Utilization`(또는 Tx 부하).
  * 트래픽이 많으면 PA가 더 방사 → 에너지↑ (사용자가 강조한 인과).
* `RuPowerTot`: 구간 누적 소모전력(Wh 환산 가능), `RuPowerCnt`: 샘플/집계 카운트.
* ESM의 효율지표와 정합: **EE = (AirMacDLByte + AirMacULByte) / Consumed[Wh]**. 생성 데이터도 이 관계가
  현실적으로 성립해야 한다(에너지 절감 알고리즘의 학습 대상).

### 4-4. User Perceived Throughput — `IP Tput` (체감 품질)
* **사용자 정의**: 전송하고자 하는 데이터가 있을 때, **전송 시작부터 종료까지 소요된 시간**으로
  **전송된 데이터량**을 나눈 값 = 사용자 체감 속도.
* **수식**: `IP Tput = ThpVolume / ThpTime`.
  * `ThpVolume`: 활성 데이터 전송 구간에 전달된 볼륨.
  * `ThpTime`: 버퍼에 데이터가 있어 실제 전송 중이던 시간(활성 시간).
* **3GPP 정합(TS 28.552 DRB.IPThpDl/Ul)**: 표준 정의는 버퍼가 비는 마지막 slot/TTI를 제외해 "빈 버퍼로
  인한 저평가"를 막는다. 본 툴도 개념적으로 **활성 전송 시간 기준**으로 산출한다.
* **핵심 인과(사용자 강조)**: `ThpTime`은 **동시 접속/활성 사용자 수**의 영향을 받는다. 사용자가 많으면
  스케줄러가 자원을 나눠주므로 한 사용자가 "전송을 못 받는(대기) 시간"이 늘어 `ThpTime`↑ → **IP Tput↓**.
  → 체감 품질은 트래픽뿐 아니라 **사용자 수·혼잡도의 함수**로 모사해야 한다(§5-3).

### 4-5. Failure Volume — (신규 컬럼, ESM 미사용)
* 개념: 접속성/유지성 실패 건수. 후보 세부 KPI(3GPP 기준):
  * **Accessibility**: RRC 연결 시도/성공/실패, E-RAB(4G)/DRB(5G) 설정 실패.
  * **Retainability**: 비정상 해제(drop), 무선링크 실패(RLF).
  * **Mobility**: 핸드오버 시도/실패.
* 모사 원칙: **혼잡(PRB Util·사용자수)이 높을수록 실패율↑**(수락제어·자원부족·간섭). 저부하에선 낮은
  기저 실패율 + 소량 랜덤.
* 컬럼명은 인터뷰로 확정(예: `RrcConnFail`, `ErabSetupFail`, `DropCall` 등).

### 4-6. Active Users — (신규 컬럼, 체감 품질의 원인 변수)
* **접속 사용자 수**(RRC connected)와 **활성 사용자 수**(버퍼에 데이터가 있는 UE)를 구분해 모사.
* 트래픽 볼륨·시간대와 상관, 그리고 §4-4의 `ThpTime`/`IP Tput` 산출의 입력이 된다.
* 컬럼명 후보: `ConnectedUsers`, `ActiveUsersDl`, `ActiveUsersUl`.

---

## 5. KPI 간 인과/생성 모델 (Generative Logic)

> 본 툴의 차별점은 **인과관계가 살아있는** 데이터 생성이다. 아래 체인을 확률·물리 규칙으로 구현한다.

```
[시간/지역/사이트유형] ─► 수요(Demand)
        │
        ▼
  (1) Active Users, Traffic Volume(DL/UL)         ← 일주기 + 랜덤 + 사이트특성
        │
        ▼
  (2) RB 수요 = Volume ÷ SpectralEfficiency(무선품질)
      → UsedRB = min(RB수요, nRB)  →  PRB Util[%]  (포화 시 클리핑)
        │
        ├──► (3) IP Tput = f(가용자원/사용자수, 혼잡)   ← 사용자↑ → ThpTime↑ → Tput↓
        │
        ├──► (4) Energy: RuPower = P_idle + (P_max−P_idle)×load   ← load ≈ PRB Util
        │
        └──► (5) Failure Volume = 기저율 + g(PRB Util, 사용자수)  ← 혼잡↑ → 실패↑
```

### 5-1. 수요(Demand) 모델
* 일주기(24h) 프로파일 × 요일 × 지역(타임존별 피크 시프트) × 사이트유형(도심/주거/교외/이벤트).
* 노이즈: 셀별 랜덤 시드로 재현 가능(reproducible)하게.

### 5-2. 자원·포화 모델
* 스펙트럼 효율(무선품질/MCS)을 셀별 분포로 부여 → 같은 볼륨도 셀마다 RB 사용이 다름.
* `UsedRB`가 `nRB`에 근접/포화하면: 초과 수요는 **지연/실패로 전이**(단순 절단이 아니라 큐잉 효과).

### 5-3. 체감 품질(IP Tput) 모델 — 사용자 강조 포인트
* 셀 용량(가용 RB × 효율)을 **활성 사용자 수로 분배** → 사용자당 유효 rate.
* `ThpTime` = 전송량 ÷ (사용자당 유효 rate), 사용자수↑·혼잡↑일수록 증가.
* `IP Tput = Volume / ThpTime`. 저부하에선 피크 rate 근접, 고부하에선 급락(현실적 곡선).

### 5-4. 에너지 모델
* RU HW별 `P_idle`/`P_max` 파라미터(ESM의 RU Spec 개념과 정합) → 부하 곡선으로 소모전력 산출.
* (선택) ESM의 Learning Energy Curve가 학습하는 loading→power 관계를 **역으로 생성**하도록 파라미터화.

### 5-5. 실패 모델
* 기저 실패율 + 혼잡 가중(로지스틱/임계) + 드문 대형 이벤트(장애) 옵션.

---

## 6. 데이터 모델 / 출력 스키마 (ESM 호환 우선)

* **출력 형태**: CSV(엑셀 호환, `utf-8-sig`)를 기본. 파일 구성은 ESM 입력과 동일 계열로:
  * **Traffic PM 파일**: `Time`, 식별자(`eNB_ID`/`Sector`/`cell-num`), `IP Tput`, `UsedRB`, `nRB`,
    `AirMacDLByte`, `AirMacULByte`, (+ Active Users, Failure 컬럼).
  * **Energy Stat 파일**: 식별자 + RU 번호(`BID`/`PID`/`CID`) + `RuPowerTot`, `RuPowerCnt`, `Time`.
  * **CM/토폴로지 파일(선택)**: 기지국/섹터/셀/RU 매핑, `PA-shared-cell`, `nRB`, 밴드, 방위각 등 —
    ESM의 Cell-RU Mapping/CIQ와 호환.
* **식별자 정규화**: `eNB_ID`/`Sector`/`cell-num`은 **콤마 없는 순수 숫자 문자열**(ESM 규칙과 동일).
* **시간 축**: 15분 스텝(설정 가능), 여러 날 연속 생성 지원.
* **재현성**: 시드 고정 시 동일 출력. 시나리오 파라미터(사이트 수/지역/기간/부하 프로파일)는 설정 파일로.

---

## 7. 아키텍처 / 기술 스택 (제안, 인터뷰로 확정)

* **언어/스택**: Python + NumPy/Pandas (ESM과 동일 계열, 상호운용 쉬움).
* **구성(안)**:
  1. **시나리오 설정**(사이트 수·지역·기간·프로파일) → 2. **토폴로지 생성**(기지국/섹터/셀/RU) →
  3. **시계열 생성 엔진**(§5 인과체인) → 4. **CSV Export**(ESM 호환) → 5.(선택) **검증/시각화**.
* **UI**: 우선 CLI + 설정파일(YAML/JSON)로 시작, 이후 필요 시 ESM처럼 Tkinter GUI 검토.
* **검증**: 생성 데이터를 ESM에 실제로 로드해 파싱/분석이 되는지 왕복 검증(round-trip)을 수용 기준으로.

---

## 7-A. 첫 시스템 스펙 (확정, TrafficGen r0) 🏗️

* **단일 사이트 오버레이**: 한 사이트에 **LTE 시스템 1 + NR 시스템 1**이 지리적으로 겹쳐 존재.
  * **LTE**: 멀티캐리어(커버리지 오버랩) **3 캐리어 = 3 셀** (예: B1/2100·B3/1800·B7/2600, 각 20MHz/100RB).
  * **NR**: **3 캐리어 = 3 셀** (예: n78 100MHz/273RB 위주).
* **ENDC/NSA·SA 반영**: 현행 상용망은 NSA(ENDC, LTE 앵커 + NR SCG Dual Connectivity)로 운용. SA(NR 단독)도
  포함. → 에너지세이빙/로드밸런싱(트래픽 오프로딩: NR off→LTE 이전, DC 해제→LTE anchor만 등)을 위해
  **사이트 수요를 사용자클래스(Legacy-LTE/ENDC/NR-SA)별로 나눠 RAT/캐리어로 분배(steering)하는 구조**로
  설계. **[r1 구현 완료]** `SteeringConfig`(캐리어 on/off, `endc_split_nr`, `dc_release`,
  `nr_to_lte_offload`, `sa_fallback_to_lte`) + `_route_demand`(트래픽 보존 라우팅).
* **KPI 집계 4레벨**: ① Cell → ② LTE Sector(LTE 셀 aggregation) → ③ NR Sector(NR 셀 aggregation) →
  ④ LTE+NR Total. 각 레벨 간 지표 수준을 비교.
* **GUI(필수)**: Tkinter + Matplotlib. 시계열/**CDF**/히스토그램 시각화 + KPI 테이블 비교 + CSV 다운로드
  (ESM·LBM 연동) + Steering 패널(프리셋/셀 on-off/split/offload). 활성 구현: `TrafficGen/trafficgen_r1.py`
  (r0 → r1, steering 추가).

## 8. 오픈 퀘스천 (인터뷰 대상) ❓

아래 1·2는 **확정**, 나머지는 진행하며 확인.

1. **RAT 범위** ✅ 확정: **LTE + NR 오버레이(둘 다)**, NSA(ENDC)/SA 반영.
2. **출력 스키마** ✅ 확정: **ESM 입력 CSV 호환**(PM/Energy/Topology, `utf-8-sig`, 식별자 정규화). ESM·LBM
   연동 다운로드 지원. (실제 round-trip 로드 검증은 §다음 단계.)
3. **규모/해상도**: 기지국(셀) 개수 목표 규모? 시간 해상도(15분 확정?) 및 생성 기간(예: 7일/30일)?
4. **지역/글로벌**: 미국/한국/캐나다 등 **지역별(타임존·문화 피크) 차이**를 실제로 반영할까? 사이트
   유형(도심/주거/교외/이벤트) 분류를 어디까지 둘까?
5. **생성 충실도**: (A) 통계/난수 위주 경량 모델 vs (B) 큐잉/스케줄러 기반의 물리 충실 모델 — 어느 수준?
6. **Failure/Active Users 세부 KPI**: 실패는 어느 단위(RRC/E-RAB/Drop/HO)까지, 컬럼명 규칙은? 사용자
   수는 Connected/Active 구분이 필요한가?
7. **에너지 파라미터 출처**: RU HW별 `P_idle`/`P_max`를 ESM의 RU Spec에서 가져올까, 별도 정의할까?
8. **정답(ground truth) 라벨**: 데이터 애널리스트가 알고리즘을 만들 때 검증할 수 있도록, 생성 시 사용한
   **숨은 파라미터/이벤트(정답 라벨)** 를 함께 출력할까?
9. **이상/이벤트 주입**: 장애·혼잡·트래픽 급증 같은 **이상 시나리오**를 옵션으로 넣을까(이상탐지 알고리즘용)?
10. **UI 형태**: CLI+설정파일로 시작 vs 처음부터 GUI.

---

## 9. 개발 원칙 (Working Rules)

1. **컨텍스트 최우선**: 매 작업 전 이 문서를 읽고, 주요 변경 후 자동 갱신(요청 여부 무관).
2. **ESM 호환 우선**: 식별자 정규화·컬럼 의미·15분 스텝·`utf-8-sig` CSV 등 ESM 관례를 따른다.
3. **인과관계 보존**: 난수 남발 금지 — §5 체인을 통해 KPI 상관이 현실적으로 성립하게 한다.
4. **재현성**: 시드/설정으로 동일 출력 보장.
5. **규격 정합**: 용어/정의 모호 시 3GPP(TS 36/38, 28.552/32.425 등) 기준, ESM과 충돌하면 사용자 확인.
6. **커밋/푸시**: 검증된 변경은 지정 브랜치(`claude/wireless-network-kpi-docs-yjm6y4`)에 커밋·푸시.

---
*Last Updated: 2026-07-10*
*AI Directive Status: Active (Always Read First, Always Update Post-Task)*
