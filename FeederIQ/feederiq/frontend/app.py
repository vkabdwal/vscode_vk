"""
FeederIQ – Streamlit Frontend (R3)
"""
import re
import time
import base64
import json
from html import escape
from pathlib import Path
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

    .top-bar {{ display: flex; align-items: center; justify-content: space-between; padding: 10px 0 12px 0; border-bottom: 3px solid {C1}; margin-bottom: 18px; }}
    .top-bar .name {{ color:{C_DARK}; font: 700 1.05rem Arial,sans-serif; }}
    .top-bar .logo {{ height: 50px; }}

    .sec-head {{ font: 700 1.1rem Arial,sans-serif; color:{C_DARK}; margin: 20px 0 8px; padding-bottom: 5px; border-bottom: 2px solid {C1}; }}
    .sub-head {{ font: 700 0.88rem Arial,sans-serif; color:{C_DARK}; margin: 14px 0 5px; }}

    .card {{ background:white; border-radius:8px; padding:14px 16px; margin-bottom:8px; box-shadow:0 1px 3px rgba(0,0,0,0.05); border:1px solid #EFEFEF; border-left:4px solid {C1}; }}
    .card .lbl {{ font: 600 0.68rem Arial,sans-serif; color:{C_GREY}; text-transform:uppercase; letter-spacing:0.3px; }}
    .card .val {{ font: 700 1.3rem Arial,sans-serif; color:{C_DARK}; margin-top:2px; }}
    .card .sub {{ font: 400 0.78rem Arial,sans-serif; color:{C_GREY}; margin-top:2px; }}

    .step-cards {{ display: flex; gap: 12px; margin-bottom: 20px; }}
    .step-cards .card {{ flex: 1; }}

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

    .memo-area h1 {{ font-size: 1.05rem; font-weight:700; color:{C_DARK}; }}
    .memo-area h2 {{ font-size: 0.92rem; font-weight:700; color:{C_DARK}; }}
    .memo-area p {{ font-size: 0.85rem; }}
    .memo-area table {{
        font-size: 0.82rem;
        width: 100%;
        border-collapse: collapse;
        border: 1px solid #E7D6C7;
        margin: 10px 0;
        background: #FFFEFC;
    }}
    .memo-area th {{
        background: #FFF2E5;
        color: {C_DARK};
        border: 1px solid #E7D6C7;
        padding: 8px 10px;
        text-align: center;
        font: 700 0.72rem Arial,sans-serif;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }}
    .memo-area td {{
        border: 1px solid #EDE2D8;
        padding: 8px 10px;
        color: {C_DARK};
        vertical-align: top;
        font: 400 0.8rem Arial,sans-serif;
    }}
    .memo-area li {{ font-size: 0.82rem; }}

    .lvl-tip {{ position: relative; display: inline-block; margin-left: 6px; }}
    .lvl-tip summary {{
        list-style: none;
        cursor: pointer;
        color: {C1};
        font: 700 0.72rem Arial,sans-serif;
        display: inline;
        user-select: none;
    }}
    .lvl-tip summary::-webkit-details-marker {{ display: none; }}
    .lvl-tip[open] > div {{
        position: absolute;
        z-index: 10;
        top: 16px;
        left: -8px;
        width: 350px;
        max-width: 52vw;
        background: #FFFFFF;
        border: 1px solid #E6D6C8;
        border-left: 3px solid {C1};
        border-radius: 8px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        padding: 9px 10px;
        color: {C_DARK};
        font: 400 0.74rem Arial,sans-serif;
        line-height: 1.45;
        white-space: normal;
    }}

    /* Defensive guard: ensure only active tab panel is visible. */
    [data-baseweb="tab-panel"][aria-hidden="true"],
    [data-baseweb="tab-panel"][hidden],
    [role="tabpanel"][aria-hidden="true"],
    [role="tabpanel"][hidden] {{
        display: none !important;
    }}
</style>
""", unsafe_allow_html=True)


def card_html(label, value, sub=""):
    sub_h = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="card"><div class="lbl">{label}</div><div class="val">{value}</div>{sub_h}</div>'


def score_bar_html(label, value, max_val=10, tooltip=""):
    pct = min(100, (value / max_val) * 100)
    # Color the bar based on score value
    if value >= 8:
        bar_color = "#1B8C3A"
    elif value >= 6:
        bar_color = "#7CB342"
    elif value >= 4:
        bar_color = "#E88D14"
    else:
        bar_color = "#C92A2A"
    tip_html = f' title="{tooltip}"' if tooltip else ""
    return f'''<div class="score-row"{tip_html}>
        <div class="lbl">{label}</div>
        <div class="bar"><div class="fill" style="width:{pct}%;background:{bar_color};"></div></div>
        <div class="num" style="color:{bar_color};">{value:.1f} / 10</div>
    </div>'''


INTERVENTION_KEYS = ["ManagedCharging", "PhasedInterconnection", "DemandTariff", "Battery", "TransformerUpgrade"]
INTERVENTION_LABELS = {
    "ManagedCharging": "Managed EV Charging",
    "PhasedInterconnection": "Staged Load Connection",
    "DemandTariff": "Dynamic Tariffs",
    "Battery": "Battery Storage",
    "TransformerUpgrade": "Capacity Upgrade",
}


def _level_label(level):
    lvl = int(level or 0)
    if lvl >= 100:
        return "High (100)"
    if lvl >= 66:
        return "Medium (66)"
    if lvl >= 33:
        return "Low (33)"
    return "Off (0)"


def _active_interventions(portfolio):
    active = []
    for k in INTERVENTION_KEYS:
        lvl = int(portfolio.get(k, 0) or 0)
        if lvl > 0:
            active.append({
                "key": k,
                "label": INTERVENTION_LABELS.get(k, k),
                "level": lvl,
                "level_label": _level_label(lvl),
            })
    return active


@st.cache_data(show_spinner=False, ttl=3600)
def _load_strategy_docs():
    docs_dir = Path(__file__).resolve().parent.parent.parent / "docs"
    doc_names = ["Intervention explainer.md", "assumptions_rationale.md", "FeederIQ_reference.md"]
    out = {}
    for name in doc_names:
        p = docs_dir / name
        out[name] = p.read_text(encoding="utf-8") if p.exists() else ""
    return out


def _extract_json_dict(raw_text):
    if not raw_text:
        return {}
    txt = raw_text.strip()
    txt = re.sub(r'^```(?:json)?\s*', '', txt, flags=re.IGNORECASE)
    txt = re.sub(r'\s*```$', '', txt)
    try:
        parsed = json.loads(txt)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        pass
    m = re.search(r'\{.*\}', txt, flags=re.DOTALL)
    if not m:
        return {}
    try:
        parsed = json.loads(m.group(0))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _fallback_implementation_pack(selected):
    active = _active_interventions(selected)
    defaults = {
        "ManagedCharging": {
            "operating_mechanism": "Shift EV charging from evening peak to off-peak window.",
            "field_implementation": "Enroll EV customers, integrate EVSE control, and set dispatch schedules.",
            "timeline": "3-9 months",
            "dependencies": "AMI interval data, EVSE communications, customer enrollment.",
            "kpis": "Peak EV MW reduction, evening transformer loading, participation rate.",
            "risks": "Customer opt-out and limited controllable charger coverage.",
        },
        "PhasedInterconnection": {
            "operating_mechanism": "Stage data center energization to defer near-term peak stress.",
            "field_implementation": "Revise interconnection agreement with phased commissioning milestones.",
            "timeline": "4-12 months",
            "dependencies": "Customer contracting, interconnection studies, metering checkpoints.",
            "kpis": "Connected MW vs plan, feeder peak delta, deferred capex value.",
            "risks": "Commercial schedule pressure from large-load customer.",
        },
        "DemandTariff": {
            "operating_mechanism": "Use tariff signals to reduce demand in critical peak periods.",
            "field_implementation": "Implement TOU/critical-peak tariff, customer comms, and billing updates.",
            "timeline": "4-14 months",
            "dependencies": "Regulatory approval, billing configuration, customer response analytics.",
            "kpis": "Peak period kW reduction, event response rate, bill impact acceptance.",
            "risks": "Regulatory lead time and uncertain elasticity response.",
        },
        "Battery": {
            "operating_mechanism": "Charge at lower-stress hours and discharge during evening peak.",
            "field_implementation": "Deploy feeder/distributed BESS with dispatch policy and telemetry.",
            "timeline": "6-18 months",
            "dependencies": "Siting, procurement, interconnection, controls commissioning.",
            "kpis": "Peak shaving MW, voltage support, discharge availability.",
            "risks": "Permitting lead time and performance degradation assumptions.",
        },
        "TransformerUpgrade": {
            "operating_mechanism": "Increase thermal capacity headroom through conventional reinforcement.",
            "field_implementation": "Engineer, procure, and replace constrained transformer assets.",
            "timeline": "12-36 months",
            "dependencies": "Equipment lead time, outage scheduling, field construction.",
            "kpis": "Thermal margin increase, overload-hour reduction, SAIDI impact.",
            "risks": "Long lead times, outage complexity, and capex approval cycle.",
        },
    }

    rows = []
    for item in active:
        d = defaults.get(item["key"], {})
        rows.append({
            "intervention": item["label"],
            "level": item["level_label"],
            "operating_mechanism": d.get("operating_mechanism", ""),
            "field_implementation": d.get("field_implementation", ""),
            "timeline": d.get("timeline", ""),
            "dependencies": d.get("dependencies", ""),
            "kpis": d.get("kpis", ""),
            "risks": d.get("risks", ""),
        })

    if not rows:
        rows.append({
            "intervention": "No active intervention",
            "level": "Off (0)",
            "operating_mechanism": "No portfolio measure selected.",
            "field_implementation": "No field deployment actions required.",
            "timeline": "N/A",
            "dependencies": "N/A",
            "kpis": "N/A",
            "risks": "Baseline risk remains unchanged.",
        })

    return {
        "summary": f"{selected.get('portfolio_name', 'Selected portfolio')} is delivered through a phased utility program with operational controls, field governance, and measurable reliability KPIs.",
        "implementation_rows": rows,
        "governance_rows": [
            {
                "workstream": "System Planning",
                "owner": "Distribution Planning",
                "deliverable": "Implementation package and feeder impact validation",
                "timing": "Weeks 0-4",
            },
            {
                "workstream": "Regulatory / Commercial",
                "owner": "Regulatory + Key Accounts",
                "deliverable": "Tariff/interconnection approvals and customer commitments",
                "timing": "Weeks 2-10",
            },
            {
                "workstream": "Operations",
                "owner": "Grid Operations",
                "deliverable": "Control activation, KPI monitoring, and monthly review",
                "timing": "Go-live + ongoing",
            },
        ],
    }


@st.cache_data(show_spinner=False, ttl=1800)
def _generate_implementation_pack(selected, scenario, base_summary, docs_bundle):
    fallback = _fallback_implementation_pack(selected)
    active = _active_interventions(selected)
    if not active:
        return fallback

    try:
        from feederiq.backend.llm_client import invoke_llm
    except Exception:
        return fallback

    intervention_doc = (docs_bundle.get("Intervention explainer.md", "") or "")[:14000]
    assumptions_doc = (docs_bundle.get("assumptions_rationale.md", "") or "")[:5000]
    reference_doc = (docs_bundle.get("FeederIQ_reference.md", "") or "")[:5000]

    system_prompt = """
You are a PwC electric utility implementation consultant.
Produce concise, boardroom-quality implementation guidance as STRICT JSON.
Return only a JSON object with keys:
- summary: string
- implementation_rows: list of objects with keys [intervention, level, operating_mechanism, field_implementation, timeline, dependencies, kpis, risks]
- governance_rows: list of objects with keys [workstream, owner, deliverable, timing]
Keep wording practical, specific, and grounded in the provided references.
Do not use markdown.
"""

    user_context = {
        "scenario": scenario,
        "baseline": {
            "grid_stress_score": base_summary.get("grid_stress_score", 0),
            "line_overloads": base_summary.get("total_line_overloads", 0),
            "transformer_overloads": base_summary.get("total_transformer_overloads", 0),
        },
        "selected_portfolio": selected,
        "active_interventions": active,
        "reference_docs": {
            "intervention_explainer": intervention_doc,
            "assumptions": assumptions_doc,
            "project_reference": reference_doc,
        },
    }

    raw = invoke_llm(system_prompt, json.dumps(user_context, indent=2), max_tokens=1000)
    parsed = _extract_json_dict(raw)
    if not parsed:
        return fallback

    rows = parsed.get("implementation_rows") if isinstance(parsed.get("implementation_rows"), list) else []
    gov_rows = parsed.get("governance_rows") if isinstance(parsed.get("governance_rows"), list) else []
    if not rows:
        return fallback

    clean_rows = []
    required_keys = ["intervention", "level", "operating_mechanism", "field_implementation", "timeline", "dependencies", "kpis", "risks"]
    for row in rows[:6]:
        if not isinstance(row, dict):
            continue
        clean_rows.append({k: str(row.get(k, "")).strip() for k in required_keys})
    if not clean_rows:
        return fallback

    clean_gov_rows = []
    for row in gov_rows[:4]:
        if not isinstance(row, dict):
            continue
        clean_gov_rows.append({
            "workstream": str(row.get("workstream", "")).strip(),
            "owner": str(row.get("owner", "")).strip(),
            "deliverable": str(row.get("deliverable", "")).strip(),
            "timing": str(row.get("timing", "")).strip(),
        })

    return {
        "summary": str(parsed.get("summary", fallback["summary"])).strip() or fallback["summary"],
        "implementation_rows": clean_rows,
        "governance_rows": clean_gov_rows or fallback["governance_rows"],
    }


def _intervention_key_from_label(label):
    norm = re.sub(r"[^a-z0-9]+", "", str(label or "").lower())
    mapping = {
        "managedevcharging": "ManagedCharging",
        "stagedloadconnection": "PhasedInterconnection",
        "dynamictariffs": "DemandTariff",
        "batterystorage": "Battery",
        "capacityupgrade": "TransformerUpgrade",
        "managedcharging": "ManagedCharging",
        "phasedinterconnection": "PhasedInterconnection",
        "demandtariff": "DemandTariff",
        "battery": "Battery",
        "transformerupgrade": "TransformerUpgrade",
    }
    # Exact match first
    if norm in mapping:
        return mapping[norm]
    # Substring/prefix match for LLM-generated labels with extra text (e.g. "capacityupgradelow")
    for key, val in mapping.items():
        if norm.startswith(key) or key.startswith(norm):
            return val
    # Partial keyword match
    keyword_map = {
        "capacity": "TransformerUpgrade",
        "transformer": "TransformerUpgrade",
        "battery": "Battery",
        "storage": "Battery",
        "managedcharging": "ManagedCharging",
        "evcharging": "ManagedCharging",
        "staged": "PhasedInterconnection",
        "phased": "PhasedInterconnection",
        "interconnection": "PhasedInterconnection",
        "tariff": "DemandTariff",
        "dynamic": "DemandTariff",
        "demand": "DemandTariff",
    }
    for keyword, val in keyword_map.items():
        if keyword in norm:
            return val
    return ""


def _fallback_intervention_level_guide():
    return {
        "ManagedCharging": {
            "label": "Managed EV Charging",
            "low": "33: Shift ~15% of evening EV charging (18:00-21:00) to late-night window (00:00-05:00).",
            "medium": "66: Shift ~30% of evening EV charging to late-night window with stronger control participation.",
            "high": "100: Shift ~50% of evening EV charging; strongest modeled EV peak reduction.",
            "implementation": "Programmatic EV control through utility/aggregator dispatch and customer enrollment.",
        },
        "PhasedInterconnection": {
            "label": "Staged Load Connection",
            "low": "33: Reduce near-term data center load by ~20% via staged energization.",
            "medium": "66: Reduce near-term data center load by ~40%; significant deferral effect.",
            "high": "100: Reduce near-term data center load by ~60%; aggressive commissioning phasing.",
            "implementation": "Interconnection agreement milestones tied to phased commissioning and feeder readiness.",
        },
        "DemandTariff": {
            "label": "Dynamic Tariffs",
            "low": "33: Reduce feeder demand ~3% during peak window (17:00-20:00).",
            "medium": "66: Reduce feeder demand ~6% during peak window with stronger price signal.",
            "high": "100: Reduce feeder demand ~10% during peak window; highest modeled tariff response.",
            "implementation": "TOU/critical-peak tariff design, customer communication, and billing analytics.",
        },
        "Battery": {
            "label": "Battery Storage",
            "low": "33: Evening feeder reduction ~4%; midday charging increase ~1%.",
            "medium": "66: Evening feeder reduction ~8%; midday charging increase ~2%.",
            "high": "100: Evening feeder reduction ~12%; midday charging increase ~3%.",
            "implementation": "Feeder/distributed BESS dispatch: charge lower-stress hours, discharge evening peak.",
        },
        "TransformerUpgrade": {
            "label": "Capacity Upgrade",
            "low": "33: Effective transformer capacity x1.10 and line headroom x1.08.",
            "medium": "66: Effective transformer capacity x1.20 and line headroom x1.15.",
            "high": "100: Effective transformer capacity x1.30 and line headroom x1.25.",
            "implementation": "Conventional reinforcement via targeted asset replacement and thermal headroom expansion.",
        },
    }


@st.cache_data(show_spinner=False, ttl=1800)
def _generate_intervention_level_guide(docs_bundle):
    fallback = _fallback_intervention_level_guide()
    try:
        from feederiq.backend.llm_client import invoke_llm
    except Exception:
        return fallback

    system_prompt = """
You are a utility implementation expert.
Return STRICT JSON only in this shape:
{
  "ManagedCharging": {"label": "", "low": "", "medium": "", "high": "", "implementation": ""},
  "PhasedInterconnection": {...},
  "DemandTariff": {...},
  "Battery": {...},
  "TransformerUpgrade": {...}
}
Use the provided intervention explainer as source of truth and keep each field concise.
"""

    context = {
        "intervention_reference": (docs_bundle.get("Intervention explainer.md", "") or "")[:16000],
        "assumptions_reference": (docs_bundle.get("assumptions_rationale.md", "") or "")[:4000],
    }
    raw = invoke_llm(system_prompt, json.dumps(context, indent=2), max_tokens=1800)
    parsed = _extract_json_dict(raw)
    if not parsed:
        return fallback

    out = {}
    required = ["label", "low", "medium", "high", "implementation"]
    for k in ["ManagedCharging", "PhasedInterconnection", "DemandTariff", "Battery", "TransformerUpgrade"]:
        row = parsed.get(k)
        if not isinstance(row, dict):
            out[k] = fallback[k]
            continue
        clean = {rk: str(row.get(rk, fallback[k].get(rk, ""))).strip() for rk in required}
        out[k] = clean
    return out


def _fallback_implementation_summary(selected, scenario, base_summary):
    return (
        f"For the {scenario.get('horizon_label', 'planning')} horizon, the selected portfolio "
        f"{selected.get('portfolio_name', 'N/A')} is positioned to address a baseline grid stress score of "
        f"{base_summary.get('grid_stress_score', 0):.0f} through staged controls and operational governance, "
        "prioritizing near-term reliability relief while preserving optionality for additional reinforcement if growth materializes faster than forecast."
    )


@st.cache_data(show_spinner=False, ttl=1800)
def _generate_implementation_summary(selected, scenario, base_summary, implementation_pack, docs_bundle):
    fallback = _fallback_implementation_summary(selected, scenario, base_summary)
    try:
        from feederiq.backend.llm_client import invoke_llm
    except Exception:
        return fallback

    system_prompt = """
You are a PwC distribution implementation lead.
Write one executive paragraph (90-140 words) summarizing implementation approach, dependencies, and expected reliability effect.
Use only the provided scenario inputs, selected portfolio details, implementation rows, and reference excerpts.
Do NOT speculate, do NOT add open questions, and do NOT mention unknowns.
Use plain text only (no bullets, no markdown).
"""

    context = {
        "selected_portfolio": selected,
        "scenario": scenario,
        "baseline": base_summary,
        "implementation_rows": implementation_pack.get("implementation_rows", []),
        "implementation_guidance": implementation_pack.get("summary", ""),
        "intervention_reference": (docs_bundle.get("Intervention explainer.md", "") or "")[:8000],
    }
    raw = invoke_llm(system_prompt, json.dumps(context, indent=2), max_tokens=350)
    text = (raw or "").strip()
    if not text:
        return fallback
    text = re.sub(r"\s+", " ", text)
    return text


def _fallback_selected_memo(selected, runner_up, scenario, base_summary, ranking_preview, implementation_pack):
    severity = "Critical" if base_summary.get("grid_stress_score", 0) > 3000 else (
        "High" if base_summary.get("grid_stress_score", 0) > 1000 else (
            "Moderate" if base_summary.get("grid_stress_score", 0) > 300 else "Low"
        )
    )

    lines = []
    lines.append("## Executive Summary")
    lines.append(implementation_pack.get("summary", ""))
    lines.append("")
    lines.append("## Planning Scenario")
    lines.append("| Parameter | Value |")
    lines.append("|---|---|")
    lines.append(f"| Planning Horizon | {scenario.get('horizon_label', 'N/A')} |")
    lines.append(f"| EV Growth | {scenario.get('ev_level', 'N/A')} |")
    lines.append(f"| Solar Adoption | {scenario.get('solar_level', 'N/A')} |")
    lines.append(f"| Data Center Load | {scenario.get('dc_level', 'N/A')} |")
    lines.append("")
    lines.append("## Baseline Assessment")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Grid Stress Score | {base_summary.get('grid_stress_score', 0):.0f} ({severity}) |")
    lines.append(f"| Line Overloads (24h) | {base_summary.get('total_line_overloads', 0)} |")
    lines.append(f"| Transformer Overloads (24h) | {base_summary.get('total_transformer_overloads', 0)} |")
    lines.append(f"| Undervoltage Events | {base_summary.get('total_undervoltage_buses', 0)} |")
    lines.append("")
    lines.append("## Selected Solution")
    lines.append(f"**{selected.get('portfolio_name', 'N/A')}**")
    lines.append("| Dimension | Score |")
    lines.append("|---|---|")
    lines.append(f"| Final Score | {selected.get('final_score', 0):.2f} / 10 |")
    lines.append(f"| Grid Relief | {selected.get('grid_relief_score', selected.get('technical_score', 0)):.1f} / 10 |")
    lines.append(f"| Cost Efficiency | {selected.get('cost_score', 0):.1f} / 10 |")
    lines.append(f"| Speed to Value | {selected.get('speed_to_value_score', 0):.1f} / 10 |")
    lines.append(f"| ESG Alignment | {selected.get('esg_score', 0):.1f} / 10 |")
    lines.append(f"| Technical Improvement | {selected.get('technical_improvement_pct', 0):.1f}% |")
    lines.append("")

    lines.append("## Alternative Options")
    lines.append("| Portfolio | Final Score | Grid Relief % |")
    lines.append("|---|---:|---:|")
    for row in ranking_preview[:5]:
        lines.append(f"| {row.get('portfolio_name', 'N/A')} | {row.get('final_score', 0):.2f} | {row.get('technical_improvement_pct', 0):.1f}% |")
    lines.append("")

    lines.append("## Real-World Implementation Plan")
    lines.append("| Intervention | Level | Field Implementation | Timeline | KPI |")
    lines.append("|---|---|---|---|---|")
    for row in implementation_pack.get("implementation_rows", []):
        lines.append(
            f"| {row.get('intervention', '')} | {row.get('level', '')} | {row.get('field_implementation', '')} | {row.get('timeline', '')} | {row.get('kpis', '')} |"
        )

    if runner_up:
        lines.append("")
        lines.append(f"Runner-up for governance consideration: **{runner_up.get('portfolio_name', 'N/A')}** at **{runner_up.get('final_score', 0):.2f}/10**.")

    return "\n".join(lines)


@st.cache_data(show_spinner=False, ttl=1800)
def _generate_selected_memo(selected, runner_up, scenario, base_summary, ranking_preview, implementation_pack, docs_bundle):
    fallback = _fallback_selected_memo(selected, runner_up, scenario, base_summary, ranking_preview, implementation_pack)

    try:
        from feederiq.backend.llm_client import invoke_llm
    except Exception:
        return fallback

    system_prompt = """
You are a senior PwC distribution planning consultant writing a client-ready memo section.
Return Markdown only. Use a table-first style for all quantitative information.
Required sections in this exact order:
1) ## Executive Summary
2) ## Planning Scenario (table)
3) ## Baseline Assessment (table)
4) ## Selected Solution (table)
5) ## Alternative Options (table, top 5)
6) ## Real-World Implementation Plan (table)
Tone: concise, executive, implementation-ready.
Do not add a top-level title.
"""

    context = {
        "selected_portfolio": selected,
        "runner_up": runner_up or {},
        "scenario": scenario,
        "baseline": base_summary,
        "ranking_top5": ranking_preview[:5],
        "implementation_pack": implementation_pack,
        "intervention_reference": (docs_bundle.get("Intervention explainer.md", "") or "")[:12000],
    }

    raw = invoke_llm(system_prompt, json.dumps(context, indent=2), max_tokens=1200)
    text = (raw or "").strip()
    if not text or "## Executive Summary" not in text:
        return fallback
    return text


def _implementation_pack_html(pack, selected_name, level_guide=None, summary_text=""):
    level_guide = level_guide or _fallback_intervention_level_guide()
    rows_html = []
    for row in pack.get("implementation_rows", []):
        iv_key = _intervention_key_from_label(row.get("intervention", ""))
        guide = level_guide.get(iv_key, {})
        tip_low = escape(guide.get('low', 'N/A'))
        tip_med = escape(guide.get('medium', 'N/A'))
        tip_high = escape(guide.get('high', 'N/A'))
        tip_impl = escape(guide.get('implementation', 'N/A'))
        rows_html.append(
            "<tr>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #EDEDED;font:700 0.73rem Arial;color:{C_DARK};'>{escape(row.get('intervention', ''))} "
            "<details class='lvl-tip'><summary>ⓘ</summary>"
            f"<div><b>Low (33):</b> {tip_low}<br><b>Medium (66):</b> {tip_med}<br><b>High (100):</b> {tip_high}<br><b>Implementation Intent:</b> {tip_impl}</div>"
            "</details></td>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #EDEDED;font:600 0.71rem Arial;color:{C1};'>{escape(row.get('level', ''))}</td>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #EDEDED;font:400 0.73rem Arial;color:{C_DARK};'>{escape(row.get('field_implementation', ''))}</td>"
            f"<td style='padding:8px 10px;border-bottom:1px solid #EDEDED;font:400 0.73rem Arial;color:{C_DARK};'>{escape(row.get('timeline', ''))}</td>"
            "</tr>"
        )

    summary = summary_text or pack.get("summary", "")

    return f'''
    <div style="background:white;border-radius:10px;padding:15px 18px;margin:12px 0;border:1px solid #E9E2DB;border-top:3px solid {C1};box-shadow:0 1px 4px rgba(0,0,0,0.04);">
        <div style="font:700 0.9rem Arial;color:{C_DARK};margin-bottom:4px;">Implementation Blueprint: {escape(selected_name)}</div>
        <table style="width:100%;border-collapse:collapse;background:#FFFDFB;border:1px solid #EFE3D6;">
            <thead>
                <tr style="background:#FFF3E7;">
                    <th style="text-align:center;padding:8px 10px;font:700 0.68rem Arial;color:{C_DARK};text-transform:uppercase;letter-spacing:0.04em;">Intervention</th>
                    <th style="text-align:center;padding:8px 10px;font:700 0.68rem Arial;color:{C_DARK};text-transform:uppercase;letter-spacing:0.04em;">Level</th>
                    <th style="text-align:center;padding:8px 10px;font:700 0.68rem Arial;color:{C_DARK};text-transform:uppercase;letter-spacing:0.04em;">Field Implementation</th>
                    <th style="text-align:center;padding:8px 10px;font:700 0.68rem Arial;color:{C_DARK};text-transform:uppercase;letter-spacing:0.04em;">Timeline</th>
                </tr>
            </thead>
            <tbody>
                {''.join(rows_html)}
            </tbody>
        </table>
        <div style="margin-top:10px;background:#FFF8EF;border:1px solid #F2DDC8;border-left:3px solid {C1};border-radius:8px;padding:11px 12px;">
            <div style="font:700 0.76rem Arial;color:{C1};margin-bottom:5px;">Implementation Summary</div>
            <div style="font:400 0.8rem Arial;color:{C_DARK};line-height:1.65;">{escape(summary)}</div>
        </div>
    </div>
    '''


def parse_line_connections():
    """Parse line connections from master_lite.dss to get bus-to-bus edges."""
    from pathlib import Path
    dss_path = Path(__file__).resolve().parent.parent.parent / "ai_synthetic_data" / "master_lite.dss"
    edges = []
    if not dss_path.exists():
        return edges
    with open(dss_path) as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith("new line."):
                bus1_match = re.search(r'Bus1=(\S+)', line, re.IGNORECASE)
                bus2_match = re.search(r'Bus2=(\S+)', line, re.IGNORECASE)
                if bus1_match and bus2_match:
                    b1 = bus1_match.group(1).split('.')[0].lower().rstrip('r')
                    b2 = bus2_match.group(1).split('.')[0].lower().rstrip('r')
                    edges.append((b1, b2))
    return edges


@st.cache_data(show_spinner=False, ttl=3600)
def render_grid_map():
    """Render IEEE 123-bus feeder on a US street map (illustrative suburban placement)."""
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
    ev_buses = {"60", "83", "90", "92", "114"}
    solar_buses = {"66", "80", "92", "104", "110"}
    dc_bus = "67"

    # Illustrative placement: Apex, NC - typical US suburban distribution area
    ANCHOR_LAT = 35.7327
    ANCHOR_LON = -78.8503
    SPREAD_LAT = 0.022
    SPREAD_LON = 0.028

    # Normalize XY to lat/lon
    all_x = [v[0] for v in primary.values()]
    all_y = [v[1] for v in primary.values()]
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    x_span = x_max - x_min or 1
    y_span = y_max - y_min or 1

    geo = {}
    for bus, (x, y) in primary.items():
        norm_x = (x - x_min) / x_span - 0.5
        norm_y = (y - y_min) / y_span - 0.5
        geo[bus] = (ANCHOR_LAT + norm_y * SPREAD_LAT, ANCHOR_LON + norm_x * SPREAD_LON)

    edges = parse_line_connections()
    fig = go.Figure()

    # Draw ALL lines in ONE trace
    line_lats = []
    line_lons = []
    for b1, b2 in edges:
        if b1 in geo and b2 in geo:
            lat1, lon1 = geo[b1]
            lat2, lon2 = geo[b2]
            line_lats.extend([lat1, lat2, None])
            line_lons.extend([lon1, lon2, None])
    fig.add_trace(go.Scattermapbox(
        lat=line_lats, lon=line_lons,
        mode='lines', line=dict(color='#999999', width=1.2),
        hoverinfo='skip', showlegend=False
    ))

    # Categorize buses
    cat_order = [
        ("Data Center", {dc_bus}, "#8B0000", 20),
        ("EV + Solar", ev_buses & solar_buses, "#7B2D8B", 15),
        ("EV Charging", ev_buses - solar_buses, C1, 15),
        ("Solar PV", solar_buses - ev_buses, C_GREEN, 15),
    ]
    key_buses_set = ev_buses | solar_buses | {dc_bus}
    other_buses = set(geo.keys()) - key_buses_set

    # Regular buses - sized by load
    if other_buses:
        try:
            import opendssdirect as dss_lib
            master_path = Path(__file__).resolve().parent.parent.parent / "ai_synthetic_data" / "master_lite.dss"
            dss_lib.Basic.ClearAll()
            dss_lib.Text.Command(f"Compile [{master_path.as_posix()}]")
            dss_lib.Solution.Solve()
            bus_kw_ieee = {}
            for ln in dss_lib.Loads.AllNames():
                dss_lib.Loads.Name(ln)
                bus = dss_lib.CktElement.BusNames()[0].split('.')[0].lower()
                bus_kw_ieee[bus] = bus_kw_ieee.get(bus, 0) + dss_lib.Loads.kW()
            max_kw_ieee = max(bus_kw_ieee.values()) if bus_kw_ieee else 1
        except Exception:
            bus_kw_ieee = {}
            max_kw_ieee = 1

        bus_sizes_ieee = []
        for b in other_buses:
            kw = bus_kw_ieee.get(b.lower(), 0)
            bus_sizes_ieee.append(max(6, min(14, 6 + 8 * (kw / max_kw_ieee))) if max_kw_ieee > 0 else 6)

        other_list = list(other_buses)
        fig.add_trace(go.Scattermapbox(
            lat=[geo[b][0] for b in other_list],
            lon=[geo[b][1] for b in other_list],
            mode='markers',
            marker=dict(size=bus_sizes_ieee, color='#1565C0', opacity=0.7),
            text=[f"Bus {b}<br>{bus_kw_ieee.get(b.lower(), 0):.0f} kW" for b in other_list],
            hoverinfo='text', showlegend=False,
        ))

    # Key asset buses with legend
    for cat_name, bus_set, color, size in cat_order:
        valid = [b for b in bus_set if b in geo]
        if not valid:
            continue
        fig.add_trace(go.Scattermapbox(
            lat=[geo[b][0] for b in valid],
            lon=[geo[b][1] for b in valid],
            mode='markers+text',
            marker=dict(size=size, color=color),
            text=[b for b in valid],
            textposition='top center',
            textfont=dict(size=10, color=C_DARK, family='Arial'),
            hovertext=[f"<b>Bus {b}</b><br>{cat_name}" for b in valid],
            hoverinfo='text',
            name=f"<b>{cat_name}</b>",
        ))

    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=ANCHOR_LAT, lon=ANCHOR_LON),
            zoom=14,
        ),
        height=550, margin=dict(t=30, b=5, l=5, r=5),
        paper_bgcolor='white',
        legend=dict(orientation='h', y=1.02, x=0.5, xanchor='center',
                    font=dict(size=11, family='Arial', color=C_DARK)),
    )
    return fig


@st.cache_data(show_spinner=False, ttl=3600)
def render_gis_map():
    """Render EPRI ckt5 real feeder on industry-standard light GIS basemap (carto-positron)."""
    from pathlib import Path
    import json
    data_dir = Path(__file__).resolve().parent.parent.parent / "ai_synthetic_data"
    coords_path = data_dir / "epri_ckt5_coords.json"
    edges_path = data_dir / "epri_ckt5_edges.json"
    if not coords_path.exists() or not edges_path.exists():
        return None

    with open(coords_path) as f:
        geo = json.load(f)
    with open(edges_path) as f:
        edges = json.load(f)

    lats = [v[0] for v in geo.values()]
    lons = [v[1] for v in geo.values()]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    fig = go.Figure()

    # ALL lines in one trace (fast)
    line_lats = []
    line_lons = []
    for b1, b2 in edges:
        if b1 in geo and b2 in geo:
            line_lats.extend([geo[b1][0], geo[b2][0], None])
            line_lons.extend([geo[b1][1], geo[b2][1], None])
    fig.add_trace(go.Scattermapbox(
        lat=line_lats, lon=line_lons,
        mode='lines', line=dict(color='#999999', width=1.2),
        hoverinfo='skip', showlegend=False
    ))

    # Bus nodes - sized by load (compile feeder to get load data)
    bus_list = list(geo.keys())
    try:
        import opendssdirect as dss_lib
        from pathlib import Path as P2
        epri_master = P2(__file__).resolve().parent.parent.parent / "ai_synthetic_data" / "epri_ckt5" / "Master_ckt5.dss"
        dss_lib.Basic.ClearAll()
        dss_lib.Text.Command(f"Compile [{epri_master.as_posix()}]")
        dss_lib.Solution.Solve()
        bus_kw = {}
        for ln in dss_lib.Loads.AllNames():
            dss_lib.Loads.Name(ln)
            bus = dss_lib.CktElement.BusNames()[0].split('.')[0].lower()
            bus_kw[bus] = bus_kw.get(bus, 0) + dss_lib.Loads.kW()
        max_kw = max(bus_kw.values()) if bus_kw else 1
    except Exception:
        bus_kw = {}
        max_kw = 1

    bus_sizes = []
    for b in bus_list:
        kw = bus_kw.get(b.lower(), 0)
        bus_sizes.append(max(6, min(18, 6 + 12 * (kw / max_kw))) if max_kw > 0 else 6)

    fig.add_trace(go.Scattermapbox(
        lat=[geo[b][0] for b in bus_list],
        lon=[geo[b][1] for b in bus_list],
        mode='markers',
        marker=dict(size=bus_sizes, color='#1565C0', opacity=0.7),
        text=[f"Bus {b}<br>{bus_kw.get(b.lower(), 0):.1f} kW" if bus_kw.get(b.lower(), 0) > 0 else f"Bus {b}<br>Junction node (through-flow)" for b in bus_list],
        hoverinfo='text', showlegend=False,
    ))

    # Place EV, Solar, Data Center on selected buses (demonstrative scenario)
    ev_buses_epri = bus_list[10:16]   # 6 EV charging locations
    solar_buses_epri = bus_list[50:56]  # 6 solar PV locations
    dc_bus_epri = bus_list[200]  # 1 data center

    fig.add_trace(go.Scattermapbox(
        lat=[geo[dc_bus_epri][0]], lon=[geo[dc_bus_epri][1]],
        mode='markers', marker=dict(size=18, color='#8B0000'),
        hovertext=[f"<b>Data Center</b><br>Bus {dc_bus_epri}<br>Load: 1.75 MW<br>Power Factor: 0.97"],
        hoverinfo='text', name='<b>Data Center</b>',
    ))
    fig.add_trace(go.Scattermapbox(
        lat=[geo[b][0] for b in ev_buses_epri],
        lon=[geo[b][1] for b in ev_buses_epri],
        mode='markers', marker=dict(size=14, color=C1),
        hovertext=[f"<b>EV Charging</b><br>Bus {b}<br>Load: {0.3/6*1000:.0f} kW per station<br>Total EV: 300 kW" for b in ev_buses_epri],
        hoverinfo='text', name='<b>EV Charging</b>',
    ))
    fig.add_trace(go.Scattermapbox(
        lat=[geo[b][0] for b in solar_buses_epri],
        lon=[geo[b][1] for b in solar_buses_epri],
        mode='markers', marker=dict(size=14, color=C_GREEN),
        hovertext=[f"<b>Solar PV</b><br>Bus {b}<br>Generation: {2.0/6*1000:.0f} kW per site<br>Total Solar: 2.0 MW" for b in solar_buses_epri],
        hoverinfo='text', name='<b>Solar PV</b>',
    ))

    # Substation
    fig.add_trace(go.Scattermapbox(
        lat=[center_lat], lon=[center_lon],
        mode='markers+text',
        marker=dict(size=16, color='#1C1C1C'),
        text=['Substation'],
        textposition='bottom center',
        textfont=dict(size=10, color=C_DARK, family='Arial'),
        hovertext=[(
            "<b>EPRI Test Circuit 5 - Real US Distribution Topology</b><br>"
            "<b>Placement:</b> Roswell, GA (illustrative suburban location)<br>"
            "<b>Topology:</b> Real EPRI ckt5 (981 buses, 1,050 lines)<br>"
            "<b>Span:</b> ~2.5 x 2.9 miles<br>"
            "<b>Source:</b> EPRI Distribution Test Circuits (public dataset)<br>"
            "<br>"
            "<b>Scenario assets placed:</b><br>"
            "- 1 Data Center (1.75 MW)<br>"
            "- 6 EV Charging stations<br>"
            "- 6 Solar PV installations<br>"
            "<br>"
            "<b>Context:</b> Georgia Power territory, suburban Atlanta,<br>"
            "SE US solar belt, growing EV + data center corridor"
        )],
        hoverinfo='text',
        name='<b>Substation</b>',
    ))

    # Legend
    fig.add_trace(go.Scattermapbox(
        lat=[None], lon=[None], mode='markers',
        marker=dict(size=10, color='#888888'),
        name='<b>Distribution Lines (981 buses)</b>',
    ))

    fig.update_layout(
        mapbox=dict(
            style='open-street-map',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=13.5,
        ),
        height=650, margin=dict(t=30, b=5, l=5, r=5),
        paper_bgcolor='white',
        legend=dict(orientation='h', y=1.02, x=0.5, xanchor='center',
                    font=dict(size=11, family='Arial', color=C_DARK)),
    )
    return fig


def render_before_after_map(improvement_pct):
    """Render side-by-side grid maps using actual feeder topology.
    
    Stress propagation follows electrical distance from overload sources
    (EV buses, DC bus) along the actual line connections in master_lite.dss.
    This ensures the before/after visualization matches the network topology
    shown in the main grid map.
    """
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

    ev_buses = {"60", "83", "90", "92", "114"}
    solar_buses = {"66", "80", "92", "104", "110"}
    dc_bus = "67"
    overload_sources = ev_buses | {dc_bus}

    # Build adjacency from actual line connections
    edges = parse_line_connections()
    adjacency = {}
    for b1, b2 in edges:
        if b1 in primary and b2 in primary:
            adjacency.setdefault(b1, set()).add(b2)
            adjacency.setdefault(b2, set()).add(b1)

    # BFS from overload sources to find electrically close buses (stress propagation)
    stressed_buses = set()
    stress_distance = {}  # bus -> hop distance from nearest source
    from collections import deque
    queue = deque()
    for src in overload_sources:
        if src in primary:
            queue.append((src, 0))
            stress_distance[src] = 0
            stressed_buses.add(src)

    max_hops = 3  # stress propagates up to 3 hops electrically
    while queue:
        bus, dist = queue.popleft()
        if dist >= max_hops:
            continue
        for neighbor in adjacency.get(bus, []):
            if neighbor not in stress_distance:
                stress_distance[neighbor] = dist + 1
                stressed_buses.add(neighbor)
                queue.append((neighbor, dist + 1))

    from plotly.subplots import make_subplots
    fig = make_subplots(rows=1, cols=2, subplot_titles=["<b>Before (Baseline)</b>", "<b>After (Intervention)</b>"],
                        horizontal_spacing=0.05)

    # Draw topology lines on both panels
    for col in [1, 2]:
        for b1, b2 in edges:
            if b1 in primary and b2 in primary:
                x0, y0 = primary[b1]
                x1, y1 = primary[b2]
                fig.add_trace(go.Scatter(
                    x=[x0, x1, None], y=[y0, y1, None],
                    mode='lines', line=dict(color='#999999', width=1.2),
                    hoverinfo='skip', showlegend=False
                ), row=1, col=col)

    for col, is_after in [(1, False), (2, True)]:
        xs, ys, colors, sizes = [], [], [], []
        for bus, (x, y) in primary.items():
            xs.append(x)
            ys.append(y)
            if is_after:
                if bus in stressed_buses:
                    dist = stress_distance.get(bus, 0)
                    if improvement_pct >= 80:
                        colors.append("#1565C0")
                        sizes.append(7)
                    elif improvement_pct >= 40 or dist >= 2:
                        colors.append("#E88D14")
                        sizes.append(9)
                    else:
                        colors.append("#1565C0" if dist >= 2 else "#E88D14")
                        sizes.append(9)
                else:
                    colors.append("#1565C0")
                    sizes.append(6)
            else:
                if bus == dc_bus:
                    colors.append("#8B0000")
                    sizes.append(14)
                elif bus in overload_sources:
                    colors.append(C_RED)
                    sizes.append(11)
                elif bus in stressed_buses:
                    dist = stress_distance.get(bus, 3)
                    if dist == 1:
                        colors.append(C_RED)
                        sizes.append(9)
                    elif dist == 2:
                        colors.append("#E88D14")
                        sizes.append(8)
                    else:
                        colors.append("#E88D14")
                        sizes.append(7)
                else:
                    colors.append("#1565C0")
                    sizes.append(6)

        fig.add_trace(go.Scatter(x=xs, y=ys, mode='markers',
                                  marker=dict(size=sizes, color=colors, line=dict(width=0.3, color='white')),
                                  showlegend=False, hoverinfo='skip'), row=1, col=col)

    fig.update_layout(height=550, margin=dict(t=35, b=5, l=5, r=5),
                      plot_bgcolor='#F8F8F8', paper_bgcolor='white',
                      font=dict(family="Arial", size=10))
    fig.update_annotations(font_size=11, font_family="Arial")
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return fig


def render_before_after_map_epri(improvement_pct):
    """Render before/after stress maps for EPRI ckt5 on real basemap (same style as landing page)."""
    from pathlib import Path
    import json
    from collections import deque
    data_dir = Path(__file__).resolve().parent.parent.parent / "ai_synthetic_data"
    coords_path = data_dir / "epri_ckt5_coords.json"
    edges_path = data_dir / "epri_ckt5_edges.json"
    if not coords_path.exists() or not edges_path.exists():
        return None, None

    with open(coords_path) as f:
        geo = json.load(f)
    with open(edges_path) as f:
        edges = json.load(f)

    bus_list = list(geo.keys())
    ev_buses_epri = set(bus_list[10:16])
    solar_buses_epri = set(bus_list[50:56])
    dc_bus_epri = bus_list[200]
    overload_sources = ev_buses_epri | {dc_bus_epri}

    # Build adjacency
    adjacency = {}
    for b1, b2 in edges:
        if b1 in geo and b2 in geo:
            adjacency.setdefault(b1, set()).add(b2)
            adjacency.setdefault(b2, set()).add(b1)

    # BFS stress propagation
    stressed_buses = set()
    stress_distance = {}
    queue = deque()
    for src in overload_sources:
        if src in geo:
            queue.append((src, 0))
            stress_distance[src] = 0
            stressed_buses.add(src)
    max_hops = 4
    while queue:
        bus, dist = queue.popleft()
        if dist >= max_hops:
            continue
        for neighbor in adjacency.get(bus, []):
            if neighbor not in stress_distance:
                stress_distance[neighbor] = dist + 1
                stressed_buses.add(neighbor)
                queue.append((neighbor, dist + 1))

    lats = [v[0] for v in geo.values()]
    lons = [v[1] for v in geo.values()]
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    # Build lines trace (shared)
    line_lats, line_lons = [], []
    for b1, b2 in edges:
        if b1 in geo and b2 in geo:
            line_lats.extend([geo[b1][0], geo[b2][0], None])
            line_lons.extend([geo[b1][1], geo[b2][1], None])

    figs = []
    for is_after in [False, True]:
        fig = go.Figure()
        # Lines - gray, thin
        fig.add_trace(go.Scattermapbox(
            lat=line_lats, lon=line_lons,
            mode='lines', line=dict(color='#999999', width=1.2),
            hoverinfo='skip', showlegend=False
        ))
        # Buses colored by stress - blue for resolved (not green), yellow for partial
        bus_lats, bus_lons, colors, sizes = [], [], [], []
        for bus in geo:
            bus_lats.append(geo[bus][0])
            bus_lons.append(geo[bus][1])
            if is_after:
                if bus in stressed_buses:
                    dist = stress_distance.get(bus, 0)
                    if improvement_pct >= 80:
                        colors.append("#1565C0"); sizes.append(6)
                    elif improvement_pct >= 40 or dist >= 2:
                        colors.append("#E88D14"); sizes.append(9)
                    else:
                        colors.append("#1565C0" if dist >= 2 else "#E88D14"); sizes.append(9)
                else:
                    colors.append("#1565C0"); sizes.append(5)
            else:
                if bus == dc_bus_epri:
                    colors.append("#8B0000"); sizes.append(14)
                elif bus in overload_sources:
                    colors.append(C_RED); sizes.append(11)
                elif bus in stressed_buses:
                    dist = stress_distance.get(bus, 3)
                    if dist == 1:
                        colors.append(C_RED); sizes.append(9)
                    elif dist == 2:
                        colors.append("#E88D14"); sizes.append(8)
                    else:
                        colors.append("#E88D14"); sizes.append(7)
                else:
                    colors.append("#1565C0"); sizes.append(5)

        fig.add_trace(go.Scattermapbox(
            lat=bus_lats, lon=bus_lons, mode='markers',
            marker=dict(size=sizes, color=colors),
            showlegend=False, hoverinfo='skip'
        ))
        fig.update_layout(
            mapbox=dict(style='open-street-map', center=dict(lat=center_lat, lon=center_lon), zoom=13.5),
            height=650, margin=dict(t=25, b=5, l=5, r=5), paper_bgcolor='white',
            title=dict(text="<b>After (Intervention)</b>" if is_after else "<b>Before (Baseline)</b>",
                       font=dict(size=11, family="Arial", color=C_DARK), x=0.5),
        )
        figs.append(fig)

    return figs[0], figs[1]


# ─── Session State ────────────────────────────────────────────────────────────
if "study_data" not in st.session_state:
    st.session_state.study_data = None
if "running" not in st.session_state:
    st.session_state.running = False
if "scroll_to_top_once" not in st.session_state:
    st.session_state.scroll_to_top_once = False

# ─── Sidebar ──────────────────────────────────────────────────────────────────
sidebar_locked = st.session_state.running or st.session_state.study_data is not None

with st.sidebar:
    st.markdown(f'<div style="font:700 0.95rem Arial,sans-serif;color:{C_DARK};margin-bottom:14px;border-bottom:2px solid {C1};padding-bottom:8px;">Parameter Selection</div>', unsafe_allow_html=True)
    if sidebar_locked:
        st.caption("⚠️ Parameters locked during/after study. Click 'New Study' to reset.")

    st.markdown(f'<div class="sidebar-section"><b>📅 Planning Horizon</b></div>', unsafe_allow_html=True)
    horizon = st.selectbox(
        "Planning Horizon", ["3m", "6m", "12m", "18m", "3yr", "5yr"], index=2,
        format_func=lambda x: {"3m": "3 Months", "6m": "6 Months", "12m": "12 Months",
                               "18m": "18 Months", "3yr": "3 Years", "5yr": "5 Years"}[x],
        label_visibility="collapsed",
        help="Time horizon for the planning study. Longer horizons capture compounding growth effects.",
        disabled=sidebar_locked
    )

    st.markdown(f'<div class="sidebar-section"><b>📂 Data Source</b></div>', unsafe_allow_html=True)
    use_gis_map = st.checkbox("EPRI real feeder (981 buses, Roswell GA)", value=False, key="gis_map",
                              help="**This is a real dataset with real distribution nodes from EPRI public test circuits.** 981 buses, 1,050 line segments, ~2.5 x 2.9 miles. Total base load: 6.8 MW across 1,379 loads. Assets placed: 1 Data Center (1.75 MW, Bus 8163), 6 EV Charging stations (Buses 8164, 829, 834, 44582, 8160, 6584), 6 Solar PV installations (Buses 8113, 8124, 14880, 63707, 63657, 6584). Primary voltage: 12.47 kV. Supply: single substation source. Real feeder topology placed on suburban Atlanta map (illustrative location).",
                              disabled=sidebar_locked)
    use_real_data = st.checkbox("DOE openEDI real load profiles (IEEE 123-bus)", value=True, key="real_data",
                                help="IEEE 123-bus test feeder with 91 real measured load profiles from US DOE openEDI. Total base load: ~3.5 MW across 85 loads. Assets placed: 1 Data Center (1-3 MW, Bus 67), 5 EV Charging stations (Buses 60, 83, 90, 92, 114), 5 Solar PV installations (Buses 66, 80, 92, 104, 110). Primary voltage: 4.16 kV. Supply: single substation source. Each load profile has 35,040 data points at 15-minute intervals across 365 days. Peak-stress day auto-selected. **This is actual metered utility data, not synthetic curves.**",
                                disabled=use_gis_map)
    if use_gis_map and use_real_data:
        use_real_data = False
    if use_gis_map:
        st.caption("EPRI ckt5 real topology - 981 buses - Illustrative placement (Roswell, GA) - EV + Solar + Data Center")
    elif use_real_data:
        st.caption("Real US utility data - 91 bus profiles x 35,040 points - peak stress day auto-selected from 365 days")
    else:
        st.caption("Parametric synthetic profiles (math-generated 24h curves)")

    ev_options = ["Low (15% annually)", "Base (20% annually)", "High (25% annually)", "Custom"]
    ev_choice = st.selectbox("⚡ EV Growth", ev_options, index=1,
                             help="Projected annual growth rate in EV charging demand on this feeder. Low/Base/High represent 15%/20%/25% compound annual growth respectively.\n\n**Time period:** This rate compounds over the selected planning horizon. E.g. 'Base (20%)' over 12 months = 20% more EV load; over 3 years = ~73% cumulative growth.\n\n**Source:** EIA Annual Energy Outlook 2024 (15-25% range through 2030).")
    ev_level_map = {"Low (15% annually)": "Low", "Base (20% annually)": "Base", "High (25% annually)": "High"}
    ev_level = ev_level_map.get(ev_choice, "Base")
    if ev_choice == "Custom":
        ev_custom = st.number_input("Custom EV growth %", min_value=5, max_value=50, value=20, step=1, key="evc")
        ev_level = "Base"

    solar_options = ["Low (1 MW)", "Base (2 MW)", "High (3 MW)", "Custom"]
    solar_choice = st.selectbox("☀️ Solar Adoption", solar_options, index=1,
                                help="Total distributed solar PV capacity expected on this feeder. Low/Base/High represent 1/2/3 MW of cumulative installed rooftop and community solar.\n\n**Time period:** This is the total capacity at the END of the planning horizon — not an annual addition. 'Base (2 MW)' means 2 MW total DER by the horizon date regardless of whether the horizon is 6 months or 5 years.\n\n**Source:** SEIA Solar Market Insight Q1 2024.")
    solar_level_map = {"Low (1 MW)": "Low", "Base (2 MW)": "Base", "High (3 MW)": "High"}
    solar_level = solar_level_map.get(solar_choice, "Base")
    if solar_choice == "Custom":
        solar_custom = st.number_input("Custom feeder MW", min_value=0.5, max_value=10.0, value=2.0, step=0.5, key="solc")
        solar_level = "Base"

    st.markdown(f'<div class="sidebar-section"><b>🏢 Data Center</b></div>', unsafe_allow_html=True)
    dc_options = ["Low (1.0 MW)", "Moderate (1.75 MW)", "High (3.0 MW)", "Custom"]
    dc_choice = st.selectbox("Data Center Load", dc_options, index=1, label_visibility="collapsed",
                             help="DOE Grid Deployment Office 2024: typical data center interconnection loads.")
    dc_level_map = {"Low (1.0 MW)": "Low", "Moderate (1.75 MW)": "Moderate", "High (3.0 MW)": "High"}
    dc_level = dc_level_map.get(dc_choice, "Moderate")
    if dc_choice == "Custom":
        dc_custom = st.number_input("Custom DC MW", min_value=0.5, max_value=10.0, value=1.75, step=0.25, key="dcc")
        dc_level = "Moderate"

    dc_timeline = st.selectbox(
        "DC Timeline", ["6m", "12m", "18m"], index=1,
        format_func=lambda x: {"6m": "Online in 6 Months", "12m": "Online in 12 Months", "18m": "Online in 18 Months"}[x],
        label_visibility="collapsed",
        help="Expected timeline for data center to come online."
    )

    st.markdown(f'<div class="sidebar-section"><b>🕐 Peak Demand Window</b></div>', unsafe_allow_html=True)
    st.caption("System peak hours for demand tariff and managed charging application (based on US utility standard practice 5-9 PM).")
    peak_start, peak_end = st.slider("Peak hours", 0, 23, (17, 21), key="peak_hrs")
    st.caption(f"Peak window: {peak_start}:00 - {peak_end}:00")

    st.markdown("---")
    st.markdown(f'<div class="sidebar-section"><b>Candidate Portfolios to Evaluate</b></div>', unsafe_allow_html=True)
    max_portfolios = st.slider("count", 10, 120, 60, step=10, label_visibility="collapsed")

    st.markdown(f'<div class="sidebar-section"><b>Max Measures per Portfolio</b></div>', unsafe_allow_html=True)
    max_active = st.slider("measures", 1, 5, 3, label_visibility="collapsed",
                           help="Maximum number of different interventions that can be combined in a single portfolio. Higher values explore more complex solutions but increase computation time.")

    st.markdown(f'<div class="sidebar-section"><b>Min Measures per Portfolio</b></div>', unsafe_allow_html=True)
    min_active = st.slider("min measures", 1, 5, 2, label_visibility="collapsed",
                           help="Minimum number of interventions required in each portfolio. Set > 1 to exclude single-measure solutions and focus on combined approaches.")
    if min_active > max_active:
        st.warning("Min measures cannot exceed max measures. Using max value.")
        min_active = max_active

    st.markdown(f'<div class="sidebar-section"><b>🎯 Solution Preferences</b> <span class="optional-tag">(optional)</span></div>', unsafe_allow_html=True)
    filter_mode = st.radio("Filter mode", ["Must include", "Only these"], index=0,
                           help="'Must include': solutions contain at least the selected interventions. 'Only these': solutions contain ONLY the selected interventions.",
                           label_visibility="collapsed", horizontal=True)
    if filter_mode == "Must include":
        st.caption("Solutions must include selected interventions (may also include others):")
    else:
        st.caption("Solutions will contain ONLY the selected interventions (nothing else):")
    filter_mc = st.checkbox("Managed EV Charging", key="f_mc")
    filter_pi = st.checkbox("Staged Load Connection", key="f_pi")
    filter_dt = st.checkbox("Dynamic Tariffs", key="f_dt")
    filter_battery = st.checkbox("Battery Storage", key="f_bat")
    filter_tu = st.checkbox("Capacity Upgrade", key="f_tu")

    st.markdown(f'<div class="sidebar-section"><b>📊 Minimum Grid Relief</b></div>', unsafe_allow_html=True)
    min_grid_relief = st.slider("Min grid relief %", 0, 50, 10, step=5, key="min_gr",
                                help="Exclude solutions with technical improvement below this threshold")
    st.caption(f"Only show solutions with ≥ {min_grid_relief}% grid stress reduction")

    st.markdown(f'<div class="sidebar-section"><b> Save Results</b></div>', unsafe_allow_html=True)
    save_outputs = st.checkbox("Save run outputs to disk", value=False, key="save_out",
                               help="When enabled, results are saved to outputs/ folder")

    st.markdown("---")
    run_btn = st.button("▶  Run Study", use_container_width=True)

# ─── Main ─────────────────────────────────────────────────────────────────────
top_left, top_right = st.columns([7, 2])
with top_left:
    st.markdown(f'<div style="color:{C_DARK};font:700 1.35rem Arial,sans-serif;padding-top:18px;">FeederIQ Agentic Distribution Planning</div>', unsafe_allow_html=True)
with top_right:
    logo_path = Path(__file__).resolve().parent / "assets" / "pwc_logo.svg"
    if logo_path.exists():
        try:
            # Render SVG natively in browser (avoids PIL.UnidentifiedImageError in st.image for SVG bytes)
            svg_text = logo_path.read_text(encoding="utf-8")
            svg_b64 = base64.b64encode(svg_text.encode("utf-8")).decode("ascii")
            st.markdown(
                f'<div style="display:flex;justify-content:flex-end;padding-top:0px;transform:translateY(-8px);">'
                f'<img src="data:image/svg+xml;base64,{svg_b64}" width="92" style="display:block;" />'
                f'</div>',
                unsafe_allow_html=True,
            )
        except Exception:
            st.markdown(f'<div style="color:{C1};font:900 1.6rem Georgia,serif;text-align:right;padding-top:8px;">pwc</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{C1};font:900 1.6rem Georgia,serif;text-align:right;padding-top:8px;">pwc</div>', unsafe_allow_html=True)
st.markdown(f'<div style="border-bottom:3px solid {C1}; margin:4px 0 18px;"></div>', unsafe_allow_html=True)

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

    # Build required interventions list from filter checkboxes
    req_interventions = []
    if filter_mc:
        req_interventions.append("ManagedCharging")
    if filter_pi:
        req_interventions.append("PhasedInterconnection")
    if filter_dt:
        req_interventions.append("DemandTariff")
    if filter_battery:
        req_interventions.append("Battery")
    if filter_tu:
        req_interventions.append("TransformerUpgrade")

    payload = {
        "horizon_label": horizon,
        "ev_level": ev_level,
        "solar_level": solar_level,
        "dc_level": dc_level,
        "dc_timeline_label": dc_timeline,
        "max_active_measures": max_active,
        "min_active_measures": min_active,
        "max_portfolios": max_portfolios,
        "required_interventions": req_interventions if req_interventions else None,
        "use_real_data": use_real_data,
        "use_epri": use_gis_map,
    }

    def _node_status(node_idx, current_idx):
        if node_idx < current_idx:
            return "done"
        if node_idx == current_idx:
            return "running"
        return "pending"

    def _render_node(icon, title, subtitle, status, pct=0, reco=False, max_width=440):
        if status == "done":
            bg = "#EDF8F4" if not reco else "#E7F3EE"
            accent = "#2F7D6B"
            card_border = "#C8E4DB"
            status_label = "COMPLETED" if not reco else "FINALIZED"
            status_color = "#2A6F60"
            status_chip_bg = "#DDEFE8"
            status_chip_border = "#B8D9CE"
            detail_color = "#44675E"
            icon_bg = "#D3EAE2"
            shadow_color = "rgba(30, 96, 80, 0.14)"
            meter = ""
        elif status == "running":
            bg = "#E3EEFF"
            accent = "#1C5AA2"
            card_border = "#AFCBEF"
            status_label = "IN PROGRESS"
            status_color = "#1C5AA2"
            status_chip_bg = "#D6E6FC"
            status_chip_border = "#A9C4EA"
            detail_color = "#314F71"
            icon_bg = "#C9DEFB"
            shadow_color = "rgba(24, 78, 142, 0.16)"
            if reco:
                dots = "●" * (pct // 10) + "○" * (10 - pct // 10)
                score_preview = f"{pct / 12.5:.1f}" if pct > 20 else "..."
                meter = (
                    f'<div style="margin-top:5px;font:600 0.6rem monospace;color:#1C5AA2;letter-spacing:1px;">{dots}</div>'
                    f'<div style="font:500 0.56rem Arial;color:#3E648F;letter-spacing:0.04em;text-transform:uppercase;">Score convergence: {score_preview}</div>'
                )
            else:
                meter = (
                    '<div style="margin:6px auto 0 auto;height:3px;background:#D0E0F5;border-radius:2px;width:116px;">'
                    f'<div style="height:3px;background:linear-gradient(90deg,#4B8DD9 0%,#1C5AA2 100%);border-radius:2px;width:{pct}%;transition:width 0.1s;"></div>'
                    '</div>'
                )
        else:
            bg = "#FFF1E1"
            accent = C1
            card_border = "#EFB886"
            status_label = "QUEUED"
            status_color = "#A64908"
            status_chip_bg = "#FFDDBB"
            status_chip_border = "#EFAE75"
            detail_color = "#6A4A31"
            icon_bg = "#FFD5AF"
            shadow_color = "rgba(140, 71, 14, 0.16)"
            meter = ""

        return (
            '<div style="display:flex;justify-content:center;">'
            f'<div style="width:min(100%, {max_width}px);background:{bg};border:1px solid {card_border};border-top:2px solid {accent};'
            f'border-radius:10px;padding:7px 10px 8px 10px;text-align:center;box-shadow:0 2px 6px {shadow_color};">'
            '<div style="display:flex;align-items:center;justify-content:center;gap:6px;">'
            f'<span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:999px;background:{icon_bg};font-size:0.8rem;line-height:1;">{icon}</span>'
            f'<span style="font:700 0.82rem Arial;color:{C_DARK};line-height:1.15;">{title}</span>'
            '</div>'
            f'<div style="display:inline-block;font:600 0.58rem Arial;color:{status_color};letter-spacing:0.08em;text-transform:uppercase;margin-top:4px;padding:2px 8px;border-radius:999px;background:{status_chip_bg};border:1px solid {status_chip_border};">{status_label}</div>'
            f'<div style="font:400 0.7rem Arial;color:{detail_color};margin-top:2px;line-height:1.24;max-width:92%;margin-left:auto;margin-right:auto;">{subtitle}</div>'
            f'{meter}'
            '</div></div>'
        )

    def _render_agent_tree(states, texts, pct):
        stage = next((idx for idx, s in enumerate(states) if s == "running"), len(states) - 1)

        def _line_color(active, major=False):
            if active:
                return "#1F5FA8" if major else "#4E88CA"
            return "#E88D14"

        c01 = _line_color(stage >= 0, major=True)
        c12 = _line_color(stage >= 1, major=True)
        c2b = _line_color(stage >= 2, major=False)
        c3 = _line_color(stage >= 3, major=False)
        c4 = _line_color(stage >= 4, major=False)
        cmerge = _line_color(stage >= 4, major=True)

        nodes = [
            _render_node(agents[0][0], agents[0][1], texts[0], states[0], pct, max_width=420),
            _render_node(agents[1][0], agents[1][1], texts[1], states[1], pct, max_width=420),
            _render_node(agents[2][0], agents[2][1], texts[2], states[2], pct, max_width=420),
            _render_node(agents[3][0], agents[3][1], texts[3], states[3], pct, max_width=270),
            _render_node(agents[4][0], agents[4][1], texts[4], states[4], pct, max_width=270),
            _render_node(agents[5][0], agents[5][1], texts[5], states[5], pct, reco=True, max_width=460),
        ]

        return f'''
        <div style="padding:10px 8px 10px 8px;max-width:760px;margin:0 auto;background:linear-gradient(180deg,#FFF6EB 0%,#FFFFFF 48%,#F3F8FF 100%);border:1px solid #E6C7A9;border-top:2px solid {C1};border-radius:12px;">
            {nodes[0]}
            <div style="display:flex;justify-content:center;"><div style="width:2px;height:8px;background:{c01};"></div></div>
            {nodes[1]}
            <div style="display:flex;justify-content:center;"><div style="width:2px;height:8px;background:{c12};"></div></div>
            {nodes[2]}
            <div style="display:flex;justify-content:center;"><div style="width:2px;height:7px;background:{c2b};"></div></div>
            <div style="display:flex;justify-content:center;"><div style="width:8px;height:8px;border-radius:50%;background:{c2b};"></div></div>
            <div style="display:flex;justify-content:center;"><div style="width:min(100%, 360px);height:2px;background:{c2b};"></div></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;width:min(100%, 580px);margin:6px auto 2px auto;">
                {nodes[3]}
                {nodes[4]}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;width:min(100%, 580px);margin:0 auto;">
                <div style="display:flex;justify-content:center;"><div style="width:2px;height:8px;background:{c3};"></div></div>
                <div style="display:flex;justify-content:center;"><div style="width:2px;height:8px;background:{c4};"></div></div>
            </div>
            <div style="display:flex;justify-content:center;"><div style="width:min(100%, 360px);height:2px;background:{cmerge};"></div></div>
            <div style="display:flex;justify-content:center;"><div style="width:8px;height:8px;border-radius:50%;background:{cmerge};"></div></div>
            <div style="display:flex;justify-content:center;"><div style="width:2px;height:7px;background:{cmerge};"></div></div>
            {nodes[5]}
        </div>
        '''

    api_done = False
    for i, (icon, name, detail) in enumerate(agents):
        for pct in range(0, 101, 5):
            progress.progress((i + pct / 100) / len(agents))
            states = [_node_status(j, i) for j in range(len(agents))]
            texts = [dt for _, _, dt in agents]
            html = _render_agent_tree(states, texts, pct)
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
                time.sleep(0.06)

    progress.progress(1.0)
    # Show agent summaries from actual results
    study = st.session_state.study_data
    if not study or not study.get("ranking"):
        st.error("Study returned empty results. Please check backend logs.")
        st.session_state.running = False
        st.session_state.study_data = None
        st.stop()

    bs = study.get("base_summary", {})
    top_rec = study.get("top_recommendation", {})
    agent_summaries = [
        f"Profiles generated. Data source: {'Real (openEDI)' if study.get('scenario', {}).get('use_real_data') else 'Synthetic'}",
        "24-hour power flow complete. Feeder: IEEE 123-bus.",
        f"Grid stress: {bs.get('grid_stress_score', 0):.0f}. Line overloads: {bs.get('total_line_overloads', 0)}. Transformer overloads: {bs.get('total_transformer_overloads', 0)}.",
        f"Best NWA: {top_rec.get('portfolio_name', 'N/A') if top_rec.get('TransformerUpgrade', 0) == 0 else 'Evaluated'}. {len(study.get('ranking', []))} portfolios scored.",
        "Capex options evaluated for comparison.",
        f"Top recommendation: {top_rec.get('portfolio_name', 'N/A')} (score: {top_rec.get('final_score', 0):.2f})",
    ]
    html = _render_agent_tree(["done"] * len(agents), agent_summaries, 100)
    agent_container.markdown(html, unsafe_allow_html=True)

    st.success("✅ All agents completed. Review summaries above, then view results.")
    if st.button("▶  View Results", key="view_results_btn"):
        st.session_state.running = False
        st.session_state.scroll_to_top_once = True
        st.session_state.results_section = "✅ Recommendation"
        st.rerun()
    st.stop()  # Prevent anything below from rendering while on this page

# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.study_data:
    if st.session_state.scroll_to_top_once:
        import streamlit.components.v1 as _components
        _components.html('''<script>
            (function () {
                function scrollAll() {
                    var d = window.parent.document;
                    var targets = [
                        window.parent,
                        d.scrollingElement,
                        d.documentElement,
                        d.body,
                        d.querySelector("section.main"),
                        d.querySelector(".main"),
                        d.querySelector("[data-testid='stAppViewContainer']"),
                        d.querySelector("[data-testid='stMain']")
                    ];
                    for (var i = 0; i < targets.length; i++) {
                        var t = targets[i];
                        if (!t) continue;
                        try {
                            if (typeof t.scrollTo === "function") t.scrollTo(0, 0);
                        } catch (e) {}
                        try {
                            t.scrollTop = 0;
                        } catch (e) {}
                    }
                }

                [0, 60, 180, 420, 900, 1600].forEach(function (ms) {
                    setTimeout(scrollAll, ms);
                });
            })();
        </script>''', height=0)
        st.session_state.scroll_to_top_once = False

    data = st.session_state.study_data
    ranking = data.get("ranking", [])

    # Apply minimum grid relief filter
    if min_grid_relief > 0:
        ranking = [r for r in ranking if r.get("technical_improvement_pct", 0) >= min_grid_relief]
    if not ranking:
        st.warning("No solutions meet the minimum grid relief threshold. Try lowering the threshold or adjusting scenario parameters.")
        ranking = data.get("ranking", [])  # fallback to unfiltered

    # Apply "Only these" filter if selected
    if filter_mode == "Only these":
        allowed = set()
        if filter_mc: allowed.add("ManagedCharging")
        if filter_pi: allowed.add("PhasedInterconnection")
        if filter_dt: allowed.add("DemandTariff")
        if filter_battery: allowed.add("Battery")
        if filter_tu: allowed.add("TransformerUpgrade")
        if allowed:
            all_keys = {"ManagedCharging", "PhasedInterconnection", "DemandTariff", "Battery", "TransformerUpgrade"}
            excluded = all_keys - allowed
            filtered = [r for r in ranking if all(r.get(k, 0) == 0 for k in excluded)]
            if filtered:
                ranking = filtered
            else:
                st.info("No solutions use only the selected interventions. Showing all results.")

    if not ranking:
        st.warning("No ranked solutions available for display.")
        st.stop()

    # Shared selected solution state across all tabs
    top10 = ranking[:10]
    rank_pos = {r.get("portfolio_name", f"row-{i}"): i + 1 for i, r in enumerate(ranking)}
    top10_by_name = {r.get("portfolio_name", f"row-{i}"): r for i, r in enumerate(top10)}

    if "selected_solution_name" not in st.session_state or st.session_state.selected_solution_name not in top10_by_name:
        st.session_state.selected_solution_name = top10[0].get("portfolio_name", "")

    selected_solution = top10_by_name.get(st.session_state.selected_solution_name, top10[0])
    runner_up_solution = next((r for r in ranking if r.get("portfolio_name") != selected_solution.get("portfolio_name")), None)

    # LLM-generated implementation content grounded in project docs
    docs_bundle = _load_strategy_docs()
    implementation_pack = _generate_implementation_pack(
        selected_solution,
        data.get("scenario", {}),
        data.get("base_summary", {}),
        docs_bundle,
    )
    selected_memo = _generate_selected_memo(
        selected_solution,
        runner_up_solution,
        data.get("scenario", {}),
        data.get("base_summary", {}),
        ranking[:5],
        implementation_pack,
        docs_bundle,
    )
    intervention_level_guide = _generate_intervention_level_guide(docs_bundle)
    implementation_summary_text = _generate_implementation_summary(
        selected_solution,
        data.get("scenario", {}),
        data.get("base_summary", {}),
        implementation_pack,
        docs_bundle,
    )

    # Results navigation: render one section at a time to avoid stacked-content behavior.
    result_sections = ["✅ Recommendation", "📊 Rankings", "🔍 Baseline", "📈 Profiles", "📝 Memo"]
    if "results_section" not in st.session_state or st.session_state.results_section not in result_sections:
        st.session_state.results_section = result_sections[0]
    selected_results_section = st.segmented_control(
        "Results sections",
        options=result_sections,
        key="results_section",
        label_visibility="collapsed",
    )

    # ═══ RECOMMENDATION ═══════════════════════════════════════════════════════
    if selected_results_section == "✅ Recommendation":
        st.markdown('<div class="sec-head">Recommended Solution</div>', unsafe_allow_html=True)

        selected_name = st.selectbox(
            "Select solution",
            list(top10_by_name.keys()),
            format_func=lambda name: (
                f"#{rank_pos.get(name, '?')}  {name}  "
                f"(Score: {top10_by_name[name].get('final_score', 0):.2f} / 10)"
            ),
            key="selected_solution_name",
            label_visibility="collapsed"
        )
        selected_solution = top10_by_name.get(selected_name, top10[0])
        runner_up_solution = next((r for r in ranking if r.get("portfolio_name") != selected_solution.get("portfolio_name")), None)
        implementation_pack = _generate_implementation_pack(
            selected_solution,
            data.get("scenario", {}),
            data.get("base_summary", {}),
            docs_bundle,
        )
        selected_memo = _generate_selected_memo(
            selected_solution,
            runner_up_solution,
            data.get("scenario", {}),
            data.get("base_summary", {}),
            ranking[:5],
            implementation_pack,
            docs_bundle,
        )
        implementation_summary_text = _generate_implementation_summary(
            selected_solution,
            data.get("scenario", {}),
            data.get("base_summary", {}),
            implementation_pack,
            docs_bundle,
        )

        selected = selected_solution

        if data.get("nwa_resolved_all"):
            st.success("✅ Non-wires alternatives fully resolve all grid violations. No traditional capex required.")

        # Solution card - color score by scale position
        score_val = selected["final_score"]
        if score_val >= 8:
            score_color = "#1B8C3A"
        elif score_val >= 6:
            score_color = "#7CB342"
        elif score_val >= 4:
            score_color = "#E88D14"
        elif score_val >= 2:
            score_color = "#E06030"
        else:
            score_color = "#C92A2A"

        # Build intervention-level tooltip for the solution card
        _active = _active_interventions(selected)
        _lg = intervention_level_guide or _fallback_intervention_level_guide()
        _tip_parts = []
        for _a in _active:
            _g = _lg.get(_a['key'], {})
            _tip_parts.append(
                f"<b>{escape(_a['label'])}</b><br>"
                f"<b>Low (33):</b> {escape(_g.get('low','N/A'))}<br>"
                f"<b>Medium (66):</b> {escape(_g.get('medium','N/A'))}<br>"
                f"<b>High (100):</b> {escape(_g.get('high','N/A'))}"
            )
        _tip_html = "<hr style='margin:6px 0;border:none;border-top:1px solid #EDE2D8;'>".join(_tip_parts) if _tip_parts else "No active interventions."
        _info_icon = (
            f"<details class='lvl-tip'><summary>ⓘ</summary>"
            f"<div>{_tip_html}</div>"
            f"</details>"
        ) if _tip_parts else ""

        st.markdown(f'''<div class="rank-card top" style="margin:10px 0;">
            <div style="display:flex;align-items:center;justify-content:space-between;">
                <div style="font:700 1.05rem Arial,sans-serif;color:{C_DARK};">{selected["portfolio_name"]} {_info_icon}</div>
                <div style="font:800 1.4rem Arial,sans-serif;color:{score_color};">{selected["final_score"]:.2f} <span style="font:400 0.75rem Arial;color:{C_GREY};">/ 10</span></div>
            </div>
        </div>''', unsafe_allow_html=True)

        # Score scale graphic (moved below solution card per feedback)
        st.markdown(f'''<div style="background:#F5F5F5;border-radius:6px;padding:10px 16px;margin-bottom:14px;">
            <div style="font:600 0.78rem Arial;color:{C_DARK};margin-bottom:6px;">Final score is a weighted sum of Grid Relief, Cost Efficiency, Speed to Value, and ESG</div>
            <div style="display:flex;align-items:center;gap:0;height:14px;border-radius:7px;overflow:hidden;">
                <div style="flex:1;background:#C92A2A;height:100%;"></div>
                <div style="flex:1;background:#E06030;height:100%;"></div>
                <div style="flex:1;background:#E88D14;height:100%;"></div>
                <div style="flex:1;background:#D4A017;height:100%;"></div>
                <div style="flex:1;background:#7CB342;height:100%;"></div>
                <div style="flex:1;background:#1B8C3A;height:100%;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:4px;">
                <span style="font:600 0.7rem Arial;color:{C_GREY};">0 - No improvement</span>
                <span style="font:600 0.7rem Arial;color:{C_GREY};">5 - Moderate</span>
                <span style="font:600 0.7rem Arial;color:{C_GREY};">10 - Fully resolved</span>
            </div>
        </div>''', unsafe_allow_html=True)

        # Extract scores for display
        grid_relief = selected.get("grid_relief_score", selected.get("technical_score", 0))
        cost_sc = selected.get("cost_score", 0)
        speed_sc = selected.get("speed_to_value_score", (selected.get("feasibility_score", 0) + selected.get("deployment_score", 0)) / 2)
        esg_sc = selected.get("esg_score", 8)

        # Score Breakdown - light PwC style
        sb_col1, sb_col2 = st.columns([20, 1])
        with sb_col1:
            st.markdown(f'''<div style="background:#FAFAFA;border-radius:8px;padding:14px 16px;margin-bottom:12px;border:1px solid #EBEBEB;border-top:3px solid {C1};">
                <div style="font:700 0.95rem Arial;color:{C_DARK};margin-bottom:10px;">Score Breakdown</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <div style="background:white;border-radius:6px;padding:10px 14px;border:1px solid #EBEBEB;border-left:3px solid {C1};">
                    <div style="font:600 0.72rem Arial;color:{C_GREY};text-transform:uppercase;letter-spacing:0.3px;">Grid Relief</div>
                    <div style="font:800 1.3rem Arial;color:{("#1B8C3A" if grid_relief >= 7 else (C1 if grid_relief >= 4 else C_RED))};margin-top:3px;">{grid_relief:.1f}<span style="font:400 0.75rem Arial;color:{C_GREY};"> / 10</span></div>
                    <div style="font:400 0.68rem Arial;color:{C_GREY};margin-top:2px;">{selected.get('technical_improvement_pct', 0):.1f}% stress reduction</div>
                </div>
                <div style="background:white;border-radius:6px;padding:10px 14px;border:1px solid #EBEBEB;border-left:3px solid {C2};">
                    <div style="font:600 0.72rem Arial;color:{C_GREY};text-transform:uppercase;letter-spacing:0.3px;">Cost Efficiency</div>
                    <div style="font:800 1.3rem Arial;color:{("#1B8C3A" if cost_sc >= 7 else (C1 if cost_sc >= 4 else C_RED))};margin-top:3px;">{cost_sc:.1f}<span style="font:400 0.75rem Arial;color:{C_GREY};"> / 10</span></div>
                    <div style="font:400 0.68rem Arial;color:{C_GREY};margin-top:2px;">vs. full capex baseline</div>
                </div>
                <div style="background:white;border-radius:6px;padding:10px 14px;border:1px solid #EBEBEB;border-left:3px solid {C3};">
                    <div style="font:600 0.72rem Arial;color:{C_GREY};text-transform:uppercase;letter-spacing:0.3px;">Speed to Value</div>
                    <div style="font:800 1.3rem Arial;color:{("#1B8C3A" if speed_sc >= 7 else (C1 if speed_sc >= 4 else C_RED))};margin-top:3px;">{speed_sc:.1f}<span style="font:400 0.75rem Arial;color:{C_GREY};"> / 10</span></div>
                    <div style="font:400 0.68rem Arial;color:{C_GREY};margin-top:2px;">Feasibility + deployment</div>
                </div>
                <div style="background:white;border-radius:6px;padding:10px 14px;border:1px solid #EBEBEB;border-left:3px solid {C_GREEN};">
                    <div style="font:600 0.72rem Arial;color:{C_GREY};text-transform:uppercase;letter-spacing:0.3px;">ESG Alignment</div>
                    <div style="font:800 1.3rem Arial;color:{("#1B8C3A" if esg_sc >= 7 else (C1 if esg_sc >= 4 else C_RED))};margin-top:3px;">{esg_sc:.1f}<span style="font:400 0.75rem Arial;color:{C_GREY};"> / 10</span></div>
                    <div style="font:400 0.68rem Arial;color:{C_GREY};margin-top:2px;">Sustainability benefit</div>
                </div>
            </div>
        </div>''', unsafe_allow_html=True)
        with sb_col2:
            with st.popover("?"):
                st.markdown(f'''
**Grid Relief** ({grid_relief:.1f}/10)  
Raw improvement: {selected.get('technical_improvement_pct', 0):.1f}% → sigmoid mapping → {grid_relief:.1f}

**Cost Efficiency** ({cost_sc:.1f}/10)  
`10 × (1 - cost / max_capex_cost)` → {cost_sc:.1f}

**Speed to Value** ({speed_sc:.1f}/10)  
`(feasibility + deployment_speed) / 2` → {speed_sc:.1f}

**ESG Alignment** ({esg_sc:.1f}/10)  
Behavioral = 9-10, Hybrid = 7-8, Capex = 4-5

**Final** = 0.40×Relief + 0.25×Cost + 0.20×Speed + 0.15×ESG = **{selected['final_score']:.2f}**
                ''')

        # Score Waterfall - shows weighted contribution of each dimension to final score
        col_spacer, col_chart_center, col_spacer2 = st.columns([0.5, 3, 0.5])
        with col_chart_center:
            # Weighted contributions
            w_gr = grid_relief * 0.40
            w_cost = cost_sc * 0.25
            w_speed = speed_sc * 0.20
            w_esg = esg_sc * 0.15
            final = w_gr + w_cost + w_speed + w_esg

            fig = go.Figure(go.Waterfall(
                orientation="v",
                measure=["relative", "relative", "relative", "relative", "total"],
                x=["<b>Grid Relief</b>", "<b>Cost Efficiency</b>",
                   "<b>Speed to Value</b>", "<b>ESG Alignment</b>", "<b>Final Score</b>"],
                y=[w_gr, w_cost, w_speed, w_esg, 0],
                text=[f"+{w_gr:.2f}", f"+{w_cost:.2f}", f"+{w_speed:.2f}", f"+{w_esg:.2f}", f"<b>{final:.2f}</b>"],
                textposition="outside",
                textfont=dict(size=11, family="Arial"),
                connector=dict(line=dict(color="#DDDDDD", width=1)),
                increasing=dict(marker=dict(color=C1)),
                totals=dict(marker=dict(color=C_DARK)),
            ))
            fig.update_layout(
                height=270, margin=dict(t=20, b=40, l=40, r=20),
                plot_bgcolor='white', paper_bgcolor='white',
                yaxis=dict(title='<b>Weighted Score</b>', title_font=dict(size=10, family='Arial'),
                           gridcolor='#F0F0F0', tickfont=dict(size=9, family='Arial')),
                xaxis=dict(tickfont=dict(size=9, family='Arial', color=C_DARK)),
                font=dict(family='Arial', size=11),
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
            st.markdown(f'<div style="text-align:center;font:400 0.8rem Arial;color:{C_GREY};margin-top:-8px;">Waterfall shows how each weighted dimension builds up to the final composite score.</div>', unsafe_allow_html=True)

        # Impact Assessment
        st.markdown(f'<div class="sub-head">Impact Assessment (Grid Relief)</div>', unsafe_allow_html=True)
        st.caption("Grid stress comparison before and after applying the selected solution.")
        bs = data.get("base_summary", {})
        impr = selected.get("technical_improvement_pct", 0)
        after_stress = bs.get("grid_stress_score", 0) * (1 - impr / 100)

        # Severity line
        stress_val = bs.get('grid_stress_score', 0)
        if stress_val > 3000: sev_txt, sev_clr = "Critical", C_RED
        elif stress_val > 1000: sev_txt, sev_clr = "High", C1
        elif stress_val > 300: sev_txt, sev_clr = "Moderate", C2
        else: sev_txt, sev_clr = "Low", C_GREEN
        st.markdown(f'''<div style="font:400 0.82rem Arial;color:{C_DARK};margin-bottom:8px;">
            <b>Current severity:</b> <b style="color:{sev_clr};">{sev_txt}</b> (score: {stress_val:.0f})
        </div>''', unsafe_allow_html=True)
        with st.popover("ⓘ"):
            st.markdown(f'''
**Grid Stress Score**

Composite metric combining equipment overloads and voltage violations across the 24-hour simulation.

**Formula:**  
`Score = 20×convergence_failures + 5×line_overloads + 6×transformer_overloads + 2×voltage_violations`

**Weights reflect severity:** Convergence failures (20×) indicate near-collapse conditions. Transformer overloads (6×) damage expensive long-lead assets. Line overloads (5×) cause thermal degradation. Voltage violations (2×) affect power quality.

**Scale:**  
- 0 = No issues | <300 = Low | 300-1000 = Moderate | 1000-3000 = High | >3000 = Critical

Current: **{stress_val:.0f}** ({sev_txt})
            ''')

        ba1, ba2, ba3 = st.columns(3)
        ba1.markdown(f'''<div class="card" style="border-left:4px solid {C_RED};">
            <div class="lbl" style="color:{C_RED};">Before (No Intervention)</div>
            <div class="val">{bs.get('grid_stress_score', 0):.0f}</div>
            <div class="sub">Grid stress score</div>
        </div>''', unsafe_allow_html=True)
        ba2.markdown(f'''<div class="card" style="border-left:4px solid {C_GREEN};">
            <div class="lbl" style="color:{C_GREEN};">After (Selected Solution)</div>
            <div class="val">{after_stress:.0f}</div>
            <div class="sub">↓ {impr:.1f}% reduction</div>
        </div>''', unsafe_allow_html=True)
        ba3.markdown(card_html("Technical Improvement", f"{impr:.1f}%", "Overload and violation reduction"), unsafe_allow_html=True)

        # Before/After Grid Map
        st.markdown(f'<div style="font:700 0.82rem Arial,sans-serif;color:{C_DARK};margin:14px 0 5px;">Grid Stress Visualization</div>', unsafe_allow_html=True)
        st.markdown(f'''<div style="font:400 0.75rem Arial;color:{C_GREY};margin-bottom:6px;">
            <span style="color:#C92A2A;font-weight:bold;">Red</span> nodes indicate stressed equipment.
            <span style="color:#1565C0;font-weight:bold;">Blue</span> indicates resolved.
            <span style="color:#E88D14;font-weight:bold;">Orange</span> indicates partially resolved.
        </div>''', unsafe_allow_html=True)
        if use_gis_map:
            ba_before, ba_after = render_before_after_map_epri(impr)
            if ba_before and ba_after:
                col_ba1, col_ba2 = st.columns(2)
                with col_ba1:
                    st.plotly_chart(ba_before, use_container_width=True)
                with col_ba2:
                    st.plotly_chart(ba_after, use_container_width=True)
        else:
            ba_map = render_before_after_map(impr)
            if ba_map:
                st.plotly_chart(ba_map, use_container_width=True)

        # Hourly comparison with non-uniform reduction (stronger during peak)
        base_results = data.get("base_results", [])
        profiles = data.get("profiles", {})
        if base_results and profiles:
            st.markdown(f'<div class="sub-head">Hourly Overload Comparison</div>', unsafe_allow_html=True)
            st.caption("Baseline line overloads vs estimated post-intervention. Zero-overload hours indicate periods where solar generation offsets demand (typically midday).")
            br_df = pd.DataFrame(base_results)

            # Non-uniform reduction: stronger during peak hours, weaker off-peak
            hours = np.arange(24)
            reduction_weight = np.where(
                (hours >= peak_start) & (hours <= peak_end),
                1.0,  # full reduction during peak
                np.where(
                    (hours >= peak_start - 2) & (hours <= peak_end + 2),
                    0.7,  # moderate near-peak
                    0.3   # minimal off-peak
                )
            )
            if len(reduction_weight) == len(br_df):
                reduction = (impr / 100) * reduction_weight
            else:
                reduction = impr / 100

            after_lines = (br_df["num_overloaded_lines"] * (1 - reduction)).clip(lower=0).astype(int)

            fig_comp = go.Figure()
            fig_comp.add_trace(go.Bar(x=br_df["time"], y=br_df["num_overloaded_lines"], name="<b>Baseline</b>", marker_color=C1, opacity=0.75))
            fig_comp.add_trace(go.Bar(x=br_df["time"], y=after_lines, name="<b>After Intervention</b>", marker_color=C_GREEN, opacity=0.75))
            fig_comp.update_layout(
                barmode="group", height=250, margin=dict(t=10, b=30),
                xaxis_title="<b>Hour</b>", yaxis_title="<b>Line Overloads (count)</b>",
                plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", font=dict(family="Arial", size=11, color=C_DARK)),
                font=dict(family="Arial", size=11),
                xaxis=dict(title_font=dict(size=10, family="Arial")),
                yaxis=dict(title_font=dict(size=10, family="Arial")),
            )
            st.plotly_chart(fig_comp, use_container_width=True)

    # ═══ RANKINGS ═════════════════════════════════════════════════════════════
    if selected_results_section == "📊 Rankings":
        st.markdown('<div class="sec-head">Portfolio Rankings</div>', unsafe_allow_html=True)
        st.caption("All solutions ranked by weighted score. Score range: 0 (worst) to 10 (best).")

        # Sort-by selector (item 9)
        sort_options = {
            "Overall Score": "final_score",
            "Grid Relief": "grid_relief_score",
            "Cost Efficiency": "cost_score",
            "Speed to Value": "speed_to_value_score",
            "ESG Alignment": "esg_score",
        }
        sort_choice = st.selectbox("Sort by", list(sort_options.keys()), index=0,
                                   help="Re-rank portfolios by a single dimension to see the best option for that specific criterion.")
        sort_key = sort_options[sort_choice]

        # Re-sort ranking by selected dimension
        ranking_sorted = sorted(ranking, key=lambda r: r.get(sort_key, 0), reverse=True)

        for idx, row in enumerate(ranking_sorted[:3]):
            badges = ["🥇", "🥈", "🥉"]
            badges = ["🥇", "🥈", "🥉"]
            cls = "rank-card top" if idx == 0 else "rank-card"
            speed_val = row.get("speed_to_value_score", (row.get("feasibility_score", 0) + row.get("deployment_score", 0)) / 2)
            # Color score by value
            rs = row["final_score"]
            rs_color = C_GREEN if rs >= 8 else ("#7CB342" if rs >= 6 else (C2 if rs >= 4 else C_RED))
            st.markdown(f'''<div class="{cls}">
                <div style="display:flex;align-items:center;justify-content:space-between;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <span style="font-size:1.1rem;">{badges[idx]}</span>
                        <span style="font:700 0.92rem Arial;color:{C_DARK};">{row["portfolio_name"]}</span>
                    </div>
                    <span style="font:800 1.1rem Arial;color:{rs_color};">{row["final_score"]:.2f} / 10</span>
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:6px;margin-top:6px;">
                    <div><span style="font:600 0.7rem Arial;color:{C_GREY};">Grid Relief</span><br><b style="color:{C1};">{row.get("technical_improvement_pct", 0):.1f}%</b></div>
                    <div><span style="font:600 0.7rem Arial;color:{C_GREY};">Cost</span><br><b style="color:{C1};">{row.get("cost_score", 0):.1f}/10</b></div>
                    <div><span style="font:600 0.7rem Arial;color:{C_GREY};">Speed</span><br><b style="color:{C1};">{speed_val:.1f}/10</b></div>
                    <div><span style="font:600 0.7rem Arial;color:{C_GREY};">ESG</span><br><b style="color:{C1};">{row.get("esg_score", 0):.1f}/10</b></div>
                </div>
            </div>''', unsafe_allow_html=True)

        if len(ranking_sorted) > 3:
            top_n = min(10, len(ranking_sorted))
            chart_data = ranking_sorted[:top_n]
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                y=[r["portfolio_name"] for r in chart_data][::-1],
                x=[r["final_score"] for r in chart_data][::-1],
                orientation='h', marker_color=[C1 if i == top_n - 1 else C2 for i in range(top_n)],
                text=[f'<b>{r["final_score"]:.2f}</b>' for r in chart_data][::-1], textposition='inside',
                insidetextanchor='middle', textfont=dict(color='white', size=11, family='Arial')
            ))
            fig_bar.update_layout(
                height=max(250, top_n * 36), margin=dict(t=10, l=260, b=20, r=40),
                xaxis_title="Score (0-10)", plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Arial", size=11),
                legend=dict(font=dict(family="Arial", size=11))
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown(f'<div class="sub-head">Full Results</div>', unsafe_allow_html=True)
        rank_df = pd.DataFrame(ranking_sorted)
        if "speed_to_value_score" not in rank_df.columns and "feasibility_score" in rank_df.columns:
            rank_df["speed_to_value_score"] = (rank_df["feasibility_score"] + rank_df["deployment_score"]) / 2
        display_cols = [c for c in ["portfolio_name", "final_score", "technical_improvement_pct", "cost_score", "speed_to_value_score", "esg_score"] if c in rank_df.columns]
        st.dataframe(rank_df[display_cols] if display_cols else rank_df, use_container_width=True, height=300)

    # ═══ BASELINE ═════════════════════════════════════════════════════════════
    if selected_results_section == "🔍 Baseline":
        st.markdown('<div class="sec-head">Baseline Grid Assessment</div>', unsafe_allow_html=True)
        st.caption("24-hour simulation under projected future load without any intervention.")

        bs = data.get("base_summary", {})
        c1_, c2_, c3_, c4_ = st.columns(4)
        c1_.markdown(card_html("Grid Stress Score", f"{bs.get('grid_stress_score', 0):.0f}", "Higher → more violations"), unsafe_allow_html=True)
        c2_.markdown(card_html("Line Overloads", str(bs.get('total_line_overloads', 0)), "Total across 24 hours"), unsafe_allow_html=True)
        c3_.markdown(card_html("Transformer Overloads", str(bs.get('total_transformer_overloads', 0)), "Total across 24 hours"), unsafe_allow_html=True)
        c4_.markdown(card_html("Undervoltage Events", str(bs.get('total_undervoltage_buses', 0)), "Below 0.95 per-unit"), unsafe_allow_html=True)

        # Grid stress severity indicator
        stress = bs.get('grid_stress_score', 0)
        if stress > 3000:
            severity_txt = "Critical"
            sev_color = C_RED
        elif stress > 1000:
            severity_txt = "High"
            sev_color = C1
        elif stress > 300:
            severity_txt = "Moderate"
            sev_color = C2
        else:
            severity_txt = "Low"
            sev_color = C_GREEN
        st.markdown(f'''<div style="font:400 0.85rem Arial;color:{C_DARK};margin:8px 0;">
            <b>Current severity:</b> <b style="color:{sev_color};">{severity_txt}</b> (score: {stress:.0f})
        </div>''', unsafe_allow_html=True)

        base_results = data.get("base_results", [])
        if base_results:
            st.markdown(f'<div class="sub-head">Hourly Violation Breakdown</div>', unsafe_allow_html=True)
            st.caption("Stacked equipment overloads and voltage violations at each hour.")
            br_df = pd.DataFrame(base_results)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=br_df["time"], y=br_df["num_overloaded_lines"], name="<b>Line Overloads</b>", marker_color=C1))
            fig2.add_trace(go.Bar(x=br_df["time"], y=br_df["num_overloaded_transformers"], name="<b>Transformer Overloads</b>", marker_color=C2))
            fig2.add_trace(go.Bar(x=br_df["time"], y=br_df["undervoltage_buses"], name="<b>Undervoltage</b>", marker_color=C_RED))
            fig2.update_layout(
                barmode="stack", height=270, margin=dict(t=10, b=30),
                xaxis_title="<b>Hour of Day</b>", yaxis_title="<b>Count</b>",
                plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", y=1.1, x=0.5, xanchor="center", font=dict(family="Arial", size=11, color=C_DARK)),
                font=dict(family="Arial", size=11),
                xaxis=dict(title_font=dict(size=10, family="Arial")),
                yaxis=dict(title_font=dict(size=10, family="Arial")),
            )
            st.plotly_chart(fig2, use_container_width=True)

        if use_gis_map:
            st.markdown(f'<div class="sub-head">Real US Feeder - EPRI Test Circuit 5 (Roswell, GA)</div>', unsafe_allow_html=True)
            st.caption("981-bus real EPRI topology - Illustrative suburban placement - EV, Solar, Data Center assets placed - Hover substation for details")
            grid_fig = render_gis_map()
        else:
            st.markdown(f'<div class="sub-head">IEEE 123-Bus Feeder (Simulation Model)</div>', unsafe_allow_html=True)
            st.caption("123-bus test feeder placed on US suburban street map - This is the grid being simulated - Hover nodes for asset details")
            grid_fig = render_grid_map()
        if grid_fig:
            st.plotly_chart(grid_fig, use_container_width=True)

    # ═══ PROFILES ═════════════════════════════════════════════════════════════
    if selected_results_section == "📈 Profiles":
        st.markdown('<div class="sec-head">24-Hour Load Profiles</div>', unsafe_allow_html=True)
        st.caption("Synthetic demand and generation curves shaped by scenario selections, scaled by planning horizon.")

        profiles = data.get("profiles", {})
        if profiles:
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(
                x=profiles["time"], y=profiles["feeder_mult"], name="<b>Feeder Load Multiplier</b>",
                line=dict(width=2.5, color=C_DARK), fill='tozeroy', fillcolor='rgba(45,45,45,0.04)'
            ))
            fig3.add_trace(go.Scatter(
                x=profiles["time"], y=profiles["ev_mw"], name="<b>EV Demand (MW)</b>",
                line=dict(width=2.5, color=C1), fill='tozeroy', fillcolor='rgba(216,86,4,0.06)'
            ))
            fig3.add_trace(go.Scatter(
                x=profiles["time"], y=profiles["solar_mw"], name="<b>Solar Generation (MW)</b>",
                line=dict(width=2.5, color=C_GREEN, dash="dot")
            ))
            fig3.add_trace(go.Scatter(
                x=profiles["time"], y=profiles["dc_mw"], name="<b>Data Center (MW)</b>",
                line=dict(width=2.5, color=C_RED, dash="dash")
            ))
            fig3.update_layout(
                height=380, margin=dict(t=50, b=50),
                xaxis_title="<b>Hour of Day</b>", yaxis_title="<b>Value</b>",
                plot_bgcolor="white", paper_bgcolor="white",
                legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center", font=dict(family="Arial", size=11, color=C_DARK)),
                font=dict(family="Arial", size=11),
                xaxis=dict(title_font=dict(size=10, family="Arial"), tickangle=-45),
                yaxis=dict(title_font=dict(size=10, family="Arial")),
            )
            st.plotly_chart(fig3, use_container_width=True)

            st.markdown(f'''<div style="background:white;border-radius:8px;padding:16px 20px;margin:10px 0;border:1px solid #EBEBEB;border-top:3px solid {C1};">
                <div style="font:700 0.82rem Arial;color:{C_DARK};margin-bottom:10px;">Profile Descriptions</div>
                <div style="font:400 0.82rem Arial;color:{C_DARK};line-height:2.0;">
                <span style="display:inline-block;width:6px;height:6px;background:{C_DARK};border-radius:50%;margin-right:8px;vertical-align:middle;"></span><b style="color:{C_DARK};">Feeder Multiplier</b> - Scales all existing loads (morning and evening peaks, 3% annual growth).<br>
                <span style="display:inline-block;width:6px;height:6px;background:{C1};border-radius:50%;margin-right:8px;vertical-align:middle;"></span><b style="color:{C1};">EV Demand</b> - Peaks 19:00-22:00 based on US residential charging research.<br>
                <span style="display:inline-block;width:6px;height:6px;background:{C_GREEN};border-radius:50%;margin-right:8px;vertical-align:middle;"></span><b style="color:{C_GREEN};">Solar Generation</b> - Bell curve sunrise to sunset, reduces net demand at midday.<br>
                <span style="display:inline-block;width:6px;height:6px;background:{C_RED};border-radius:50%;margin-right:8px;vertical-align:middle;"></span><b style="color:{C_RED};">Data Center</b> - Near-constant baseload at 97% utilization.
                </div>
                <div style="font-style:italic;font:400 0.7rem Arial;color:{C_GREY};margin-top:10px;padding-top:8px;border-top:1px solid #EBEBEB;">
                Sources: EIA Annual Energy Outlook 2024 (EV growth), SEIA Solar Market Insight 2024 (solar adoption), DOE Grid Deployment Office 2024 (DC load patterns), FERC Form 1 (3% base growth consistent with 2020-2024 US distribution load growth of 2.5-3.5% annually).
                </div>
            </div>''', unsafe_allow_html=True)

            # AI-generated profile interpretation
            peak_ev = max(profiles.get("ev_mw", [0]))
            peak_solar = max(profiles.get("solar_mw", [0]))
            peak_dc = max(profiles.get("dc_mw", [0]))
            peak_feeder = max(profiles.get("feeder_mult", [0]))
            ev_peak_hr = profiles["time"][profiles["ev_mw"].index(peak_ev)] if peak_ev > 0 else "N/A"
            solar_peak_hr = profiles["time"][profiles["solar_mw"].index(peak_solar)] if peak_solar > 0 else "N/A"
            # Net demand analysis
            net_demand = [profiles["feeder_mult"][i] + profiles["ev_mw"][i] + profiles["dc_mw"][i] - profiles["solar_mw"][i]
                         for i in range(len(profiles["time"]))]
            peak_net_hr = profiles["time"][net_demand.index(max(net_demand))]
            min_net_hr = profiles["time"][net_demand.index(min(net_demand))]
            active_solution_labels = ", ".join([a["label"] for a in _active_interventions(selected_solution)]) or "No active intervention"

            # LLM-generated portfolio linkage
            try:
                from feederiq.backend.llm_client import invoke_llm
                linkage_system = "You are a distribution grid planning analyst. Write exactly 4-5 sentences of portfolio linkage analysis. Be specific about timing, synergies, and outcomes. Plain text only, no markdown."
                linkage_user = f"""Profile context:
- Feeder peaks at {peak_feeder:.2f}x base load
- EV peak: {peak_ev:.2f} MW at {ev_peak_hr}
- Solar peak: {peak_solar:.2f} MW at {solar_peak_hr}
- Data center constant: {peak_dc:.2f} MW
- Worst stress hour: {peak_net_hr}
- Lowest stress hour: {min_net_hr}

Selected portfolio: {selected_solution.get('portfolio_name', 'N/A')}
Active interventions: {active_solution_labels}
Grid stress reduction: {selected_solution.get('technical_improvement_pct', 0):.1f}%

Explain: WHY this portfolio addresses the stress pattern, HOW interventions work together, WHAT hours benefit most, and the expected operational outcome."""
                linkage_text = invoke_llm(linkage_system, linkage_user, max_tokens=500)
                if not linkage_text:
                    raise ValueError("Empty LLM response")
            except Exception:
                linkage_text = (
                    f"{selected_solution.get('portfolio_name', 'N/A')} applies {active_solution_labels}, "
                    f"targeting the {peak_net_hr} stress window when EV charging ({peak_ev:.2f} MW) coincides with data center base load ({peak_dc:.2f} MW) "
                    f"and solar output drops to zero. The interventions work together by shifting controllable EV demand to off-peak hours while staged load connection "
                    f"defers the data center's full impact. This reduces thermal loading on constrained lines during the critical 17:00-21:00 window, "
                    f"achieving {selected_solution.get('technical_improvement_pct', 0):.1f}% grid stress reduction with fastest deployment path."
                )

            st.markdown(f'''<div style="background:#FFF8F0;border-radius:8px;padding:14px 18px;margin:10px 0;border:1px solid #F5E6D3;border-left:3px solid {C1};">
                <div style="font:700 0.78rem Arial;color:{C1};margin-bottom:6px;">Profile Summary</div>
                <div style="font:400 0.82rem Arial;color:{C_DARK};line-height:1.8;">
                The feeder peaks at <b>{peak_feeder:.2f}x</b> base load during evening hours, compounded by
                EV charging demand of <b>{peak_ev:.2f} MW</b> (peak at {ev_peak_hr}) and a constant data center
                draw of <b>{peak_dc:.2f} MW</b>. Solar generation peaks at <b>{peak_solar:.2f} MW</b> ({solar_peak_hr}),
                providing midday relief but creating a steep ramp from afternoon to evening.
                <b>Critical window:</b> Net system stress is highest at <b>{peak_net_hr}</b> when EV charging
                coincides with evening feeder load and solar output has dropped to zero, and lowest at
                <b>{min_net_hr}</b> during peak solar production.
                <br><br>
                <b>Selected portfolio linkage: {selected_solution.get('portfolio_name', 'N/A')}</b><br>
                {linkage_text}
                </div>
            </div>''', unsafe_allow_html=True)

            # Selected-solution implementation details (LLM-generated from intervention references)
            st.markdown(
                _implementation_pack_html(
                    implementation_pack,
                    selected_solution.get("portfolio_name", "Selected solution"),
                    intervention_level_guide,
                    implementation_summary_text,
                ),
                unsafe_allow_html=True,
            )

    # ═══ MEMO ═════════════════════════════════════════════════════════════════
    if selected_results_section == "📝 Memo":
        st.markdown('<div class="sec-head">Planning Decision Memo</div>', unsafe_allow_html=True)
        memo = selected_memo or data.get("memo", "")

        # Fetch LLM-generated memo on-demand if not yet rich
        if not memo or ("## Executive Summary" not in memo) or len(memo) < 500:
            study_id = data.get("study_id", "")
            if study_id:
                try:
                    import requests
                    memo_resp = requests.get(f"http://localhost:8000/study/{study_id}/memo", timeout=30)
                    if memo_resp.status_code == 200:
                        memo = memo_resp.json().get("memo", memo)
                except Exception:
                    pass

        if memo:
            # Remove duplicate title and custom implementation section (rendered once below with tooltips)
            memo_clean = memo.replace("# FeederIQ Planning Decision Memo\n", "").strip()
            memo_clean = re.sub(r'## Real-World Implementation Plan.*?(?=## |$)', '', memo_clean, flags=re.DOTALL).strip()
            st.markdown(f'<div class="memo-area">{memo_clean}</div>', unsafe_allow_html=True)

            # LLM-generated detailed recommendation on the proposed solution
            try:
                from feederiq.backend.llm_client import invoke_llm
                reco_system = "You are a senior PwC utility consulting partner. Write an authoritative 6-8 sentence executive recommendation. Boardroom tone, third person, plain text only."
                reco_user = f"""Context:
- Selected solution: {selected_solution.get('portfolio_name', 'N/A')}
- Final score: {selected_solution.get('final_score', 0):.2f}/10
- Grid relief: {selected_solution.get('technical_improvement_pct', 0):.1f}% stress reduction
- Grid stress before: {data.get('base_summary', {}).get('grid_stress_score', 0):.0f}
- Active interventions: {', '.join([a['label'] + ' (' + a['level_label'] + ')' for a in _active_interventions(selected_solution)])}
- Planning horizon: {data.get('scenario', {}).get('horizon_label', '12m')}
- Feeder: {'EPRI ckt5 (981 buses)' if use_gis_map else 'IEEE 123-bus'}

Write a recommendation that: states the recommended action, quantifies expected benefit, identifies implementation sequencing, notes dependencies and risk mitigations, recommends governance checkpoints, and ends with a clear call to action."""
                reco_text = invoke_llm(reco_system, reco_user, max_tokens=600)
                if not reco_text:
                    raise ValueError("Empty")
                st.markdown(f'''<div style="background:#F0FFF4;border-radius:8px;padding:14px 18px;margin:14px 0;border:1px solid #C8E4DB;border-left:3px solid {C_GREEN};">
                    <div style="font:700 0.82rem Arial;color:{C_GREEN};margin-bottom:8px;">Recommendation on Proposed Solution</div>
                    <div style="font:400 0.82rem Arial;color:{C_DARK};line-height:1.8;">{reco_text}</div>
                </div>''', unsafe_allow_html=True)
            except Exception:
                # Fallback static recommendation
                active_labels = ', '.join([a['label'] for a in _active_interventions(selected_solution)]) or "selected interventions"
                st.markdown(f'''<div style="background:#F0FFF4;border-radius:8px;padding:14px 18px;margin:14px 0;border:1px solid #C8E4DB;border-left:3px solid {C_GREEN};">
                    <div style="font:700 0.82rem Arial;color:{C_GREEN};margin-bottom:8px;">Recommendation on Proposed Solution</div>
                    <div style="font:400 0.82rem Arial;color:{C_DARK};line-height:1.8;">
                    The planning team recommends proceeding with {selected_solution.get('portfolio_name', 'the selected portfolio')} as the primary intervention strategy, delivering {selected_solution.get('technical_improvement_pct', 0):.1f}% grid stress reduction from a baseline score of {data.get('base_summary', {}).get('grid_stress_score', 0):.0f}. This portfolio combines {active_labels} to address thermal overloads and voltage violations during the critical evening peak window. Implementation should follow a phased approach: initiate program design and stakeholder engagement within 30 days, secure regulatory approvals and customer commitments by day 90, and achieve operational deployment within the {data.get('scenario', {}).get('horizon_label', '12-month')} planning horizon. Key dependencies include metering infrastructure readiness, customer enrollment targets, and interconnection agreement execution. A quarterly governance review is recommended to track KPI performance against the baseline and adjust intervention levels based on actual load growth. The steering committee should approve the implementation business case within 2 weeks to maintain schedule alignment.
                    </div>
                </div>''', unsafe_allow_html=True)

            st.markdown(
                _implementation_pack_html(
                    implementation_pack,
                    selected_solution.get("portfolio_name", "Selected solution"),
                    intervention_level_guide,
                    implementation_summary_text,
                ),
                unsafe_allow_html=True,
            )

            # Download button for memo as PDF
            st.markdown("---")

            def _build_pdf_memo(data, memo_text, selected_portfolio, implementation_content, implementation_summary):
                """Generate a professional 3-4 page PDF memo with PwC branding."""
                from fpdf import FPDF
                import io

                # PwC brand colors
                PWC_ORANGE = (216, 86, 4)
                PWC_GOLD = (232, 141, 20)
                PWC_DARK = (45, 45, 45)
                PWC_GREY = (100, 100, 100)
                PWC_LIGHT = (255, 243, 231)

                class MemoDoc(FPDF):
                    def _safe_text(self, text):
                        t = str(text or "")
                        repl = {
                            "\u2013": "-",
                            "\u2014": "-",
                            "\u2018": "'",
                            "\u2019": "'",
                            "\u201c": '"',
                            "\u201d": '"',
                            "\u2026": "...",
                            "\u00a0": " ",
                            "\u2009": " ",
                            "\u200b": "",
                            "\ufeff": "",
                            "\u2265": ">=",
                            "\u2264": "<=",
                            "\u2192": "->",
                            "\u00b1": "+/-",
                            "\u2022": "-",
                        }
                        for src, dst in repl.items():
                            t = t.replace(src, dst)
                        t = re.sub(r"\s+", " ", t).strip()
                        return t.encode("latin-1", "replace").decode("latin-1")

                    def _fit_text(self, text, width_mm):
                        txt = self._safe_text(text)
                        if self.get_string_width(txt) <= max(2, width_mm - 2):
                            return txt
                        suffix = "..."
                        while txt and self.get_string_width(txt + suffix) > max(2, width_mm - 2):
                            txt = txt[:-1]
                        return (txt + suffix) if txt else suffix

                    def _wrap_text(self, text, width_mm):
                        txt = self._safe_text(text)
                        if not txt:
                            return [""]
                        max_w = max(2, width_mm)
                        words = txt.split(" ")
                        lines = []
                        current = ""

                        for word in words:
                            candidate = word if not current else f"{current} {word}"
                            if self.get_string_width(candidate) <= max_w:
                                current = candidate
                                continue

                            if current:
                                lines.append(current)
                                current = ""

                            # Break very long tokens if needed.
                            token = ""
                            for ch in word:
                                cand = token + ch
                                if self.get_string_width(cand) <= max_w:
                                    token = cand
                                else:
                                    if token:
                                        lines.append(token)
                                    token = ch
                            current = token

                        if current:
                            lines.append(current)
                        return lines or [""]

                    def header(self):
                        # PwC logo from the same official SVG used in frontend
                        self.set_draw_color(*PWC_ORANGE)
                        self.set_line_width(0.8)
                        self.line(10, 10, 200, 10)
                        logo_path = Path(__file__).resolve().parent / "assets" / "pwc_logo.svg"
                        if logo_path.exists():
                            # Ensure default-colored SVG paths render consistently across pages.
                            self.set_draw_color(0, 0, 0)
                            self.set_fill_color(0, 0, 0)
                            self.set_text_color(0, 0, 0)
                            self.image(str(logo_path), x=184, y=11.8, w=16)
                        else:
                            self.set_font("Times", "B", 14)
                            self.set_text_color(26, 26, 26)
                            self.set_y(12)
                            self.cell(0, 6, "pwc", align="R", new_x="LMARGIN", new_y="NEXT")
                        self.set_y(18)

                    def footer(self):
                        self.set_y(-18)
                        self.set_draw_color(200, 200, 200)
                        self.set_line_width(0.3)
                        self.line(10, self.get_y(), 200, self.get_y())
                        self.ln(3)
                        self.set_font("Helvetica", "", 7)
                        self.set_text_color(*PWC_GREY)
                        self.cell(0, 4, "PwC Advisory  |  FeederIQ Agentic Distribution Planning", new_x="END")
                        self.cell(0, 4, f"Page {self.page_no()}/{{nb}}", align="R", new_x="LMARGIN", new_y="NEXT")

                    def section_title(self, title):
                        self.ln(6)
                        self.set_font("Helvetica", "B", 13)
                        self.set_text_color(*PWC_DARK)
                        self.cell(0, 8, self._safe_text(title), new_x="LMARGIN", new_y="NEXT")
                        self.set_draw_color(*PWC_ORANGE)
                        self.set_line_width(0.6)
                        self.line(10, self.get_y(), 60, self.get_y())
                        self.ln(5)

                    def subsection_title(self, title):
                        self.ln(3)
                        self.set_font("Helvetica", "B", 10)
                        self.set_text_color(*PWC_DARK)
                        self.cell(0, 6, self._safe_text(title), new_x="LMARGIN", new_y="NEXT")
                        self.ln(2)

                    def body_text(self, text):
                        if self.get_y() > 250:
                            self.add_page()
                        self.set_font("Helvetica", "", 9.5)
                        self.set_text_color(60, 60, 60)
                        self.multi_cell(0, 5.5, self._safe_text(text))
                        self.ln(2)

                    def table_header(self, cols, widths):
                        self.set_font("Helvetica", "B", 8.5)
                        self.set_text_color(*PWC_DARK)
                        self.set_fill_color(*PWC_LIGHT)
                        self.set_draw_color(229, 208, 186)
                        self.set_x(self.l_margin)
                        for col, w in zip(cols, widths):
                            self.cell(w, 7, self._fit_text(col, w), border=1, fill=True, align="C")
                        self.ln(7)

                    def table_row(self, cells, widths, bold_first=False, aligns=None):
                        aligns = aligns or ["L"] * len(cells)
                        self.set_draw_color(235, 222, 209)
                        line_h = 4.1

                        wrapped = []
                        max_lines = 1
                        for i, (cell, w) in enumerate(zip(cells, widths)):
                            if i == 0 and bold_first:
                                self.set_font("Helvetica", "B", 9)
                            else:
                                self.set_font("Helvetica", "", 9)
                            lines = self._wrap_text(cell, w - 2)
                            wrapped.append(lines)
                            max_lines = max(max_lines, len(lines))

                        row_h = max(6.5, max_lines * line_h + 2)

                        # Check if row fits on current page, if not add page
                        if self.get_y() + row_h > 270:
                            self.add_page()

                        y0 = self.get_y()
                        self.set_x(self.l_margin)

                        for i, (lines, w) in enumerate(zip(wrapped, widths)):
                            x = self.get_x()
                            self.rect(x, y0, w, row_h)

                            if i == 0 and bold_first:
                                self.set_font("Helvetica", "B", 9)
                                self.set_text_color(*PWC_DARK)
                            else:
                                self.set_font("Helvetica", "", 9)
                                self.set_text_color(70, 70, 70)

                            align = aligns[i] if i < len(aligns) else "L"
                            block_h = len(lines) * line_h
                            y_txt = y0 + (row_h - block_h) / 2
                            for j, ln in enumerate(lines):
                                self.set_xy(x + 1, y_txt + j * line_h)
                                self.cell(w - 2, line_h, ln, border=0, align=align)

                            self.set_xy(x + w, y0)

                        self.set_xy(self.l_margin, y0 + row_h)

                    def highlight_box(self, text, color=PWC_ORANGE):
                        self.set_draw_color(*color)
                        self.set_line_width(0.4)
                        x = self.get_x()
                        y = self.get_y()
                        self.rect(x, y, 190, 10)
                        self.set_xy(x + 4, y + 2)
                        self.set_font("Helvetica", "B", 9.5)
                        self.set_text_color(*color)
                        self.cell(0, 6, self._safe_text(text))
                        self.set_xy(x, y + 12)

                pdf = MemoDoc()
                pdf.alias_nb_pages()
                pdf.set_auto_page_break(auto=False)

                # ── PAGE 1: Cover + Executive Summary ──
                pdf.add_page()

                # Document title block
                pdf.set_font("Helvetica", "B", 24)
                pdf.set_text_color(*PWC_DARK)
                pdf.cell(0, 12, "Distribution Planning", new_x="LMARGIN", new_y="NEXT")
                pdf.set_font("Helvetica", "", 16)
                pdf.set_text_color(*PWC_GREY)
                pdf.cell(0, 10, "Decision Memo", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(*PWC_GREY)
                pdf.cell(0, 6, "FeederIQ Agentic Analysis  |  IEEE 123-Bus Test Feeder", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, f"Date: {pd.Timestamp.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT")
                pdf.cell(0, 6, "Classification: Confidential", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(8)

                scenario = data.get('scenario', {})
                top_rec = selected_portfolio or data.get('top_recommendation', {})
                bs_data = data.get('base_summary', {})
                ranking = data.get('ranking', [])
                ranking_by_name = {r.get('portfolio_name', ''): idx + 1 for idx, r in enumerate(ranking)}
                ordered_alternatives = [top_rec] + [
                    r for r in ranking if r.get('portfolio_name') != top_rec.get('portfolio_name')
                ]

                def _clip(text, max_len=42):
                    t = str(text)
                    return t if len(t) <= max_len else (t[: max_len - 3] + "...")

                severity = "Critical" if bs_data.get('grid_stress_score', 0) > 3000 else ("High" if bs_data.get('grid_stress_score', 0) > 1000 else ("Moderate" if bs_data.get('grid_stress_score', 0) > 300 else "Low"))

                # Executive Summary
                pdf.section_title("1. Executive Summary")
                pdf.body_text(
                    f"This memo presents findings from an AI-driven distribution planning analysis of the "
                    f"IEEE 123-bus test feeder under projected load growth over a {scenario.get('horizon_label', '12m')} "
                    f"planning horizon. The study evaluates the impact of concurrent EV charging growth "
                    f"({scenario.get('ev_level', 'Base')}), distributed solar adoption ({scenario.get('solar_level', 'Base')}), "
                    f"and data center interconnection ({scenario.get('dc_level', 'Moderate')}) on feeder hosting capacity."
                )
                pdf.body_text(
                    f"Baseline analysis reveals {severity.lower()}-severity grid stress (score: "
                    f"{bs_data.get('grid_stress_score', 0):.0f}) with {bs_data.get('total_line_overloads', 0)} line overloads, "
                    f"{bs_data.get('total_transformer_overloads', 0)} transformer overloads, and "
                    f"{bs_data.get('total_undervoltage_buses', 0)} undervoltage events across a 24-hour simulation period."
                )
                pdf.body_text(
                    f"The recommended non-wires alternative achieves {top_rec.get('technical_improvement_pct', 0):.1f}% "
                    f"grid stress reduction with a composite score of {top_rec.get('final_score', 0):.2f}/10, "
                    f"balancing technical effectiveness, cost efficiency, implementation speed, and sustainability."
                )

                # Key Finding highlight
                pdf.ln(2)
                nwa_text = ("Non-wires alternatives fully resolve all violations. No traditional capex required."
                           if data.get('nwa_resolved_all')
                           else f"Recommended: {top_rec.get('portfolio_name', 'N/A')} - Score: {top_rec.get('final_score', 0):.2f}/10")
                pdf.highlight_box(nwa_text)

                # ── PAGE 2: Study Configuration + Baseline ──
                pdf.add_page()
                pdf.section_title("2. Study Configuration")
                pdf.body_text(
                    "The following parameters define the planning scenario under evaluation. "
                    "Load growth assumptions are sourced from EIA Annual Energy Outlook 2024, "
                    "SEIA Solar Market Insight Q1 2024, and DOE Grid Deployment Office reports."
                )
                widths = [80, 100]
                pdf.table_header(["Parameter", "Value"], widths)
                config_rows = [
                    ("Planning Horizon", scenario.get('horizon_label', 'N/A')),
                    ("EV Growth Scenario", scenario.get('ev_level', 'N/A')),
                    ("Solar Adoption", scenario.get('solar_level', 'N/A')),
                    ("Data Center Load", scenario.get('dc_level', 'N/A')),
                    ("Data Source", "Real profiles (DOE openEDI)" if scenario.get('use_real_data') else "Synthetic parametric profiles"),
                    ("Feeder Model", "IEEE 123-bus (modified)"),
                    ("Simulation Engine", "OpenDSS QSTS (24h, hourly)"),
                    ("Portfolios Evaluated", str(len(ranking))),
                ]
                for label, val in config_rows:
                    pdf.table_row([label, val], widths, bold_first=True)
                pdf.ln(4)

                # Baseline Assessment
                pdf.section_title("3. Baseline Assessment")
                pdf.body_text(
                    "The baseline represents projected feeder conditions at the end of the planning horizon "
                    "without any intervention. A 24-hour power flow simulation identifies equipment thermal "
                    "violations, voltage deviations, and composite grid stress."
                )

                pdf.subsection_title("3.1 Grid Health Metrics")
                widths_bl = [118, 72]
                pdf.table_header(["Metric", "Value"], widths_bl)
                baseline_rows = [
                    ("Grid Stress Score", f"{bs_data.get('grid_stress_score', 0):.0f}  ({severity})"),
                    ("Total Line Overloads (24h)", str(bs_data.get('total_line_overloads', 0))),
                    ("Total Transformer Overloads (24h)", str(bs_data.get('total_transformer_overloads', 0))),
                    ("Undervoltage Events (< 0.95 p.u.)", str(bs_data.get('total_undervoltage_buses', 0))),
                    ("Convergence Failures", str(bs_data.get('convergence_failures', 0))),
                    ("Peak Hour Violations", f"{bs_data.get('peak_overloaded_lines', 'N/A')} lines, {bs_data.get('peak_overloaded_xfmrs', 'N/A')} transformers"),
                ]
                for label, val in baseline_rows:
                    pdf.table_row([label, val], widths_bl, bold_first=True)
                pdf.ln(3)

                pdf.subsection_title("3.2 Severity Classification")
                widths_sev = [120, 70]
                pdf.table_header(["Classification Rule", "Assessment"], widths_sev)
                sev_rows = [
                    ("0-299", "Low"),
                    ("300-1000", "Moderate"),
                    ("1001-3000", "High"),
                    (">3000", "Critical"),
                    (f"Current score: {bs_data.get('grid_stress_score', 0):.0f}", severity),
                ]
                for idx, (rule, cls) in enumerate(sev_rows):
                    pdf.table_row([rule, cls], widths_sev, bold_first=(idx == 4))
                pdf.ln(2)

                # ── PAGE 3: Recommendation + Scoring ──
                pdf.add_page()
                pdf.section_title("4. Recommended Solution")

                pdf.set_font("Helvetica", "B", 12)
                pdf.set_text_color(*PWC_ORANGE)
                pdf.cell(0, 8, top_rec.get('portfolio_name', 'N/A'), new_x="LMARGIN", new_y="NEXT")
                pdf.ln(3)

                pdf.subsection_title("4.1 Score Summary")
                widths_sc = [80, 50, 50]
                pdf.table_header(["Dimension", "Score", "Weight"], widths_sc)
                gr_score = top_rec.get('grid_relief_score', 0)
                cost_score = top_rec.get('cost_score', 0)
                speed_score = top_rec.get('speed_to_value_score', 0)
                esg_score = top_rec.get('esg_score', 0)
                score_rows = [
                    ("Grid Relief", f"{gr_score:.1f} / 10", "40%"),
                    ("Cost Efficiency", f"{cost_score:.1f} / 10", "25%"),
                    ("Speed to Value", f"{speed_score:.1f} / 10", "20%"),
                    ("ESG Alignment", f"{esg_score:.1f} / 10", "15%"),
                ]
                for label, val, wt in score_rows:
                    pdf.table_row([label, val, wt], widths_sc, bold_first=True, aligns=["L", "R", "R"])
                pdf.table_row([
                    "FINAL SCORE",
                    f"{top_rec.get('final_score', 0):.2f} / 10",
                    "Weighted",
                ], widths_sc, bold_first=True, aligns=["L", "R", "R"])
                pdf.ln(4)

                pdf.subsection_title("4.2 Technical Impact")
                stress_before = bs_data.get('grid_stress_score', 0)
                stress_after = stress_before * (1 - top_rec.get('technical_improvement_pct', 0) / 100)
                widths_impact = [95, 85]
                pdf.table_header(["Impact Metric", "Value"], widths_impact)
                impact_rows = [
                    ("Baseline Grid Stress", f"{stress_before:.0f}"),
                    ("Post-Solution Grid Stress", f"{stress_after:.0f}"),
                    ("Technical Improvement", f"{top_rec.get('technical_improvement_pct', 0):.1f}%"),
                    ("Residual Severity", "Resolved" if data.get('nwa_resolved_all') else "Residual constraints remain"),
                ]
                for label, val in impact_rows:
                    pdf.table_row([label, val], widths_impact, bold_first=True, aligns=["L", "R"])
                pdf.ln(2)
                if data.get('nwa_resolved_all'):
                    pdf.set_font("Helvetica", "B", 9.5)
                    pdf.set_text_color(27, 140, 58)
                    pdf.cell(0, 7, "All grid violations fully resolved through non-wires alternatives.", new_x="LMARGIN", new_y="NEXT")
                else:
                    pdf.set_font("Helvetica", "B", 9.2)
                    pdf.set_text_color(*PWC_ORANGE)
                    pdf.cell(0, 6, "Residual violations require targeted follow-on mitigation.", new_x="LMARGIN", new_y="NEXT")
                pdf.set_text_color(*PWC_DARK)
                pdf.ln(1)

                pdf.subsection_title("4.3 Alternative Solutions Considered")
                widths_alt = [130, 22, 22, 16]
                pdf.table_header(["Portfolio", "Score", "Relief %", "Rank"], widths_alt)
                for idx, r in enumerate(ordered_alternatives[:5]):
                    name = r.get('portfolio_name', 'N/A')
                    pdf.table_row([
                        name,
                        f"{r.get('final_score', 0):.2f}",
                        f"{r.get('technical_improvement_pct', 0):.1f}%",
                        f"#{ranking_by_name.get(name, idx + 1)}"
                    ], widths_alt, bold_first=(idx == 0), aligns=["L", "R", "R", "R"])
                pdf.ln(3)

                pdf.subsection_title("4.4 Real-World Implementation Plan")
                impl_rows = implementation_content.get("implementation_rows", []) if isinstance(implementation_content, dict) else []
                widths_impl = [46, 22, 92, 30]
                pdf.table_header(["Intervention", "Level", "Field Implementation", "Timeline"], widths_impl)
                for row in impl_rows[:6]:
                    pdf.table_row([
                        row.get("intervention", ""),
                        row.get("level", ""),
                        row.get("field_implementation", ""),
                        row.get("timeline", ""),
                    ], widths_impl, bold_first=True)
                pdf.ln(2)
                pdf.body_text(implementation_summary)

                # ── PAGE 4: Methodology + Next Steps ──
                pdf.add_page()
                pdf.section_title("5. Methodology")

                pdf.subsection_title("5.1 Scoring Framework")
                widths_fw = [85, 30, 75]
                pdf.table_header(["Dimension", "Weight", "Method"], widths_fw)
                framework_rows = [
                    ("Grid Relief", "40%", "Sigmoid-normalized technical improvement"),
                    ("Cost Efficiency", "25%", "Relative to full capex alternative"),
                    ("Speed to Value", "20%", "Average of feasibility and deployment speed"),
                    ("ESG Alignment", "15%", "Sustainability and material-intensity benefit"),
                ]
                for row in framework_rows:
                    pdf.table_row(list(row), widths_fw, bold_first=True, aligns=["L", "C", "L"])
                pdf.ln(2)

                pdf.subsection_title("5.2 Analytical Pipeline")
                widths_pipe = [35, 55, 100]
                pdf.table_header(["Step", "Agent", "Output"], widths_pipe)
                pipeline_rows = [
                    ("1", "Scenario", "24-hour load and DER profiles"),
                    ("2", "Simulation", "OpenDSS hourly power-flow results"),
                    ("3", "Constraint", "Thermal and voltage violation summary"),
                    ("4", "NWA", "Non-wires portfolio evaluation"),
                    ("5", "Capex", "Conventional reinforcement benchmark"),
                    ("6", "Recommendation", "Ranked portfolio and decision memo"),
                ]
                for row in pipeline_rows:
                    pdf.table_row(list(row), widths_pipe, aligns=["C", "L", "L"])
                pdf.ln(2)

                pdf.subsection_title("5.3 Agent Execution Log")
                widths_log = [20, 40, 130]
                pdf.table_header(["Status", "Step", "Message"], widths_log)
                for cp in data.get("checkpoints", []):
                    step_name = cp["step"].replace("_", " ").title().replace("Nwa", "NWA")
                    requires_approval = cp.get("requires_approval", False)
                    status = "PASS" if not requires_approval else "FLAG"
                    msg = _clip(cp.get("message", ""), 80)
                    pdf.table_row([status, step_name, msg], widths_log, aligns=["C", "L", "L"])

                pdf.ln(4)
                if pdf.get_y() > 220:
                    pdf.add_page()
                pdf.section_title("6. Recommendations & Next Steps")

                # LLM or fallback recommendation paragraph
                active_labels_pdf = ', '.join([a['label'] for a in _active_interventions(top_rec)]) or "selected interventions"
                reco_para = (
                    f"The planning team recommends proceeding with '{top_rec.get('portfolio_name', 'N/A')}' as the primary intervention strategy, "
                    f"delivering {top_rec.get('technical_improvement_pct', 0):.1f}% grid stress reduction from a baseline score of {bs_data.get('grid_stress_score', 0):.0f}. "
                    f"This portfolio combines {active_labels_pdf} to address thermal overloads and voltage violations during the critical evening peak window. "
                    f"Implementation should follow a phased approach: initiate program design within 30 days, secure approvals by day 90, "
                    f"and achieve operational deployment within the planning horizon. "
                    f"Key dependencies include metering infrastructure, customer enrollment, and interconnection agreements. "
                    f"A quarterly governance review is recommended to track KPI performance and adjust intervention levels."
                )
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(*PWC_DARK)
                if pdf.get_y() > 230:
                    pdf.add_page()
                pdf.multi_cell(0, 4.5, pdf._safe_text(reco_para))
                pdf.ln(3)

                if pdf.get_y() > 240:
                    pdf.add_page()
                widths_ns = [18, 122, 50]
                pdf.table_header(["#", "Action", "Timing"], widths_ns)
                next_steps = [
                    ("1", f"Proceed with implementation of '{top_rec.get('portfolio_name', 'N/A')}' as primary portfolio.", "0-30 days"),
                    ("2", "Complete engineering and controls design for selected interventions.", "30-90 days"),
                    ("3", "Secure regulatory/interconnection approvals and customer commitments.", "60-120 days"),
                    ("4", "Launch KPI dashboard for stress reduction and reliability tracking.", "Go-live + monthly"),
                    ("5", "Re-run study with updated growth actuals and program performance.", "Quarterly"),
                ]
                for row in next_steps:
                    pdf.table_row(list(row), widths_ns, aligns=["C", "L", "L"])

                pdf.ln(4)
                pdf.section_title("7. Disclaimers")
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(*PWC_GREY)
                use_real = scenario.get('use_real_data', False)
                data_source_text = ("real measured load profiles from the DOE Open Energy Data Initiative (openEDI)"
                                   if use_real else "synthetic parametric load growth assumptions")
                pdf.multi_cell(0, 4.5,
                    f"This analysis is based on the IEEE 123-bus test feeder model with {data_source_text}. "
                    "Results are indicative and should be validated against utility-specific asset data, "
                    "protection coordination studies, and detailed engineering analysis prior to capital commitment. "
                    "Scoring weights reflect general industry practice and may be adjusted per utility planning criteria."
                )

                buf = io.BytesIO()
                pdf.output(buf)
                buf.seek(0)
                return buf.getvalue()

            pdf_bytes = _build_pdf_memo(data, memo, selected_solution, implementation_pack, implementation_summary_text)
            st.download_button(
                "📥 Download Decision Memo (.pdf)",
                data=pdf_bytes,
                file_name=f"FeederIQ_Decision_Memo_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        st.markdown(f'<div class="sub-head">Agent Workflow Log</div>', unsafe_allow_html=True)
        for cp in data.get("checkpoints", []):
            icon = "✅" if not cp.get("requires_approval") else "⚠️"
            step_name = cp["step"].replace("_", " ").title().replace("Nwa", "NWA")
            # Longer write-ups per agent step
            step_detail = cp["message"]
            st.markdown(f'''<div class="agent-row done" style="flex-direction:column;align-items:flex-start;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <span style="font-size:1rem;">{icon}</span>
                    <div class="name">{step_name}</div>
                </div>
                <div class="detail" style="margin-top:4px;line-height:1.5;">{step_detail}</div>
            </div>''', unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔄  Start New Study"):
        st.session_state.study_data = None
        st.session_state.running = False
        st.rerun()

elif not st.session_state.study_data and not st.session_state.running:
    # Landing
    st.markdown(f'''<div style="display:flex;gap:12px;margin-bottom:16px;">
        <div class="card" style="flex:1;"><div class="lbl" style="color:{C1};">Step 1</div><div class="val" style="font-size:1.1rem;">Configure</div><div class="sub">Select growth scenarios and preferences</div></div>
        <div class="card" style="flex:1;border-left-color:{C2};"><div class="lbl" style="color:{C2};">Step 2</div><div class="val" style="font-size:1.1rem;">Analyze</div><div class="sub">6 AI agents powered by Claude evaluate options</div></div>
        <div class="card" style="flex:1;border-left-color:{C3};"><div class="lbl" style="color:{C3};">Step 3</div><div class="val" style="font-size:1.1rem;">Decide</div><div class="sub">Multi-criteria ranked recommendations</div></div>
    </div>''', unsafe_allow_html=True)

    st.caption("Configure parameters in the sidebar and click **Run Study**.")

    if use_gis_map:
        st.markdown(f'<div class="sub-head">Real US Feeder - EPRI Test Circuit 5 (Roswell, GA)</div>', unsafe_allow_html=True)
        st.caption("981-bus real EPRI topology - Illustrative suburban placement - EV, Solar, Data Center assets placed - Hover substation for details")
        grid_fig = render_gis_map()
    else:
        st.markdown(f'<div class="sub-head">IEEE 123-Bus Feeder (Simulation Model)</div>', unsafe_allow_html=True)
        st.caption("123-bus test feeder placed on US suburban street map - This is the grid being simulated - Hover nodes for asset details")
        grid_fig = render_grid_map()
    if grid_fig:
        st.plotly_chart(grid_fig, use_container_width=True)
