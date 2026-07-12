# -*- coding: utf-8 -*-
"""TrafficGen r2 — 상용망(4G LTE + 5G NR 오버레이) 트래픽/KPI Generator.

r1(ENDC/DC·SA Steering)을 복제해 시작. r2의 핵심 추가는 **사용자 편집 가능성 3종**:

  1. **주파수(캐리어) 편집**: 토폴로지(셀/캐리어)를 추가/삭제/수정 가능(GUI Carriers 탭 + API).
     캐리어 수가 3+3 고정이 아니라 임의 개수·임의 밴드로 구성할 수 있다.
  2. **트래픽 패턴 설정**(`TrafficPattern`): 트래픽 **양**(site peak Mbps)과 **시간대 shape**
     (피크 시각/세기/폭, 주말 감쇠, 기저 레벨)을 설정. 프리셋(default/business/evening/flat/night) 제공.
  3. **셀별 UE 비율 조정**(`ue_weight`): 특정 셀의 **유저 수 밀도**를 높이거나 낮춘다. 트래픽 분배
     (`load_weight`)와 **독립적** — 같은 트래픽이라도 UE가 많으면 사용자당 자원이 줄어 IP Tput(체감)↓.

r1의 steering(사용자 클래스별 LTE/NR 라우팅, 셀 on/off, DC 해제, 오프로딩)은 그대로 유지한다.
단, 트래픽 **양**은 r1에서 SteeringConfig.site_peak_dl_mbps 였던 것을 r2에서 TrafficPattern 으로 이관
(양+시간대를 한 곳에서 관리). Steering 은 라우팅/on-off 정책만 담당.

설계 원칙:
  * 엔진(생성/집계/Export/플로팅)은 tkinter 없이 동작 → headless 검증 가능.
  * GUI는 tkinter가 있을 때만 활성(없으면 base=object 로 안전하게 import).
  * KPI 간 인과관계를 규칙/확률로 반영(난수 남발 금지): 수요(양·패턴) → (steering) → 자원 → 체감/에너지/실패.

컬럼(ESM 호환): IP Tput(=(IpThruThpVoDLByte/IpThruThpDLTime)*8) / IpThruThpVoDLByte(vol 성분) /
IpThruThpDLTime(time 성분) / UsedRB / nRB / AirMacDLByte / AirMacULByte / RuPowerTot / RuPowerCnt.
식별자: eNB_ID / Sector / cell-num (콤마 없는 순수 숫자 문자열).
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 상수 / 컬럼명 (ESM 호환)
# ---------------------------------------------------------------------------
COL_TIME = "Time"
COL_ENB = "eNB_ID"
COL_SYS = "System"
COL_SECTOR = "Sector"
COL_CELL = "cell-num"
COL_BAND = "Band"
COL_FREQ = "Freq_MHz"
COL_BW = "BW_MHz"
COL_NRB = "nRB"
COL_IPTPUT = "IP Tput"          # Mbps (사용자 체감 throughput) = (ThpVol/ThpTime)*8
COL_THPVOL = "IpThruThpVoDLByte"   # DL IP Tput volume 성분 (ESM: (Vol/Time)*8 = Mbps)
COL_THPTIME = "IpThruThpDLTime"    # DL IP Tput time 성분 (활성 유저수의 함수 → 유저↑이면 커짐)
COL_USEDRB = "UsedRB"
COL_PRBUTIL = "PRB_Util"        # %
COL_DLB = "AirMacDLByte"
COL_ULB = "AirMacULByte"
COL_RUTOT = "RuPowerTot"        # RU 전력 샘플 합(W·samples)
COL_RUCNT = "RuPowerCnt"        # 샘플 수 → avg power = RuPowerTot/RuPowerCnt [W]
COL_CONN = "ConnectedUsers"
COL_ACTIVE = "ActiveUsers"
COL_RRCATT = "RrcConnAtt"
COL_RRCFAIL = "RrcConnFail"
COL_DROP = "ErabDrop"

KPI_COLS = [COL_IPTPUT, COL_THPVOL, COL_THPTIME, COL_USEDRB, COL_PRBUTIL, COL_DLB, COL_ULB,
            COL_RUTOT, COL_RUCNT, COL_CONN, COL_ACTIVE, COL_RRCATT, COL_RRCFAIL, COL_DROP]

# 토폴로지(캐리어) 스키마 — GUI 에디터가 다루는 셀 파라미터
TOPO_COLS = ["System", "eNB_ID", "Sector", "cell_num", "Band", "Freq_MHz", "BW_MHz",
             "nRB", "avg_cell_mbps", "peak_user_mbps", "max_users",
             "p_idle", "p_max", "dl_ratio", "ul_ratio", "load_weight", "ue_weight"]
# 숫자형 컬럼(에디터 입력 시 형변환)
TOPO_NUMERIC = {"Freq_MHz", "BW_MHz", "nRB", "avg_cell_mbps", "peak_user_mbps", "max_users",
                "p_idle", "p_max", "dl_ratio", "ul_ratio", "load_weight", "ue_weight"}
TOPO_ID_COLS = ("eNB_ID", "Sector", "cell_num")

DEFAULT_STEP_MIN = 15
LTE_ENB_ID = "1001"
NR_ENB_ID = "2001"


# ---------------------------------------------------------------------------
# 토폴로지 (기본: 단일 사이트 LTE×3 + NR×3 오버레이) — 편집 가능
# ---------------------------------------------------------------------------
def build_default_topology() -> pd.DataFrame:
    """MASTER_PROMPT §7-A 의 첫 시스템 토폴로지를 DataFrame 으로 반환(편집 가능한 기본값).

    각 셀에 물리/용량/에너지/유저 파라미터를 부여한다. `ue_weight`(신규, r2)는 셀의 유저 수 밀도
    배수(1.0=기본)로, 트래픽 분배(load_weight)와 독립적으로 특정 셀의 UE 비율을 조정한다.
    """
    cells = [
        # --- LTE (FDD, 20 MHz = 100 RB) ---
        dict(System="LTE", eNB_ID=LTE_ENB_ID, Sector="1", cell_num="1", Band="B1",
             Freq_MHz=2100, BW_MHz=20, nRB=100,
             avg_cell_mbps=95, peak_user_mbps=130, max_users=200,
             p_idle=320, p_max=700, dl_ratio=1.0, ul_ratio=0.12, load_weight=0.95, ue_weight=1.0),
        dict(System="LTE", eNB_ID=LTE_ENB_ID, Sector="1", cell_num="2", Band="B3",
             Freq_MHz=1800, BW_MHz=20, nRB=100,
             avg_cell_mbps=95, peak_user_mbps=130, max_users=200,
             p_idle=320, p_max=700, dl_ratio=1.0, ul_ratio=0.12, load_weight=0.90, ue_weight=1.0),
        dict(System="LTE", eNB_ID=LTE_ENB_ID, Sector="1", cell_num="3", Band="B7",
             Freq_MHz=2600, BW_MHz=20, nRB=100,
             avg_cell_mbps=90, peak_user_mbps=125, max_users=180,
             p_idle=330, p_max=720, dl_ratio=1.0, ul_ratio=0.12, load_weight=0.75, ue_weight=1.0),
        # --- NR (n78 TDD, 100 MHz / 30 kHz = 273 RB; 마지막은 소역폭) ---
        dict(System="NR", eNB_ID=NR_ENB_ID, Sector="1", cell_num="1", Band="n78",
             Freq_MHz=3500, BW_MHz=100, nRB=273,
             avg_cell_mbps=780, peak_user_mbps=950, max_users=320,
             p_idle=560, p_max=1360, dl_ratio=1.0, ul_ratio=0.10, load_weight=1.00, ue_weight=1.0),
        dict(System="NR", eNB_ID=NR_ENB_ID, Sector="1", cell_num="2", Band="n78",
             Freq_MHz=3600, BW_MHz=100, nRB=273,
             avg_cell_mbps=760, peak_user_mbps=930, max_users=300,
             p_idle=560, p_max=1360, dl_ratio=1.0, ul_ratio=0.10, load_weight=0.85, ue_weight=1.0),
        dict(System="NR", eNB_ID=NR_ENB_ID, Sector="1", cell_num="3", Band="n78",
             Freq_MHz=3700, BW_MHz=40, nRB=106,
             avg_cell_mbps=300, peak_user_mbps=420, max_users=180,
             p_idle=430, p_max=900, dl_ratio=1.0, ul_ratio=0.10, load_weight=0.60, ue_weight=1.0),
    ]
    return normalize_topology(pd.DataFrame(cells))


def normalize_topology(df: pd.DataFrame) -> pd.DataFrame:
    """토폴로지 DataFrame 을 표준 스키마로 정규화(누락 컬럼 보정 + 식별자/숫자 형변환)."""
    df = df.copy()
    # 누락 컬럼 채우기(하위호환: ue_weight 등 신규 컬럼이 없을 수 있음)
    defaults = {"ue_weight": 1.0, "load_weight": 1.0, "dl_ratio": 1.0, "ul_ratio": 0.1}
    for c in TOPO_COLS:
        if c not in df.columns:
            df[c] = defaults.get(c, 0)
    # ESM 식별자 규칙: 콤마 없는 순수 숫자 문자열
    for c in TOPO_ID_COLS:
        df[c] = df[c].astype(str).str.replace(",", "", regex=False).str.strip()
    for c in TOPO_NUMERIC:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["System"] = df["System"].astype(str).str.upper().str.strip()
    df["Band"] = df["Band"].astype(str).str.strip()
    return df[TOPO_COLS].reset_index(drop=True)


# ---------------------------------------------------------------------------
# 트래픽 패턴 (양 + 시간대 shape) — r2 신규
# ---------------------------------------------------------------------------
class TrafficPattern:
    """사이트 수요의 **양**과 **시간대 shape**를 정의한다.

    * `site_peak_dl_mbps` : 트래픽 양 — 정규화 shape(≈0~1)에 곱해 사이트 offered DL(Mbps)로 환산.
    * `peaks`             : 시간대 피크 목록. 각 항목 dict(hour, amp, width) — 가우시안 합으로 shape 구성.
    * `base_level`        : 기저 레벨(0에 가까울수록 야간 저점이 깊음; 크면 평탄해짐).
    * `weekend_factor`    : 주말(토·일) 진폭 배수(<1 이면 주말 트래픽 감소).
    * `noise_cv`          : 스텝 노이즈 변동계수.
    """

    def __init__(self, site_peak_dl_mbps: float = 900.0, peaks=None,
                 base_level: float = 0.08, weekend_factor: float = 0.80,
                 noise_cv: float = 0.06, floor: float = 0.02, ceil: float = 1.15):
        self.site_peak_dl_mbps = float(site_peak_dl_mbps)
        self.peaks = list(peaks) if peaks is not None else [
            dict(hour=9, amp=0.25, width=1.5),
            dict(hour=13, amp=0.55, width=2.5),
            dict(hour=21, amp=0.80, width=2.0),
        ]
        self.base_level = float(base_level)
        self.weekend_factor = float(weekend_factor)
        self.noise_cv = float(noise_cv)
        self.floor = float(floor)
        self.ceil = float(ceil)

    def shape(self, n_steps: int, step_min: int, rng: np.random.Generator) -> np.ndarray:
        """0~ceil 범위의 정규화 offered-load 시계열(피크 최대≈1, 노이즈·주말 반영)."""
        steps_per_day = int(round(24 * 60 / step_min))
        idx = np.arange(n_steps)
        hod = (idx % steps_per_day) * step_min / 60.0  # hour-of-day 0..24
        base = np.full(n_steps, self.base_level, dtype=float)
        for p in self.peaks:
            w = max(float(p.get("width", 1.0)), 1e-6)
            base = base + float(p.get("amp", 0.0)) * np.exp(-((hod - float(p.get("hour", 12))) ** 2) / (2 * w ** 2))
        mx = base.max()
        base = base / mx if mx > 0 else base
        dow = (idx // steps_per_day) % 7
        weekend = np.isin(dow, [5, 6])
        amp = np.where(weekend, self.weekend_factor, 1.0)
        noise = np.clip(rng.normal(1.0, self.noise_cv, n_steps), 0.7, 1.3)
        return np.clip(base * amp * noise, self.floor, self.ceil)

    def demand_mbps(self, n_steps: int, step_min: int, rng: np.random.Generator) -> np.ndarray:
        """사이트 offered DL 수요(Mbps) 시계열 = shape × 양(site_peak_dl_mbps)."""
        return self.shape(n_steps, step_min, rng) * self.site_peak_dl_mbps

    @classmethod
    def preset(cls, name: str) -> "TrafficPattern":
        name = (name or "").lower()
        if name in ("business", "office", "업무"):        # 업무시간 위주, 주말 낮음
            return cls(site_peak_dl_mbps=900, weekend_factor=0.5, base_level=0.05,
                       peaks=[dict(hour=10, amp=0.60, width=2.0), dict(hour=14, amp=0.60, width=2.5)])
        if name in ("evening", "residential", "주거"):     # 저녁 피크(주거지)
            return cls(site_peak_dl_mbps=1000, weekend_factor=1.0, base_level=0.07,
                       peaks=[dict(hour=13, amp=0.30, width=2.0), dict(hour=21, amp=1.00, width=2.5)])
        if name in ("flat", "평탄"):                        # 거의 평탄(고정 부하)
            return cls(site_peak_dl_mbps=700, weekend_factor=0.95, base_level=0.50,
                       peaks=[dict(hour=12, amp=0.20, width=6.0)])
        if name in ("night", "야간"):                       # 야간 피크
            return cls(site_peak_dl_mbps=800, weekend_factor=1.0, base_level=0.10,
                       peaks=[dict(hour=2, amp=0.70, width=2.5), dict(hour=23, amp=0.50, width=2.0)])
        return cls()  # default (점심+저녁 피크)


# 하위호환/단순 사용용 래퍼(기존 코드가 build_diurnal 을 참조할 수 있음)
def build_diurnal(n_steps: int, step_min: int, rng: np.random.Generator) -> np.ndarray:
    return TrafficPattern().shape(n_steps, step_min, rng)


# ---------------------------------------------------------------------------
# Steering 정책 (ENDC/DC·SA) — r1 유지, 단 트래픽 양(site_peak)은 TrafficPattern 으로 이관
# ---------------------------------------------------------------------------
class SteeringConfig:
    """사이트 수요를 사용자 클래스별로 나눠 LTE/NR 캐리어로 라우팅하는 정책.

    사용자 클래스:
      * Legacy-LTE  : NR 미지원 → 항상 LTE.
      * ENDC (NSA)  : LTE 앵커(MCG) + NR(SCG) 듀얼커넥티비티. 데이터는 endc_split_nr 비율로 NR/LTE 분배.
      * NR-SA       : NR 단독(제어+데이터).

    Steering 레버:
      * lte_enabled / nr_enabled : 캐리어 on/off (cell 순서의 bool 리스트). off 셀은 sleep 전력.
      * endc_split_nr            : ENDC 데이터 중 NR(SCG) 비중(0~1).
      * dc_release               : True → ENDC 데이터 전부 LTE anchor 로(=DC 해제).
      * nr_to_lte_offload        : NR 풀에서 LTE 로 강제 이전 비율(0~1, 로드밸런싱).
      * sa_fallback_to_lte       : NR 전면 off 시 NR-SA 사용자의 LTE 폴백 비율(나머지는 차단).
    """

    def __init__(self, frac_legacy: float = 0.15, frac_endc: float = 0.60, frac_sa: float = 0.25,
                 endc_split_nr: float = 0.80, dc_release: bool = False,
                 nr_to_lte_offload: float = 0.0, sa_fallback_to_lte: float = 0.5,
                 lte_enabled=None, nr_enabled=None):
        s = float(frac_legacy) + float(frac_endc) + float(frac_sa)
        s = s if s > 0 else 1.0
        self.frac_legacy = frac_legacy / s
        self.frac_endc = frac_endc / s
        self.frac_sa = frac_sa / s
        self.endc_split_nr = float(np.clip(endc_split_nr, 0.0, 1.0))
        self.dc_release = bool(dc_release)
        self.nr_to_lte_offload = float(np.clip(nr_to_lte_offload, 0.0, 1.0))
        self.sa_fallback_to_lte = float(np.clip(sa_fallback_to_lte, 0.0, 1.0))
        self.lte_enabled = lte_enabled          # None → 전부 on
        self.nr_enabled = nr_enabled

    def enabled_for(self, system: str, n_cells: int) -> list:
        flags = self.lte_enabled if system == "LTE" else self.nr_enabled
        if flags is None:
            return [True] * n_cells
        return [bool(flags[i]) if i < len(flags) else True for i in range(n_cells)]

    # -- 프리셋 시나리오 --
    @classmethod
    def preset(cls, name: str) -> "SteeringConfig":
        name = (name or "").lower()
        if name in ("baseline", "기본"):
            return cls()
        if name in ("nr_off", "nr off", "energy"):          # NR 마지막 캐리어 off (에너지 세이빙)
            return cls(nr_enabled=[True, True, False])
        if name in ("nr_all_off", "all nr off"):            # NR 전면 off
            return cls(nr_enabled=[False, False, False])
        if name in ("dc_release", "dc release"):            # DC 해제 → LTE anchor
            return cls(dc_release=True)
        if name in ("offload", "nr_to_lte"):                # NR→LTE 50% 오프로딩
            return cls(nr_to_lte_offload=0.5)
        return cls()


# ---------------------------------------------------------------------------
# 생성 엔진
# ---------------------------------------------------------------------------
class TrafficGenEngine:
    """단일 사이트 LTE/NR 오버레이의 셀 단위 KPI 시계열을 생성한다."""

    def __init__(self, topology: pd.DataFrame | None = None,
                 days: int = 7, step_min: int = DEFAULT_STEP_MIN,
                 start: str = "2026-07-01", seed: int = 42,
                 steering: SteeringConfig | None = None,
                 pattern: TrafficPattern | None = None):
        topo = topology if topology is not None else build_default_topology()
        self.topology = normalize_topology(topo)
        self.days = int(days)
        self.step_min = int(step_min)
        self.start = start
        self.seed = int(seed)
        self.steering = steering if steering is not None else SteeringConfig()
        self.pattern = pattern if pattern is not None else TrafficPattern()

    def _route_demand(self, site_demand_mbps: np.ndarray) -> dict:
        """사이트 수요(Mbps)를 사용자 클래스로 나눠 steering 정책대로 캐리어별 배정 Mbps 로 라우팅.

        반환: {(eNB_ID, cell-num): assigned_dl_mbps 시계열}, enabled, 진단용 pool 시계열.
        트래픽 보존: LTE 풀 + NR 풀 (+차단분) == 서비스 대상 수요.
        """
        st = self.steering
        topo = self.topology
        site_demand = np.asarray(site_demand_mbps, dtype=float)

        d_leg = site_demand * st.frac_legacy
        d_endc = site_demand * st.frac_endc
        d_sa = site_demand * st.frac_sa

        lte_cells = topo[topo[COL_SYS] == "LTE"].reset_index(drop=True)
        nr_cells = topo[topo[COL_SYS] == "NR"].reset_index(drop=True)
        lte_on = st.enabled_for("LTE", len(lte_cells))
        nr_on = st.enabled_for("NR", len(nr_cells))
        nr_available = any(nr_on) if len(nr_cells) else False
        lte_available = any(lte_on) if len(lte_cells) else False

        lte_pool = d_leg.astype(float).copy()
        nr_pool = np.zeros_like(site_demand)
        # ENDC: NR(SCG)/LTE(MCG) 분배 — DC 해제 또는 NR 미가용 시 전부 LTE anchor
        if nr_available and not st.dc_release:
            nr_pool = nr_pool + d_endc * st.endc_split_nr
            lte_pool = lte_pool + d_endc * (1.0 - st.endc_split_nr)
        else:
            lte_pool = lte_pool + d_endc
        # NR-SA: NR 가용 시 NR, 아니면 일부만 LTE 폴백(나머지 차단)
        if nr_available:
            nr_pool = nr_pool + d_sa
        else:
            lte_pool = lte_pool + d_sa * st.sa_fallback_to_lte
        # 로드밸런싱: NR→LTE 강제 오프로딩
        moved = nr_pool * st.nr_to_lte_offload
        nr_pool = nr_pool - moved
        lte_pool = lte_pool + moved
        # LTE 가 전혀 없으면 LTE 풀은 서비스 불가(차단)
        if not lte_available:
            lte_pool = np.zeros_like(site_demand)

        assigned = {}

        def _distribute(cells, on_flags, pool):
            w = np.array([(float(cells.loc[i, "avg_cell_mbps"]) * float(cells.loc[i, "load_weight"]))
                          if on_flags[i] else 0.0 for i in range(len(cells))])
            wsum = w.sum()
            for i in range(len(cells)):
                key = (cells.loc[i, "eNB_ID"], cells.loc[i, "cell_num"])
                assigned[key] = pool * (w[i] / wsum) if wsum > 0 else np.zeros_like(pool)

        _distribute(lte_cells, lte_on, lte_pool)
        _distribute(nr_cells, nr_on, nr_pool)
        enabled = {}
        for i in range(len(lte_cells)):
            enabled[(lte_cells.loc[i, "eNB_ID"], lte_cells.loc[i, "cell_num"])] = lte_on[i]
        for i in range(len(nr_cells)):
            enabled[(nr_cells.loc[i, "eNB_ID"], nr_cells.loc[i, "cell_num"])] = nr_on[i]
        return dict(assigned=assigned, enabled=enabled, lte_pool=lte_pool, nr_pool=nr_pool)

    # -- 셀 1개의 시계열 --
    def _generate_cell(self, cell: pd.Series, assigned_dl_mbps: np.ndarray,
                       enabled: bool, rng: np.random.Generator, step_sec: int) -> dict:
        n = len(assigned_dl_mbps)
        p_sleep = 0.12 * float(cell["p_idle"])               # 셀 off 시 sleep 전력
        ue_w = float(cell.get("ue_weight", 1.0) or 1.0)      # r2: 셀별 UE 밀도 배수

        if not enabled:                                      # 꺼진 셀: 트래픽/유저 0, sleep 전력
            z = np.zeros(n)
            zi = np.zeros(n, dtype=int)
            ru_cnt = np.full(n, step_sec, dtype=float)
            return dict(
                offered=z, used_rb=zi, prb_util=z, dl_bytes=z, ul_bytes=z,
                conn=zi, active=zi, ip_tput=z.copy(), thp_vol=z.copy(), thp_time=z.copy(),
                ru_tot=p_sleep * ru_cnt, ru_cnt=ru_cnt,
                rrc_att=zi, rrc_fail=zi, drop=zi)

        # offered load = 배정 수요 ÷ 셀 용량 (1 초과 시 혼잡)
        offered = (assigned_dl_mbps / max(float(cell["avg_cell_mbps"]), 1e-9)
                   ) * np.clip(rng.normal(1.0, 0.05, n), 0.85, 1.15)
        offered = np.clip(offered, 0.0, 1.5)
        util = np.minimum(offered, 1.0)                      # 자원 포화(≤100%)

        used_rb = np.round(util * float(cell["nRB"])).astype(int)
        prb_util = 100.0 * used_rb / max(float(cell["nRB"]), 1e-9)

        served_mbps = util * float(cell["avg_cell_mbps"])    # 실제 전달 = min(배정, 용량)
        dl_bytes = served_mbps * 1e6 / 8.0 * step_sec * float(cell["dl_ratio"])
        ul_bytes = dl_bytes * float(cell["ul_ratio"])

        # 사용자 수: 배정 수요(offered)에 비례 × 셀별 UE 밀도(ue_weight) → 수요 0이면 유저 0
        conn = np.maximum(0, np.round(float(cell["max_users"]) * ue_w * np.clip(offered, 0, 1)
                                      * np.clip(rng.normal(1.0, 0.08, n), 0.6, 1.4))).astype(int)
        active = np.maximum(0, np.round(conn * (0.4 + 0.5 * util)
                                        * np.clip(rng.normal(1.0, 0.10, n), 0.5, 1.5))).astype(int)
        active_eff = np.maximum(active, 1)

        # 사용자 체감 throughput: 셀 용량을 활성 유저로 분배, 단일유저 피크 상한, 혼잡 감쇠.
        # → ue_weight↑ 이면 active↑ 이므로 사용자당 처짐↓ (특정 셀 UE 비율 조정 효과가 여기서 드러남).
        ip_tput = np.minimum(float(cell["peak_user_mbps"]), float(cell["avg_cell_mbps"]) / active_eff)
        ip_tput = ip_tput * (1.0 - 0.35 * np.clip(offered - 1.0, 0, 0.5) / 0.5)
        ip_tput = np.where(active > 0, np.maximum(ip_tput, 0.1), 0.0)   # 트래픽 없으면 0

        # IP Tput 의 volume/time 성분을 각각 생성 — ESM 정의: IP Tput[Mbps] = (Vol/Time)*8.
        #  * Vol 성분(thp_vol): 전달 DL 볼륨의 대부분(마지막 TTI 제외 근사, ×0.95). 단위 KByte 스케일.
        #  * Time 성분(thp_time): Vol÷rate 로 유도 → 활성 유저수↑(⇒ip_tput↓)일수록 커진다(사용자 강조:
        #    "전송 소요시간은 유저 수의 함수"). 여러 UE 의 활성시간 합이므로 ROP(15분)를 초과할 수 있음(정상).
        #  * 정의상 (thp_vol/thp_time)*8 == ip_tput 이 정확히 성립 → ESM 이 두 성분으로 재계산해도 동일.
        thp_vol = dl_bytes * 0.95 / 1000.0                              # KByte
        thp_time = np.where(ip_tput > 0, thp_vol * 8.0 / np.maximum(ip_tput, 1e-9), 0.0)  # ms
        no_traffic = (dl_bytes <= 0) | (active <= 0)
        thp_vol = np.where(no_traffic, 0.0, thp_vol)
        thp_time = np.where(no_traffic, 0.0, thp_time)

        # 에너지: RU 소모전력 = 정적 + 부하 비례
        power_w = float(cell["p_idle"]) + (float(cell["p_max"]) - float(cell["p_idle"])) * util
        power_w = power_w * np.clip(rng.normal(1.0, 0.02, n), 0.95, 1.05)
        ru_cnt = np.full(n, step_sec, dtype=float)
        ru_tot = power_w * ru_cnt

        # 실패: 기저율 + 혼잡(제곱) 가중
        attempts = np.maximum(0, conn * 0.12 + active * 0.20)
        cong = np.clip(offered - 0.8, 0, 0.7)
        fail_rate = 0.002 + 0.18 * (cong ** 2)
        rrc_fail = rng.poisson(np.maximum(attempts * fail_rate, 0)).astype(int)
        drop = rng.poisson(np.maximum(active * (0.001 + 0.05 * cong ** 2), 0)).astype(int)

        return dict(
            offered=offered, used_rb=used_rb, prb_util=prb_util,
            dl_bytes=dl_bytes, ul_bytes=ul_bytes, conn=conn, active=active,
            ip_tput=ip_tput, thp_vol=thp_vol, thp_time=thp_time, ru_tot=ru_tot, ru_cnt=ru_cnt,
            rrc_att=np.round(attempts).astype(int), rrc_fail=rrc_fail, drop=drop,
        )

    def generate(self) -> pd.DataFrame:
        """모든 셀의 KPI를 long-format DataFrame 으로 반환(패턴+steering 반영)."""
        rng = np.random.default_rng(self.seed)
        n_steps = self.days * int(round(24 * 60 / self.step_min))
        times = pd.date_range(self.start, periods=n_steps, freq=f"{self.step_min}min")
        step_sec = self.step_min * 60
        site_demand = self.pattern.demand_mbps(n_steps, self.step_min, rng)
        routed = self._route_demand(site_demand)

        frames = []
        for _, cell in self.topology.iterrows():
            key = (cell["eNB_ID"], cell["cell_num"])
            # 셀마다 독립 스트림(재현성 유지): 셀 식별자로 서브시드
            sub = rng.integers(0, 2**31 - 1)
            crng = np.random.default_rng(int(sub))
            g = self._generate_cell(cell, routed["assigned"][key],
                                    routed["enabled"][key], crng, step_sec)
            df = pd.DataFrame({
                COL_TIME: times,
                COL_ENB: cell["eNB_ID"], COL_SYS: cell["System"],
                COL_SECTOR: cell["Sector"], COL_CELL: cell["cell_num"],
                COL_BAND: cell["Band"], COL_FREQ: cell["Freq_MHz"],
                COL_BW: cell["BW_MHz"], COL_NRB: cell["nRB"],
                COL_CONN: g["conn"], COL_ACTIVE: g["active"],
                COL_USEDRB: g["used_rb"], COL_PRBUTIL: np.round(g["prb_util"], 2),
                COL_DLB: np.round(g["dl_bytes"]).astype("int64"),
                COL_ULB: np.round(g["ul_bytes"]).astype("int64"),
                COL_IPTPUT: np.round(g["ip_tput"], 3),
                COL_THPVOL: np.round(g["thp_vol"], 1), COL_THPTIME: np.round(g["thp_time"], 1),
                COL_RUTOT: np.round(g["ru_tot"], 1), COL_RUCNT: g["ru_cnt"].astype("int64"),
                COL_RRCATT: g["rrc_att"], COL_RRCFAIL: g["rrc_fail"], COL_DROP: g["drop"],
            })
            frames.append(df)
        out = pd.concat(frames, ignore_index=True)
        return out


# ---------------------------------------------------------------------------
# 집계 (Cell / LTE Sector / NR Sector / Total)
# ---------------------------------------------------------------------------
def _consumed_wh(df: pd.DataFrame, step_min: int) -> pd.Series:
    """RuPowerTot/RuPowerCnt(=avg W) × 시간(h) = 소모 에너지[Wh]."""
    avg_w = df[COL_RUTOT] / df[COL_RUCNT].replace(0, np.nan)
    return avg_w.fillna(0) * (step_min / 60.0)


def _agg_group(df: pd.DataFrame, step_min: int) -> pd.DataFrame:
    """이미 (Time 기준) 한 그룹으로 필터된 셀 집합을 Time 축으로 집계."""
    g = df.groupby(COL_TIME, sort=True)
    used = g[COL_USEDRB].sum()
    nrb = g[COL_NRB].sum()
    dlb = g[COL_DLB].sum()
    ulb = g[COL_ULB].sum()
    # IP Tput: 성분 합으로 계산 = (ΣThpVol / ΣThpTime)*8 [Mbps] (ESM 정의와 동일한 볼륨가중 결합).
    tvol = g[COL_THPVOL].sum()
    ttime = g[COL_THPTIME].sum()
    ip = (8.0 * tvol / ttime.replace(0, np.nan)).fillna(0)
    out = pd.DataFrame({
        COL_TIME: used.index,
        COL_USEDRB: used.values, COL_NRB: nrb.values,
        COL_PRBUTIL: np.round(100.0 * used.values / nrb.replace(0, np.nan).values, 2),
        COL_DLB: dlb.values, COL_ULB: ulb.values,
        COL_IPTPUT: np.round(ip.values, 3),
        COL_THPVOL: np.round(tvol.values, 1), COL_THPTIME: np.round(ttime.values, 1),
        COL_CONN: g[COL_CONN].sum().values, COL_ACTIVE: g[COL_ACTIVE].sum().values,
        COL_RUTOT: g[COL_RUTOT].sum().values, COL_RUCNT: g[COL_RUCNT].sum().values,
        COL_RRCATT: g[COL_RRCATT].sum().values, COL_RRCFAIL: g[COL_RRCFAIL].sum().values,
        COL_DROP: g[COL_DROP].sum().values,
    })
    # 에너지는 "평균전력 합"이 아니라 셀별 Wh 를 먼저 구해 합산해야 총량이 맞다.
    wh_row = (df[COL_RUTOT] / df[COL_RUCNT].replace(0, np.nan)).fillna(0) * (step_min / 60.0)
    consumed = df.assign(_wh=wh_row).groupby(COL_TIME, sort=True)["_wh"].sum()
    out["Consumed_Wh"] = np.round(consumed.reindex(out[COL_TIME]).values, 2)
    return out


def aggregate_kpis(cell_df: pd.DataFrame, step_min: int = DEFAULT_STEP_MIN) -> dict:
    """Cell / LTE Sector / NR Sector / Total 4레벨 집계 결과를 dict 로 반환."""
    lte = cell_df[cell_df[COL_SYS] == "LTE"]
    nr = cell_df[cell_df[COL_SYS] == "NR"]
    return {
        "cell": cell_df,
        "lte_sector": _agg_group(lte, step_min) if not lte.empty else pd.DataFrame(),
        "nr_sector": _agg_group(nr, step_min) if not nr.empty else pd.DataFrame(),
        "total": _agg_group(cell_df, step_min) if not cell_df.empty else pd.DataFrame(),
    }


def summary_table(agg: dict) -> pd.DataFrame:
    """레벨별 대표 통계(평균/피크)를 비교용 표로 요약."""
    rows = []
    for name, df in (("LTE Sector", agg["lte_sector"]),
                     ("NR Sector", agg["nr_sector"]),
                     ("LTE+NR Total", agg["total"])):
        if df is None or df.empty:
            continue
        rows.append(dict(
            Level=name,
            Mean_PRB_Util=round(df[COL_PRBUTIL].mean(), 1),
            Peak_PRB_Util=round(df[COL_PRBUTIL].max(), 1),
            Mean_IP_Tput=round(df[COL_IPTPUT].mean(), 1),
            Total_DL_GB=round(df[COL_DLB].sum() / 1e9, 2),
            Total_UL_GB=round(df[COL_ULB].sum() / 1e9, 2),
            Total_Energy_kWh=round(df["Consumed_Wh"].sum() / 1000.0, 2),
            Mean_Active_Users=round(df[COL_ACTIVE].mean(), 1),
            Total_RrcFail=int(df[COL_RRCFAIL].sum()),
        ))
    return pd.DataFrame(rows)


def cell_summary_table(cell_df: pd.DataFrame, step_min: int = DEFAULT_STEP_MIN) -> pd.DataFrame:
    """셀 단위 대표 통계(캐리어/UE 조정 효과 비교용)."""
    rows = []
    for (sysv, enb, cn), sub in cell_df.groupby([COL_SYS, COL_ENB, COL_CELL], sort=False):
        wh = _consumed_wh(sub, step_min)
        rows.append(dict(
            System=sysv, eNB_ID=enb, Cell=cn, Band=sub[COL_BAND].iloc[0],
            Freq=sub[COL_FREQ].iloc[0], nRB=int(sub[COL_NRB].iloc[0]),
            Mean_PRB_Util=round(sub[COL_PRBUTIL].mean(), 1),
            Mean_IP_Tput=round(sub[COL_IPTPUT].replace(0, np.nan).mean(), 1),
            Total_DL_GB=round(sub[COL_DLB].sum() / 1e9, 2),
            Mean_Active_Users=round(sub[COL_ACTIVE].mean(), 1),
            Energy_kWh=round(wh.sum() / 1000.0, 2),
        ))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Export (ESM 호환 CSV)
# ---------------------------------------------------------------------------
def export_esm_csv(cell_df: pd.DataFrame, topology: pd.DataFrame, out_dir: str,
                   step_min: int = DEFAULT_STEP_MIN) -> list[str]:
    """PM(Traffic) / Energy Stat / Topology(CM) 3개 CSV 를 utf-8-sig 로 저장."""
    os.makedirs(out_dir, exist_ok=True)
    written = []

    pm_cols = [COL_TIME, COL_ENB, COL_SYS, COL_SECTOR, COL_CELL, COL_BAND, COL_NRB,
               COL_IPTPUT, COL_THPVOL, COL_THPTIME, COL_USEDRB, COL_PRBUTIL, COL_DLB, COL_ULB,
               COL_CONN, COL_ACTIVE, COL_RRCATT, COL_RRCFAIL, COL_DROP]
    pm_path = os.path.join(out_dir, "traffic_pm.csv")
    cell_df[pm_cols].to_csv(pm_path, index=False, encoding="utf-8-sig")
    written.append(pm_path)

    en = cell_df.copy()
    en["Consumed_Wh"] = np.round(_consumed_wh(en, step_min), 2)
    en_cols = [COL_TIME, COL_ENB, COL_SYS, COL_SECTOR, COL_CELL,
               COL_RUTOT, COL_RUCNT, "Consumed_Wh"]
    en_path = os.path.join(out_dir, "energy_stat.csv")
    en[en_cols].to_csv(en_path, index=False, encoding="utf-8-sig")
    written.append(en_path)

    topo_path = os.path.join(out_dir, "topology_cm.csv")
    topology.to_csv(topo_path, index=False, encoding="utf-8-sig")
    written.append(topo_path)
    return written


# ---------------------------------------------------------------------------
# 시각화 (Axes 주입식 → GUI/headless 공용)
# ---------------------------------------------------------------------------
def plot_kpi(ax, df: pd.DataFrame, kpi: str, plot_type: str = "time", label: str = ""):
    """시계열/CDF/히스토그램 그리기. df 는 Time 컬럼을 가진 프레임."""
    series = pd.to_numeric(df[kpi], errors="coerce").dropna().values
    if plot_type == "time":
        ax.plot(df[COL_TIME], pd.to_numeric(df[kpi], errors="coerce"), label=label or kpi)
        ax.set_xlabel("Time"); ax.set_ylabel(kpi)
    elif plot_type == "cdf":
        s = np.sort(series)
        y = np.arange(1, len(s) + 1) / max(len(s), 1)
        ax.plot(s, y, label=label or kpi)
        ax.set_xlabel(kpi); ax.set_ylabel("CDF"); ax.set_ylim(0, 1)
    elif plot_type == "hist":
        ax.hist(series, bins=30, alpha=0.7, label=label or kpi)
        ax.set_xlabel(kpi); ax.set_ylabel("Count")
    ax.set_title(f"{kpi} — {plot_type.upper()}")
    ax.grid(True, alpha=0.3)


# ---------------------------------------------------------------------------
# GUI (Tkinter) — tkinter 없으면 base=object 로 안전하게 import
# ---------------------------------------------------------------------------
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    _HAS_TK = True
except Exception:  # pragma: no cover - 헤드리스 환경
    _HAS_TK = False
    tk = None  # type: ignore

_GUI_BASE = tk.Tk if _HAS_TK else object


class TrafficGenApp(_GUI_BASE):  # type: ignore[misc]
    """6탭 GUI: Carriers / Traffic & Steering / Generate / Visualize / Compare / Export."""

    LEVELS = ["Cell", "LTE Sector", "NR Sector", "LTE+NR Total"]
    PATTERN_PRESETS = ["default", "business", "evening", "flat", "night"]

    def __init__(self):
        if not _HAS_TK:
            raise RuntimeError("tkinter 를 사용할 수 없습니다(GUI는 로컬 환경에서 실행하세요).")
        super().__init__()
        self.title("TrafficGen r2 — LTE/NR Overlay KPI Generator (Carrier · Pattern · UE editable)")
        self.geometry("1140x800")
        self.topology = build_default_topology()
        self.pattern_peaks = [dict(p) for p in TrafficPattern().peaks]
        self.cell_df = None
        self.agg = None
        self._build_ui()

    # --- UI 구성 ---
    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self.tab_car = ttk.Frame(nb); nb.add(self.tab_car, text="📡 Carriers")
        self.tab_traf = ttk.Frame(nb); nb.add(self.tab_traf, text="📶 Traffic & Steering")
        self.tab_gen = ttk.Frame(nb); nb.add(self.tab_gen, text="▶️ Generate")
        self.tab_viz = ttk.Frame(nb); nb.add(self.tab_viz, text="📈 Visualize")
        self.tab_cmp = ttk.Frame(nb); nb.add(self.tab_cmp, text="📊 Compare")
        self.tab_exp = ttk.Frame(nb); nb.add(self.tab_exp, text="💾 Export")
        self._build_carriers_tab()
        self._build_traffic_tab()
        self._build_generate_tab()
        self._build_visualize_tab()
        self._build_compare_tab()
        self._build_export_tab()

    # ===== Carriers (주파수 편집) =====
    def _build_carriers_tab(self):
        top = ttk.Frame(self.tab_car); top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="Days:").pack(side="left")
        self.var_days = tk.IntVar(value=7)
        ttk.Spinbox(top, from_=1, to=60, width=5, textvariable=self.var_days).pack(side="left", padx=4)
        ttk.Label(top, text="Step(min):").pack(side="left")
        self.var_step = tk.IntVar(value=15)
        ttk.Spinbox(top, from_=5, to=60, increment=5, width=5, textvariable=self.var_step).pack(side="left", padx=4)
        ttk.Label(top, text="Seed:").pack(side="left")
        self.var_seed = tk.IntVar(value=42)
        ttk.Spinbox(top, from_=0, to=99999, width=7, textvariable=self.var_seed).pack(side="left", padx=4)

        ttk.Label(self.tab_car, text="캐리어(주파수/셀) 목록 — 행 선택 후 수정/삭제, 아래 폼으로 추가",
                  font=("", 9, "bold")).pack(anchor="w", padx=8)
        self.car_tv = ttk.Treeview(self.tab_car, columns=TOPO_COLS, show="headings", height=8)
        for c in TOPO_COLS:
            self.car_tv.heading(c, text=c)
            self.car_tv.column(c, width=74, anchor="center")
        self.car_tv.pack(fill="x", padx=8, pady=4)
        self.car_tv.bind("<<TreeviewSelect>>", self._on_car_select)

        # 편집 폼(모든 토폴로지 컬럼) — 2행 그리드
        form = ttk.LabelFrame(self.tab_car, text="Carrier 편집 (Add / Update / Delete)")
        form.pack(fill="x", padx=8, pady=6)
        self.car_vars = {}
        per_row = 6
        for i, c in enumerate(TOPO_COLS):
            r, col = divmod(i, per_row)
            cell = ttk.Frame(form); cell.grid(row=r, column=col, padx=4, pady=3, sticky="w")
            ttk.Label(cell, text=c, width=13).pack(side="top", anchor="w")
            v = tk.StringVar()
            ttk.Entry(cell, textvariable=v, width=13).pack(side="top")
            self.car_vars[c] = v

        btns = ttk.Frame(self.tab_car); btns.pack(fill="x", padx=8, pady=4)
        ttk.Button(btns, text="➕ Add", command=self._car_add).pack(side="left", padx=3)
        ttk.Button(btns, text="✏️ Update", command=self._car_update).pack(side="left", padx=3)
        ttk.Button(btns, text="🗑️ Delete", command=self._car_delete).pack(side="left", padx=3)
        ttk.Button(btns, text="↺ Reset default", command=self._car_reset).pack(side="left", padx=3)
        ttk.Button(btns, text="⤵ Load form from default row", command=self._car_fill_template).pack(side="left", padx=3)
        self.car_status = tk.StringVar(value="")
        ttk.Label(self.tab_car, textvariable=self.car_status, foreground="#2255aa").pack(anchor="w", padx=8)
        self._refresh_car_tree()

    def _refresh_car_tree(self):
        self.topology = normalize_topology(self.topology)
        self.car_tv.delete(*self.car_tv.get_children())
        for _, r in self.topology.iterrows():
            self.car_tv.insert("", "end", values=[r[c] for c in TOPO_COLS])

    def _on_car_select(self, _evt=None):
        sel = self.car_tv.selection()
        if not sel:
            return
        vals = self.car_tv.item(sel[0], "values")
        for c, v in zip(TOPO_COLS, vals):
            self.car_vars[c].set(v)

    def _car_fill_template(self):
        d = build_default_topology().iloc[0]
        for c in TOPO_COLS:
            self.car_vars[c].set(d[c])
        self.car_status.set("기본 셀 템플릿을 폼에 불러왔습니다. 값을 고쳐 Add 하세요.")

    def _form_row(self) -> dict:
        row = {}
        for c in TOPO_COLS:
            val = self.car_vars[c].get().strip()
            row[c] = val
        return row

    def _car_add(self):
        row = self._form_row()
        if not row["System"] or not row["cell_num"]:
            self.car_status.set("System 과 cell_num 은 필수입니다."); return
        self.topology = normalize_topology(pd.concat(
            [self.topology, pd.DataFrame([row])], ignore_index=True))
        self._refresh_car_tree(); self._rebuild_cell_toggles()
        self.car_status.set(f"추가됨: {row['System']} {row['Band']} (cell {row['cell_num']}). 총 {len(self.topology)} 셀.")

    def _car_update(self):
        sel = self.car_tv.selection()
        if not sel:
            self.car_status.set("수정할 행을 먼저 선택하세요."); return
        idx = self.car_tv.index(sel[0])
        row = self._form_row()
        for c in TOPO_COLS:
            self.topology.loc[idx, c] = row[c]
        self.topology = normalize_topology(self.topology)
        self._refresh_car_tree(); self._rebuild_cell_toggles()
        self.car_status.set(f"수정됨: index {idx}.")

    def _car_delete(self):
        sel = self.car_tv.selection()
        if not sel:
            self.car_status.set("삭제할 행을 먼저 선택하세요."); return
        idx = self.car_tv.index(sel[0])
        self.topology = self.topology.drop(index=idx).reset_index(drop=True)
        self._refresh_car_tree(); self._rebuild_cell_toggles()
        self.car_status.set(f"삭제됨: index {idx}. 총 {len(self.topology)} 셀.")

    def _car_reset(self):
        self.topology = build_default_topology()
        self._refresh_car_tree(); self._rebuild_cell_toggles()
        self.car_status.set("기본 토폴로지로 초기화했습니다(LTE×3 + NR×3).")

    # ===== Traffic & Steering =====
    def _build_traffic_tab(self):
        # --- Traffic Pattern ---
        pf = ttk.LabelFrame(self.tab_traf, text="Traffic Pattern (양 + 시간대)")
        pf.pack(fill="x", padx=8, pady=6)
        r1 = ttk.Frame(pf); r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Preset:").pack(side="left")
        self.var_pat = tk.StringVar(value="default")
        ttk.Combobox(r1, values=self.PATTERN_PRESETS, textvariable=self.var_pat, width=10,
                     state="readonly").pack(side="left", padx=4)
        ttk.Button(r1, text="Apply Pattern Preset", command=self._apply_pattern_preset).pack(side="left", padx=6)
        ttk.Label(r1, text="Site peak DL(Mbps)=양:").pack(side="left", padx=(12, 2))
        self.var_speak = tk.DoubleVar(value=900.0)
        ttk.Spinbox(r1, from_=50, to=10000, increment=50, width=8, textvariable=self.var_speak).pack(side="left")

        r2 = ttk.Frame(pf); r2.pack(fill="x", pady=3)
        ttk.Label(r2, text="Weekend factor:").pack(side="left")
        self.var_weekend = tk.DoubleVar(value=0.80)
        ttk.Spinbox(r2, from_=0.1, to=1.5, increment=0.05, width=6, textvariable=self.var_weekend).pack(side="left", padx=4)
        ttk.Label(r2, text="Base level:").pack(side="left", padx=(10, 2))
        self.var_base = tk.DoubleVar(value=0.08)
        ttk.Spinbox(r2, from_=0.0, to=1.0, increment=0.02, width=6, textvariable=self.var_base).pack(side="left")

        ttk.Label(pf, text="시간대 피크 목록 (hour / amp / width) — 선택 후 Update·Delete, 폼으로 Add").pack(anchor="w", padx=6)
        pkrow = ttk.Frame(pf); pkrow.pack(fill="x", padx=6, pady=2)
        self.pk_tv = ttk.Treeview(pkrow, columns=["hour", "amp", "width"], show="headings", height=4)
        for c in ("hour", "amp", "width"):
            self.pk_tv.heading(c, text=c); self.pk_tv.column(c, width=80, anchor="center")
        self.pk_tv.pack(side="left", fill="x", expand=True)
        self.pk_tv.bind("<<TreeviewSelect>>", self._on_pk_select)
        pkform = ttk.Frame(pkrow); pkform.pack(side="left", padx=8)
        self.var_pk_hour = tk.DoubleVar(value=12.0)
        self.var_pk_amp = tk.DoubleVar(value=0.5)
        self.var_pk_width = tk.DoubleVar(value=2.0)
        for lab, var in (("hour", self.var_pk_hour), ("amp", self.var_pk_amp), ("width", self.var_pk_width)):
            fr = ttk.Frame(pkform); fr.pack(side="top", anchor="w")
            ttk.Label(fr, text=lab, width=6).pack(side="left")
            ttk.Spinbox(fr, from_=0, to=24, increment=0.5, width=7, textvariable=var).pack(side="left")
        pkbtn = ttk.Frame(pkform); pkbtn.pack(side="top", pady=3)
        ttk.Button(pkbtn, text="➕", width=3, command=self._pk_add).pack(side="left", padx=2)
        ttk.Button(pkbtn, text="✏️", width=3, command=self._pk_update).pack(side="left", padx=2)
        ttk.Button(pkbtn, text="🗑️", width=3, command=self._pk_delete).pack(side="left", padx=2)
        self._refresh_pk_tree()

        # --- Steering ---
        sf = ttk.LabelFrame(self.tab_traf, text="Steering (ENDC/DC·SA)")
        sf.pack(fill="x", padx=8, pady=6)
        s1 = ttk.Frame(sf); s1.pack(fill="x", pady=3)
        ttk.Label(s1, text="Preset:").pack(side="left")
        self.var_preset = tk.StringVar(value="baseline")
        ttk.Combobox(s1, values=["baseline", "nr_off", "nr_all_off", "dc_release", "offload"],
                     textvariable=self.var_preset, width=12, state="readonly").pack(side="left", padx=4)
        ttk.Button(s1, text="Apply Steering Preset", command=self._apply_preset).pack(side="left", padx=6)
        ttk.Label(s1, text="ENDC split→NR:").pack(side="left", padx=(12, 2))
        self.var_split = tk.DoubleVar(value=0.80)
        ttk.Spinbox(s1, from_=0, to=1, increment=0.05, width=5, textvariable=self.var_split).pack(side="left")
        self.var_dcrel = tk.BooleanVar(value=False)
        ttk.Checkbutton(s1, text="DC release", variable=self.var_dcrel).pack(side="left", padx=8)
        ttk.Label(s1, text="NR→LTE offload:").pack(side="left")
        self.var_offload = tk.DoubleVar(value=0.0)
        ttk.Spinbox(s1, from_=0, to=1, increment=0.1, width=5, textvariable=self.var_offload).pack(side="left", padx=4)

        self.toggle_frame = ttk.Frame(sf); self.toggle_frame.pack(fill="x", pady=4)
        self.var_lte_on, self.var_nr_on = [], []
        self._rebuild_cell_toggles()

    def _rebuild_cell_toggles(self):
        """현재 토폴로지의 LTE/NR 셀 개수에 맞춰 on/off 체크박스를 재구성."""
        if not hasattr(self, "toggle_frame"):
            return
        for w in self.toggle_frame.winfo_children():
            w.destroy()
        topo = normalize_topology(self.topology)
        lte_cells = topo[topo[COL_SYS] == "LTE"]
        nr_cells = topo[topo[COL_SYS] == "NR"]
        self.var_lte_on = [tk.BooleanVar(value=True) for _ in range(len(lte_cells))]
        self.var_nr_on = [tk.BooleanVar(value=True) for _ in range(len(nr_cells))]
        ttk.Label(self.toggle_frame, text="Cell on/off — LTE:").pack(side="left")
        for i, (_, c) in enumerate(lte_cells.iterrows()):
            ttk.Checkbutton(self.toggle_frame, text=f"{c['Band']}", variable=self.var_lte_on[i]).pack(side="left")
        ttk.Label(self.toggle_frame, text="  NR:").pack(side="left")
        for i, (_, c) in enumerate(nr_cells.iterrows()):
            ttk.Checkbutton(self.toggle_frame, text=f"{c['Band']}", variable=self.var_nr_on[i]).pack(side="left")

    def _refresh_pk_tree(self):
        self.pk_tv.delete(*self.pk_tv.get_children())
        for p in self.pattern_peaks:
            self.pk_tv.insert("", "end", values=[p["hour"], p["amp"], p["width"]])

    def _on_pk_select(self, _evt=None):
        sel = self.pk_tv.selection()
        if not sel:
            return
        h, a, w = self.pk_tv.item(sel[0], "values")
        self.var_pk_hour.set(float(h)); self.var_pk_amp.set(float(a)); self.var_pk_width.set(float(w))

    def _pk_add(self):
        self.pattern_peaks.append(dict(hour=self.var_pk_hour.get(), amp=self.var_pk_amp.get(),
                                       width=self.var_pk_width.get()))
        self._refresh_pk_tree()

    def _pk_update(self):
        sel = self.pk_tv.selection()
        if not sel:
            return
        idx = self.pk_tv.index(sel[0])
        self.pattern_peaks[idx] = dict(hour=self.var_pk_hour.get(), amp=self.var_pk_amp.get(),
                                       width=self.var_pk_width.get())
        self._refresh_pk_tree()

    def _pk_delete(self):
        sel = self.pk_tv.selection()
        if not sel:
            return
        idx = self.pk_tv.index(sel[0])
        del self.pattern_peaks[idx]
        self._refresh_pk_tree()

    def _apply_pattern_preset(self):
        pat = TrafficPattern.preset(self.var_pat.get())
        self.var_speak.set(pat.site_peak_dl_mbps)
        self.var_weekend.set(pat.weekend_factor)
        self.var_base.set(pat.base_level)
        self.pattern_peaks = [dict(p) for p in pat.peaks]
        self._refresh_pk_tree()

    def _apply_preset(self):
        cfg = SteeringConfig.preset(self.var_preset.get())
        self.var_split.set(cfg.endc_split_nr)
        self.var_dcrel.set(cfg.dc_release)
        self.var_offload.set(cfg.nr_to_lte_offload)
        topo = normalize_topology(self.topology)
        n_lte = int((topo[COL_SYS] == "LTE").sum())
        n_nr = int((topo[COL_SYS] == "NR").sum())
        lte = cfg.enabled_for("LTE", n_lte); nr = cfg.enabled_for("NR", n_nr)
        for i in range(min(n_lte, len(self.var_lte_on))):
            self.var_lte_on[i].set(lte[i])
        for i in range(min(n_nr, len(self.var_nr_on))):
            self.var_nr_on[i].set(nr[i])

    def _current_pattern(self) -> "TrafficPattern":
        peaks = self.pattern_peaks if self.pattern_peaks else [dict(hour=13, amp=0.5, width=2.0)]
        return TrafficPattern(site_peak_dl_mbps=self.var_speak.get(),
                              peaks=[dict(p) for p in peaks],
                              base_level=self.var_base.get(),
                              weekend_factor=self.var_weekend.get())

    def _current_steering(self) -> "SteeringConfig":
        return SteeringConfig(
            endc_split_nr=self.var_split.get(), dc_release=self.var_dcrel.get(),
            nr_to_lte_offload=self.var_offload.get(),
            lte_enabled=[v.get() for v in self.var_lte_on],
            nr_enabled=[v.get() for v in self.var_nr_on])

    # ===== Generate =====
    def _build_generate_tab(self):
        ttk.Button(self.tab_gen, text="Generate KPIs", command=self._on_generate).pack(pady=10)
        self.gen_status = tk.StringVar(value="대기 중…")
        ttk.Label(self.tab_gen, textvariable=self.gen_status).pack(pady=4)
        ttk.Label(self.tab_gen, text="레벨 요약").pack(anchor="w", padx=8)
        self.gen_tv = ttk.Treeview(self.tab_gen, show="headings", height=5)
        self.gen_tv.pack(fill="x", padx=8, pady=4)
        ttk.Label(self.tab_gen, text="셀 단위 요약 (캐리어/UE 조정 효과 확인)").pack(anchor="w", padx=8)
        self.gen_cell_tv = ttk.Treeview(self.tab_gen, show="headings", height=10)
        self.gen_cell_tv.pack(fill="both", expand=True, padx=8, pady=4)

    def _on_generate(self):
        eng = TrafficGenEngine(self.topology, days=self.var_days.get(),
                               step_min=self.var_step.get(), seed=self.var_seed.get(),
                               steering=self._current_steering(), pattern=self._current_pattern())
        self.topology = eng.topology
        self.cell_df = eng.generate()
        self.agg = aggregate_kpis(self.cell_df, step_min=self.var_step.get())
        self._fill_tree(self.gen_tv, summary_table(self.agg))
        self._fill_tree(self.gen_cell_tv, cell_summary_table(self.cell_df, self.var_step.get()))
        self.gen_status.set(f"생성 완료: {len(self.cell_df):,} 행 "
                            f"({self.topology.shape[0]} 셀 × {self.var_days.get()}일)")

    # ===== Visualize =====
    def _build_visualize_tab(self):
        bar = ttk.Frame(self.tab_viz); bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(bar, text="Level:").pack(side="left")
        self.var_level = tk.StringVar(value="LTE+NR Total")
        ttk.Combobox(bar, values=self.LEVELS, textvariable=self.var_level, width=14,
                     state="readonly").pack(side="left", padx=4)
        ttk.Label(bar, text="KPI:").pack(side="left")
        self.var_kpi = tk.StringVar(value=COL_PRBUTIL)
        ttk.Combobox(bar, values=[COL_PRBUTIL, COL_IPTPUT, COL_THPVOL, COL_THPTIME, COL_DLB,
                                  COL_ULB, COL_ACTIVE, COL_CONN, COL_USEDRB, COL_RRCFAIL],
                     textvariable=self.var_kpi, width=18, state="readonly").pack(side="left", padx=4)
        ttk.Label(bar, text="Plot:").pack(side="left")
        self.var_plot = tk.StringVar(value="time")
        ttk.Combobox(bar, values=["time", "cdf", "hist"], textvariable=self.var_plot,
                     width=8, state="readonly").pack(side="left", padx=4)
        ttk.Button(bar, text="Plot", command=self._on_plot).pack(side="left", padx=8)

        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self._fig = Figure(figsize=(9, 4.5), dpi=100)
        self._ax = self._fig.add_subplot(111)
        self._canvas = FigureCanvasTkAgg(self._fig, master=self.tab_viz)
        self._canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=6)

    def _current_level_df(self):
        if self.agg is None:
            return None
        lvl = self.var_level.get()
        if lvl == "Cell":
            return self.cell_df
        return self.agg[{"LTE Sector": "lte_sector", "NR Sector": "nr_sector",
                         "LTE+NR Total": "total"}[lvl]]

    def _on_plot(self):
        df = self._current_level_df()
        if df is None or df.empty:
            messagebox.showwarning("TrafficGen", "먼저 Generate 를 실행하세요."); return
        self._ax.clear()
        kpi = self.var_kpi.get()
        if self.var_level.get() == "Cell":
            for (sysv, cn), sub in df.groupby([COL_SYS, COL_CELL]):
                plot_kpi(self._ax, sub, kpi, self.var_plot.get(),
                         label=f"{sysv}-{sub[COL_BAND].iloc[0]}-{cn}")
            self._ax.legend(fontsize=7, ncol=2)
        else:
            plot_kpi(self._ax, df, kpi, self.var_plot.get(), label=self.var_level.get())
        self._fig.tight_layout(); self._canvas.draw()

    # ===== Compare =====
    def _build_compare_tab(self):
        ttk.Button(self.tab_cmp, text="Refresh Comparison", command=self._on_compare).pack(pady=8)
        ttk.Label(self.tab_cmp, text="레벨 요약").pack(anchor="w", padx=8)
        self.cmp_tv = ttk.Treeview(self.tab_cmp, show="headings", height=5)
        self.cmp_tv.pack(fill="x", padx=8, pady=4)
        ttk.Label(self.tab_cmp, text="셀 단위 요약").pack(anchor="w", padx=8)
        self.cmp_cell_tv = ttk.Treeview(self.tab_cmp, show="headings", height=10)
        self.cmp_cell_tv.pack(fill="both", expand=True, padx=8, pady=4)

    def _on_compare(self):
        if self.agg is None:
            messagebox.showwarning("TrafficGen", "먼저 Generate 를 실행하세요."); return
        self._fill_tree(self.cmp_tv, summary_table(self.agg))
        self._fill_tree(self.cmp_cell_tv, cell_summary_table(self.cell_df, self.var_step.get()))

    # ===== Export =====
    def _build_export_tab(self):
        row = ttk.Frame(self.tab_exp); row.pack(fill="x", padx=8, pady=10)
        self.var_outdir = tk.StringVar(value=os.path.join(os.getcwd(), "Output"))
        ttk.Entry(row, textvariable=self.var_outdir, width=60).pack(side="left", padx=4)
        ttk.Button(row, text="…", command=self._pick_dir).pack(side="left")
        ttk.Button(self.tab_exp, text="Export ESM-compatible CSVs",
                   command=self._on_export).pack(pady=8)
        self.exp_status = tk.StringVar(value="")
        ttk.Label(self.tab_exp, textvariable=self.exp_status).pack(pady=4)

    def _on_export(self):
        if self.cell_df is None:
            messagebox.showwarning("TrafficGen", "먼저 Generate 를 실행하세요."); return
        paths = export_esm_csv(self.cell_df, self.topology, self.var_outdir.get(),
                               step_min=self.var_step.get())
        self.exp_status.set("저장: " + ", ".join(os.path.basename(p) for p in paths))

    def _pick_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.var_outdir.set(d)

    @staticmethod
    def _fill_tree(tv, df: pd.DataFrame):
        tv.delete(*tv.get_children())
        tv["columns"] = list(df.columns)
        for c in df.columns:
            tv.heading(c, text=c); tv.column(c, width=104, anchor="center")
        for _, r in df.iterrows():
            tv.insert("", "end", values=list(r.values))


# ---------------------------------------------------------------------------
# 진입점 / headless 검증
# ---------------------------------------------------------------------------
def run_scenario(steering: SteeringConfig | None = None, pattern: TrafficPattern | None = None,
                 topology: pd.DataFrame | None = None, days: int = 7, seed: int = 42) -> dict:
    """주어진 steering/pattern/topology 로 생성→집계하고 요약을 반환."""
    eng = TrafficGenEngine(topology=topology, days=days, seed=seed,
                           steering=steering or SteeringConfig(),
                           pattern=pattern or TrafficPattern())
    cell_df = eng.generate()
    agg = aggregate_kpis(cell_df)
    return dict(engine=eng, cell_df=cell_df, agg=agg, summary=summary_table(agg),
                cell_summary=cell_summary_table(cell_df))


def run_headless_demo(out_dir: str) -> dict:
    """GUI 없이 r2 신규 기능(패턴/캐리어/UE)을 시연·검증하고 Export/PNG 를 산출."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure

    base = run_scenario()                                              # default pattern + baseline
    evening = run_scenario(pattern=TrafficPattern.preset("evening"))   # 시간대 패턴 변경
    # 셀별 UE 비율 조정: 첫 LTE 셀의 ue_weight 를 3배 → 해당 셀 IP Tput 하락 확인
    topo_ue = build_default_topology()
    topo_ue.loc[0, "ue_weight"] = 3.0
    ue = run_scenario(topology=topo_ue)
    # 캐리어 추가: NR 4번째 캐리어(n78 200MHz 급) 추가
    topo_add = build_default_topology()
    topo_add = normalize_topology(pd.concat([topo_add, pd.DataFrame([dict(
        System="NR", eNB_ID=NR_ENB_ID, Sector="1", cell_num="4", Band="n78",
        Freq_MHz=3800, BW_MHz=100, nRB=273, avg_cell_mbps=800, peak_user_mbps=980,
        max_users=340, p_idle=560, p_max=1360, dl_ratio=1.0, ul_ratio=0.10,
        load_weight=1.0, ue_weight=1.0)])], ignore_index=True))
    added = run_scenario(topology=topo_add)

    paths = export_esm_csv(base["cell_df"], base["engine"].topology, out_dir)
    fig = Figure(figsize=(8, 4)); ax = fig.add_subplot(111)
    for name, key in (("LTE", "lte_sector"), ("NR", "nr_sector"), ("Total", "total")):
        plot_kpi(ax, base["agg"][key], COL_IPTPUT, "cdf", label=name)
    ax.legend()
    png = os.path.join(out_dir, "ip_tput_cdf.png")
    fig.tight_layout(); fig.savefig(png)

    return dict(rows=len(base["cell_df"]), base=base, evening=evening, ue=ue, added=added,
                paths=paths + [png])


def main():
    if _HAS_TK:
        TrafficGenApp().mainloop()
    else:
        res = run_headless_demo(os.path.join(os.getcwd(), "Output"))
        print("[headless] rows:", res["rows"])
        print("\n=== Baseline (default pattern) — 레벨 요약 ===")
        print(res["base"]["summary"].to_string(index=False))
        print("\n=== Baseline — 셀 요약 ===")
        print(res["base"]["cell_summary"].to_string(index=False))
        print("\n=== UE 조정: LTE 첫 셀 ue_weight=3.0 (해당 셀 Active↑·IP Tput↓ 확인) ===")
        print(res["ue"]["cell_summary"].head(3).to_string(index=False))
        print("\n=== 캐리어 추가: NR 4번째 캐리어 → 셀 수 %d ===" % len(res["added"]["cell_df"][COL_CELL].unique()))
        print(res["added"]["summary"].to_string(index=False))
        print("\nwritten:", [os.path.basename(p) for p in res["paths"]])


if __name__ == "__main__":
    main()
