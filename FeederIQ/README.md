# FeederIQ - Agentic Distribution Planning

An AI-powered planning copilot that stress-tests distribution feeders under future load-growth scenarios and recommends optimal interventions using multi-criteria scoring - prioritizing **non-wires alternatives** (NWA) before expensive capex.

**Documentation**: See `docs/` folder for detailed project reference, assumptions rationale, and progress tracker.

## Quick Start

### Prerequisites

- Python 3.12+
- OpenDSS engine (via `opendssdirect.py` - works on Windows, Linux, macOS)

---

### Option A: GitHub Codespaces / Dev Container

When running in a Codespace or dev container, the workspace root is `/workspaces/feederiq_hackathon26`. You must `cd` into the `FeederIQ/` directory first.

```bash
cd /workspaces/feederiq_hackathon26/FeederIQ
pip install -r requirements.txt
```

### Reliable 2-Terminal Run Flow (Codespaces)

Use this exact sequence before demos/submission.

1. Start backend in terminal 1:

```bash
cd /workspaces/feederiq_hackathon26/FeederIQ
fuser -k 8000/tcp || true
python scripts/run_backend.py
```

2. Start frontend in terminal 2:

```bash
cd /workspaces/feederiq_hackathon26/FeederIQ
fuser -k 8501/tcp || true
python scripts/run_frontend.py
```

The startup scripts now auto-set port visibility in Codespaces:

- `run_backend.py` sets port `8000` to public
- `run_frontend.py` sets port `8501` to public

3. Open URLs:

- Local frontend: **http://localhost:8501**
- Public frontend: **https://$CODESPACE_NAME-8501.app.github.dev/**

If `gh` is not authenticated or the public URL still returns 404, run once:

```bash
gh codespace ports visibility 8000:public 8501:public -c "$CODESPACE_NAME"
```

---

### Option B: Local VS Code (Windows)

When running locally, open the `FeederIQ/` folder directly in VS Code. Use a virtual environment at `.venv/`.

```bash
pip install -r requirements.txt
```

Before starting the backend, kill any previous session occupying port 8000:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
```

**Run the Backend:**

```bash
python scripts/run_backend.py
```

**Run the Frontend** (separate terminal):

```bash
python scripts/run_frontend.py
```

- Backend: **http://localhost:8000**
- Frontend: **http://localhost:8501**

---

## API Reference

### `GET /health`

Health check.

```json
{"status": "ok"}
```

### `GET /options`

Returns all available scenario options for building the frontend UI.

```json
{
  "planning_horizons": ["3m", "6m", "12m", "18m", "3yr", "5yr"],
  "ev_levels": ["Low", "Base", "High"],
  "solar_levels": ["Low", "Base", "High"],
  "dc_levels": ["Low", "Moderate", "High"],
  "dc_timelines": ["6m", "12m", "18m"],
  "interventions": ["TransformerUpgrade", "Battery", "ManagedCharging", "PhasedInterconnection", "DemandTariff"],
  "levels": [0, 33, 66, 100],
  "scoring_weights": {"technical": 0.4, "cost": 0.25, "feasibility": 0.2, "deployment": 0.15}
}
```

### `POST /study`

Run a full planning study. Returns results synchronously.

**Request body:**

```json
{
  "horizon_label": "12m",
  "ev_level": "Base",
  "solar_level": "Base",
  "dc_level": "Moderate",
  "dc_timeline_label": "12m",
  "max_active_measures": 3,
  "max_portfolios": 60
}
```

**Response (abbreviated):**

```json
{
  "study_id": "uuid",
  "scenario": { ... },
  "base_summary": {
    "grid_stress_score": 3490.0,
    "total_undervoltage_buses": 0,
    "total_line_overloads": 478,
    "total_transformer_overloads": 72,
    ...
  },
  "top_recommendation": {
    "portfolio_name": "PhasedInterconnection:66",
    "final_score": 6.854,
    "technical_improvement_pct": 38.97,
    "cost_score": 9.23,
    ...
  },
  "ranking": [ ... ],
  "profiles": {
    "time": ["00:00", "01:00", ...],
    "feeder_mult": [...],
    "ev_mw": [...],
    "solar_mw": [...],
    "dc_mw": [...]
  },
  "base_results": [ ... ],
  "nwa_resolved_all": false,
  "memo": "# FeederIQ Decision Memo\n...",
  "checkpoints": [
    {"step": "scenario", "message": "...", "requires_approval": false},
    {"step": "constraint_analysis", "message": "...", "requires_approval": true},
    {"step": "nwa_evaluation", "message": "...", "requires_approval": true},
    {"step": "recommendation", "message": "...", "requires_approval": false}
  ]
}
```

### `GET /study/{study_id}`

Retrieve a previously computed study by its ID.

---

## Scenario Parameters

| Parameter | Options | Description |
|-----------|---------|-------------|
| `horizon_label` | 6m, 12m, 18m, 3yr, 5yr | Planning horizon |
| `ev_level` | Low, Base, High | EV growth rate (15%, 20%, 25% annual) |
| `solar_level` | Low, Base, High | Solar adoption (100, 200, 300 MW) |
| `dc_level` | Low, Moderate, High | Data center size (1.0, 1.75, 3.0 MW) |
| `dc_timeline_label` | 6m, 12m, 18m | When data center comes online |
| `max_active_measures` | 1-5 | Max interventions per portfolio |
| `max_portfolios` | 10-120 | How many portfolios to evaluate |

---

## Agent Architecture

The backend uses **LangGraph** for orchestration with human-in-the-loop checkpoints:

1. **Scenario Agent** - Converts selections into numeric growth assumptions and 24-hour profiles
2. **Simulation Agent** - Runs OpenDSS 24-hour power flow (baseline)
3. **Constraint Agent** - Detects voltage violations and equipment overloads ← *[CHECKPOINT]*
4. **NWA Agent** - Evaluates non-wires alternative portfolios ← *[CHECKPOINT]*
5. **Capex Agent** - Evaluates hybrid/capex options (skipped if NWA resolves all)
6. **Recommendation Agent** - Ranks all options and generates decision memo

---

## Scoring Framework

Portfolios are scored on 4 dimensions (weighted sum, scale 0-10):

- **Grid Relief** (40%) - % reduction in equipment overloads and voltage violations
- **Cost Efficiency** (25%) - Lower implementation cost relative to full capex
- **Speed to Value** (20%) - Combined feasibility and deployment timeline
- **ESG Alignment** (15%) - Sustainability benefit (lower carbon, less material intensity)

**The system does not simply recommend the cheapest option.** All dimension scores are exposed in the ranking table, so planners can sort/filter by any single criterion and select based on their operational priority.

NWA options inherently score higher across cost, speed, and ESG dimensions. See `assumptions_rationale.md` for full market-backed defensibility of all scores.

---

## Performance

- Feeder compile: 0.014s (master_lite.dss with stub shapes)
- Full study (10 portfolios): ~15s
- Full study (60 portfolios): ~90s

---

## Tech Stack

- **LLM**: Claude 3 Sonnet (Anthropic) via AWS Bedrock
- **Backend**: FastAPI + Uvicorn
- **Frontend**: Streamlit + Plotly
- **Orchestration**: LangGraph (with interrupt-based human-in-the-loop)
- **Simulation**: OpenDSS via opendssdirect.py
- **Feeder model**: IEEE 123-bus (openEDI/oedisi-ieee123, BSD-3-Clause)
- **Agent instructions**: Markdown files (system prompts) driving agent behavior
