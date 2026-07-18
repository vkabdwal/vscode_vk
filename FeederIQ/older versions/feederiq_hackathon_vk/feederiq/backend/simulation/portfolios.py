import numpy as np
from itertools import product
from ..config import (
    INTERVENTION_KEYS, LEVELS, LEVEL_LABELS, INTERVENTION_LABELS,
    COST_BY_LEVEL, FEASIBILITY_BY_LEVEL, DEPLOYMENT_BY_LEVEL, ESG_BY_LEVEL,
    SCORING_WEIGHTS,
)


def generate_portfolios(max_active_measures=3, max_portfolios=None):
    portfolios = []
    for combo in product(LEVELS, repeat=len(INTERVENTION_KEYS)):
        p = dict(zip(INTERVENTION_KEYS, combo))
        if all(v == 0 for v in p.values()):
            continue
        if sum(1 for v in p.values() if v > 0) > max_active_measures:
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


def score_portfolio(portfolio, improvement_pct):
    cost_raw = sum(COST_BY_LEVEL[k][v] for k, v in portfolio.items())
    feasibility_raw = float(np.mean([FEASIBILITY_BY_LEVEL[k][v] for k, v in portfolio.items()]))
    deployment_raw = float(np.mean([DEPLOYMENT_BY_LEVEL[k][v] for k, v in portfolio.items()]))
    esg_raw = float(np.mean([ESG_BY_LEVEL[k][v] for k, v in portfolio.items()]))

    max_cost = sum(max(v.values()) for v in COST_BY_LEVEL.values())
    cost_score = 10 * (1 - cost_raw / max_cost)
    tech_score = min(10.0, improvement_pct / 10.0)
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
