"""
LangGraph orchestrator for FeederIQ.
Coordinates agents with human-in-the-loop checkpoints at key decision points.
"""
import pandas as pd
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .agents.scenario_agent import ScenarioAgent
from .agents.simulation_agent import SimulationAgent
from .agents.constraint_agent import ConstraintAgent
from .agents.nwa_agent import NWAAgent
from .agents.capex_agent import CapexAgent
from .agents.recommendation_agent import RecommendationAgent


def _df_to_records(df):
    """Convert DataFrame to list of dicts for serialization."""
    d = df.copy()
    if "time" in d.columns:
        d["time"] = d["time"].astype(str)
    return d.to_dict(orient="records")


def _records_to_df(records):
    """Convert list of dicts back to DataFrame."""
    df = pd.DataFrame(records)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
    return df


class StudyState(TypedDict):
    # Inputs
    scenario: dict
    max_portfolios: int
    min_active_measures: int
    required_interventions: list
    use_epri: bool
    # Intermediate
    profiles_records: list  # serializable list of dicts
    assumptions: dict
    base_results: list
    base_summary: dict
    violations_detected: bool
    severity: str
    nwa_scored: list
    capex_scored: list
    # Outputs
    ranking: list
    top_recommendation: dict
    second_best: dict
    nwa_resolved_all: bool
    memo: str
    # Human-in-the-loop
    checkpoints: list
    human_approved: bool


def scenario_node(state: StudyState) -> dict:
    agent = ScenarioAgent()
    result = agent.run(state["scenario"])
    data_source = result["assumptions"].get("data_source", "synthetic")
    return {
        "profiles_records": _df_to_records(result["profiles"]),
        "assumptions": result["assumptions"],
        "checkpoints": state.get("checkpoints", []) + [{
            "step": "scenario",
            "message": f"Scenario configured: {state['scenario']['horizon_label']} horizon. "
                       f"EV growth: {state['scenario']['ev_level']}, Solar: {state['scenario']['solar_level']}, "
                       f"Data Center: {state['scenario']['dc_level']}. "
                       f"Peak EV demand: {result['assumptions']['peak_ev_mw']:.2f} MW. "
                       f"Peak Solar generation: {result['assumptions']['peak_solar_mw']:.2f} MW. "
                       f"Data source: {data_source}.",
            "requires_approval": False,
        }],
    }


def simulation_node(state: StudyState) -> dict:
    agent = SimulationAgent(use_epri=state.get("use_epri", False))
    profiles = _records_to_df(state["profiles_records"])
    base_results = agent.run_baseline(profiles)
    return {"base_results": base_results}


def constraint_node(state: StudyState) -> dict:
    agent = ConstraintAgent()
    analysis = agent.analyze(state["base_results"])
    interpretation = analysis.get("interpretation", "")
    return {
        "base_summary": analysis["summary"],
        "violations_detected": analysis["violations_detected"],
        "severity": analysis["severity"],
        "checkpoints": state.get("checkpoints", []) + [{
            "step": "constraint_analysis",
            "message": interpretation if interpretation else (
                f"Baseline grid stress score: {analysis['summary']['grid_stress_score']:.0f} "
                f"(severity: {analysis['severity']}). "
                f"Violations detected: {analysis['violations_detected']}. "
                f"Undervoltage buses: {analysis['summary']['total_undervoltage_buses']}, "
                f"Line overloads: {analysis['summary']['total_line_overloads']}."
            ),
            "requires_approval": True,
        }],
    }


def nwa_node(state: StudyState) -> dict:
    agent = NWAAgent()
    max_p = min(state.get("max_portfolios", 30), 30)
    min_m = state.get("min_active_measures", 1)
    profiles = _records_to_df(state["profiles_records"])
    required = state.get("required_interventions") or None
    nwa_scored = agent.run(profiles, state["base_summary"], max_portfolios=max_p, required_interventions=required, min_active_measures=min_m, use_epri=state.get("use_epri", False))

    best_nwa_name = nwa_scored[0]["portfolio_name"] if nwa_scored else "None"
    best_nwa_score = nwa_scored[0]["final_score"] if nwa_scored else 0

    return {
        "nwa_scored": nwa_scored,
        "checkpoints": state.get("checkpoints", []) + [{
            "step": "nwa_evaluation",
            "message": f"Evaluated {len(nwa_scored)} Non-Wires Alternative portfolios. "
                       f"Best NWA option: {best_nwa_name} (score: {best_nwa_score:.2f}). "
                       f"Evaluating capex/hybrid options for comparison.",
            "requires_approval": True,
        }],
    }


def capex_node(state: StudyState) -> dict:
    agent = CapexAgent()
    max_p = min(state.get("max_portfolios", 30), 30)
    min_m = state.get("min_active_measures", 1)
    profiles = _records_to_df(state["profiles_records"])
    required = state.get("required_interventions") or None
    capex_scored = agent.run(profiles, state["base_summary"], max_portfolios=max_p, required_interventions=required, min_active_measures=min_m, use_epri=state.get("use_epri", False))
    return {"capex_scored": capex_scored}


def recommendation_node(state: StudyState) -> dict:
    agent = RecommendationAgent()
    result = agent.run(
        state.get("nwa_scored", []),
        state.get("capex_scored", []),
        state["base_summary"],
        state["assumptions"],
    )
    return {
        "ranking": result["ranking"],
        "top_recommendation": result["top_recommendation"],
        "second_best": result["second_best"],
        "nwa_resolved_all": result["nwa_resolved_all"],
        "memo": result["memo"],
        "checkpoints": state.get("checkpoints", []) + [{
            "step": "recommendation",
            "message": f"Study complete. Top recommendation: {result['top_recommendation']['portfolio_name']} "
                       f"(score: {result['top_recommendation']['final_score']:.2f}). "
                       f"{'NWA fully resolves all violations.' if result['nwa_resolved_all'] else 'Residual violations remain; hybrid approach recommended.'}",
            "requires_approval": False,
        }],
    }


def should_run_capex(state: StudyState) -> str:
    """Decision: skip capex if NWA fully resolves violations."""
    if state.get("nwa_scored"):
        best = state["nwa_scored"][0]
        if "alt_summary" in best and best["alt_summary"]["grid_stress_score"] == 0:
            return "skip_capex"
    return "run_capex"


def build_graph():
    """Build the LangGraph workflow with human-in-the-loop interrupt points."""
    graph = StateGraph(StudyState)

    # Add nodes
    graph.add_node("scenario", scenario_node)
    graph.add_node("simulation", simulation_node)
    graph.add_node("constraint", constraint_node)
    graph.add_node("nwa", nwa_node)
    graph.add_node("capex", capex_node)
    graph.add_node("recommendation", recommendation_node)

    # Define edges
    graph.set_entry_point("scenario")
    graph.add_edge("scenario", "simulation")
    graph.add_edge("simulation", "constraint")
    graph.add_edge("constraint", "nwa")

    # Conditional: skip capex if NWA resolves everything
    graph.add_conditional_edges("nwa", should_run_capex, {
        "run_capex": "capex",
        "skip_capex": "recommendation",
    })
    graph.add_edge("capex", "recommendation")
    graph.add_edge("recommendation", END)

    # Compile with checkpointer for human-in-the-loop
    checkpointer = MemorySaver()
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_after=["constraint", "nwa"],  # Pause for human approval
    )


def run_study(scenario: dict, max_portfolios: int = 60, thread_id: str = "default", required_interventions: list = None, min_active_measures: int = 1, use_epri: bool = False):
    """Run without interrupts (auto-approve). Used by the API for non-interactive mode."""
    graph = build_graph()
    initial_state = {
        "scenario": scenario,
        "max_portfolios": max_portfolios,
        "min_active_measures": min_active_measures,
        "required_interventions": required_interventions or [],
        "use_epri": use_epri,
        "profiles_records": [],
        "assumptions": {},
        "base_results": [],
        "base_summary": {},
        "violations_detected": False,
        "severity": "none",
        "nwa_scored": [],
        "capex_scored": [],
        "ranking": [],
        "top_recommendation": {},
        "second_best": {},
        "nwa_resolved_all": False,
        "memo": "",
        "checkpoints": [],
        "human_approved": True,
    }
    config = {"configurable": {"thread_id": thread_id}}

    # Run through all nodes, resuming after each interrupt
    result = graph.invoke(initial_state, config)

    # If interrupted, keep resuming (auto-approve mode)
    while graph.get_state(config).next:
        result = graph.invoke(None, config)

    return result
