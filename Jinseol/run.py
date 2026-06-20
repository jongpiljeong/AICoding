"""
run.py — ㈜진설초해 충진라인 MES Lite 품질 배치 분석
출력: summary_tables.md, dashboard.png
실행: python run.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                       # 파일 저장 전용 백엔드
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

# ── 상수 ─────────────────────────────────────────────────────
DATA_DIR = Path("data")
USL, LSL = 515.0, 485.0                    # 규격 한계 (500 ± 15 ml)

# n=5 서브그룹 SPC 계수
A2, D3, D4, d2 = 0.577, 0.0, 2.114, 2.326

plt.rcParams["font.family"]        = ["Malgun Gothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


# ════════════════════════════════════════════════════════════
# 데이터 로드
# ════════════════════════════════════════════════════════════
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    pr   = pd.read_csv(DATA_DIR / "production_records.csv", encoding="utf-8-sig")
    lots = pd.read_csv(DATA_DIR / "lots.csv",               encoding="utf-8-sig")
    pr["timestamp"]  = pd.to_datetime(pr["timestamp"])
    lots["lot_date"] = pd.to_datetime(lots["lot_date"])
    return pr, lots


# ════════════════════════════════════════════════════════════
# 1. X-bar / R 관리도 계산
# ════════════════════════════════════════════════════════════
def compute_xbar_r(pr: pd.DataFrame) -> dict:
    """
    LOT(= 서브그룹 n=5)별 X-bar, R 및 3σ 관리 한계선 반환.

    σ̂ = R̄ / d2  (within-subgroup 단기 변동 추정)
    """
    sg = (
        pr.groupby("lot_id", sort=False)["fill_volume_ml"]
        .agg(xbar="mean", r=lambda x: x.max() - x.min())
        .reset_index(drop=True)             # 0-base index → x_idx로 1-base 변환
    )
    xbar_bar = sg["xbar"].mean()            # X̄̄ (Grand Mean)
    r_bar    = sg["r"].mean()               # R̄  (Average Range)
    sigma    = r_bar / d2                   # σ̂

    return dict(
        sg       = sg,
        xbar_bar = xbar_bar,
        r_bar    = r_bar,
        sigma    = sigma,
        ucl_x    = xbar_bar + A2 * r_bar,
        lcl_x    = xbar_bar - A2 * r_bar,
        ucl_r    = D4 * r_bar,
        lcl_r    = D3 * r_bar,              # n=5 → 0
    )


# ════════════════════════════════════════════════════════════
# 2. 공정능력지수 Cpk
# ════════════════════════════════════════════════════════════
def compute_cpk(xbar_bar: float, sigma: float) -> dict:
    """Cp, Cpk(= min(Cpu, Cpl)) 계산."""
    cpu = (USL - xbar_bar) / (3 * sigma)
    cpl = (xbar_bar - LSL) / (3 * sigma)
    return {
        "Cp" : round((USL - LSL) / (6 * sigma), 3),
        "Cpk": round(min(cpu, cpl), 3),
        "Cpu": round(cpu, 3),
        "Cpl": round(cpl, 3),
    }


# ════════════════════════════════════════════════════════════
# 3. 불량 파레토
# ════════════════════════════════════════════════════════════
def compute_pareto(pr: pd.DataFrame) -> pd.DataFrame:
    """불량코드별 건수 내림차순 + 누적비율 (정상 제외)."""
    counts = (
        pr[pr["defect_code"] != "정상"]["defect_code"]
        .value_counts()
        .reset_index()
    )
    counts.columns = ["불량코드", "건수"]
    total = counts["건수"].sum()
    counts["누적비율(%)"] = (counts["건수"].cumsum() / total * 100).round(1)
    return counts.reset_index(drop=True)


# ════════════════════════════════════════════════════════════
# 4. 설비별 UPH
# ════════════════════════════════════════════════════════════
def compute_uph(pr: pd.DataFrame, lots: pd.DataFrame) -> pd.DataFrame:
    """
    UPH = 총 생산수량 / (총 work_time_sec ÷ 3600)
    lots와 조인해 equipment별로 분리 계산.
    """
    merged = pr.merge(lots[["lot_id", "equipment"]], on="lot_id", how="left")
    grp    = merged.groupby("equipment", sort=True)

    uph = pd.DataFrame({
        "생산수량(건)":  grp["record_id"].count(),
        "총작업시간(h)": (grp["work_time_sec"].sum() / 3600).round(2),
    }).reset_index()
    uph["UPH"] = (uph["생산수량(건)"] / uph["총작업시간(h)"]).round(1)
    return uph


# ════════════════════════════════════════════════════════════
# 마크다운 출력 유틸
# ════════════════════════════════════════════════════════════
def _md_table(df: pd.DataFrame) -> str:
    header = "| " + " | ".join(str(c) for c in df.columns) + " |"
    sep    = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    rows   = [
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in df.itertuples(index=False)
    ]
    return "\n".join([header, sep] + rows)


def write_summary(ctrl: dict, cpk: dict,
                  pareto: pd.DataFrame, uph: pd.DataFrame) -> None:
    ctrl_df = pd.DataFrame({
        "항목"  : ["X̄̄ Grand Mean", "R̄ Avg Range", "σ̂",
                   "UCL_Xbar", "LCL_Xbar", "UCL_R", "LCL_R"],
        "값(ml)": [
            f"{ctrl['xbar_bar']:.4f}", f"{ctrl['r_bar']:.4f}",
            f"{ctrl['sigma']:.4f}",    f"{ctrl['ucl_x']:.3f}",
            f"{ctrl['lcl_x']:.3f}",   f"{ctrl['ucl_r']:.3f}",
            f"{ctrl['lcl_r']:.3f}",
        ],
    })
    cpk_df = pd.DataFrame([cpk])

    lines = [
        "# ㈜진설초해 충진라인 품질 분석 요약",
        f"> 서브그룹 크기 n=5 | USL={USL} ml | LSL={LSL} ml | n=5 계수: A2={A2}, D4={D4}, d2={d2}",
        "",
        "## 1. X-bar / R 관리 한계선",
        _md_table(ctrl_df),
        "",
        "## 2. 공정능력지수",
        _md_table(cpk_df),
        "> Cpk ≥ 1.33: 충분 | 1.00–1.33: 주의 | < 1.00: 불량",
        "",
        "## 3. 불량 파레토 (정상 제외)",
        _md_table(pareto),
        "",
        "## 4. 설비별 UPH",
        _md_table(uph),
        "",
    ]
    Path("summary_tables.md").write_text("\n".join(lines), encoding="utf-8")
    print("  → summary_tables.md 저장 완료")


# ════════════════════════════════════════════════════════════
# dashboard.png — 4분할 관리도
# ════════════════════════════════════════════════════════════
def draw_dashboard(ctrl: dict, pareto: pd.DataFrame,
                   pr: pd.DataFrame) -> None:
    sg    = ctrl["sg"]
    x_idx = np.arange(1, len(sg) + 1)      # 서브그룹 번호 (1-base)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=150)
    fig.suptitle("㈜진설초해 충진라인 품질 현황판",
                 fontsize=17, fontweight="bold", y=0.995)

    # ── 좌상: X-bar 관리도 ───────────────────────────────────
    ax = axes[0, 0]
    ax.plot(x_idx, sg["xbar"], "o-", color="#1f77b4",
            lw=1.2, ms=3.5, label="X-bar", zorder=3)

    for val, lbl, ls, col in [
        (ctrl["ucl_x"],    f"UCL = {ctrl['ucl_x']:.2f}",    "--", "#d62728"),
        (ctrl["xbar_bar"], f"X̄̄  = {ctrl['xbar_bar']:.2f}", "-",  "#7f7f7f"),
        (ctrl["lcl_x"],    f"LCL = {ctrl['lcl_x']:.2f}",    "--", "#d62728"),
    ]:
        ax.axhline(val, ls=ls, color=col, lw=1.3, label=lbl)

    ooc_x = (sg["xbar"] > ctrl["ucl_x"]) | (sg["xbar"] < ctrl["lcl_x"])
    if ooc_x.any():
        ax.scatter(x_idx[ooc_x.values], sg.loc[ooc_x, "xbar"].values,
                   color="#d62728", zorder=5, s=60, label=f"관리이탈 ({ooc_x.sum()}개)")

    ax.set_title("X-bar 관리도", fontweight="bold", pad=8)
    ax.set_xlabel("서브그룹 번호 (LOT)")
    ax.set_ylabel("평균 충진량 (ml)")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3)

    # ── 우상: R 관리도 ────────────────────────────────────────
    ax = axes[0, 1]
    ax.plot(x_idx, sg["r"], "s-", color="#ff7f0e",
            lw=1.2, ms=3.5, label="R", zorder=3)

    for val, lbl, ls, col in [
        (ctrl["ucl_r"], f"UCL = {ctrl['ucl_r']:.2f}", "--", "#d62728"),
        (ctrl["r_bar"], f"R̄   = {ctrl['r_bar']:.2f}", "-",  "#7f7f7f"),
    ]:
        ax.axhline(val, ls=ls, color=col, lw=1.3, label=lbl)

    ooc_r = sg["r"] > ctrl["ucl_r"]
    if ooc_r.any():
        ax.scatter(x_idx[ooc_r.values], sg.loc[ooc_r, "r"].values,
                   color="#d62728", zorder=5, s=60, label=f"관리이탈 ({ooc_r.sum()}개)")

    ax.set_title("R 관리도", fontweight="bold", pad=8)
    ax.set_xlabel("서브그룹 번호 (LOT)")
    ax.set_ylabel("범위 R (ml)")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3)

    # ── 좌하: 충진량 히스토그램 ──────────────────────────────
    ax = axes[1, 0]
    fill_vals = pr["fill_volume_ml"]
    ax.hist(fill_vals, bins=40, color="#2ca02c", edgecolor="white",
            alpha=0.82, label="충진량 분포")

    for val, lbl, col in [
        (LSL,            f"LSL = {LSL} ml",         "#d62728"),
        (USL,            f"USL = {USL} ml",         "#d62728"),
        (fill_vals.mean(), f"X̄ = {fill_vals.mean():.2f} ml", "navy"),
    ]:
        ax.axvline(val, ls="--", color=col, lw=1.6, label=lbl)

    # 규격 이탈 음영
    x_lo = np.linspace(fill_vals.min(), LSL, 100)
    x_hi = np.linspace(USL, fill_vals.max(), 100)
    ax.axvspan(fill_vals.min(), LSL, alpha=0.08, color="red")
    ax.axvspan(USL, fill_vals.max(), alpha=0.08, color="red")

    oor_pct = ((fill_vals < LSL) | (fill_vals > USL)).mean() * 100
    ax.set_title(f"충진량 분포  (규격이탈 {oor_pct:.1f}%)", fontweight="bold", pad=8)
    ax.set_xlabel("충진량 (ml)")
    ax.set_ylabel("빈도")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis="y")

    # ── 우하: 불량 파레토 ─────────────────────────────────────
    ax  = axes[1, 1]
    ax2 = ax.twinx()

    x_par = range(len(pareto))
    bars  = ax.bar(x_par, pareto["건수"],
                   color="#d62728", alpha=0.82, label="불량 건수", zorder=3)
    ax2.plot(x_par, pareto["누적비율(%)"], "D--",
             color="#9467bd", lw=1.8, ms=7, label="누적비율", zorder=4)
    ax2.axhline(80, ls=":", color="#7f7f7f", lw=1.2, label="80% 기준선")

    # 막대 위 건수 레이블
    for rect, cnt in zip(bars, pareto["건수"]):
        ax.text(rect.get_x() + rect.get_width() / 2,
                rect.get_height() + 0.3, str(cnt),
                ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(list(x_par))
    ax.set_xticklabels(pareto["불량코드"].tolist(), fontsize=10)
    ax.set_title("불량 파레토 (정상 제외)", fontweight="bold", pad=8)
    ax.set_xlabel("불량 코드")
    ax.set_ylabel("건수")
    ax2.set_ylabel("누적비율 (%)")
    ax2.set_ylim(0, 115)
    ax2.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.grid(alpha=0.3, axis="y", zorder=0)

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="lower right")

    plt.tight_layout(rect=[0, 0, 1, 0.975])
    fig.savefig("dashboard.png", bbox_inches="tight")
    plt.close(fig)
    print("  → dashboard.png 저장 완료")


# ════════════════════════════════════════════════════════════
# 메인
# ════════════════════════════════════════════════════════════
if __name__ == "__main__":
    SEP = "─" * 55
    print("=== ㈜진설초해 충진라인 품질 분석 시작 ===\n")

    pr, lots = load_data()
    print(f"  production_records : {len(pr)}건")
    print(f"  lots               : {len(lots)}건 / {pr['lot_id'].nunique()}개 서브그룹")

    ctrl   = compute_xbar_r(pr)
    cpk    = compute_cpk(ctrl["xbar_bar"], ctrl["sigma"])
    pareto = compute_pareto(pr)
    uph    = compute_uph(pr, lots)

    # ── 콘솔 출력 ─────────────────────────────────────────────
    print(f"\n{SEP}")
    print("[1] X-bar / R 관리도")
    print(SEP)
    print(f"  서브그룹 수   : {len(ctrl['sg'])}")
    print(f"  X̄̄ (Grand Mean) = {ctrl['xbar_bar']:.4f} ml")
    print(f"  R̄  (Avg Range)  = {ctrl['r_bar']:.4f} ml")
    print(f"  σ̂               = {ctrl['sigma']:.4f} ml")
    print(f"  UCL_Xbar = {ctrl['ucl_x']:.3f}  |  LCL_Xbar = {ctrl['lcl_x']:.3f}")
    print(f"  UCL_R    = {ctrl['ucl_r']:.3f}  |  LCL_R    = {ctrl['lcl_r']:.3f}")
    sg = ctrl["sg"]
    ooc_cnt = int(((sg["xbar"] > ctrl["ucl_x"]) | (sg["xbar"] < ctrl["lcl_x"])).sum())
    print(f"  관리이탈 서브그룹 : {ooc_cnt}개")

    print(f"\n{SEP}")
    print("[2] 공정능력지수")
    print(SEP)
    for k, v in cpk.items():
        flag = ""
        if k == "Cpk":
            flag = "  ✓ 충분" if v >= 1.33 else ("  △ 주의" if v >= 1.0 else "  ✗ 불량")
        print(f"  {k} = {v}{flag}")

    print(f"\n{SEP}")
    print("[3] 불량 파레토 (정상 제외)")
    print(SEP)
    print(pareto.to_string(index=False))

    print(f"\n{SEP}")
    print("[4] 설비별 UPH")
    print(SEP)
    print(uph.to_string(index=False))

    print()
    write_summary(ctrl, cpk, pareto, uph)
    draw_dashboard(ctrl, pareto, pr)

    print("\n=== 분석 완료 ===")
