"""
app.py — ㈜진설초해 충진라인 MES Lite 웹 대시보드
실행: streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from mes_core import (
    load_data, execute_lot_production, get_lot_traceability,
    get_order_summary, get_production_status,
)
from run import compute_xbar_r, compute_cpk, compute_pareto, compute_uph

USL, LSL = 515.0, 485.0

# ════════════════════════════════════════════════════════════
# 페이지 설정
# ════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="㈜진설초해 MES Lite",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ════════════════════════════════════════════════════════════
# 데이터 & 분석 (캐시)
# ════════════════════════════════════════════════════════════
@st.cache_data
def get_analytics():
    data   = load_data()
    pr     = data["production_records"]
    lots   = data["lots"]
    ctrl   = compute_xbar_r(pr)
    cpk    = compute_cpk(ctrl["xbar_bar"], ctrl["sigma"])
    pareto = compute_pareto(pr)
    uph    = compute_uph(pr, lots)
    return data, ctrl, cpk, pareto, uph

data, ctrl, cpk, pareto, uph = get_analytics()
pr     = data["production_records"]
lots   = data["lots"]
wo     = data["work_orders"]
orders = data["orders"]
sg     = ctrl["sg"]
x_idx  = list(range(1, len(sg) + 1))

# ── 관리이탈 마스크 ──────────────────────────────────────────
ooc_x = (sg["xbar"] > ctrl["ucl_x"]) | (sg["xbar"] < ctrl["lcl_x"])
ooc_r = sg["r"] > ctrl["ucl_r"]

# ════════════════════════════════════════════════════════════
# 사이드바 — LOT 선택
# ════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("🔍 LOT 추적성 조회")
    selected_lot = st.selectbox("LOT 선택", lots["lot_id"].tolist())
    st.divider()
    st.markdown("**범례**")
    st.markdown("- UCL/LCL : 관리 한계선\n- USL/LSL : 규격 한계선\n- 🔴 : 관리이탈 포인트")

# ════════════════════════════════════════════════════════════
# 타이틀
# ════════════════════════════════════════════════════════════
st.title("🏭 ㈜진설초해 충진라인 품질 현황판")
st.caption(
    f"생산실적 **{len(pr):,}건** · LOT **{pr['lot_id'].nunique()}개** · "
    f"서브그룹 크기 n=5 · USL={USL} ml / LSL={LSL} ml"
)

# ════════════════════════════════════════════════════════════
# KPI 메트릭 행
# ════════════════════════════════════════════════════════════
k1, k2, k3, k4, k5 = st.columns(5)

defect_rate = (pr["defect_code"] != "정상").mean() * 100
oor_rate    = ((pr["fill_volume_ml"] < LSL) | (pr["fill_volume_ml"] > USL)).mean() * 100

k1.metric("총 생산량",       f"{len(pr):,} 건")
k2.metric("평균 충진량",     f"{ctrl['xbar_bar']:.2f} ml",
          delta=f"σ̂={ctrl['sigma']:.2f}")
k3.metric("Cpk",             f"{cpk['Cpk']}",
          delta="불량" if cpk["Cpk"] < 1.0 else "양호",
          delta_color="inverse" if cpk["Cpk"] < 1.0 else "normal")
k4.metric("불량률",          f"{defect_rate:.1f} %")
k5.metric("관리이탈 LOT",   f"{int(ooc_x.sum()) + int(ooc_r.sum())} 개",
          delta=f"X-bar {int(ooc_x.sum())} / R {int(ooc_r.sum())}")

st.divider()

# ════════════════════════════════════════════════════════════
# 차트 행 1 — 관리도(좌) + 히스토그램 & 파레토(우)
# ════════════════════════════════════════════════════════════
col_ctrl, col_qual = st.columns([3, 2], gap="large")

# ── 좌: X-bar / R 관리도 ─────────────────────────────────────
with col_ctrl:
    st.subheader("📈 관리도 (X-bar / R)")

    fig_ctrl = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.10,
        subplot_titles=("X-bar 관리도", "R 관리도"),
    )

    # ── X-bar 데이터 트레이스 ────────────────────────────────
    fig_ctrl.add_trace(go.Scatter(
        x=x_idx, y=sg["xbar"].tolist(),
        mode="lines+markers",
        name="X-bar",
        line=dict(color="#1f77b4", width=1.2),
        marker=dict(size=3.5),
        hovertemplate="서브그룹 %{x}<br>X-bar: %{y:.3f} ml<extra></extra>",
    ), row=1, col=1)

    # X-bar 관리 한계선
    for y_val, name, color, dash in [
        (ctrl["ucl_x"],    f"UCL {ctrl['ucl_x']:.2f}", "#d62728", "dash"),
        (ctrl["xbar_bar"], f"X̄̄  {ctrl['xbar_bar']:.2f}", "#7f7f7f",  "dot"),
        (ctrl["lcl_x"],    f"LCL {ctrl['lcl_x']:.2f}", "#d62728", "dash"),
    ]:
        fig_ctrl.add_trace(go.Scatter(
            x=[x_idx[0], x_idx[-1]], y=[y_val, y_val],
            mode="lines", name=name,
            line=dict(color=color, width=1.3, dash=dash),
            hoverinfo="skip", showlegend=True,
        ), row=1, col=1)

    # X-bar 관리이탈 강조
    if ooc_x.any():
        ooc_xi = np.where(ooc_x.values)[0]
        fig_ctrl.add_trace(go.Scatter(
            x=[x_idx[i] for i in ooc_xi],
            y=sg.loc[ooc_x, "xbar"].tolist(),
            mode="markers", name="X 이탈",
            marker=dict(color="#d62728", size=9,
                        symbol="circle-open", line=dict(width=2.5)),
            hovertemplate="🔴 X이탈 #%{x}<br>%{y:.3f} ml<extra></extra>",
        ), row=1, col=1)

    # ── R 데이터 트레이스 ────────────────────────────────────
    fig_ctrl.add_trace(go.Scatter(
        x=x_idx, y=sg["r"].tolist(),
        mode="lines+markers",
        name="R",
        line=dict(color="#ff7f0e", width=1.2),
        marker=dict(size=3.5),
        hovertemplate="서브그룹 %{x}<br>R: %{y:.3f} ml<extra></extra>",
    ), row=2, col=1)

    for y_val, name, color, dash in [
        (ctrl["ucl_r"], f"UCL_R {ctrl['ucl_r']:.2f}", "#d62728", "dash"),
        (ctrl["r_bar"], f"R̄  {ctrl['r_bar']:.2f}",   "#7f7f7f",  "dot"),
    ]:
        fig_ctrl.add_trace(go.Scatter(
            x=[x_idx[0], x_idx[-1]], y=[y_val, y_val],
            mode="lines", name=name,
            line=dict(color=color, width=1.3, dash=dash),
            hoverinfo="skip", showlegend=True,
        ), row=2, col=1)

    if ooc_r.any():
        ooc_ri = np.where(ooc_r.values)[0]
        fig_ctrl.add_trace(go.Scatter(
            x=[x_idx[i] for i in ooc_ri],
            y=sg.loc[ooc_r, "r"].tolist(),
            mode="markers", name="R 이탈",
            marker=dict(color="#d62728", size=9,
                        symbol="circle-open", line=dict(width=2.5)),
            hovertemplate="🔴 R이탈 #%{x}<br>%{y:.3f} ml<extra></extra>",
        ), row=2, col=1)

    fig_ctrl.update_layout(
        height=500,
        legend=dict(orientation="v", x=1.02, y=1),
        margin=dict(l=50, r=130, t=50, b=40),
        hovermode="x unified",
    )
    fig_ctrl.update_xaxes(title_text="서브그룹 번호 (LOT)", row=2, col=1)
    fig_ctrl.update_yaxes(title_text="평균 충진량 (ml)", row=1, col=1)
    fig_ctrl.update_yaxes(title_text="범위 R (ml)", row=2, col=1)

    st.plotly_chart(fig_ctrl)

# ── 우: 히스토그램 + 파레토 ──────────────────────────────────
with col_qual:
    st.subheader("📊 충진량 분포")

    # 히스토그램
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=pr["fill_volume_ml"].tolist(),
        nbinsx=40,
        name="충진량",
        marker_color="#2ca02c",
        opacity=0.82,
        hovertemplate="구간: %{x}<br>빈도: %{y}<extra></extra>",
    ))
    for x_val, lbl, col_ in [
        (LSL,              f"LSL={LSL}",              "#d62728"),
        (USL,              f"USL={USL}",              "#d62728"),
        (ctrl["xbar_bar"], f"X̄̄={ctrl['xbar_bar']:.2f}", "navy"),
    ]:
        fig_hist.add_vline(x=x_val, line_dash="dash", line_color=col_,
                           line_width=1.8,
                           annotation_text=lbl,
                           annotation_position="top right" if x_val >= ctrl["xbar_bar"] else "top left",
                           annotation_font_size=11)

    fig_hist.update_layout(
        height=220,
        showlegend=False,
        margin=dict(l=50, r=20, t=20, b=40),
        xaxis_title="충진량 (ml)",
        yaxis_title="빈도",
        bargap=0.02,
    )
    st.plotly_chart(fig_hist)

    # 파레토 차트
    st.subheader("📉 불량 파레토")
    fig_par = make_subplots(specs=[[{"secondary_y": True}]])

    fig_par.add_trace(go.Bar(
        x=pareto["불량코드"].tolist(),
        y=pareto["건수"].tolist(),
        name="불량 건수",
        marker_color="#d62728",
        opacity=0.85,
        text=pareto["건수"].tolist(),
        textposition="outside",
        hovertemplate="%{x}<br>건수: %{y}<extra></extra>",
    ), secondary_y=False)

    fig_par.add_trace(go.Scatter(
        x=pareto["불량코드"].tolist(),
        y=pareto["누적비율(%)"].tolist(),
        mode="lines+markers",
        name="누적비율",
        marker=dict(symbol="diamond", size=8, color="#9467bd"),
        line=dict(color="#9467bd", width=1.8, dash="dash"),
        hovertemplate="%{x}<br>누적: %{y:.1f}%<extra></extra>",
    ), secondary_y=True)

    fig_par.add_trace(go.Scatter(
        x=[pareto["불량코드"].iloc[0], pareto["불량코드"].iloc[-1]],
        y=[80, 80],
        mode="lines", name="80% 기준",
        line=dict(color="gray", width=1.2, dash="dot"),
        hoverinfo="skip",
    ), secondary_y=True)

    fig_par.update_layout(
        height=240,
        legend=dict(orientation="h", y=1.12, x=0),
        margin=dict(l=50, r=60, t=20, b=40),
    )
    fig_par.update_yaxes(title_text="건수",          secondary_y=False)
    fig_par.update_yaxes(title_text="누적비율 (%)",  secondary_y=True, range=[0, 115])

    st.plotly_chart(fig_par)

st.divider()

# ════════════════════════════════════════════════════════════
# 요약 테이블 탭
# ════════════════════════════════════════════════════════════
st.subheader("📋 분석 요약 테이블")
tab_cpk, tab_uph, tab_order, tab_wo = st.tabs(
    ["공정능력지수", "설비별 UPH", "수주 현황", "작업지시 현황"]
)

with tab_cpk:
    cpk_df = pd.DataFrame([{
        "σ̂ (ml)": f"{ctrl['sigma']:.4f}",
        "Cp":     cpk["Cp"],
        "Cpk":    cpk["Cpk"],
        "Cpu":    cpk["Cpu"],
        "Cpl":    cpk["Cpl"],
        "판정":   "충분 ✓" if cpk["Cpk"] >= 1.33 else ("주의 △" if cpk["Cpk"] >= 1.0 else "불량 ✗"),
    }])
    st.dataframe(cpk_df, hide_index=True)
    st.caption("Cpk ≥ 1.33: 충분 | 1.00–1.33: 주의 | < 1.00: 불량")

with tab_uph:
    st.dataframe(uph, hide_index=True)

with tab_order:
    summary = get_order_summary(orders, wo)
    st.dataframe(summary, hide_index=True)

with tab_wo:
    wo_status = get_production_status(wo)
    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.dataframe(wo_status, hide_index=True)
    with col_b:
        fig_donut = go.Figure(go.Pie(
            labels=wo_status["status"].tolist(),
            values=wo_status["작업지시_건수"].tolist(),
            hole=0.55,
            marker_colors=["#aec7e8", "#ff7f0e", "#2ca02c"],
            textinfo="label+percent",
        ))
        fig_donut.update_layout(height=220, margin=dict(l=0, r=0, t=0, b=0),
                                showlegend=False)
        st.plotly_chart(fig_donut)

st.divider()

# ════════════════════════════════════════════════════════════
# LOT 추적성 패널 (사이드바 선택 연동)
# ════════════════════════════════════════════════════════════
st.subheader(f"🔍 LOT 추적성 — {selected_lot}")

lot_stat = execute_lot_production(lots, pr, selected_lot)
trace    = get_lot_traceability(selected_lot, orders, wo, lots, pr)

r1, r2, r3 = st.columns(3)

with r1:
    st.markdown("**📦 수주**")
    st.markdown(f"- 수주번호: `{trace['order']['order_id']}`")
    st.markdown(f"- 제품: **{trace['order']['product_name']}**")
    st.markdown(f"- 고객사: {trace['order']['customer']}")

with r2:
    st.markdown("**⚙️ 작업지시**")
    st.markdown(f"- WO ID: `{trace['work_order']['wo_id']}`")
    st.markdown(f"- 설비: {trace['work_order']['equipment']}")
    st.markdown(f"- 계획수량: {trace['work_order']['planned_qty']} 병")

with r3:
    st.markdown("**🗂️ LOT 실적**")
    st.markdown(f"- 작업일: {trace['lot']['lot_date']}")
    st.markdown(f"- 작업자: {trace['lot']['operator']}")
    st.markdown(f"- 평균 충진량: **{lot_stat['avg_fill_ml']} ml**")
    st.markdown(f"- 불량률: **{lot_stat['defect_rate_pct']} %**")
    st.markdown(f"- 총 작업시간: {lot_stat['work_time_total_sec']} 초")

# LOT 단위실적 상세
with st.expander("단위실적 상세 보기"):
    lot_recs = pr[pr["lot_id"] == selected_lot].reset_index(drop=True)
    st.dataframe(lot_recs, hide_index=True)

# 불량 분포 미니 차트
if trace["defect_summary"]:
    def_df = pd.DataFrame(
        list(trace["defect_summary"].items()),
        columns=["코드", "건수"]
    )
    fig_pie = go.Figure(go.Pie(
        labels=def_df["코드"].tolist(),
        values=def_df["건수"].tolist(),
        hole=0.4,
        marker_colors=["#2ca02c", "#d62728", "#ff7f0e", "#9467bd", "#1f77b4"],
        textinfo="label+value",
    ))
    fig_pie.update_layout(
        title=f"{selected_lot} 불량 분포",
        height=260,
        margin=dict(l=0, r=0, t=40, b=0),
        showlegend=False,
    )
    st.plotly_chart(fig_pie)
