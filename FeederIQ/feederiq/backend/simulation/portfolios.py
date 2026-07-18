import numpy as np
import pandas as pd
from itertools import product
from ..config import (
    INTERVENTION_KEYS, LEVELS, LEVEL_LABELS, INTERVENTION_LABELS,
    COST_BY_LEVEL, FEASIBILITY_BY_LEVEL, DEPLOYMENT_BY_LEVEL, ESG_BY_LEVEL,
    SCORING_WEIGHTS,
)


def generate_portfolios(max_active_measures=3, min_active_measures=1, max_portfolios=None, required_interventions=None):
    portfolios = []
    for combo in product(LEVELS, repeat=len(INTERVENTION_KEYS)):
        p = dict(zip(INTERVENTION_KEYS, combo))
        if all(v == 0 for v in p.values()):
            continue
        active_count = sum(1 for v in p.values() if v > 0)
        if active_count > max_active_measures:
            continue
        if active_count < min_active_measures:
            continue
        # If user requires certain interventions, skip portfolios without them
        if required_interventions:
            if not all(p.get(k, 0) > 0 for k in required_interventions):
                continue
        portfolios.append(p)
    if max_portfolios:
        portfolios = portfolios[:max_portfolios]
    return portfolios


def apply_portfolio_to_profiles(profiles, portfolio):
    mod = profiles.copy()

    # Battery
    bl = portfolio.get("Battery", 0)
    if bl > 0:
        discharge = mod["time"].dt.hour.isin([17, 18, 19, 20, 21])
        charge = mod["time"].dt.hour.isin([11, 12, 13, 14])
        df = {33: 0.04, 66: 0.08, 100: 0.12}[bl]
        cf = {33: 0.01, 66: 0.02, 100: 0.03}[bl]
        mod.loc[discharge, "feeder_mult"] *= (1 - df)
        mod.loc[charge, "feeder_mult"] *= (1 + cf)

    # Managed Charging
    mc = portfolio.get("ManagedCharging", 0)
    if mc > 0:
        sf = {33: 0.15, 66: 0.30, 100: 0.50}[mc]
        evening = mod["time"].dt.hour.isin([18, 19, 20, 21])
        late = mod["time"].dt.hour.isin([0, 1, 2, 3, 4, 5])
        shifted = mod.loc[evening, "ev_mw"] * sf
        mod.loc[evening, "ev_mw"] *= (1 - sf)
        mod.loc[late, "ev_mw"] += shifted.sum() / max(late.sum(), 1)

    # Phased Interconnection
    pi = portfolio.get("PhasedInterconnection", 0)
    if pi > 0:
        mod["dc_mw"] *= (1 - {33: 0.20, 66: 0.40, 100: 0.60}[pi])

    # Demand Tariff
    dt = portfolio.get("DemandTariff", 0)
    if dt > 0:
        fr = {33: 0.03, 66: 0.06, 100: 0.10}[dt]
        er = {33: 0.05, 66: 0.10, 100: 0.15}[dt]
        peak = mod["time"].dt.hour.isin([17, 18, 19, 20])
        mod.loc[peak, "feeder_mult"] *= (1 - fr)
        mod.loc[peak, "ev_mw"] *= (1 - er)

    return mod


def transformer_capacity_multiplier(level):
    return {0: 1.00, 33: 1.10, 66: 1.20, 100: 1.30}[level]


def line_capacity_multiplier(level):
    return {0: 1.00, 33: 1.08, 66: 1.15, 100: 1.25}[level]


def summarize_results(results):
    import pandas as pd
    df = pd.DataFrame(results)
    summary = {
        "convergence_failures": int((~df["converged"]).sum()),
        "worst_vmin": float(df["vmin_pu"].min()),
        "worst_vmax": float(df["vmax_pu"].max()),
        "total_undervoltage_buses": int(df["undervoltage_buses"].sum()),
        "total_overvoltage_buses": int(df["overvoltage_buses"].sum()),
        "total_line_overloads": int(df["num_overloaded_lines"].sum()),
        "total_transformer_overloads": int(df["num_overloaded_transformers"].sum()),
    }
    summary["grid_stress_score"] = float(
        20 * summary["convergence_failures"] +
        5 * summary["total_line_overloads"] +
        6 * summary["total_transformer_overloads"] +
        2 * summary["total_undervoltage_buses"] +
        2 * summary["total_overvoltage_buses"]
    )
    return summary


def _logistic_score(x, midpoint=35.0, steepness=0.08, floor=0.5, ceiling=9.8):
    """Logistic (sigmoid) normalization for grid relief scoring.
    
    Maps improvement % to a 0-10 score using a sigmoid curve.
    This avoids the linear trap where 30% improvement = 3.0/10.
    Instead, moderate improvements (20-50%) map to the useful 4-8 range,
    reflecting diminishing marginal value of incremental improvement.
    
    Based on EPRI Distribution Planning methodology (2023) which uses
    non-linear utility functions for reliability improvement valuation.
    
    Parameters:
        midpoint: improvement % that maps to score 5.0 (inflection point)
        steepness: controls transition sharpness (higher = sharper S-curve)
        floor: minimum score for any positive improvement
        ceiling: maximum achievable score (below 10 to preserve meaning)
    """
    if x <= 0:
        return 0.0
    raw = 1.0 / (1.0 + np.exp(-steepness * (x - midpoint)))
    # Rescale from [sigmoid(0), sigmoid(100)] to [floor, ceiling]
    sig_at_0 = 1.0 / (1.0 + np.exp(-steepness * (0 - midpoint)))
    sig_at_100 = 1.0 / (1.0 + np.exp(-steepness * (100 - midpoint)))
    normalized = (raw - sig_at_0) / (sig_at_100 - sig_at_0)
    return float(floor + normalized * (ceiling - floor))


def score_portfolio(portfolio, improvement_pct):
    cost_raw = sum(COST_BY_LEVEL[k][v] for k, v in portfolio.items())
    feasibility_raw = float(np.mean([FEASIBILITY_BY_LEVEL[k][v] for k, v in portfolio.items()]))
    deployment_raw = float(np.mean([DEPLOYMENT_BY_LEVEL[k][v] for k, v in portfolio.items()]))
    esg_raw = float(np.mean([ESG_BY_LEVEL[k][v] for k, v in portfolio.items()]))

    max_cost = sum(max(v.values()) for v in COST_BY_LEVEL.values())
    cost_score = 10 * (1 - cost_raw / max_cost)

    # Grid relief: logistic-curve scoring (EPRI-style non-linear utility)
    # Reflects diminishing marginal value - first 20% improvement is more
    # valuable than going from 70% to 90%. Midpoint calibrated so that
    # a 35% improvement (typical NWA ceiling) maps to ~5.0/10.
    tech_score = _logistic_score(improvement_pct, midpoint=35.0, steepness=0.08)

    # Speed to Value = average of feasibility + deployment
    speed_score = (feasibility_raw + deployment_raw) / 2.0

    w = SCORING_WEIGHTS
    final = (w["technical"] * tech_score + w["cost"] * cost_score +
             w["speed_to_value"] * speed_score + w["esg"] * esg_raw)

    # Human-friendly portfolio name
    active = []
    for k, v in portfolio.items():
        if v > 0:
            label = INTERVENTION_LABELS.get(k, k)
            level_label = LEVEL_LABELS.get(v, str(v))
            active.append(f"{label} ({level_label})")
    name = "Base Case" if not active else " + ".join(active)

    return {
        **portfolio,
        "portfolio_name": name,
        "technical_improvement_pct": round(improvement_pct, 2),
        "grid_relief_score": round(tech_score, 2),
        "cost_score": round(cost_score, 2),
        "speed_to_value_score": round(speed_score, 2),
        "esg_score": round(esg_raw, 2),
        "final_score": round(final, 3),
    }


def portfolio_name(portfolio):
    active = []
    for k, v in portfolio.items():
        if v > 0:
            label = INTERVENTION_LABELS.get(k, k)
            level_label = LEVEL_LABELS.get(v, str(v))
            active.append(f"{label} ({level_label})")
    return "Base Case" if not active else " + ".join(active)
