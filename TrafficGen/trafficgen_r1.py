# -*- coding: utf-8 -*-
"""TrafficGen r1 — 상용망(4G LTE + 5G NR 오버레이) 트래픽/KPI Generator + ENDC/DC·SA Steering.

r0(단일 사이트 LTE×3 + NR×3 오버레이 생성기)를 복제해 시작. r1의 핵심 추가는 **명시적 steering**:
사이트 전체 수요(Mbps)를 사용자 클래스(Legacy-LTE / ENDC(NSA) / NR-SA)로 나눈 뒤, steering 정책에
따라 LTE 풀 / NR 풀로 라우팅하고 캐리어별로 분배한다. 이를 통해 다음을 명시적 파라미터로 실험한다:
  * **NR 셀 on/off** (에너지 세이빙): NR 캐리어를 끄면 그 트래픽이 LTE로 이전, 꺼진 셀은 sleep 전력.
  * **DC 해제(dc_release)**: ENDC 사용자 데이터를 전부 LTE anchor(MCG)로 이전.
  * **ENDC split(endc_split_nr)**: ENDC 사용자 데이터의 NR(SCG) vs LTE(MCG) 분배 비율.
  * **NR→LTE 오프로딩(nr_to_lte_offload)**: 로드밸런싱용 강제 이전 비율.
  * **SA 폴백(sa_fallback_to_lte)**: NR 전면 off 시 NR-SA 사용자의 LTE 폴백 비율.

이 구조는 향후 에너지 세이빙/로드밸런싱 알고리즘이 "셀을 끄거나 트래픽을 옮겼을 때 KPI가 어떻게
변하는지"를 데이터로 관찰할 수 있게 한다(트래픽 보존: 옮긴 만큼 목적지 셀 부하가 오른다).

설계 원칙:
  * 엔진(생성/집계/Export/플로팅)은 tkinter 없이 동작 → headless 검증 가능.
  * GUI는 tkinter가 있을 때만 활성(없으면 base=object 로 안전하게 import).
  * KPI 간 인과관계를 규칙/확률로 반영(난수 남발 금지): 수요 → (steering) → 자원 → 체감/에너지/실패.

컬럼(ESM 호환): IP Tput / UsedRB / nRB / AirMacDLByte / AirMacULByte / RuPowerTot / RuPowerCnt.
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
COL_IPTPUT = "IP Tput"          # Mbps (사용자 체감 throughput)
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

KPI_COLS = [COL_IPTPUT, COL_USEDRB, COL_PRBUTIL, COL_DLB, COL_ULB, COL_RUTOT,
            COL_RUCNT, COL_CONN, COL_ACTIVE, COL_RRCATT, COL_RRCFAIL, COL_DROP]

DEFAULT_STEP_MIN = 15
LTE_ENB_ID = "1001"
NR_ENB_ID = "2001"


# ---------------------------------------------------------------------------
# 토폴로지 (단일 사이트 LTE×3 + NR×3 오버레이)
# ---------------------------------------------------------------------------
def build_default_topology() -> pd.DataFrame:
    """MASTER_PROMPT §7-A 의 첫 시스템 토폴로지를 DataFrame 으로 반환.

    각 셀에 물리/용량/에너지/유저 파라미터를 부여한다. 오버레이이므로 LTE 3셀은 하나의
    LTE Sector(eNB_ID=1001), NR 3셀은 하나의 NR Sector(eNB_ID=2001)로 묶인다.
    """
    cells = [
        # --- LTE (FDD, 20 MHz = 100 RB) ---
        dict(System="LTE", eNB_ID=LTE_ENB_ID, Sector="1", cell_num="1", Band="B1",
             Freq_MHz=2100, BW_MHz=20, nRB=100,
             avg_cell_mbps=95, peak_user_mbps=130, max_users=200,
             p_idle=320, p_max=700, dl_ratio=1.0, ul_ratio=0.12, load_weight=0.95),
        dict(System="LTE", eNB_ID=LTE_ENB_ID, Sector="1", cell_num="2", Band="B3",
             Freq_MHz=1800, BW_MHz=20, nRB=100,
             avg_cell_mbps=95, peak_user_mbps=130, max_users=200,
             p_idle=320, p_max=700, dl_ratio=1.0, ul_ratio=0.12, load_weight=0.90),
        dict(System="LTE", eNB_ID=LTE_ENB_ID, Sector="1", cell_num="3", Band="B7",
             Freq_MHz=2600, BW_MHz=20, nRB=100,
             avg_cell_mbps=90, peak_user_mbps=125, max_users=180,
             p_idle=330, p_max=720, dl_ratio=1.0, ul_ratio=0.12, load_weight=0.75),
        # --- NR (n78 TDD, 100 MHz / 30 kHz = 273 RB; 마지막은 소역폭) ---
        dict(System="NR", eNB_ID=NR_ENB_ID, Sector="1", cell_num="1", Band="n78",
             Freq_MHz=3500, BW_MHz=100, nRB=273,
             avg_cell_mbps=780, peak_user_mbps=950, max_users=320,
             p_idle=560, p_max=1360, dl_ratio=1.0, ul_ratio=0.10, load_weight=1.00),
        dict(System="NR", eNB_ID=NR_ENB_ID, Sector="1", cell_num="2", Band="n78",
             Freq_MHz=3600, BW_MHz=100, nRB=273,
             avg_cell_mbps=760, peak_user_mbps=930, max_users=300,
             p_idle=560, p_max=1360, dl_ratio=1.0, ul_ratio=0.10, load_weight=0.85),
        dict(System="NR", eNB_ID=NR_ENB_ID, Sector="1", cell_num="3", Band="n78",
             Freq_MHz=3700, BW_MHz=40, nRB=106,
             avg_cell_mbps=300, peak_user_mbps=420, max_users=180,
             p_idle=430, p_max=900, dl_ratio=1.0, ul_ratio=0.10, load_weight=0.60),
    ]
    df = pd.DataFrame(cells)
    # ESM 식별자 규칙: 콤마 없는 순수 숫자 문자열
    for c in ("eNB_ID", "Sector", "cell_num"):
        df[c] = df[c].astype(str).str.replace(",", "", regex=False)
    return df


# ---------------------------------------------------------------------------
# Steering 정책 (ENDC/DC·SA)
# ---------------------------------------------------------------------------
class SteeringConfig:
    """사이트 수요를 사용자 클래스별로 나눠 LTE/NR 캐리어로 라우팅하는 정책.

    사용자 클래스:
      * Legacy-LTE  : NR 미지원 → 항상 LTE.
      * ENDC (NSA)  : LTE 앵커(MCG) + NR(SCG) 듀얼커넥티비티. 데이터는 endc_split_nr 비율로 NR/LTE 분배.
      * NR-SA       : NR 단독(제어+데이터).

    Steering 레버:
      * lte_enabled / nr_enabled : 캐리어 on/off (cell-num 순서의 bool 리스트). off 셀은 sleep 전력.
      * endc_split_nr            : ENDC 데이터 중 NR(SCG) 비중(0~1).
      * dc_release               : True → ENDC 데이터 전부 LTE anchor 로(=DC 해제).
      * nr_to_lte_offload        : NR 풀에서 LTE 로 강제 이전 비율(0~1, 로드밸런싱).
      * sa_fallback_to_lte       : NR 전면 off 시 NR-SA 사용자의 LTE 폴백 비율(나머지는 차단).
    """

    def __init__(self, site_peak_dl_mbps: float = 900.0,
                 frac_legacy: float = 0.15, frac_endc: float = 0.60, frac_sa: float = 0.25,
                 endc_split_nr: float = 0.80, dc_release: bool = False,
                 nr_to_lte_offload: float = 0.0, sa_fallback_to_lte: float = 0.5,
                 lte_enabled=None, nr_enabled=None):
        self.site_peak_dl_mbps = float(site_peak_dl_mbps)
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
# 수요(Demand) — 일주기 프로파일
# ---------------------------------------------------------------------------
def build_diurnal(n_steps: int, step_min: int, rng: np.random.Generator) -> np.ndarray:
    """0~약1.15 범위의 사이트 공통 offered-load 시계열(15분 스텝).

    점심(≈13시)·저녁(≈21시) 피크 + 아침 소피크, 주말 감쇠, 스텝 노이즈를 반영.
    """
    steps_per_day = int(round(24 * 60 / step_min))
    idx = np.arange(n_steps)
    hod = (idx % steps_per_day) * step_min / 60.0  # hour-of-day 0..24
    base = (0.08
            + 0.25 * np.exp(-((hod - 9) ** 2) / (2 * 1.5 ** 2))
            + 0.55 * np.exp(-((hod - 13) ** 2) / (2 * 2.5 ** 2))
            + 0.80 * np.exp(-((hod - 21) ** 2) / (2 * 2.0 ** 2)))
    base = base / base.max()
    dow = (idx // steps_per_day) % 7
    weekend = np.isin(dow, [5, 6])
    amp = np.where(weekend, 0.80, 1.0)
    noise = np.clip(rng.normal(1.0, 0.06, n_steps), 0.7, 1.3)
    return np.clip(base * amp * noise, 0.02, 1.15)


# ---------------------------------------------------------------------------
# 생성 엔진
# ---------------------------------------------------------------------------
class TrafficGenEngine:
    """단일 사이트 LTE/NR 오버레이의 셀 단위 KPI 시계열을 생성한다."""

    def __init__(self, topology: pd.DataFrame | None = None,
                 days: int = 7, step_min: int = DEFAULT_STEP_MIN,
                 start: str = "2026-07-01", seed: int = 42,
                 steering: SteeringConfig | None = None):
        self.topology = topology if topology is not None else build_default_topology()
        self.days = int(days)
        self.step_min = int(step_min)
        self.start = start
        self.seed = int(seed)
        self.steering = steering if steering is not None else SteeringConfig()

    def _route_demand(self, site_load: np.ndarray) -> dict:
        """사이트 수요(Mbps)를 사용자 클래스로 나눠 steering 정책대로 캐리어별 배정 Mbps 로 라우팅.

        반환: {(eNB_ID, cell-num): assigned_dl_mbps 시계열}, 그리고 진단용 pool 시계열.
        트래픽 보존: LTE 풀 + NR 풀 (+차단분) == 서비스 대상 수요.
        """
        st = self.steering
        topo = self.topology
        site_demand = site_load * st.site_peak_dl_mbps                 # Mbps (DL) 사이트 offered

        d_leg = site_demand * st.frac_legacy
        d_endc = site_demand * st.frac_endc
        d_sa = site_demand * st.frac_sa

        lte_cells = topo[topo[COL_SYS] == "LTE"].reset_index(drop=True)
        nr_cells = topo[topo[COL_SYS] == "NR"].reset_index(drop=True)
        lte_on = st.enabled_for("LTE", len(lte_cells))
        nr_on = st.enabled_for("NR", len(nr_cells))
        nr_available = any(nr_on)

        lte_pool = d_leg.astype(float).copy()
        nr_pool = np.zeros_like(site_demand)
        # ENDC: NR(SCG)/LTE(MCG) 분배 — DC 해제 또는 NR 전면 off 시 전부 LTE anchor
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

        assigned = {}

        def _distribute(cells, on_flags, pool):
            w = np.array([(cells.loc[i, "avg_cell_mbps"] * cells.loc[i, "load_weight"])
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
        p_sleep = 0.12 * cell["p_idle"]                      # 셀 off 시 sleep 전력

        if not enabled:                                      # 꺼진 셀: 트래픽/유저 0, sleep 전력
            z = np.zeros(n)
            zi = np.zeros(n, dtype=int)
            ru_cnt = np.full(n, step_sec, dtype=float)
            return dict(
                offered=z, used_rb=zi, prb_util=z, dl_bytes=z, ul_bytes=z,
                conn=zi, active=zi, ip_tput=z.copy(), ru_tot=p_sleep * ru_cnt, ru_cnt=ru_cnt,
                rrc_att=zi, rrc_fail=zi, drop=zi)

        # offered load = 배정 수요 ÷ 셀 용량 (1 초과 시 혼잡)
        offered = (assigned_dl_mbps / max(cell["avg_cell_mbps"], 1e-9)
                   ) * np.clip(rng.normal(1.0, 0.05, n), 0.85, 1.15)
        offered = np.clip(offered, 0.0, 1.5)
        util = np.minimum(offered, 1.0)                      # 자원 포화(≤100%)

        used_rb = np.round(util * cell["nRB"]).astype(int)
        prb_util = 100.0 * used_rb / cell["nRB"]

        served_mbps = util * cell["avg_cell_mbps"]           # 실제 전달 = min(배정, 용량)
        dl_bytes = served_mbps * 1e6 / 8.0 * step_sec * cell["dl_ratio"]
        ul_bytes = dl_bytes * cell["ul_ratio"]

        # 사용자 수: 배정 수요(offered)에 비례 → 수요 0이면 유저 0
        conn = np.maximum(0, np.round(cell["max_users"] * np.clip(offered, 0, 1)
                                      * np.clip(rng.normal(1.0, 0.08, n), 0.6, 1.4))).astype(int)
        active = np.maximum(0, np.round(conn * (0.4 + 0.5 * util)
                                        * np.clip(rng.normal(1.0, 0.10, n), 0.5, 1.5))).astype(int)
        active_eff = np.maximum(active, 1)

        # 사용자 체감 throughput: 셀 용량을 활성 유저로 분배, 단일유저 피크 상한, 혼잡 감쇠.
        ip_tput = np.minimum(cell["peak_user_mbps"], cell["avg_cell_mbps"] / active_eff)
        ip_tput = ip_tput * (1.0 - 0.35 * np.clip(offered - 1.0, 0, 0.5) / 0.5)
        ip_tput = np.where(active > 0, np.maximum(ip_tput, 0.1), 0.0)   # 트래픽 없으면 0

        # 에너지: RU 소모전력 = 정적 + 부하 비례
        power_w = cell["p_idle"] + (cell["p_max"] - cell["p_idle"]) * util
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
            ip_tput=ip_tput, ru_tot=ru_tot, ru_cnt=ru_cnt,
            rrc_att=np.round(attempts).astype(int), rrc_fail=rrc_fail, drop=drop,
        )

    def generate(self) -> pd.DataFrame:
        """모든 셀의 KPI를 long-format DataFrame 으로 반환(steering 정책 반영)."""
        rng = np.random.default_rng(self.seed)
        n_steps = self.days * int(round(24 * 60 / self.step_min))
        times = pd.date_range(self.start, periods=n_steps, freq=f"{self.step_min}min")
        step_sec = self.step_min * 60
        site_load = build_diurnal(n_steps, self.step_min, rng)
        routed = self._route_demand(site_load)

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
    # IP Tput: 볼륨 가중 평균(사용자 체감 대표값)
    vol = df[COL_DLB] + df[COL_ULB]
    w = df.assign(_vw=df[COL_IPTPUT] * vol, _v=vol).groupby(COL_TIME)
    ip = (w["_vw"].sum() / w["_v"].sum().replace(0, np.nan)).fillna(0)
    out = pd.DataFrame({
        COL_TIME: used.index,
        COL_USEDRB: used.values, COL_NRB: nrb.values,
        COL_PRBUTIL: np.round(100.0 * used.values / nrb.replace(0, np.nan).values, 2),
        COL_DLB: dlb.values, COL_ULB: ulb.values,
        COL_IPTPUT: np.round(ip.values, 3),
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
        "total": _agg_group(cell_df, step_min),
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


# ---------------------------------------------------------------------------
# Export (ESM 호환 CSV)
# ---------------------------------------------------------------------------
def export_esm_csv(cell_df: pd.DataFrame, topology: pd.DataFrame, out_dir: str,
                   step_min: int = DEFAULT_STEP_MIN) -> list[str]:
    """PM(Traffic) / Energy Stat / Topology(CM) 3개 CSV 를 utf-8-sig 로 저장."""
    os.makedirs(out_dir, exist_ok=True)
    written = []

    pm_cols = [COL_TIME, COL_ENB, COL_SYS, COL_SECTOR, COL_CELL, COL_BAND, COL_NRB,
               COL_IPTPUT, COL_USEDRB, COL_PRBUTIL, COL_DLB, COL_ULB,
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
    """5탭 GUI: Config / Generate / Visualize / Compare / Export."""

    LEVELS = ["Cell", "LTE Sector", "NR Sector", "LTE+NR Total"]

    def __init__(self):
        if not _HAS_TK:
            raise RuntimeError("tkinter 를 사용할 수 없습니다(GUI는 로컬 환경에서 실행하세요).")
        super().__init__()
        self.title("TrafficGen r1 — LTE/NR Overlay KPI Generator + Steering")
        self.geometry("1080x760")
        self.topology = build_default_topology()
        self.cell_df = None
        self.agg = None
        self._build_ui()

    # --- UI 구성 ---
    def _build_ui(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True)
        self.tab_cfg = ttk.Frame(nb); nb.add(self.tab_cfg, text="⚙️ Config")
        self.tab_gen = ttk.Frame(nb); nb.add(self.tab_gen, text="▶️ Generate")
        self.tab_viz = ttk.Frame(nb); nb.add(self.tab_viz, text="📈 Visualize")
        self.tab_cmp = ttk.Frame(nb); nb.add(self.tab_cmp, text="📊 Compare")
        self.tab_exp = ttk.Frame(nb); nb.add(self.tab_exp, text="💾 Export")
        self._build_config_tab()
        self._build_generate_tab()
        self._build_visualize_tab()
        self._build_compare_tab()
        self._build_export_tab()

    def _build_config_tab(self):
        top = ttk.Frame(self.tab_cfg); top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="Days:").pack(side="left")
        self.var_days = tk.IntVar(value=7)
        ttk.Spinbox(top, from_=1, to=60, width=5, textvariable=self.var_days).pack(side="left", padx=4)
        ttk.Label(top, text="Step(min):").pack(side="left")
        self.var_step = tk.IntVar(value=15)
        ttk.Spinbox(top, from_=5, to=60, increment=5, width=5, textvariable=self.var_step).pack(side="left", padx=4)
        ttk.Label(top, text="Seed:").pack(side="left")
        self.var_seed = tk.IntVar(value=42)
        ttk.Spinbox(top, from_=0, to=99999, width=7, textvariable=self.var_seed).pack(side="left", padx=4)

        cols = list(self.topology.columns)
        tv = ttk.Treeview(self.tab_cfg, columns=cols, show="headings", height=8)
        for c in cols:
            tv.heading(c, text=c); tv.column(c, width=90, anchor="center")
        for _, r in self.topology.iterrows():
            tv.insert("", "end", values=[r[c] for c in cols])
        tv.pack(fill="x", padx=8, pady=6)
        ttk.Label(self.tab_cfg, text="단일 사이트: LTE 3캐리어 + NR 3캐리어 오버레이 (기본 토폴로지)").pack(pady=2)

        # --- Steering 패널 ---
        sf = ttk.LabelFrame(self.tab_cfg, text="Steering (ENDC/DC·SA)")
        sf.pack(fill="x", padx=8, pady=6)
        r1 = ttk.Frame(sf); r1.pack(fill="x", pady=3)
        ttk.Label(r1, text="Preset:").pack(side="left")
        self.var_preset = tk.StringVar(value="baseline")
        ttk.Combobox(r1, values=["baseline", "nr_off", "nr_all_off", "dc_release", "offload"],
                     textvariable=self.var_preset, width=12, state="readonly").pack(side="left", padx=4)
        ttk.Button(r1, text="Apply Preset", command=self._apply_preset).pack(side="left", padx=6)
        ttk.Label(r1, text="Site peak DL(Mbps):").pack(side="left", padx=(12, 2))
        self.var_speak = tk.DoubleVar(value=900.0)
        ttk.Spinbox(r1, from_=100, to=5000, increment=100, width=7, textvariable=self.var_speak).pack(side="left")

        r2 = ttk.Frame(sf); r2.pack(fill="x", pady=3)
        ttk.Label(r2, text="ENDC split→NR:").pack(side="left")
        self.var_split = tk.DoubleVar(value=0.80)
        ttk.Spinbox(r2, from_=0, to=1, increment=0.05, width=5, textvariable=self.var_split).pack(side="left", padx=4)
        self.var_dcrel = tk.BooleanVar(value=False)
        ttk.Checkbutton(r2, text="DC release", variable=self.var_dcrel).pack(side="left", padx=8)
        ttk.Label(r2, text="NR→LTE offload:").pack(side="left")
        self.var_offload = tk.DoubleVar(value=0.0)
        ttk.Spinbox(r2, from_=0, to=1, increment=0.1, width=5, textvariable=self.var_offload).pack(side="left", padx=4)

        r3 = ttk.Frame(sf); r3.pack(fill="x", pady=3)
        ttk.Label(r3, text="Cell on/off — LTE:").pack(side="left")
        self.var_lte_on = [tk.BooleanVar(value=True) for _ in range(3)]
        for i, v in enumerate(self.var_lte_on):
            ttk.Checkbutton(r3, text=f"L{i+1}", variable=v).pack(side="left")
        ttk.Label(r3, text="  NR:").pack(side="left")
        self.var_nr_on = [tk.BooleanVar(value=True) for _ in range(3)]
        for i, v in enumerate(self.var_nr_on):
            ttk.Checkbutton(r3, text=f"N{i+1}", variable=v).pack(side="left")

    def _apply_preset(self):
        cfg = SteeringConfig.preset(self.var_preset.get())
        self.var_speak.set(cfg.site_peak_dl_mbps)
        self.var_split.set(cfg.endc_split_nr)
        self.var_dcrel.set(cfg.dc_release)
        self.var_offload.set(cfg.nr_to_lte_offload)
        lte = cfg.enabled_for("LTE", 3); nr = cfg.enabled_for("NR", 3)
        for i in range(3):
            self.var_lte_on[i].set(lte[i]); self.var_nr_on[i].set(nr[i])

    def _current_steering(self) -> "SteeringConfig":
        return SteeringConfig(
            site_peak_dl_mbps=self.var_speak.get(),
            endc_split_nr=self.var_split.get(), dc_release=self.var_dcrel.get(),
            nr_to_lte_offload=self.var_offload.get(),
            lte_enabled=[v.get() for v in self.var_lte_on],
            nr_enabled=[v.get() for v in self.var_nr_on])

    def _build_generate_tab(self):
        ttk.Button(self.tab_gen, text="Generate KPIs", command=self._on_generate).pack(pady=10)
        self.gen_status = tk.StringVar(value="대기 중…")
        ttk.Label(self.tab_gen, textvariable=self.gen_status).pack(pady=4)
        self.gen_tv = ttk.Treeview(self.tab_gen, show="headings", height=12)
        self.gen_tv.pack(fill="both", expand=True, padx=8, pady=6)

    def _build_visualize_tab(self):
        bar = ttk.Frame(self.tab_viz); bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(bar, text="Level:").pack(side="left")
        self.var_level = tk.StringVar(value="LTE+NR Total")
        ttk.Combobox(bar, values=self.LEVELS, textvariable=self.var_level, width=14,
                     state="readonly").pack(side="left", padx=4)
        ttk.Label(bar, text="KPI:").pack(side="left")
        self.var_kpi = tk.StringVar(value=COL_PRBUTIL)
        ttk.Combobox(bar, values=[COL_PRBUTIL, COL_IPTPUT, COL_DLB, COL_ULB, COL_ACTIVE,
                                  COL_USEDRB, COL_RRCFAIL], textvariable=self.var_kpi,
                     width=16, state="readonly").pack(side="left", padx=4)
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

    def _build_compare_tab(self):
        ttk.Button(self.tab_cmp, text="Refresh Comparison", command=self._on_compare).pack(pady=8)
        self.cmp_tv = ttk.Treeview(self.tab_cmp, show="headings", height=8)
        self.cmp_tv.pack(fill="both", expand=True, padx=8, pady=6)

    def _build_export_tab(self):
        row = ttk.Frame(self.tab_exp); row.pack(fill="x", padx=8, pady=10)
        self.var_outdir = tk.StringVar(value=os.path.join(os.getcwd(), "Output"))
        ttk.Entry(row, textvariable=self.var_outdir, width=60).pack(side="left", padx=4)
        ttk.Button(row, text="…", command=self._pick_dir).pack(side="left")
        ttk.Button(self.tab_exp, text="Export ESM-compatible CSVs",
                   command=self._on_export).pack(pady=8)
        self.exp_status = tk.StringVar(value="")
        ttk.Label(self.tab_exp, textvariable=self.exp_status).pack(pady=4)

    # --- 콜백 ---
    def _on_generate(self):
        eng = TrafficGenEngine(self.topology, days=self.var_days.get(),
                               step_min=self.var_step.get(), seed=self.var_seed.get(),
                               steering=self._current_steering())
        self.cell_df = eng.generate()
        self.agg = aggregate_kpis(self.cell_df, step_min=self.var_step.get())
        st = summary_table(self.agg)
        self._fill_tree(self.gen_tv, st)
        self.gen_status.set(f"생성 완료: {len(self.cell_df):,} 행 "
                            f"({self.topology.shape[0]} 셀 × {self.var_days.get()}일)")

    def _current_level_df(self):
        if self.agg is None:
            return None
        lvl = self.var_level.get()
        if lvl == "Cell":
            return self.cell_df[self.cell_df[COL_SYS] == "NR"]  # 대표로 NR 셀들
        return {"LTE Sector": "lte_sector", "NR Sector": "nr_sector",
                "LTE+NR Total": "total"}.get(lvl) and self.agg[
            {"LTE Sector": "lte_sector", "NR Sector": "nr_sector", "LTE+NR Total": "total"}[lvl]]

    def _on_plot(self):
        df = self._current_level_df()
        if df is None or df.empty:
            messagebox.showwarning("TrafficGen", "먼저 Generate 를 실행하세요."); return
        self._ax.clear()
        kpi = self.var_kpi.get()
        if self.var_level.get() == "Cell":
            for (enb, cn), sub in df.groupby([COL_ENB, COL_CELL]):
                plot_kpi(self._ax, sub, kpi, self.var_plot.get(), label=f"{enb}-{cn}")
            self._ax.legend(fontsize=8)
        else:
            plot_kpi(self._ax, df, kpi, self.var_plot.get(), label=self.var_level.get())
        self._fig.tight_layout(); self._canvas.draw()

    def _on_compare(self):
        if self.agg is None:
            messagebox.showwarning("TrafficGen", "먼저 Generate 를 실행하세요."); return
        self._fill_tree(self.cmp_tv, summary_table(self.agg))

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
            tv.heading(c, text=c); tv.column(c, width=110, anchor="center")
        for _, r in df.iterrows():
            tv.insert("", "end", values=list(r.values))


# ---------------------------------------------------------------------------
# 진입점
# ---------------------------------------------------------------------------
def run_scenario(steering: SteeringConfig, days: int = 7, seed: int = 42) -> dict:
    """주어진 steering 으로 생성→집계하고 요약을 반환."""
    eng = TrafficGenEngine(days=days, seed=seed, steering=steering)
    cell_df = eng.generate()
    agg = aggregate_kpis(cell_df)
    return dict(engine=eng, cell_df=cell_df, agg=agg, summary=summary_table(agg))


def run_headless_demo(out_dir: str) -> dict:
    """GUI 없이 baseline vs NR-off(에너지 세이빙) steering 을 비교하고 Export/PNG 를 산출(검증용)."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure

    base = run_scenario(SteeringConfig.preset("baseline"))
    nroff = run_scenario(SteeringConfig.preset("nr_off"))     # NR 3번째 캐리어 off

    paths = export_esm_csv(base["cell_df"], base["engine"].topology, out_dir)

    fig = Figure(figsize=(8, 4)); ax = fig.add_subplot(111)
    for name, key in (("LTE", "lte_sector"), ("NR", "nr_sector"), ("Total", "total")):
        plot_kpi(ax, base["agg"][key], COL_IPTPUT, "cdf", label=name)
    ax.legend()
    png = os.path.join(out_dir, "ip_tput_cdf.png")
    fig.tight_layout(); fig.savefig(png)
    return dict(rows=len(base["cell_df"]), summary=base["summary"],
                base=base, nroff=nroff, paths=paths + [png],
                agg=base["agg"], cell_df=base["cell_df"])


def main():
    if _HAS_TK:
        TrafficGenApp().mainloop()
    else:
        res = run_headless_demo(os.path.join(os.getcwd(), "Output"))
        print("[headless] rows:", res["rows"])
        print("\n=== Baseline ===")
        print(res["base"]["summary"].to_string(index=False))
        print("\n=== NR off (3rd NR carrier) — 에너지 세이빙 ===")
        print(res["nroff"]["summary"].to_string(index=False))
        print("written:", [os.path.basename(p) for p in res["paths"]])


if __name__ == "__main__":
    main()
