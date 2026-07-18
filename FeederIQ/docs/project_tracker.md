# FeederIQ MVP – Project Tracker

## Project Overview

FeederIQ is an agentic AI planning copilot for electric distribution utilities. It forecasts feeder-level congestion and voltage issues under future load-growth scenarios, then recommends the cheapest defensible fix — prioritizing non-wires alternatives (NWA) before resorting to expensive capex.

- **Hackathon context**: Agentic AI hackathon; agents are mandatory.
- **Stack**: FastAPI backend + Streamlit frontend.
- **Simulation engine**: OpenDSS via `opendssdirect.py`.
- **Feeder model**: IEEE 123-bus (from openEDI/oedisi-ieee123).
- **Core script**: `script1.py` — end-to-end simulation, portfolio generation, scoring, and reporting.

---

## Dataset Source

- **Repository**: https://github.com/openEDI/oedisi-ieee123
- **License**: BSD-3-Clause
- **What we use**:
  - `qsts/` folder structure (master.dss, IEEE123LoadShapes.dss, IEEE123LoadsQsts.dss, IEEE123PvShapes.dss, IEEE123Pv.dss, IEEE123Regulators.dss, IEEELinecodes.dss, Buscoords.dss)
  - `profiles/load_profiles/` — 91 CSV files, 35040 rows each (15-min intervals, 1 year)
  - `profiles/pv_profiles/` — 14 PV irradiance CSVs + 1 temperature CSV
- **Local path**: `ai_synthetic_data/` contains the DSS files; `ai_synthetic_data/profiles/` contains the CSVs.

---

## Key Optimization: master_lite.dss

### Problem

The original `master.dss` redirects to `IEEE123LoadShapes.dss` and `IEEE123PvShapes.dss`, which load **106 CSV files × 35,040 rows each** (~3.7M data points). This took ~30 seconds per compile.

`script1.py` was recompiling the feeder **every single hourly timestep** (24×) for **every portfolio** (120×). That's 2,880 full compiles = 30+ minutes for a single study.

### Why those CSVs are unnecessary

- `script1.py` uses **snapshot mode** (`dss.Solution.Mode(0)`), not QSTS/yearly mode.
- It drives the 24-hour loop externally and sets load values via the Python API each hour.
- The `yearly=loadshape_XXX` references on loads are never consumed in snapshot mode.
- PV systems from `IEEE123Pv.dss` are redundant because `script1.py` adds its own solar generators.

### Solution

1. **Created `ai_synthetic_data/master_lite.dss`** — identical topology, lines, transformers, capacitors, regulators, and loads, but:
   - Redirects to `IEEE123StubShapes.dss` instead of the heavy CSV-based loadshape files.
   - Skips `IEEE123PvShapes.dss` and `IEEE123Pv.dss` entirely.

2. **Created `ai_synthetic_data/IEEE123StubShapes.dss`** — defines all 106 loadshape/tshape names as flat single-point stubs (`npts=1 mult=(1.0)`). This satisfies OpenDSS name-resolution at compile time with zero disk I/O.

3. **Compile time dropped from ~30s to 0.014s.**

---

## Key Optimization: Compile-Once Simulation Loop

### Problem

The old `run_simulation_for_portfolio()` called `compile_feeder()` inside `solve_one_timestep_portfolio()` for each of the 24 hours. This was done because OpenDSS can't remove elements once added (EV loads, solar generators change each hour).

### Solution

Refactored `run_simulation_for_portfolio()` to:

1. **Compile once** at the start of each portfolio evaluation.
2. **Pre-add placeholder devices** (EV loads, solar generators, data center load) at zero power.
3. **Loop 24 hours**: update kW/kvar values in-place via the OpenDSS API, then re-solve.
4. Inline overload detection to avoid redundant element iteration.

### Result

- 8 portfolios × 24 hours: **1.5 seconds** (was 30+ minutes).
- Projected 120 portfolios: **~22 seconds**.

---

## File Structure

```
vaibhav/
├── script1.py                  # Original monolithic simulation (reference)
├── run_backend.py              # Launch FastAPI backend (uvicorn :8000)
├── run_frontend.py             # Launch Streamlit frontend (:8501)
├── project_tracker.md          # This file
├── FeederIQ_reference.md       # Full project spec and architecture
├── assumptions_rationale.md    # Market-backed defensibility of all assumptions
├── README.md                   # How to run the app
├── requirements.txt            # Python deps (fastapi, langgraph, streamlit, etc.)
├── feederiq/                   # Main application package
│   ├── __init__.py
│   ├── backend/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app: /study, /options, /health, /study/{id}
│   │   ├── config.py           # All constants, scenario options, scoring weights
│   │   ├── models.py           # Pydantic schemas (ScenarioRequest, StudyResult, etc.)
│   │   ├── orchestrator.py     # LangGraph workflow with human-in-the-loop
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── scenario_agent.py       # Converts scenario selections → numeric assumptions + profiles
│   │   │   ├── simulation_agent.py     # Runs 24-hour OpenDSS power flow
│   │   │   ├── constraint_agent.py     # Detects violations, classifies severity
│   │   │   ├── nwa_agent.py            # Evaluates NWA-only portfolios (no capex)
│   │   │   ├── capex_agent.py          # Evaluates hybrid/capex portfolios
│   │   │   └── recommendation_agent.py # Ranks all options, generates decision memo
│   │   └── simulation/
│   │       ├── __init__.py
│   │       ├── engine.py        # compile_feeder(), run_24hr_simulation()
│   │       ├── profiles.py      # generate_profiles() with synthetic curves
│   │       └── portfolios.py    # generate_portfolios(), apply_portfolio, score_portfolio
│   └── frontend/
│       ├── app.py              # Streamlit UI – PwC-branded wizard (R2 redesign)
│       └── app_v1.py           # Original sidebar-style UI (R1 reference)
├── ai_synthetic_data/
│   ├── master.dss              # Original full master (heavy, for reference)
│   ├── master_lite.dss         # Optimized master (used by app)
│   ├── IEEE123StubShapes.dss   # Flat stub loadshapes (no CSV)
│   ├── IEEE123LoadShapes.dss   # Original (references CSV files)
│   ├── IEEE123LoadsQsts.dss    # Load definitions (kW, kvar, bus assignments)
│   ├── IEEE123Pv.dss           # PV systems (not used by master_lite)
│   ├── IEEE123PvShapes.dss     # PV irradiance shapes (not used by master_lite)
│   ├── IEEE123Regulators.dss   # Voltage regulators
│   ├── IEEELinecodes.dss       # Line impedance codes
│   ├── Buscoords.dss           # Bus coordinates for grid topology map
│   └── profiles/
│       ├── load_profiles/      # 91 CSVs (35040 pts each)
│       └── pv_profiles/        # 14 PV CSVs + temperature.csv
├── outputs/
│   └── dry_run/                # Timestamped run folders
│       └── YYYYMMDD_HHMMSS/
│           ├── tables/         # portfolio_ranking.csv, base_summary.csv
│           └── logs/           # scenario.json, run_meta.json
└── qsts/                       # Original repo metadata (README, LICENSE, sensors.json)
```

---

## Simulation Logic Summary

1. User selects: planning horizon, EV growth, solar adoption, data center demand, DC timeline.
2. `generate_profiles()` builds 24-hour synthetic curves for feeder load, EV, solar, and data center.
3. `generate_portfolios()` creates intervention combinations (TransformerUpgrade, Battery, ManagedCharging, PhasedInterconnection, DemandTariff) at levels 0/33/66/100%.
4. For each portfolio, `apply_portfolio_to_profiles()` modifies the 24-hour curves.
5. `run_simulation_for_portfolio()` compiles the feeder once, injects scenario devices, loops 24 hours updating loads and solving power flow.
6. `summarize_results()` computes a grid stress score from violations.
7. `score_portfolio()` applies weighted scoring (40% technical, 25% cost, 20% feasibility, 15% deployment speed).
8. Results are ranked; top recommendation and second-best are reported.

---

## Multi-Criteria Selection Logic

The system does **not** recommend solely based on cost. It uses a multi-criteria weighted scoring framework:
- **Grid Relief (40%)** — % reduction in equipment overloads and voltage violations
- **Cost Efficiency (25%)** — lower implementation cost relative to full capex
- **Speed to Value (20%)** — combined feasibility and deployment timeline
- **ESG Alignment (15%)** — sustainability benefit (lower carbon, less material intensity)

All dimension scores are exposed in the ranking table. Planners can select based on their operational priority (e.g., fastest deployment, highest technical improvement, or lowest cost) — not only the weighted total.

### NWA Bias

The framework inherently favors NWA because:
- NWA options (ManagedCharging, DemandTariff, PhasedInterconnection, Battery) have lower cost scores and higher feasibility/deployment scores than TransformerUpgrade.
- Pure capex (TransformerUpgrade at 66–100%) is penalized on cost, feasibility, and deployment speed.
- Mixed portfolios are generated but NWA-only solutions rank higher when they resolve violations.

---

## Dry Run Results (validated)

- **Scenario**: 12m horizon, High EV, Base solar, Moderate DC, 12m DC timeline.
- **Base case stress score**: 3494.0
- **Top recommendation**: `PhasedInterconnection:66` (score 6.754)
- **Runtime**: 1.5s for 8 portfolios (compile-once + master_lite)

---

## Next Steps

- [x] Build FastAPI backend with `/study`, `/options`, `/health`, `/study/{id}` endpoints.
- [x] Build Streamlit frontend with scenario controls, charts, ranked table, and decision memo.
- [x] Implement agent orchestration layer (6 agents + LangGraph orchestrator).
- [x] Add LangGraph human-in-the-loop checkpoints (interrupt_after constraint + NWA).
- [x] End-to-end validation: API returns stress=3490, top=PhasedInterconnection:66, score=6.854, 4 checkpoints.
- [x] Redesign frontend: PwC-branded wizard UI with sidebar config, agent visualization, grid map.
- [x] Add feeder topology visualization (Buscoords.dss + Plotly with line connections from DSS).
- [x] Create defensible assumptions rationale document with market benchmarks (assumptions_rationale.md).
- [x] Add custom numeric input alongside Low/Base/High presets.
- [x] Multi-criteria ranking UI: radar charts, score bars, portfolio cards.
- [x] Solution Preferences: "Must include" and "Only these" (exclusive) filter modes.
- [x] Minimum Grid Relief threshold slider (default 10%, excludes weak solutions).
- [x] Score color gradient matching scale (green=high, orange=mid, red=low).
- [x] Grid Stress Score explanation with severity scale in baseline tab.
- [x] Intervention levels renamed: Low/Medium/High (from Pilot/Scaled/Full).
- [x] Fixed checkpoint messages: proper formatting, no = signs, NWA spelled out.
- [x] LLM-powered agents via AWS Bedrock (Claude 3.5 Sonnet v2). Constraint + Recommendation agents use LLM.
- [x] Agent instruction files (.md) serve as system prompts for LLM reasoning.
- [x] Interventions renamed: Capacity Upgrade, Dynamic Tariffs, Staged Load Connection.
- [x] Increased Capacity Upgrade cost penalty (reflects real transformer costs).
- [x] Moved scripts to scripts/, docs to docs/, cleaned outputs/.
- [x] Real data toggle: openEDI DOE profiles (91 CSVs × 35040 pts) vs synthetic curves.
- [x] Before/after grid stress visualization (red→green node map).
- [x] Agent completion summaries (shows actual findings, not just 'Complete').
- [x] View Results button (no auto-redirect from agent page).
- [x] Agent execution view refactored to a true tree: Scenario → Simulation → Constraint → (NWA, Capex) → Recommendation.
- [x] Agent tree styling refreshed with centered compact cards and state palette (running=blue, queued=PwC orange, completed=teal).
- [x] Shared PwC logo asset integrated across Streamlit and PDF; placement/size tuned for visual consistency.
- [x] PDF header spacing reduced and logo rendering stabilized across all pages.
- [x] Recommendation memo prompt updated to exclude "Implementation Next Steps" section.
- [x] Recommendation/Profile/Memo tabs now stay synchronized to the same selected portfolio.
- [x] Added LLM-driven real-world intervention blueprint (with level guide) in Profiles and Memo views.
- [x] Replaced non-functional hover title tooltips with clickable inline info popups for intervention levels.
- [x] PDF table rendering refactor: multiline row wrapping, stable row geometry, centered headers, and right-aligned metric/value columns.
- [x] Simplified PDF Section 4.4 implementation table: removed Primary KPI column and preserved full Field Implementation text (no forced clipping).
- [ ] Deploy to cloud / containerize.

---

## App Architecture (Completed)

### Agent Pipeline (LangGraph)

```
Entry → ScenarioAgent → SimulationAgent → ConstraintAgent → [INTERRUPT: show violations]
      → NWAAgent → [INTERRUPT: confirm proceed to capex]
      → CapexAgent (skipped if NWA resolves all) → RecommendationAgent → END
```

### Human-in-the-Loop

LangGraph `interrupt_after=["constraint", "nwa"]` pauses execution at two key points:
1. After constraint analysis — shows baseline violations and severity.
2. After NWA evaluation — shows best NWA option and asks whether to evaluate capex.

In auto-approve mode (API default), the orchestrator resumes automatically through all interrupts.

### Frontend Architecture (R2 Redesign)

Wizard-style UI with PwC branding:
- **Step 1**: Planning Horizon (radio selector with descriptions)
- **Step 2**: Load Growth (EV + Solar with Low/Base/High + custom numeric input)
- **Step 3**: Data Center (size + timeline + feeder topology map)
- **Step 4**: Study Configuration (portfolio params + scenario summary cards)
- **Step 5**: Agent Execution (tree-style agent graph showing hierarchical pipeline progress)
- **Step 6**: Results (tabbed: Recommendation, Ranking, Baseline, Profiles, Memo)

Design:
- Running nodes highlighted in blue, queued nodes in PwC orange, completed nodes in minimal teal
- Light backgrounds throughout
- Radar charts for multi-criteria comparison
- Score bars for dimension breakdown
- Top-3 portfolio cards with badges
- IEEE 123-bus grid map (Plotly from Buscoords.dss)

### Assumptions Defensibility

See `assumptions_rationale.md` for full market-backed justification of:
- Deployment levels (EPRI maturity stages)
- Cost scores (NREL ATB 2024, Lazard LCOE+, FERC Form 1)
- Feasibility scores (PUC proceeding timelines)
- Deployment speed (DOE NWA case studies)
- ESG Alignment (IEA 2023, EPRI LCA 2022, NREL 2021, DOE VPP 2023)
- Scoring weights (aligned with CPUC IRP and NY REV BCA frameworks)

### LLM Integration (Active)

- **Model**: Claude 3.5 Sonnet v2 via AWS Bedrock (`us.anthropic.claude-3-5-sonnet-20241022-v2:0`)
- **Agents using LLM**: Constraint Agent (violation interpretation), Recommendation Agent (memo generation)
- **Pattern**: Agent instruction `.md` files serve as LLM system prompts
- **Fallback**: Template-based output if Bedrock unavailable (no crash)
- **Agent instructions** at `feederiq/backend/agents/instructions/` contain CONFIG blocks that drive agent behavior

### FastAPI Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/options` | Scenario options for UI |
| POST | `/study` | Run full planning study |
| GET | `/study/{id}` | Retrieve previous study |
| GET | `/options` | All available scenario options for frontend dropdowns |
| POST | `/study` | Run full study (returns results synchronously) |
| GET | `/study/{id}` | Retrieve previously computed study by ID |

### Streamlit Frontend

- Sidebar: all scenario options (horizon, EV, solar, DC size, DC timeline, max/min portfolios measures, solution preferences, min grid relief)
- Info tooltips on EV Growth and Solar Adoption explaining time period context
- Main area: agent workflow steps with animated progress, tabbed results (Recommendation, Rankings, Baseline, Profiles, Memo)
- Score Breakdown: PwC-style dark gradient card with color-coded scores per dimension
- Impact Assessment: Before (red) / After (green) colored cards, grid stress visualization using topology-based BFS
- Rankings: sort-by-dimension selector, bold in-bar scores
- Profiles: 45° x-axis labels, bold axis titles, bold legends
- Memo: PDF download with PwC branding, tightened header spacing, and consistent logo rendering on all pages
- Radar chart comparing selected vs runner-up portfolio

### Validated End-to-End Results

- **Scenario**: 12m horizon, Base EV, Base Solar, Moderate DC, 12m timeline, 10 portfolios
- **Baseline stress**: ~2700-4600 (varies by scenario)
- **Top recommendation**: varies (e.g. Staged Load Connection (High) + Dynamic Tariffs)
- **Scoring**: Logistic (sigmoid) normalization for grid relief; weighted sum across 4 dimensions
- **NWA resolved all**: scenario-dependent
- **Checkpoints returned**: 4 (scenario, constraint_analysis, nwa_evaluation, recommendation)
- **API response time**: ~15-17s for 10 portfolios

### Key Dependencies

```
fastapi, uvicorn, pydantic, streamlit, plotly, requests
langgraph, langchain-core
opendssdirect.py, numpy, pandas, matplotlib, networkx
fpdf2, boto3
```
