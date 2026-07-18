"""
FeederIQ – Streamlit Frontend (R2 v3)
"""
import time
import requests
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="FeederIQ", page_icon="⚡", layout="wide")
API_URL = "http://localhost:8000"

# Colors
C1 = "#D85604"  # PwC orange primary
C2 = "#E88D14"  # PwC gold
C3 = "#F5A623"  # Light gold
C_DARK = "#2D2D2D"
C_GREY = "#666666"
C_GREEN = "#1B8C3A"
C_RED = "#C92A2A"

st.markdown(f"""
<style>
    .stApp {{ background: white; }}
    .main .block-container {{ padding-top: 0.5rem; max-width: 1100px; }}
    section[data-testid="stSidebar"] {{ background: #FAFAFA; border-right: 1px solid #EBEBEB; }}
    section[data-testid="stSidebar"] .block-container {{ padding-top: 0.8rem; }}

    .top-bar {{ padding: 10px 0 12px 0; border-bottom: 3px solid {C1}; margin-bottom: 18px; }}
    .top-bar .logo {{ color:{C1}; font: 900 1.5rem Georgia,serif; }}
    .top-bar .name {{ color:{C_DARK}; font: 700 1.05rem Arial,sans-serif; margin-left: 10px; }}

    .sec-head {{ font: 700 1.1rem Arial,sans-serif; color:{C_DARK}; margin: 20px 0 8px; padding-bottom: 5px; border-bottom: 2px solid {C1}; }}
    .sub-head {{ font: 700 0.88rem Arial,sans-serif; color:{C_DARK}; margin: 14px 0 5px; }}

    .card {{ background:white; border-radius:8px; padding:14px 16px; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,0.05); border:1px solid #EFEFEF; border-left:4px solid {C1}; }}
    .card .lbl {{ font: 600 0.68rem Arial,sans-serif; color:{C_GREY}; text-transform:uppercase; letter-spacing:0.3px; }}
    .card .val {{ font: 700 1.3rem Arial,sans-serif; color:{C_DARK}; margin-top:2px; }}
    .card .sub {{ font: 400 0.78rem Arial,sans-serif; color:{C_GREY}; margin-top:2px; }}

    .agent-row {{ display:flex; align-items:center; gap:10px; padding:10px 14px; border-radius:6px; margin-bottom:6px; background:#FAFAFA; border:1px solid #EBEBEB; }}
    .agent-row.done {{ border-left:3px solid {C_GREEN}; background:#F0FFF4; }}
    .agent-row.running {{ border-left:3px solid {C1}; background:#FFF8F0; }}
    .agent-row .name {{ font: 700 0.85rem Arial,sans-serif; color:{C_DARK}; }}
    .agent-row .detail {{ font: 400 0.75rem Arial,sans-serif; color:{C_GREY}; }}

    .score-row {{ display:flex; align-items:center; gap:6px; margin-bottom:5px; }}
    .score-row .lbl {{ font: 600 0.8rem Arial,sans-serif; color:{C_DARK}; width:150px; }}
    .score-row .bar {{ flex:1; height:7px; background:#EFEFEF; border-radius:4px; }}
    .score-row .fill {{ height:7px; background:{C1}; border-radius:4px; }}
    .score-row .num {{ font: 700 0.82rem Arial,sans-serif; color:{C1}; width:55px; text-align:right; }}

    .rank-card {{ background:white; border-radius:8px; padding:12px 16px; margin-bottom:6px; border:1px solid #EFEFEF; }}
    .rank-card.top {{ border:2px solid {C1}; }}

    .info-box {{ background:#FAFAFA; border-radius:6px; padding:12px 16px; margin:8px 0; border:1px solid #EBEBEB; }}

    .stButton > button {{ background:{C1}; color:white; border:none; border-radius:6px; padding:10px 20px; font:700 0.85rem Arial,sans-serif; }}
    .stButton > button:hover {{ background:{C2}; }}

    .sidebar-section {{ font: 700 0.82rem Arial,sans-serif; color:{C_DARK}; margin: 12px 0 4px; }}
    .optional-tag {{ font: 400 0.68rem Arial,sans-serif; color:{C2}; font-style:italic; }}
</style>
""", unsafe_allow_html=True)


def card_html(label, value, sub=""):
    sub_h = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="card"><div class="lbl">{label}</div><div class="val">{value}</div>{sub_h}</div>'


def score_bar_html(label, value, max_val=10):
    pct = min(100, (value / max_val) * 100)
    return f'''<div class="score-row">
        <div class="lbl">{label}</div>
        <div class="bar"><div class="fill" style="width:{pct}%"></div></div>
        <div class="num">{value:.1f} / 10</div>
    </div>'''


def render_grid_map():
    from pathlib import Path
    coords_path = Path(__file__).resolve().parent.parent.parent / "ai_synthetic_data" / "Buscoords.dss"
    if not coords_path.exists():
        return None
    buses = {}
    with open(coords_path) as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3:
                name = parts[0].lower()
                try:
                    buses[name] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    continue
    primary = {k: v for k, v in buses.items() if not k.startswith("s") and not k.endswith("r")}
    ev_buses, solar_buses, dc_bus = {"60","83","90","92","114"}, {"66","80","92","104","110"}, "67"

    xs, ys, colors, sizes, hovers, texts = [], [], [], [], [], []
    for bus, (x, y) in primary.items():
        xs.append(x); ys.append(y)
        if bus == dc_bus:
            colors.append(C_RED); sizes.append(20); hovers.append(f"<b>Bus {bus}</b><br>🏢 Data Center"); texts.append(bus)
        elif bus in ev_buses and bus in solar_buses:
            colors.append("#7B2D8B"); sizes.append(16); hovers.append(f"<b>Bus {bus}</b><br>⚡ EV + ☀️ Solar"); texts.append(bus)
        elif bus in ev_buses:
            colors.append(C1); sizes.append(15); hovers.append(f"<b>Bus {bus}</b><br>⚡ EV Charging"); texts.append(bus)
        elif bus in solar_buses:
            colors.append(C_GREEN); sizes.append(15); hovers.append(f"<b>Bus {bus}</b><br>☀️ Solar PV"); texts.append(bus)
        else:
            colors.append("#999999"); sizes.append(5); hovers.append(f"Bus {bus}"); texts.append("")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=ys, mode='markers', marker=dict(size=sizes, color=colors, line=dict(width=0.8, color='white')),
                              text=hovers, hoverinfo='text', showlegend=False))
    key_xs = [x for x, t in zip(xs, texts) if t]
    key_ys = [y for y, t in zip(ys, texts) if t]
    key_texts = [t for t in texts if t]
    fig.add_trace(go.Scatter(x=key_xs, y=key_ys, mode='text', text=key_texts, textposition="top center",
                              textfont=dict(size=9, color=C_DARK, family="Arial"), showlegend=False, hoverinfo='skip'))
    for lbl, clr in [("Data Center", C_RED), ("EV Charging", C1), ("Solar PV", C_GREEN), ("EV + Solar", "#7B2D8B")]:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(size=11, color=clr), name=lbl))
    fig.update_layout(height=380, margin=dict(t=5, b=5, l=5, r=5), plot_bgcolor='#F8F8F8', paper_bgcolor='white',
                      xaxis=dict(visible=False), yaxis=dict(visible=False),
                      legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center", font=dict(size=10, family="Arial")),
                      shapes=[dict(type="rect", x0=min(xs)-30, y0=min(ys)-30, x1=max(xs)+30, y1=max(ys)+30,
                                   line=dict(color=C_DARK, width=1), fillcolor="rgba(0,0,0,0)")])
    return fig


# ─── Session State ────────────────────────────────────────────────────────────
if "study_data" not in st.session_state:
    st.session_state.study_data = None
if "running" not in st.session_state:
    st.session_state.running = False

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="color:{C1};font:900 1.4rem Georgia,serif;margin-bottom:4px;">pwc</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font:700 0.95rem Arial,sans-serif;color:{C_DARK};margin-bottom:14px;border-bottom:2px solid {C1};padding-bottom:8px;">Parameter Selection</div>', unsafe_allow_html=True)

    st.markdown(f'<div class="sidebar-section">📅 Planning Horizon</div>', unsafe_allow_html=True)
    horizon = st.selectbox("h", ["3m","6m","12m","18m","3yr","5yr"], index=2,
                           format_func=lambda x: {"3m":"3 Months","6m":"6 Months","12m":"12 Months","18m":"18 Months","3yr":"3 Years","5yr":"5 Years"}[x],
                           label_visibility="collapsed")

    st.markdown(f'<div class="sidebar-section">⚡ EV Growth &nbsp;<a href="https://www.eia.gov/outlooks/aeo/" target="_blank" title="EIA AEO 2024: 15-25% annually through 2030">ⓘ</a></div>', unsafe_allow_html=True)
    ev_level = st.selectbox("ev", ["Low","Base","High"], index=1,
                            format_func=lambda x: {"Low":"Low (15% annually)","Base":"Base (20% annually)","High":"High (25% annually)"}[x],
                            label_visibility="collapsed")
    ev_custom = st.number_input("Custom %", min_value=5, max_value=50,
                                value={"Low":15,"Base":20,"High":25}[ev_level], step=1, key="evc", label_visibility="collapsed")

    st.markdown(f'<div class="sidebar-section">☀️ Solar Adoption &nbsp;<a href="https://www.seia.org/research-resources/solar-market-insight-report" target="_blank" title="SEIA Q1 2024: 100-400 MW regional adoption">ⓘ</a></div>', unsafe_allow_html=True)
    solar_level = st.selectbox("sol", ["Low","Base","High"], index=1,
                               format_func=lambda x: {"Low":"Low (100 MW)","Base":"Base (200 MW)","High":"High (300 MW)"}[x],
                               label_visibility="collapsed")
    solar_custom = st.number_input("Custom MW", min_value=50, max_value=1000,
                                   value={"Low":100,"Base":200,"High":300}[solar_level], step=25, key="solc", label_visibility="collapsed")

    st.markdown(f'<div class="sidebar-section">🏢 Data Center</div>', unsafe_allow_html=True)
    dc_level = st.selectbox("dc", ["Low","Moderate","High"], index=1,
                            format_func=lambda x: {"Low":"Low (1.0 MW)","Moderate":"Moderate (1.75 MW)","High":"High (3.0 MW)"}[x],
                            label_visibility="collapsed")
    dc_custom = st.number_input("Custom MW", min_value=0.5, max_value=10.0,
                                value={"Low":1.0,"Moderate":1.75,"High":3.0}[dc_level], step=0.25, key="dcc", label_visibility="collapsed")
    dc_timeline = st.selectbox("timeline", ["6m","12m","18m"], index=1,
                               format_func=lambda x: {"6m":"Online in 6 Months","12m":"Online in 12 Months","18m":"Online in 18 Months"}[x],
                               label_visibility="collapsed")

    st.markdown(f'<div class="sidebar-section">🕐 Peak Load Hours</div>', unsafe_allow_html=True)
    peak_start, peak_end = st.slider("Peak hours", 0, 23, (17, 21), key="peak_hrs")
    st.caption(f"Selected: {peak_start}:00 – {peak_end}:00")

    st.markdown("---")
    st.markdown(f'<div class="sidebar-section">**Candidate Portfolios to Evaluate**</div>', unsafe_allow_html=True)
    max_portfolios = st.slider("count", 10, 120, 60, step=10, label_visibility="collapsed")

    st.markdown(f'<div class="sidebar-section">**Max Measures per Portfolio**</div>', unsafe_allow_html=True)
    max_active = st.slider("measures", 1, 5, 3, label_visibility="collapsed")

    st.markdown(f'<div class="sidebar-section">🎯 Solution Preferences <span class="optional-tag">(optional)</span></div>', unsafe_allow_html=True)
    st.caption("Lock specific interventions into all evaluated solutions:")
    filter_mc = st.checkbox("Managed EV Charging", key="f_mc")
    filter_pi = st.checkbox("Phased Interconnection", key="f_pi")
    filter_dt = st.checkbox("Demand Tariff", key="f_dt")
    filter_battery = st.checkbox("Battery Storage", key="f_bat")
    filter_tu = st.checkbox("Transformer Upgrade", key="f_tu")

    st.markdown("---")
    run_btn = st.button("▶  Run Study", use_container_width=True)

# ─── Main ─────────────────────────────────────────────────────────────────────
st.markdown(f'<div class="top-bar"><span class="logo">pwc</span><span class="name">FeederIQ Agentic Distribution Planning</span></div>', unsafe_allow_html=True)

if run_btn:
    st.session_state.running = True
    st.session_state.study_data = None

# Agent Execution
if st.session_state.running and st.session_state.study_data is None:
    st.markdown('<div class="sec-head">Agent Execution</div>', unsafe_allow_html=True)
    agents = [
        ("🔬", "Scenario Agent", "Building 24-hour synthetic load and generation profiles"),
        ("⚡", "Simulation Agent", "Running OpenDSS power flow for 24 hourly timesteps"),
        ("🔍", "Constraint Agent", "Detecting voltage violations and equipment overloads"),
        ("🌱", "NWA Agent", "Evaluating non-wires alternatives"),
        ("🔧", "Capex Agent", "Evaluating infrastructure upgrade options"),
        ("📊", "Recommendation Agent", "Scoring and ranking all candidate solutions"),
    ]
    agent_container = st.empty()
    progress = st.progress(0)

    payload = {"horizon_label": horizon, "ev_level": ev_level, "solar_level": solar_level,
               "dc_level": dc_level, "dc_timeline_label": dc_timeline,
               "max_active_measures": max_active, "max_portfolios": max_portfolios}

    api_done = False
    for i, (icon, name, detail) in enumerate(agents):
        for pct in range(0, 101, 4):
            progress.progress((i + pct/100) / len(agents))
            html = ""
            for j, (ic, nm, dt) in enumerate(agents):
                if j < i:
                    html += f'<div class="agent-row done"><span style="font-size:1.1rem;">{ic}</span><div><div class="name">{nm}</div><div class="detail">✓ Complete</div></div></div>'
                elif j == i:
                    html += f'<div class="agent-row running"><span style="font-size:1.1rem;">{ic}</span><div><div class="name">{nm}</div><div class="detail">{dt}</div><div style="margin-top:4px;height:4px;background:#EFEFEF;border-radius:2px;width:200px;"><div style="height:4px;background:{C1};border-radius:2px;width:{pct}%;"></div></div></div></div>'
                else:
                    html += f'<div class="agent-row"><span style="font-size:1.1rem;">{ic}</span><div><div class="name">{nm}</div><div class="detail">{dt}</div></div></div>'
            agent_container.markdown(html, unsafe_allow_html=True)
            if i == 0 and pct == 0 and not api_done:
                try:
                    resp = requests.post(f"{API_URL}/study", json=payload, timeout=300)
                    resp.raise_for_status()
                    st.session_state.study_data = resp.json()
                    api_done = True
                except Exception as e:
                    st.error(f"Connection failed: {e}. Is the backend running?")
                    st.session_state.running = False
                    st.stop()
            else:
                time.sleep(0.035)

    progress.progress(1.0)
    html = ""
    for ic, nm, dt in agents:
        html += f'<div class="agent-row done"><span style="font-size:1.1rem;">{ic}</span><div><div class="name">{nm}</div><div class="detail">✓ Complete</div></div></div>'
    agent_container.markdown(html, unsafe_allow_html=True)
    time.sleep(0.3)
    st.session_state.running = False
    st.rerun()

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.study_data:
    data = st.session_state.study_data
    ranking = data.get("ranking", [])

    # Apply filters
    filters = {}
    if filter_battery: filters["Battery"] = True
    if filter_mc: filters["ManagedCharging"] = True
    if filter_pi: filters["PhasedInterconnection"] = True
    if filter_dt: filters["DemandTariff"] = True
    if filter_tu: filters["TransformerUpgrade"] = True

    if filters:
        filtered = [r for r in ranking if all(r.get(k, 0) > 0 for k in filters)]
        if filtered:
            ranking = filtered
        else:
            st.warning(f"No portfolios in the evaluated set contain all selected interventions. Showing unfiltered results. Try evaluating more candidate portfolios or reducing required interventions.")

    # Tabs
    tab_rec, tab_rank, tab_baseline, tab_profiles, tab_memo = st.tabs([
        "✅ Recommendation", "📊 Rankings", "🔍 Baseline", "📈 Profiles", "📝 Memo"])

    # ═══ RECOMMENDATION ═══════════════════════════════════════════════════════
    with tab_rec:
        st.markdown('<div class="sec-head">Recommended Solution</div>', unsafe_allow_html=True)

        top10 = ranking[:10]
        selected_idx = st.selectbox(
            "Select solution",
            range(len(top10)),
            format_func=lambda i: f"#{i+1}  {top10[i]['portfolio_name']}  (Score: {top10[i]['final_score']:.2f} / 10)",
            label_visibility="collapsed")
        selected = top10[selected_idx]

        if data.get("nwa_resolved_all"):
            st.success("✅ Non-wires alternatives fully resolve all grid violations. No traditional capex required.")

        # Solution card
        st.markdown(f'''<div class="rank-card top" style="margin:10px 0;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <div style="font:700 1.05rem Arial,sans-serif;color:{C_DARK};">{selected["portfolio_name"]}</div>
                <div style="font:800 1.4rem Arial,sans-serif;color:{C1};">{selected["final_score"]:.2f} <span style="font:400 0.75rem Arial;color:{C_GREY};">/ 10</span></div>
            </div>
        </div>''', unsafe_allow_html=True)

        st.markdown(f'<div class="sub-head">Score Breakdown</div>', unsafe_allow_html=True)
        col_bars, col_radar = st.columns([1, 1])

        grid_relief = selected.get("grid_relief_score", selected.get("technical_score", 0))
        cost_sc = selected.get("cost_score", 0)
        speed_sc = selected.get("speed_to_value_score", (selected.get("feasibility_score",0)+selected.get("deployment_score",0))/2)
        esg_sc = selected.get("esg_score", 8)

        with col_bars:
            st.markdown(
                score_bar_html("Grid Relief (40%)", grid_relief) +
                score_bar_html("Cost Efficiency (25%)", cost_sc) +
                score_bar_html("Speed to Value (20%)", speed_sc) +
                score_bar_html("ESG Alignment (15%)", esg_sc),
                unsafe_allow_html=True)
            st.markdown(f'''<div class="info-box">
                <div style="font:400 0.8rem Arial;color:{C_DARK};line-height:1.7;">
                • <b style="color:{C1};">Grid Relief</b> → % reduction in equipment overloads and voltage violations<br>
                • <b style="color:{C1};">Cost Efficiency</b> → Lower implementation cost relative to full capex alternatives<br>
                • <b style="color:{C1};">Speed to Value</b> → Combined feasibility and deployment timeline<br>
                • <b style="color:{C1};">ESG Alignment</b> → Sustainability benefit: lower carbon, less material intensity
                </div>
            </div>''', unsafe_allow_html=True)

        with col_radar:
            cats = ['Grid Relief', 'Cost', 'Speed', 'ESG']
            vals = [grid_relief, cost_sc, speed_sc, esg_sc]
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(r=vals+[vals[0]], theta=cats+[cats[0]], fill='toself',
                                           fillcolor='rgba(216,86,4,0.12)', line=dict(color=C1, width=2.5), name="Selected"))
            if len(top10) > 1:
                runner = top10[1] if selected_idx == 0 else top10[0]
                r_vals = [runner.get("grid_relief_score", runner.get("technical_score",0)), runner.get("cost_score",0),
                          runner.get("speed_to_value_score",(runner.get("feasibility_score",0)+runner.get("deployment_score",0))/2),
                          runner.get("esg_score",8)]
                fig.add_trace(go.Scatterpolar(r=r_vals+[r_vals[0]], theta=cats+[cats[0]], fill='toself',
                                               fillcolor='rgba(100,100,100,0.04)', line=dict(color=C_GREY, width=1.5, dash='dot'), name="Comparison"))
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,10], tickfont=dict(size=9, family="Arial"))),
                              height=270, margin=dict(t=20,b=30,l=40,r=40), paper_bgcolor="white",
                              font=dict(family="Arial", size=10),
                              legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"))
            st.plotly_chart(fig, use_container_width=True)

        # Impact Assessment
        st.markdown(f'<div class="sub-head">Impact Assessment</div>', unsafe_allow_html=True)
        st.caption("Grid stress comparison before and after applying the selected solution.")
        bs = data.get("base_summary", {})
        impr = selected.get("technical_improvement_pct", 0)
        after_stress = bs.get("grid_stress_score", 0) * (1 - impr/100)

        ba1, ba2, ba3 = st.columns(3)
        ba1.markdown(card_html("Before (No Intervention)", f"{bs.get('grid_stress_score',0):.0f}", "Grid stress score"), unsafe_allow_html=True)
        ba2.markdown(card_html("After (Selected Solution)", f"{after_stress:.0f}", f"↓ {impr:.1f}% reduction"), unsafe_allow_html=True)
        ba3.markdown(card_html("Technical Improvement", f"{impr:.1f}%", "Overload and violation reduction"), unsafe_allow_html=True)

        # Hourly comparison with profile-weighted reduction
        base_results = data.get("base_results", [])
        profiles = data.get("profiles", {})
        if base_results and profiles:
            st.markdown(f'<div class="sub-head">Hourly Overload Comparison</div>', unsafe_allow_html=True)
            st.caption("Baseline line overloads vs estimated post-intervention reduction across 24 hours.")
            br_df = pd.DataFrame(base_results)
            # Weight reduction by load profile shape for realistic visual
            feeder_mult = np.array(profiles.get("feeder_mult", [1]*24))
            if len(feeder_mult) == len(br_df):
                weight = feeder_mult / feeder_mult.max()
                reduction = impr / 100 * (0.5 + 0.5 * weight)
            else:
                reduction = impr / 100
            after_lines = (br_df["num_overloaded_lines"] * (1 - reduction)).clip(lower=0).astype(int)

            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(x=br_df["time"], y=br_df["num_overloaded_lines"], name="Baseline", marker_color=C1, opacity=0.75))
            fig_comp.add_trace(go.Bar(x=br_df["time"], y=after_lines, name="After Intervention", marker_color=C_GREEN, opacity=0.75))
            fig_comp.update_layout(barmode="group", height=250, margin=dict(t=10,b=30),
                                    xaxis_title="Hour", yaxis_title="Line Overloads",
                                    plot_bgcolor="white", paper_bgcolor="white",
                                    legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
                                    font=dict(family="Arial", size=10))
            st.plotly_chart(fig_comp, use_container_width=True)

    # ═══ RANKINGS ═════════════════════════════════════════════════════════════
    with tab_rank:
        st.markdown('<div class="sec-head">Portfolio Rankings</div>', unsafe_allow_html=True)
        st.caption("All solutions ranked by weighted score. Score range: 0 (worst) to 10 (best).")

        for idx, row in enumerate(ranking[:3]):
            badges = ["🥇","🥈","🥉"]
            cls = "rank-card top" if idx == 0 else "rank-card"
            st.markdown(f'''<div class="{cls}">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-size:1.1rem;">{badges[idx]}</span>
                        <span style="font:700 0.92rem Arial;color:{C_DARK};">{row["portfolio_name"]}</span>
                    </div>
                    <span style="font:800 1.1rem Arial;color:{C1};">{row["final_score"]:.2f} / 10</span>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin-top:6px;">
                    <div><span style="font:600 0.7rem Arial;color:{C_GREY};">Grid Relief</span><br><b style="color:{C1};">{row.get("technical_improvement_pct",0):.1f}%</b></div>
                    <div><span style="font:600 0.7rem Arial;color:{C_GREY};">Cost</span><br><b style="color:{C1};">{row.get("cost_score",0):.1f}/10</b></div>
                    <div><span style="font:600 0.7rem Arial;color:{C_GREY};">Speed</span><br><b style="color:{C1};">{row.get("speed_to_value_score",(row.get("feasibility_score",0)+row.get("deployment_score",0))/2):.1f}/10</b></div>
                    <div><span style="font:600 0.7rem Arial;color:{C_GREY};">ESG</span><br><b style="color:{C1};">{row.get("esg_score",0):.1f}/10</b></div>
                </div>
            </div>''', unsafe_allow_html=True)

        if len(ranking) > 3:
            top_n = min(10, len(ranking))
            chart_data = ranking[:top_n]
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                y=[r["portfolio_name"] for r in chart_data][::-1],
                x=[r["final_score"] for r in chart_data][::-1],
                orientation='h', marker_color=[C1 if i==top_n-1 else C2 for i in range(top_n)],
                text=[f'{r["final_score"]:.2f}' for r in chart_data][::-1], textposition='outside'))
            fig_bar.update_layout(height=max(250, top_n*36), margin=dict(t=10,l=260,b=20,r=40),
                                   xaxis_title="Score (0-10)", plot_bgcolor="white", paper_bgcolor="white",
                                   font=dict(family="Arial", size=10))
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown(f'<div class="sub-head">Full Results</div>', unsafe_allow_html=True)
        rank_df = pd.DataFrame(ranking)
        if "speed_to_value_score" not in rank_df.columns and "feasibility_score" in rank_df.columns:
            rank_df["speed_to_value_score"] = (rank_df["feasibility_score"] + rank_df["deployment_score"]) / 2
        display_cols = [c for c in ["portfolio_name","final_score","technical_improvement_pct","cost_score","speed_to_value_score","esg_score"] if c in rank_df.columns]
        st.dataframe(rank_df[display_cols] if display_cols else rank_df, use_container_width=True, height=300)

    # ═══ BASELINE ═════════════════════════════════════════════════════════════
    with tab_baseline:
        st.markdown('<div class="sec-head">Baseline Grid Assessment</div>', unsafe_allow_html=True)
        st.caption("24-hour simulation under projected future load without any intervention.")

        bs = data.get("base_summary", {})
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(card_html("Grid Stress Score", f"{bs.get('grid_stress_score',0):.0f}", "Higher → more violations"), unsafe_allow_html=True)
        c2.markdown(card_html("Line Overloads", str(bs.get('total_line_overloads',0)), "Total across 24 hours"), unsafe_allow_html=True)
        c3.markdown(card_html("Transformer Overloads", str(bs.get('total_transformer_overloads',0)), "Total across 24 hours"), unsafe_allow_html=True)
        c4.markdown(card_html("Undervoltage Events", str(bs.get('total_undervoltage_buses',0)), "Below 0.95 per-unit"), unsafe_allow_html=True)

        base_results = data.get("base_results", [])
        if base_results:
            st.markdown(f'<div class="sub-head">Hourly Violation Breakdown</div>', unsafe_allow_html=True)
            st.caption("Stacked equipment overloads and voltage violations at each hour.")
            br_df = pd.DataFrame(base_results)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=br_df["time"], y=br_df["num_overloaded_lines"], name="Line Overloads", marker_color=C1))
            fig2.add_trace(go.Bar(x=br_df["time"], y=br_df["num_overloaded_transformers"], name="Transformer Overloads", marker_color=C2))
            fig2.add_trace(go.Bar(x=br_df["time"], y=br_df["undervoltage_buses"], name="Undervoltage", marker_color=C_RED))
            fig2.update_layout(barmode="stack", height=270, margin=dict(t=10,b=30),
                                xaxis_title="Hour of Day", yaxis_title="Count",
                                plot_bgcolor="white", paper_bgcolor="white",
                                legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
                                font=dict(family="Arial", size=10))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown(f'<div class="sub-head">Feeder Topology</div>', unsafe_allow_html=True)
        st.caption("IEEE 123-bus test feeder. Hover over nodes for details.")
        grid_fig = render_grid_map()
        if grid_fig:
            st.plotly_chart(grid_fig, use_container_width=True)

    # ═══ PROFILES ═════════════════════════════════════════════════════════════
    with tab_profiles:
        st.markdown('<div class="sec-head">24-Hour Load Profiles</div>', unsafe_allow_html=True)
        st.caption("Synthetic demand and generation curves shaped by scenario selections, scaled by planning horizon.")

        profiles = data.get("profiles", {})
        if profiles:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=profiles["time"], y=profiles["feeder_mult"], name="Feeder Load Multiplier",
                                       line=dict(width=2.5, color=C_DARK), fill='tozeroy', fillcolor='rgba(45,45,45,0.04)'))
            fig3.add_trace(go.Scatter(x=profiles["time"], y=profiles["ev_mw"], name="EV Demand (MW)",
                                       line=dict(width=2.5, color=C1), fill='tozeroy', fillcolor='rgba(216,86,4,0.06)'))
            fig3.add_trace(go.Scatter(x=profiles["time"], y=profiles["solar_mw"], name="Solar Generation (MW)",
                                       line=dict(width=2.5, color=C_GREEN, dash="dot")))
            fig3.add_trace(go.Scatter(x=profiles["time"], y=profiles["dc_mw"], name="Data Center (MW)",
                                       line=dict(width=2.5, color=C_RED, dash="dash")))
            fig3.update_layout(height=300, margin=dict(t=10,b=30), xaxis_title="Hour of Day", yaxis_title="Value",
                                plot_bgcolor="white", paper_bgcolor="white",
                                legend=dict(orientation="h", y=1.05, x=0.5, xanchor="center"),
                                font=dict(family="Arial", size=10))
            st.plotly_chart(fig3, use_container_width=True)

            st.markdown(f'''<div class="info-box"><div style="font:400 0.82rem Arial;color:{C_DARK};line-height:1.8;">
                • <b style="color:{C1};">Feeder Multiplier</b> scales all existing loads (morning and evening peaks, 3% annual growth)<br>
                • <b style="color:{C1};">EV Demand</b> peaks 19:00–22:00 reflecting residential charging patterns (EIA AEO 2024)<br>
                • <b style="color:{C1};">Solar Generation</b> bell curve sunrise to sunset, reduces net demand at midday (SEIA 2024)<br>
                • <b style="color:{C1};">Data Center</b> near-constant baseload at 97% utilization (DOE Grid Deployment Office 2024)
            </div></div>''', unsafe_allow_html=True)

    # ═══ MEMO ═════════════════════════════════════════════════════════════════
    with tab_memo:
        st.markdown('<div class="sec-head">Planning Decision Memo</div>', unsafe_allow_html=True)
        memo = data.get("memo", "")
        if memo:
            st.markdown(memo)

        st.markdown(f'<div class="sub-head">Agent Workflow Log</div>', unsafe_allow_html=True)
        for cp in data.get("checkpoints", []):
            icon = "✅" if not cp.get("requires_approval") else "⚠️"
            st.markdown(f'''<div class="agent-row done"><span style="font-size:1rem;">{icon}</span>
                <div><div class="name">{cp["step"].replace("_"," ").title()}</div><div class="detail">{cp["message"]}</div></div></div>''', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄  Start New Study"):
        st.session_state.study_data = None
        st.session_state.running = False
        st.rerun()

elif not st.session_state.running:
    # Landing
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.markdown(f'''<div style="margin-top:20px;">
            <div style="display:flex;gap:12px;margin-bottom:20px;">
                <div class="card" style="flex:1;"><div class="lbl" style="color:{C1};">Step 1</div><div class="val">Configure</div><div class="sub">Select growth scenarios</div></div>
                <div class="card" style="flex:1;border-left-color:{C2};"><div class="lbl" style="color:{C2};">Step 2</div><div class="val">Analyze</div><div class="sub">6 AI agents evaluate options</div></div>
                <div class="card" style="flex:1;border-left-color:{C3};"><div class="lbl" style="color:{C3};">Step 3</div><div class="val">Decide</div><div class="sub">Multi-criteria ranked solutions</div></div>
            </div>
        </div>''', unsafe_allow_html=True)
    with col_r:
        st.caption("Configure parameters in the sidebar and click **Run Study**.")

    st.markdown(f'<div class="sub-head">IEEE 123-Bus Test Feeder</div>', unsafe_allow_html=True)
    st.caption("Hover over nodes for details. Color indicates asset type.")
    grid_fig = render_grid_map()
    if grid_fig:
        st.plotly_chart(grid_fig, use_container_width=True)
