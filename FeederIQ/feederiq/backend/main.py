"""
FeederIQ FastAPI backend.
Endpoints for running planning studies and retrieving results.
"""
import uuid
import traceback
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ScenarioRequest, StudyResult, ViolationSummary, PortfolioScore
from .orchestrator import run_study

app = FastAPI(title="FeederIQ", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for demo (single-process)
studies: dict = {}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/study")
def create_study(req: ScenarioRequest):
    """Run a full planning study synchronously and return results."""
    study_id = str(uuid.uuid4())
    scenario = {
        "horizon_label": req.horizon_label,
        "ev_level": req.ev_level,
        "solar_level": req.solar_level,
        "dc_level": req.dc_level,
        "dc_timeline_label": req.dc_timeline_label,
        "use_real_data": req.use_real_data,
    }
    try:
        result = run_study(scenario, max_portfolios=req.max_portfolios or 60,
                           thread_id=study_id,
                           required_interventions=req.required_interventions,
                           min_active_measures=req.min_active_measures,
                           use_epri=req.use_epri)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Study failed: {str(e)}\n{traceback.format_exc()}")

    # Convert profiles to JSON-friendly dict
    profiles_records = result.get("profiles_records", [])
    profiles_json = {}
    if profiles_records:
        import pandas as pd
        profiles_df = pd.DataFrame(profiles_records)
        if "time" in profiles_df.columns:
            profiles_df["time"] = pd.to_datetime(profiles_df["time"])
        profiles_json = {
            "time": profiles_df["time"].dt.strftime("%H:%M").tolist(),
            "feeder_mult": profiles_df["feeder_mult"].round(4).tolist(),
            "ev_mw": profiles_df["ev_mw"].round(4).tolist(),
            "solar_mw": profiles_df["solar_mw"].round(4).tolist(),
            "dc_mw": profiles_df["dc_mw"].round(4).tolist(),
        }

    # Build response
    base_summary = result.get("base_summary", {})
    top_rec = result.get("top_recommendation", {})
    second = result.get("second_best", {})
    ranking = result.get("ranking", [])

    response = {
        "study_id": study_id,
        "scenario": scenario,
        "base_summary": base_summary,
        "top_recommendation": top_rec,
        "second_best": second,
        "ranking": ranking,
        "profiles": profiles_json,
        "base_results": result.get("base_results", []),
        "nwa_resolved_all": result.get("nwa_resolved_all", False),
        "memo": result.get("memo", ""),
        "checkpoints": result.get("checkpoints", []),
    }
    studies[study_id] = response
    return response


@app.get("/study/{study_id}")
def get_study(study_id: str):
    if study_id not in studies:
        raise HTTPException(status_code=404, detail="Study not found")
    return studies[study_id]


@app.get("/study/{study_id}/memo")
def get_study_memo(study_id: str):
    """Generate LLM decision memo on-demand (deferred from study run for speed)."""
    if study_id not in studies:
        raise HTTPException(status_code=404, detail="Study not found")

    study = studies[study_id]

    # If already generated via LLM (has ## Executive Summary), return cached
    memo = study.get("memo", "")
    if memo and "## Executive Summary" in memo and len(memo) > 500:
        return {"memo": memo}

    # Generate via LLM now
    from .agents.recommendation_agent import RecommendationAgent
    agent = RecommendationAgent()
    base_summary = study.get("base_summary", {})
    top = study.get("top_recommendation", {})
    second = study.get("second_best", {})
    ranking = study.get("ranking", [])
    assumptions = study.get("scenario", {})
    nwa_resolved = study.get("nwa_resolved_all", False)

    llm_memo = agent._generate_memo_llm(top, second, base_summary, assumptions, nwa_resolved, ranking[:5])
    if llm_memo:
        study["memo"] = llm_memo
        return {"memo": llm_memo}

    return {"memo": memo}


@app.get("/options")
def get_options():
    """Return all available scenario options for the frontend."""
    from .config import (
        PLANNING_HORIZONS, EV_GROWTH, SOLAR_ADOPTION,
        DATA_CENTER_MW, DATA_CENTER_TIMELINE_MONTHS,
        INTERVENTION_KEYS, LEVELS, SCORING_WEIGHTS,
        LEVEL_LABELS, INTERVENTION_LABELS,
    )
    return {
        "planning_horizons": list(PLANNING_HORIZONS.keys()),
        "ev_levels": list(EV_GROWTH.keys()),
        "solar_levels": list(SOLAR_ADOPTION.keys()),
        "dc_levels": list(DATA_CENTER_MW.keys()),
        "dc_timelines": list(DATA_CENTER_TIMELINE_MONTHS.keys()),
        "interventions": INTERVENTION_KEYS,
        "intervention_labels": INTERVENTION_LABELS,
        "levels": LEVELS,
        "level_labels": LEVEL_LABELS,
        "scoring_weights": SCORING_WEIGHTS,
    }
