"""
FeederIQ – Streamlit Frontend
Full-featured UI with all scenario options, profile charts, violation summary,
ranked portfolios table, before/after comparison, and decision memo.
"""
import requests
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="FeederIQ – Distribution Planning", layout="wide")
st.title("⚡ FeederIQ – Agentic Distribution Planning")
st.markdown("Non-wires alternative prioritization for electric distribution planning")

# ─── Sidebar: Scenario Configuration ──────────────────────────────────────────
st.sidebar.header("📋 Scenario Configuration")

# Fetch options from backend
try:
    opts = requests.get(f"{API_URL}/options", timeout=5).json()
except Exception:
    opts = {
        "planning_horizons": ["6m", "12m", "18m", "3yr", "5yr"],
        "ev_levels": ["Low", "Base", "High"],
        "solar_levels": ["Low", "Base", "High"],
        "dc_levels": ["Low", "Moderate", "High"],
        "dc_timelines": ["6m", "12m", "18m"],
    }

st.sidebar.subheader("Planning Horizon")
horizon = st.sidebar.selectbox("Horizon", opts["planning_horizons"], index=1)

st.sidebar.subheader("EV Growth")
ev_level = st.sidebar.selectbox("EV adoption level", opts["ev_levels"], index=1)

st.sidebar.subheader("Solar Adoption")
solar_level = st.sidebar.selectbox("Solar adoption level", opts["solar_levels"], index=1)

st.sidebar.subheader("Data Center")
dc_level = st.sidebar.selectbox("Data center size", opts["dc_levels"], index=1)
dc_timeline = st.sidebar.selectbox("Data center timeline", opts["dc_timelines"], index=1)

st.sidebar.subheader("Study Parameters")
max_portfolios = st.sidebar.slider("Max portfolios to evaluate", 10, 120, 60, step=10)
max_active = st.sidebar.slider("Max active measures per portfolio", 1, 5, 3)

st.sidebar.markdown("---")
run_button = st.sidebar.button("🚀 Run Study", type="primary", use_container_width=True)

# ─── Main Content ─────────────────────────────────────────────────────────────
if run_button:
    with st.spinner("Running FeederIQ agents... (scenario → simulation → constraint → NWA → capex → recommendation)"):
        payload = {
            "horizon_label": horizon,
            "ev_level": ev_level,
            "solar_level": solar_level,
            "dc_level": dc_level,
            "dc_timeline_label": dc_timeline,
            "max_active_measures": max_active,
            "max_portfolios": max_portfolios,
        }
        try:
            resp = requests.post(f"{API_URL}/study", json=payload, timeout=300)
            resp.raise_for_status()
            data = resp.json()
        except requests.exceptions.HTTPError as e:
            st.error(f"Study failed: {e.response.text}")
            st.stop()
        except Exception as e:
            st.error(f"Connection failed: {e}")
            st.stop()

    st.session_state["study_data"] = data
    st.success("Study complete!")

# ─── Display Results ──────────────────────────────────────────────────────────
if "study_data" in st.session_state:
    data = st.session_state["study_data"]

    # Checkpoints / Agent Steps
    st.subheader("🤖 Agent Workflow Steps")
    for cp in data.get("checkpoints", []):
        icon = "✅" if not cp.get("requires_approval") else "⚠️"
        st.info(f"{icon} **{cp['step']}**: {cp['message']}")

    # Profiles
    st.subheader("📊 24-Hour Load Profiles")
    profiles = data.get("profiles", {})
    if profiles:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=profiles["time"], y=profiles["feeder_mult"], name="Feeder Load Mult", line=dict(width=2)))
        fig.add_trace(go.Scatter(x=profiles["time"], y=profiles["ev_mw"], name="EV (MW)", line=dict(width=2)))
        fig.add_trace(go.Scatter(x=profiles["time"], y=profiles["solar_mw"], name="Solar (MW)", line=dict(width=2, dash="dot")))
        fig.add_trace(go.Scatter(x=profiles["time"], y=profiles["dc_mw"], name="Data Center (MW)", line=dict(width=2, dash="dash")))
        fig.update_layout(xaxis_title="Hour", yaxis_title="Value", height=350, margin=dict(t=30))
        st.plotly_chart(fig, use_container_width=True)

    # Baseline Violations
    st.subheader("🔴 Baseline Violation Summary")
    bs = data.get("base_summary", {})
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Grid Stress Score", f"{bs.get('grid_stress_score', 0):.0f}")
    col2.metric("Undervoltage Buses", bs.get("total_undervoltage_buses", 0))
    col3.metric("Line Overloads", bs.get("total_line_overloads", 0))
    col4.metric("Transformer Overloads", bs.get("total_transformer_overloads", 0))

    col5, col6, col7, col8 = st.columns(4)
    col5.metric("Worst Vmin (pu)", f"{bs.get('worst_vmin', 0):.4f}")
    col6.metric("Worst Vmax (pu)", f"{bs.get('worst_vmax', 0):.4f}")
    col7.metric("Overvoltage Buses", bs.get("total_overvoltage_buses", 0))
    col8.metric("Convergence Failures", bs.get("convergence_failures", 0))

    # Hourly violation chart
    base_results = data.get("base_results", [])
    if base_results:
        st.subheader("📈 Hourly Violations (Baseline)")
        br_df = pd.DataFrame(base_results)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=br_df["time"], y=br_df["undervoltage_buses"], name="Undervoltage"))
        fig2.add_trace(go.Bar(x=br_df["time"], y=br_df["num_overloaded_lines"], name="Line Overloads"))
        fig2.add_trace(go.Bar(x=br_df["time"], y=br_df["num_overloaded_transformers"], name="Xfmr Overloads"))
        fig2.update_layout(barmode="stack", height=300, margin=dict(t=30))
        st.plotly_chart(fig2, use_container_width=True)

    # Top Recommendation
    st.subheader("🏆 Top Recommendation")
    top = data.get("top_recommendation", {})
    if top:
        nwa_badge = "✅ NWA resolves all violations" if data.get("nwa_resolved_all") else ""
        st.markdown(f"**{top.get('portfolio_name', 'N/A')}** — Final Score: **{top.get('final_score', 0)}** {nwa_badge}")

        rc1, rc2, rc3, rc4 = st.columns(4)
        rc1.metric("Technical Improvement", f"{top.get('technical_improvement_pct', 0):.1f}%")
        rc2.metric("Cost Score", f"{top.get('cost_score', 0):.1f}/10")
        rc3.metric("Feasibility", f"{top.get('feasibility_score', 0):.1f}/10")
        rc4.metric("Deployment Speed", f"{top.get('deployment_score', 0):.1f}/10")

    # Second best
    second = data.get("second_best", {})
    if second:
        st.markdown(f"**Runner-up**: {second.get('portfolio_name', 'N/A')} — Score: {second.get('final_score', 0)}")

    # Full Ranking Table
    st.subheader("📋 Portfolio Ranking")
    ranking = data.get("ranking", [])
    if ranking:
        rank_df = pd.DataFrame(ranking)
        display_cols = [c for c in ["portfolio_name", "final_score", "technical_improvement_pct",
                                     "cost_score", "feasibility_score", "deployment_score",
                                     "Battery", "ManagedCharging", "PhasedInterconnection",
                                     "DemandTariff", "TransformerUpgrade"] if c in rank_df.columns]
        st.dataframe(rank_df[display_cols], use_container_width=True, height=400)

    # Decision Memo
    st.subheader("📝 Decision Memo")
    memo = data.get("memo", "")
    if memo:
        st.markdown(memo)

    # Before/After comparison
    st.subheader("🔄 Before / After (Top Portfolio)")
    if top and base_results:
        ba_col1, ba_col2 = st.columns(2)
        with ba_col1:
            st.markdown("**Before (Baseline)**")
            st.metric("Stress Score", f"{bs.get('grid_stress_score', 0):.0f}")
            st.metric("Undervoltage", bs.get("total_undervoltage_buses", 0))
            st.metric("Line Overloads", bs.get("total_line_overloads", 0))
        with ba_col2:
            st.markdown("**After (Top Portfolio)**")
            impr = top.get("technical_improvement_pct", 0)
            after_stress = bs.get("grid_stress_score", 0) * (1 - impr / 100)
            st.metric("Stress Score", f"{after_stress:.0f}", delta=f"-{impr:.1f}%")
            if data.get("nwa_resolved_all"):
                st.metric("Violations", "0", delta="Resolved")
            else:
                st.metric("Reduction", f"{impr:.1f}%")

else:
    st.info("Configure your scenario in the sidebar and click **Run Study** to begin.")
    st.markdown("""
    ### How FeederIQ Works
    1. **Scenario Agent** – Converts your selections into numeric growth assumptions
    2. **Simulation Agent** – Runs 24-hour power flow on IEEE 123-bus feeder
    3. **Constraint Agent** – Detects voltage violations and equipment overloads
    4. **NWA Agent** – Evaluates non-wires alternatives first (batteries, managed charging, tariffs)
    5. **Capex Agent** – Only evaluates traditional capex if NWA is insufficient
    6. **Recommendation Agent** – Ranks all options and generates decision memo

    Human-in-the-loop checkpoints are shown after constraint analysis and NWA evaluation.
    """)
