from pydantic import BaseModel
from typing import Optional


class ScenarioRequest(BaseModel):
    horizon_label: str = "12m"
    ev_level: str = "Base"
    solar_level: str = "Base"
    dc_level: str = "Moderate"
    dc_timeline_label: str = "12m"
    max_active_measures: int = 3
    max_portfolios: Optional[int] = 60


class ViolationSummary(BaseModel):
    convergence_failures: int
    worst_vmin: float
    worst_vmax: float
    total_undervoltage_buses: int
    total_overvoltage_buses: int
    total_line_overloads: int
    total_transformer_overloads: int
    grid_stress_score: float


class PortfolioScore(BaseModel):
    portfolio_name: str
    TransformerUpgrade: int
    Battery: int
    ManagedCharging: int
    PhasedInterconnection: int
    DemandTariff: int
    technical_improvement_pct: float
    technical_score: float
    cost_score: float
    feasibility_score: float
    deployment_score: float
    final_score: float


class StudyResult(BaseModel):
    scenario: dict
    base_summary: ViolationSummary
    top_recommendation: Optional[PortfolioScore]
    second_best: Optional[PortfolioScore]
    ranking: list[dict]
    profiles: dict  # time-series data for charts
    base_results: dict  # hourly violation data


class HumanCheckpoint(BaseModel):
    step: str
    message: str
    data: dict
    requires_approval: bool = True
