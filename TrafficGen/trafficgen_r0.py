# -*- coding: utf-8 -*-
"""TrafficGen r0 — 상용망(4G LTE + 5G NR 오버레이) 트래픽/KPI Generator.

첫 시스템(MASTER_PROMPT §7-A): 단일 사이트에 LTE 3캐리어 + NR 3캐리어가 커버리지 오버랩된 형상.
15분(ROP) 단위 시계열 KPI를 셀 단위로 생성하고, LTE Sector / NR Sector / LTE+NR Total 로 집계한다.
출력은 ESM 호환 CSV(PM/Energy/Topology). GUI(Tkinter)로 시각화(시계열/CDF/히스토그램)·비교·다운로드.

설계 원칙:
  * 엔진(생성/집계/Export/플로팅)은 tkinter 없이 동작 → headless 검증 가능.
  * GUI는 tkinter가 있을 때만 활성(없으면 base=object 로 안전하게 import).
  * KPI 간 인과관계를 규칙/확률로 반영(난수 남발 금지): 수요 → 자원 → 체감/에너지/실패.

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
                 start: str = "2026-07-01", seed: int = 42):
        self.topology = topology if topology is not None else build_default_topology()
        self.days = int(days)
        self.step_min = int(step_min)
        self.start = start
        self.seed = int(seed)

    # -- 셀 1개의 시계열 --
    def _generate_cell(self, cell: pd.Series, site_load: np.ndarray,
                       rng: np.random.Generator, step_sec: int) -> dict:
        n = len(site_load)
        # 셀별 offered load (사이트 수요 × 셀 가중 × 소노이즈)
        offered = np.clip(site_load * float(cell["load_weight"])
                          * np.clip(rng.normal(1.0, 0.05, n), 0.8, 1.2), 0.01, 1.2)
        util = np.minimum(offered, 1.0)                      # 자원 포화(≤100%)

        # 자원 사용
        used_rb = np.round(util * cell["nRB"]).astype(int)
        prb_util = 100.0 * used_rb / cell["nRB"]

        # 트래픽 볼륨 (Byte): 셀 평균 처리율 × 점유율 × 시간
        served_mbps = util * cell["avg_cell_mbps"]
        dl_bytes = served_mbps * 1e6 / 8.0 * step_sec * cell["dl_ratio"]
        ul_bytes = dl_bytes * cell["ul_ratio"]

        # 사용자 수 (접속/활성)
        conn = np.maximum(0, np.round(cell["max_users"] * (0.2 + 0.8 * offered)
                                      * np.clip(rng.normal(1.0, 0.08, n), 0.6, 1.4))).astype(int)
        active = np.maximum(0, np.round(conn * (0.3 + 0.5 * util)
                                        * np.clip(rng.normal(1.0, 0.10, n), 0.5, 1.5))).astype(int)
        active_eff = np.maximum(active, 1)

        # 사용자 체감 throughput: 셀 용량을 활성 유저로 분배, 단일유저 피크로 상한.
        #   유저↑ → 사용자당 처짐↓ (핵심 인과), 혼잡(offered>1) 시 추가 감쇠.
        ip_tput = np.minimum(cell["peak_user_mbps"], cell["avg_cell_mbps"] / active_eff)
        ip_tput = ip_tput * (1.0 - 0.35 * np.clip(offered - 1.0, 0, 0.2) / 0.2)
        ip_tput = np.maximum(ip_tput, 0.1)

        # 에너지: RU 소모전력 = 정적 + 부하 비례.  샘플 합/카운트로 저장(avg=tot/cnt).
        power_w = cell["p_idle"] + (cell["p_max"] - cell["p_idle"]) * util
        power_w = power_w * np.clip(rng.normal(1.0, 0.02, n), 0.95, 1.05)
        ru_cnt = np.full(n, step_sec, dtype=float)           # 초당 1샘플 가정
        ru_tot = power_w * ru_cnt                            # W·samples → avg=power_w

        # 실패: 기저율 + 혼잡(제곱) 가중.
        attempts = np.maximum(0, conn * 0.12 + active * 0.20)
        cong = np.clip(offered - 0.8, 0, 0.5)
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
        """모든 셀의 KPI를 long-format DataFrame 으로 반환."""
        rng = np.random.default_rng(self.seed)
        n_steps = self.days * int(round(24 * 60 / self.step_min))
        times = pd.date_range(self.start, periods=n_steps, freq=f"{self.step_min}min")
        step_sec = self.step_min * 60
        site_load = build_diurnal(n_steps, self.step_min, rng)

        frames = []
        for _, cell in self.topology.iterrows():
            # 셀마다 독립 스트림(재현성 유지): 셀 식별자로 서브시드
            sub = rng.integers(0, 2**31 - 1)
            crng = np.random.default_rng(int(sub))
            g = self._generate_cell(cell, site_load, crng, step_sec)
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
        self.title("TrafficGen r0 — LTE/NR Overlay KPI Generator")
        self.geometry("1080x720")
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
        tv = ttk.Treeview(self.tab_cfg, columns=cols, show="headings", height=10)
        for c in cols:
            tv.heading(c, text=c); tv.column(c, width=90, anchor="center")
        for _, r in self.topology.iterrows():
            tv.insert("", "end", values=[r[c] for c in cols])
        tv.pack(fill="both", expand=True, padx=8, pady=6)
        ttk.Label(self.tab_cfg, text="단일 사이트: LTE 3캐리어 + NR 3캐리어 오버레이 (기본 토폴로지)").pack(pady=4)

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
                               step_min=self.var_step.get(), seed=self.var_seed.get())
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
def run_headless_demo(out_dir: str) -> dict:
    """GUI 없이 생성→집계→Export→CDF PNG 를 수행하고 요약을 반환(검증용)."""
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib.figure import Figure

    eng = TrafficGenEngine(days=7, seed=42)
    cell_df = eng.generate()
    agg = aggregate_kpis(cell_df)
    st = summary_table(agg)
    paths = export_esm_csv(cell_df, eng.topology, out_dir)

    fig = Figure(figsize=(8, 4)); ax = fig.add_subplot(111)
    for name, key in (("LTE", "lte_sector"), ("NR", "nr_sector"), ("Total", "total")):
        plot_kpi(ax, agg[key], COL_IPTPUT, "cdf", label=name)
    ax.legend()
    png = os.path.join(out_dir, "ip_tput_cdf.png")
    fig.tight_layout(); fig.savefig(png)
    return dict(rows=len(cell_df), summary=st, paths=paths + [png], agg=agg, cell_df=cell_df)


def main():
    if _HAS_TK:
        TrafficGenApp().mainloop()
    else:
        res = run_headless_demo(os.path.join(os.getcwd(), "Output"))
        print("[headless] rows:", res["rows"])
        print(res["summary"].to_string(index=False))
        print("written:", [os.path.basename(p) for p in res["paths"]])


if __name__ == "__main__":
    main()
