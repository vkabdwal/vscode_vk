# Core libraries for feeder simulation, portfolio generation, plotting, and analysis.
import os
import math
from pathlib import Path
from itertools import product

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import opendssdirect as dss


# Point to the OpenDSS master file that defines the feeder model.
# Prefer local workspace paths so the script works across machines.
def resolve_master_dss_path():
    repo_root = Path(__file__).resolve().parent
    candidates = [
        repo_root / "ai_synthetic_data" / "master_lite.dss",
        repo_root / "ai_synthetic_data" / "master.dss",
        repo_root / "qsts" / "master.dss",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    # Fall back to the primary expected location for clearer errors downstream.
    return candidates[0].resolve()


MASTER_DSS_PATH = resolve_master_dss_path()

# Scenario inputs plus intervention levels and scoring metadata for portfolio evaluation.

# The study simulates one representative future day, not every day until that horizon. The horizon only scales demand/generation magnitudes
PLANNING_HORIZONS = {
    "6m": 0.5,
    "12m": 1.0,
    "18m": 1.5,
    "3yr": 3.0,
    "5yr": 5.0
}
# Annual EV growth rates by scenario (%)
EV_GROWTH = {
    "Low": 0.15,
    "Base": 0.20,
    "High": 0.25
}
# Scenario sizes for solar adoption. Later code converts these into feeder-equivalent MW
SOLAR_ADOPTION = {
    "Low": 100,
    "Base": 200,
    "High": 300
}
# Size of the new data center load by scenario (only one data center is modeled)
DATA_CENTER_MW = {
    "Low": 1.0,
    "Moderate": 1.75,
    "High": 3.0
}
# When the data center becomes active. If the planning horizon has not reached that month, the data center load is zero
DATA_CENTER_TIMELINE_MONTHS = {
    "6m": 6,
    "12m": 12,
    "18m": 18
}
# Base non-EV/non-data-center feeder load grows 3% annually
BASE_FEEDER_ANNUAL_GROWTH = 0.03

# Primary line-to-line voltage for the feeder (Used when adding 3-phase assets)
PRIMARY_KV_LL = 4.16
SINGLE_PHASE_KV_LN = 2.402 # Used when adding single-phase EV and solar devices

# Anything outside this is treated as a violation
VOLTAGE_MIN_PU = 0.95
VOLTAGE_MAX_PU = 1.05

# Hard-coded locations where new assets are placed (e.g. Data center is placed only at bus 67)
EV_BUSES = ["60", "83", "90", "92", "114"]
SOLAR_BUSES = ["66", "80", "92", "104", "110"]
DATA_CENTER_BUS = "67"

# Specifies which phase each single-phase EV/solar device connects to. Example: bus 90 uses phase .2
BUS_PHASE_MAP_EV = {
    "60": ".1",
    "83": ".1",
    "90": ".2",
    "92": ".3",
    "114": ".1"
}

BUS_PHASE_MAP_SOLAR = {
    "66": ".1",
    "80": ".1",
    "92": ".3",
    "104": ".3",
    "110": ".1"
}
# The candidate solution types.
INTERVENTION_KEYS = [
    "TransformerUpgrade",
    "Battery",
    "ManagedCharging",
    "PhasedInterconnection",
    "DemandTariff"
]
# Allowed implementation levels for each intervention. 0 means off. 33/66/100 mean partial to full deployment. Assumption: Intervention strength can be discretized into four levels.
LEVELS = [0, 33, 66, 100]

# Subjective cost scores per intervention level. Higher number here means more raw cost burden. These are heuristic planning scores, not real dollars.
COST_BY_LEVEL = {
    "TransformerUpgrade": {0: 0, 33: 3, 66: 6, 100: 9},
    "Battery": {0: 0, 33: 3, 66: 5, 100: 8},
    "ManagedCharging": {0: 0, 33: 1, 66: 2, 100: 3},
    "PhasedInterconnection": {0: 0, 33: 1, 66: 2, 100: 3},
    "DemandTariff": {0: 0, 33: 1, 66: 2, 100: 3},
}
# Subjective feasibility scores. Higher deployment level usually lowers feasibility. Example: a full transformer upgrade is harder to execute than no upgrade. Assumption: scale is 0-10 and based on judgment, not measured data.
FEASIBILITY_BY_LEVEL = {
    "TransformerUpgrade": {0: 10, 33: 8, 66: 6, 100: 4},
    "Battery": {0: 10, 33: 8, 66: 7, 100: 6},
    "ManagedCharging": {0: 10, 33: 9, 66: 8, 100: 7},
    "PhasedInterconnection": {0: 10, 33: 8, 66: 7, 100: 6},
    "DemandTariff": {0: 10, 33: 8, 66: 7, 100: 6},
}
# Subjective ease/speed of deployment. Higher score means easier/faster to deploy. Full physical upgrades score lower than operational programs.
DEPLOYMENT_BY_LEVEL = {
    "TransformerUpgrade": {0: 10, 33: 7, 66: 5, 100: 3},
    "Battery": {0: 10, 33: 8, 66: 6, 100: 5},
    "ManagedCharging": {0: 10, 33: 9, 66: 8, 100: 7},
    "PhasedInterconnection": {0: 10, 33: 8, 66: 7, 100: 6},
    "DemandTariff": {0: 10, 33: 8, 66: 7, 100: 6},
}




# Small utility helpers for validation, growth scaling, and readable portfolio labels.
def ensure_master_exists():
    if not MASTER_DSS_PATH.exists():
        raise FileNotFoundError(f"Master DSS file not found: {MASTER_DSS_PATH}")


def growth_multiplier(rate, years):
    return (1 + rate) ** years


def portfolio_name(portfolio):
    active = [f"{k}:{v}" for k, v in portfolio.items() if v > 0]
    return "BaseCase" if not active else " | ".join(active)


def count_active_measures(portfolio):
    return sum(1 for v in portfolio.values() if v > 0)




# Build synthetic 24-hour profiles for base load, EV charging, solar, and data center demand.
def make_time_index():
    return pd.date_range("2025-01-01 00:00:00", periods=24, freq="h")


def synthetic_base_feeder_profile(horizon_years):
    hours = np.arange(24)
    shape = (
        0.80
        + 0.10 * np.sin((hours - 7) / 24 * 2 * np.pi)
        + 0.18 * np.sin((hours - 18) / 24 * 2 * np.pi)
    )
    shape = np.clip(shape, 0.60, None)
    shape = shape / np.mean(shape)
    return shape * growth_multiplier(BASE_FEEDER_ANNUAL_GROWTH, horizon_years)


def synthetic_ev_profile(horizon_years, ev_growth_rate):
    hours = np.arange(24)
    profile = np.zeros(24)
    for h in hours:
        evening_peak = math.exp(-((h - 19) ** 2) / 8)
        late_peak = 0.7 * math.exp(-((h - 22) ** 2) / 5)
        morning_bump = 0.10 * math.exp(-((h - 7) ** 2) / 10)
        profile[h] = evening_peak + late_peak + morning_bump

    profile = profile / profile.max()
    base_ev_mw = 0.6
    ev_mw = base_ev_mw * growth_multiplier(ev_growth_rate, horizon_years)
    return profile * ev_mw


def synthetic_solar_profile(horizon_years, solar_adoption_mw):
    hours = np.arange(24)
    profile = np.zeros(24)

    for h in hours:
        if 6 <= h <= 18:
            profile[h] = math.sin((h - 6) / 12 * math.pi)
        else:
            profile[h] = 0.0

    profile = profile / max(profile.max(), 1e-6)
    feeder_equiv_mw = solar_adoption_mw / 100.0   # 100/200/300 -> 1/2/3 MW equivalent
    feeder_equiv_mw *= (1 + 0.02 * horizon_years)
    return profile * feeder_equiv_mw


def synthetic_data_center_profile(horizon_years, dc_mw, dc_timeline_months):
    active = (horizon_years * 12) >= dc_timeline_months
    if not active:
        return np.zeros(24)

    hours = np.arange(24)
    shape = 0.97 + 0.03 * np.sin((hours - 2) / 24 * 2 * np.pi)
    shape = shape / np.mean(shape)
    return shape * dc_mw


def generate_profiles(horizon_label, ev_level, solar_level, dc_level, dc_timeline_label):
    horizon_years = PLANNING_HORIZONS[horizon_label]
    ev_growth_rate = EV_GROWTH[ev_level]
    solar_mw = SOLAR_ADOPTION[solar_level]
    dc_mw = DATA_CENTER_MW[dc_level]
    dc_timeline_months = DATA_CENTER_TIMELINE_MONTHS[dc_timeline_label]

    return pd.DataFrame({
        "time": make_time_index(),
        "feeder_mult": synthetic_base_feeder_profile(horizon_years),
        "ev_mw": synthetic_ev_profile(horizon_years, ev_growth_rate),
        "solar_mw": synthetic_solar_profile(horizon_years, solar_mw),
        "dc_mw": synthetic_data_center_profile(horizon_years, dc_mw, dc_timeline_months)
    })




# Generate candidate intervention portfolios, then map each one onto the synthetic profiles.
def generate_portfolios(levels=LEVELS, max_active_measures=3):
    portfolios = []
    for combo in product(levels, repeat=len(INTERVENTION_KEYS)):
        p = dict(zip(INTERVENTION_KEYS, combo))
        if all(v == 0 for v in p.values()):
            continue
        if max_active_measures is not None and count_active_measures(p) > max_active_measures:
            continue
        portfolios.append(p)
    return portfolios




def apply_portfolio_to_profiles(profiles, portfolio):
    modified = profiles.copy()

    # Battery
    battery_level = portfolio.get("Battery", 0)
    if battery_level > 0:
        discharge_hours = modified["time"].dt.hour.isin([17, 18, 19, 20, 21])
        charge_hours = modified["time"].dt.hour.isin([11, 12, 13, 14])

        discharge_factor = {33: 0.04, 66: 0.08, 100: 0.12}[battery_level]
        charge_factor = {33: 0.01, 66: 0.02, 100: 0.03}[battery_level]

        modified.loc[discharge_hours, "feeder_mult"] *= (1 - discharge_factor)
        modified.loc[charge_hours, "feeder_mult"] *= (1 + charge_factor)

    # Managed Charging
    mc_level = portfolio.get("ManagedCharging", 0)
    if mc_level > 0:
        shift_fraction = {33: 0.15, 66: 0.30, 100: 0.50}[mc_level]
        evening = modified["time"].dt.hour.isin([18, 19, 20, 21])
        late_night = modified["time"].dt.hour.isin([0, 1, 2, 3, 4, 5])

        shifted = modified.loc[evening, "ev_mw"] * shift_fraction
        modified.loc[evening, "ev_mw"] *= (1 - shift_fraction)
        modified.loc[late_night, "ev_mw"] += shifted.sum() / max(late_night.sum(), 1)

    # Phased Interconnection
    pi_level = portfolio.get("PhasedInterconnection", 0)
    if pi_level > 0:
        dc_reduction = {33: 0.20, 66: 0.40, 100: 0.60}[pi_level]
        modified["dc_mw"] *= (1 - dc_reduction)

    # Demand Tariff
    dt_level = portfolio.get("DemandTariff", 0)
    if dt_level > 0:
        feeder_reduction = {33: 0.03, 66: 0.06, 100: 0.10}[dt_level]
        ev_reduction = {33: 0.05, 66: 0.10, 100: 0.15}[dt_level]
        peak = modified["time"].dt.hour.isin([17, 18, 19, 20])

        modified.loc[peak, "feeder_mult"] *= (1 - feeder_reduction)
        modified.loc[peak, "ev_mw"] *= (1 - ev_reduction)

    return modified


def transformer_capacity_multiplier(level):
    return {0: 1.00, 33: 1.10, 66: 1.20, 100: 1.30}[level]


def line_capacity_multiplier(level):
    return {0: 1.00, 33: 1.08, 66: 1.15, 100: 1.25}[level]




# Compile the feeder, inject scenario assets, and evaluate violations for each portfolio.
def compile_feeder(master_dss_path=MASTER_DSS_PATH):
    ensure_master_exists()
    dss.Basic.ClearAll()
    dss.Text.Command(f"Compile [{master_dss_path.as_posix()}]")
    dss.Solution.Mode(0)
    dss.Solution.MaxIterations(100)


def inspect_feeder():
    compile_feeder()
    print("Circuit:", dss.Circuit.Name())
    print("Num buses:", dss.Circuit.NumBuses())
    print("Num loads:", len(dss.Loads.AllNames()))
    print("Num lines:", len(dss.Lines.AllNames()))
    print("Num transformers:", len(dss.Transformers.AllNames()))
    print("Sample buses:", dss.Circuit.AllBusNames()[:30])


def scale_existing_loads(multiplier):
    for load_name in dss.Loads.AllNames():
        dss.Loads.Name(load_name)
        dss.Loads.kW(dss.Loads.kW() * multiplier)
        dss.Loads.kvar(dss.Loads.kvar() * multiplier)


def add_ev_loads(total_ev_mw):
    total_kw = total_ev_mw * 1000
    per_bus_kw = total_kw / len(EV_BUSES) if EV_BUSES else 0

    for i, bus in enumerate(EV_BUSES):
        suffix = BUS_PHASE_MAP_EV.get(bus, ".1")
        dss.Text.Command(
            f"New Load.EV_{i+1} "
            f"Bus1={bus}{suffix} "
            f"Phases=1 Conn=Wye kV={SINGLE_PHASE_KV_LN} "
            f"kW={per_bus_kw:.2f} kvar={0.20 * per_bus_kw:.2f}"
        )


def add_solar_generation(total_solar_mw):
    total_kw = total_solar_mw * 1000
    per_bus_kw = total_kw / len(SOLAR_BUSES) if SOLAR_BUSES else 0

    for i, bus in enumerate(SOLAR_BUSES):
        suffix = BUS_PHASE_MAP_SOLAR.get(bus, ".1")
        dss.Text.Command(
            f"New Generator.SOLAR_{i+1} "
            f"Bus1={bus}{suffix} "
            f"Phases=1 kV={SINGLE_PHASE_KV_LN} "
            f"kW={per_bus_kw:.2f} PF=1.0"
        )


def add_data_center_load(total_dc_mw):
    total_kw = total_dc_mw * 1000
    dss.Text.Command(
        f"New Load.DATACENTER "
        f"Bus1={DATA_CENTER_BUS}.1.2.3 "
        f"Phases=3 Conn=Wye kV={PRIMARY_KV_LL} "
        f"kW={total_kw:.2f} kvar={0.25 * total_kw:.2f}"
    )


def collect_line_overloads_for_portfolio(portfolio):
    overloaded = []
    cap_mult = line_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))

    for line_name in dss.Lines.AllNames():
        dss.Lines.Name(line_name)
        elem_name = f"Line.{line_name}"
        dss.Circuit.SetActiveElement(elem_name)

        buses = dss.CktElement.BusNames()
        currents = dss.CktElement.CurrentsMagAng()
        mags = currents[0::2] if currents else []
        max_current = max(mags) if mags else 0.0
        norm_amps = dss.Lines.NormAmps() * cap_mult
        loading_pct = 100 * max_current / norm_amps if norm_amps > 0 else np.nan

        if not np.isnan(loading_pct) and loading_pct > 100:
            overloaded.append({
                "line": line_name,
                "from_bus": buses[0].split(".")[0] if len(buses) > 0 else None,
                "to_bus": buses[1].split(".")[0] if len(buses) > 1 else None,
                "loading_pct": loading_pct
            })
    return overloaded


def collect_transformer_overloads_for_portfolio(portfolio):
    overloaded = []
    cap_mult = transformer_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))

    for xf_name in dss.Transformers.AllNames():
        dss.Transformers.Name(xf_name)
        elem_name = f"Transformer.{xf_name}"
        dss.Circuit.SetActiveElement(elem_name)

        buses = dss.CktElement.BusNames()
        currents = dss.CktElement.CurrentsMagAng()
        mags = currents[0::2] if currents else []
        max_current = max(mags) if mags else 0.0

        kva = dss.Transformers.kVA()
        kv = dss.Transformers.kV()
        if kva > 0 and kv > 0:
            rated_amps = (kva * 1000) / (math.sqrt(3) * kv * 1000)
            rated_amps *= cap_mult
            loading_pct = 100 * max_current / rated_amps if rated_amps > 0 else 0.0
            if loading_pct > 100:
                overloaded.append({
                    "transformer": xf_name,
                    "bus1": buses[0].split(".")[0] if len(buses) > 0 else None,
                    "bus2": buses[1].split(".")[0] if len(buses) > 1 else None,
                    "loading_pct": loading_pct
                })
    return overloaded


def get_bus_voltage_status():
    rows = []
    for bus in dss.Circuit.AllBusNames():
        dss.Circuit.SetActiveBus(bus)
        vals = dss.Bus.puVmagAngle()
        mags = vals[0::2] if vals else []
        if mags:
            vmin = min(mags)
            vmax = max(mags)
        else:
            vmin, vmax = np.nan, np.nan

        if np.isnan(vmin):
            status = "unknown"
        elif vmin < VOLTAGE_MIN_PU:
            status = "undervoltage"
        elif vmax > VOLTAGE_MAX_PU:
            status = "overvoltage"
        else:
            status = "normal"

        rows.append({
            "bus": bus,
            "vmin_pu": vmin,
            "vmax_pu": vmax,
            "status": status
        })
    return pd.DataFrame(rows)


def solve_one_timestep_portfolio(row, portfolio, capture_details=False):
    compile_feeder()

    scale_existing_loads(row["feeder_mult"])

    if row["ev_mw"] > 0:
        add_ev_loads(row["ev_mw"])
    if row["solar_mw"] > 0:
        add_solar_generation(row["solar_mw"])
    if row["dc_mw"] > 0:
        add_data_center_load(row["dc_mw"])

    dss.Solution.Solve()
    converged = bool(dss.Solution.Converged())

    bus_v = dss.Circuit.AllBusMagPu()
    vmin = min(bus_v) if bus_v else np.nan
    vmax = max(bus_v) if bus_v else np.nan
    underv = sum(v < VOLTAGE_MIN_PU for v in bus_v)
    overv = sum(v > VOLTAGE_MAX_PU for v in bus_v)

    overloaded_lines = collect_line_overloads_for_portfolio(portfolio)
    overloaded_transformers = collect_transformer_overloads_for_portfolio(portfolio)

    result = {
        "time": row["time"],
        "converged": converged,
        "vmin_pu": vmin,
        "vmax_pu": vmax,
        "undervoltage_buses": underv,
        "overvoltage_buses": overv,
        "num_overloaded_lines": len(overloaded_lines),
        "num_overloaded_transformers": len(overloaded_transformers),
    }

    if capture_details:
        result["bus_status_df"] = get_bus_voltage_status()
        result["overloaded_lines_df"] = pd.DataFrame(overloaded_lines)
        result["overloaded_transformers_df"] = pd.DataFrame(overloaded_transformers)

    return result


def run_simulation_for_portfolio(profiles, portfolio):
    modified_profiles = apply_portfolio_to_profiles(profiles, portfolio)
    results = []

    # Compile once, then re-solve for each hour by updating load/gen values in-place.
    compile_feeder()

    # Capture baseline kW/kvar so we can reset each hour.
    baseline_kw = {}
    baseline_kvar = {}
    for load_name in dss.Loads.AllNames():
        dss.Loads.Name(load_name)
        baseline_kw[load_name] = dss.Loads.kW()
        baseline_kvar[load_name] = dss.Loads.kvar()

    # Pre-add EV, solar, and DC devices at zero power (placeholders).
    for i, bus in enumerate(EV_BUSES):
        suffix = BUS_PHASE_MAP_EV.get(bus, ".1")
        dss.Text.Command(
            f"New Load.EV_{i+1} "
            f"Bus1={bus}{suffix} "
            f"Phases=1 Conn=Wye kV={SINGLE_PHASE_KV_LN} "
            f"kW=0 kvar=0"
        )
    for i, bus in enumerate(SOLAR_BUSES):
        suffix = BUS_PHASE_MAP_SOLAR.get(bus, ".1")
        dss.Text.Command(
            f"New Generator.SOLAR_{i+1} "
            f"Bus1={bus}{suffix} "
            f"Phases=1 kV={SINGLE_PHASE_KV_LN} "
            f"kW=0 PF=1.0"
        )
    dss.Text.Command(
        f"New Load.DATACENTER "
        f"Bus1={DATA_CENTER_BUS}.1.2.3 "
        f"Phases=3 Conn=Wye kV={PRIMARY_KV_LL} "
        f"kW=0 kvar=0"
    )

    cap_mult_line = line_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))
    cap_mult_xf = transformer_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))

    for _, row in modified_profiles.iterrows():
        # Reset existing loads to baseline * hourly multiplier
        mult = row["feeder_mult"]
        for load_name in baseline_kw:
            dss.Loads.Name(load_name)
            dss.Loads.kW(baseline_kw[load_name] * mult)
            dss.Loads.kvar(baseline_kvar[load_name] * mult)

        # Update EV loads
        ev_kw_per_bus = (row["ev_mw"] * 1000) / len(EV_BUSES) if EV_BUSES else 0
        for i in range(len(EV_BUSES)):
            dss.Loads.Name(f"EV_{i+1}")
            dss.Loads.kW(ev_kw_per_bus)
            dss.Loads.kvar(0.20 * ev_kw_per_bus)

        # Update solar generators
        solar_kw_per_bus = (row["solar_mw"] * 1000) / len(SOLAR_BUSES) if SOLAR_BUSES else 0
        for i in range(len(SOLAR_BUSES)):
            dss.Circuit.SetActiveElement(f"Generator.SOLAR_{i+1}")
            dss.Text.Command(f"Generator.SOLAR_{i+1}.kW={solar_kw_per_bus:.2f}")

        # Update data center load
        dc_kw = row["dc_mw"] * 1000
        dss.Loads.Name("DATACENTER")
        dss.Loads.kW(dc_kw)
        dss.Loads.kvar(0.25 * dc_kw)

        # Solve
        dss.Solution.Solve()
        converged = bool(dss.Solution.Converged())

        bus_v = dss.Circuit.AllBusMagPu()
        vmin = min(bus_v) if bus_v else np.nan
        vmax = max(bus_v) if bus_v else np.nan
        underv = sum(v < VOLTAGE_MIN_PU for v in bus_v)
        overv = sum(v > VOLTAGE_MAX_PU for v in bus_v)

        # Overload detection (inline for speed)
        num_overloaded_lines = 0
        for line_name in dss.Lines.AllNames():
            dss.Lines.Name(line_name)
            dss.Circuit.SetActiveElement(f"Line.{line_name}")
            currents = dss.CktElement.CurrentsMagAng()
            mags = currents[0::2] if currents else []
            max_current = max(mags) if mags else 0.0
            norm_amps = dss.Lines.NormAmps() * cap_mult_line
            if norm_amps > 0 and (100 * max_current / norm_amps) > 100:
                num_overloaded_lines += 1

        num_overloaded_xf = 0
        for xf_name in dss.Transformers.AllNames():
            dss.Transformers.Name(xf_name)
            dss.Circuit.SetActiveElement(f"Transformer.{xf_name}")
            currents = dss.CktElement.CurrentsMagAng()
            mags = currents[0::2] if currents else []
            max_current = max(mags) if mags else 0.0
            kva = dss.Transformers.kVA()
            kv = dss.Transformers.kV()
            if kva > 0 and kv > 0:
                rated_amps = (kva * 1000) / (math.sqrt(3) * kv * 1000) * cap_mult_xf
                if rated_amps > 0 and (100 * max_current / rated_amps) > 100:
                    num_overloaded_xf += 1

        results.append({
            "time": row["time"],
            "converged": converged,
            "vmin_pu": vmin,
            "vmax_pu": vmax,
            "undervoltage_buses": underv,
            "overvoltage_buses": overv,
            "num_overloaded_lines": num_overloaded_lines,
            "num_overloaded_transformers": num_overloaded_xf,
        })

    return modified_profiles, pd.DataFrame(results)





# Convert raw hourly outputs into stress metrics and weighted portfolio scores.
def summarize_results(results_df):
    summary = {
        "convergence_failures": int((~results_df["converged"]).sum()),
        "worst_vmin": float(results_df["vmin_pu"].min()),
        "worst_vmax": float(results_df["vmax_pu"].max()),
        "total_undervoltage_buses": int(results_df["undervoltage_buses"].sum()),
        "total_overvoltage_buses": int(results_df["overvoltage_buses"].sum()),
        "total_line_overloads": int(results_df["num_overloaded_lines"].sum()),
        "total_transformer_overloads": int(results_df["num_overloaded_transformers"].sum()),
    }
    stress = (
        20 * summary["convergence_failures"] +
        5 * summary["total_line_overloads"] +
        6 * summary["total_transformer_overloads"] +
        2 * summary["total_undervoltage_buses"] +
        2 * summary["total_overvoltage_buses"]
    )
    summary["grid_stress_score"] = float(stress)
    return summary


def calculate_improvement(base_summary, alt_summary):
    base = max(base_summary["grid_stress_score"], 1e-6)
    alt = alt_summary["grid_stress_score"]
    return max(0.0, (base - alt) / base * 100.0)


def aggregate_portfolio_scores(portfolio):
    cost_raw = sum(COST_BY_LEVEL[k][v] for k, v in portfolio.items())
    feasibility_raw = float(np.mean([FEASIBILITY_BY_LEVEL[k][v] for k, v in portfolio.items()]))
    deployment_raw = float(np.mean([DEPLOYMENT_BY_LEVEL[k][v] for k, v in portfolio.items()]))

    max_possible_cost = sum(max(v.values()) for v in COST_BY_LEVEL.values())
    cost_score = 10 * (1 - cost_raw / max_possible_cost)

    return {
        "cost_raw": cost_raw,
        "cost_score": round(cost_score, 2),
        "feasibility_score": round(feasibility_raw, 2),
        "deployment_score": round(deployment_raw, 2),
    }


def score_portfolio(portfolio, improvement_pct):
    agg = aggregate_portfolio_scores(portfolio)
    tech_score = min(10.0, improvement_pct / 10.0)

    final_score = (
        0.40 * tech_score +
        0.25 * agg["cost_score"] +
        0.20 * agg["feasibility_score"] +
        0.15 * agg["deployment_score"]
    )

    row = {
        **portfolio,
        "portfolio_name": portfolio_name(portfolio),
        "technical_improvement_pct": round(improvement_pct, 2),
        "technical_score": round(tech_score, 2),
        "cost_score": agg["cost_score"],
        "feasibility_score": agg["feasibility_score"],
        "deployment_score": agg["deployment_score"],
        "cost_raw": agg["cost_raw"],
        "final_score": round(final_score, 3),
    }
    return row


def run_portfolio_planning_study(
    horizon_label,
    ev_level,
    solar_level,
    dc_level,
    dc_timeline_label,
    max_active_measures=3,
    max_portfolios=None,
    progress_every=25
):
    base_profiles = generate_profiles(horizon_label, ev_level, solar_level, dc_level, dc_timeline_label)

    base_portfolio = {k: 0 for k in INTERVENTION_KEYS}
    base_profiles_mod, base_results = run_simulation_for_portfolio(base_profiles, base_portfolio)
    base_summary = summarize_results(base_results)

    portfolios = generate_portfolios(max_active_measures=max_active_measures)
    if max_portfolios is not None:
        portfolios = portfolios[:max_portfolios]

    ranking_rows = []
    detailed_outputs = {
        "BaseCase": {
            "portfolio": base_portfolio,
            "profiles": base_profiles_mod,
            "results": base_results,
            "summary": base_summary,
        }
    }

    total = len(portfolios)
    for i, portfolio in enumerate(portfolios, start=1):
        mod_profiles, alt_results = run_simulation_for_portfolio(base_profiles, portfolio)
        alt_summary = summarize_results(alt_results)
        improvement_pct = calculate_improvement(base_summary, alt_summary)
        score_row = score_portfolio(portfolio, improvement_pct)
        ranking_rows.append(score_row)

        detailed_outputs[score_row["portfolio_name"]] = {
            "portfolio": portfolio,
            "profiles": mod_profiles,
            "results": alt_results,
            "summary": alt_summary,
            "score": score_row
        }

        if (i % progress_every == 0) or (i == total):
            print(f"Completed {i}/{total} portfolios")

    ranking_df = pd.DataFrame(ranking_rows).sort_values("final_score", ascending=False).reset_index(drop=True)

    report = {
        "scenario": {
            "feeder": "IEEE123",
            "horizon_label": horizon_label,
            "ev_level": ev_level,
            "solar_level": solar_level,
            "dc_level": dc_level,
            "dc_timeline_label": dc_timeline_label,
        },
        "base_summary": base_summary,
        "ranking": ranking_df,
        "top_recommendation": ranking_df.iloc[0].to_dict() if len(ranking_df) > 0 else None,
        "second_best": ranking_df.iloc[1].to_dict() if len(ranking_df) > 1 else None,
    }

    return detailed_outputs, report




# Build helper tables and feeder maps so results can be explained visually.
def get_baseline_loads_by_bus():
    compile_feeder()
    bus_load_map = {}

    for load_name in dss.Loads.AllNames():
        dss.Loads.Name(load_name)
        buses = dss.CktElement.BusNames()
        kw = dss.Loads.kW()

        if buses:
            bus = buses[0].split(".")[0]
            bus_load_map[bus] = bus_load_map.get(bus, 0.0) + kw

    return bus_load_map


def create_bus_asset_table(profiles_row):
    compile_feeder()
    baseline_loads = get_baseline_loads_by_bus()
    all_buses = set(dss.Circuit.AllBusNames()) | set(EV_BUSES) | set(SOLAR_BUSES) | {DATA_CENTER_BUS}

    ev_total_kw = profiles_row["ev_mw"] * 1000
    ev_per_bus_kw = ev_total_kw / len(EV_BUSES) if EV_BUSES else 0

    solar_total_kw = profiles_row["solar_mw"] * 1000
    solar_per_bus_kw = solar_total_kw / len(SOLAR_BUSES) if SOLAR_BUSES else 0

    dc_kw = profiles_row["dc_mw"] * 1000

    rows = []
    for bus in sorted(all_buses, key=lambda x: str(x)):
        rows.append({
            "bus": bus,
            "baseline_load_present": bus in baseline_loads,
            "baseline_kw": round(baseline_loads.get(bus, 0.0), 2),
            "ev_added": bus in EV_BUSES,
            "ev_kw": round(ev_per_bus_kw if bus in EV_BUSES else 0.0, 2),
            "solar_added": bus in SOLAR_BUSES,
            "solar_kw": round(solar_per_bus_kw if bus in SOLAR_BUSES else 0.0, 2),
            "data_center_added": bus == DATA_CENTER_BUS,
            "data_center_kw": round(dc_kw if bus == DATA_CENTER_BUS else 0.0, 2),
        })

    return pd.DataFrame(rows)




# Plot profiles, violations, and before/after portfolio comparisons.
def build_feeder_graph():
    compile_feeder()
    G = nx.Graph()

    for line_name in dss.Lines.AllNames():
        dss.Lines.Name(line_name)
        elem_name = f"Line.{line_name}"
        dss.Circuit.SetActiveElement(elem_name)
        buses = dss.CktElement.BusNames()

        if len(buses) >= 2:
            b1 = buses[0].split(".")[0]
            b2 = buses[1].split(".")[0]
            G.add_edge(b1, b2, element=line_name)

    return G


def plot_profiles(profiles, title="Synthetic Profiles"):
    plt.figure(figsize=(12, 6))
    plt.plot(profiles["time"], profiles["feeder_mult"], label="Feeder Multiplier")
    plt.plot(profiles["time"], profiles["ev_mw"], label="EV MW")
    plt.plot(profiles["time"], profiles["solar_mw"], label="Solar MW")
    plt.plot(profiles["time"], profiles["dc_mw"], label="Data Center MW")
    plt.title(title)
    plt.xlabel("Time")
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_results(results_df, title="Simulation Results"):
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)

    axes[0].plot(results_df["time"], results_df["vmin_pu"], label="Min Voltage PU")
    axes[0].plot(results_df["time"], results_df["vmax_pu"], label="Max Voltage PU")
    axes[0].axhline(VOLTAGE_MIN_PU, color="r", linestyle="--", label="Min Limit")
    axes[0].axhline(VOLTAGE_MAX_PU, color="r", linestyle="--", label="Max Limit")
    axes[0].legend()
    axes[0].set_ylabel("Voltage PU")
    axes[0].set_title(title)

    axes[1].plot(results_df["time"], results_df["undervoltage_buses"], label="Undervoltage Buses")
    axes[1].plot(results_df["time"], results_df["overvoltage_buses"], label="Overvoltage Buses")
    axes[1].legend()
    axes[1].set_ylabel("Bus Count")

    axes[2].plot(results_df["time"], results_df["num_overloaded_lines"], label="Overloaded Lines")
    axes[2].plot(results_df["time"], results_df["num_overloaded_transformers"], label="Overloaded Transformers")
    axes[2].legend()
    axes[2].set_ylabel("Count")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_bus_asset_map(profiles_row):
    G = build_feeder_graph()
    pos = nx.spring_layout(G, seed=42)
    baseline_loads = get_baseline_loads_by_bus()

    node_colors = []
    node_sizes = []

    for node in G.nodes():
        has_baseline = node in baseline_loads
        has_ev = node in EV_BUSES
        has_solar = node in SOLAR_BUSES
        has_dc = node == DATA_CENTER_BUS

        if has_dc:
            color = "red"
        elif has_ev and has_solar:
            color = "purple"
        elif has_ev:
            color = "orange"
        elif has_solar:
            color = "green"
        elif has_baseline:
            color = "skyblue"
        else:
            color = "lightgray"

        size = 120
        if has_baseline:
            size += 80
        if has_ev:
            size += 80
        if has_solar:
            size += 80
        if has_dc:
            size += 180

        node_colors.append(color)
        node_sizes.append(size)

    plt.figure(figsize=(18, 12))
    nx.draw(
        G, pos,
        with_labels=True,
        node_color=node_colors,
        node_size=node_sizes,
        font_size=8,
        edge_color="gray"
    )
    plt.title("Bus Asset Map\nBlue=Baseline, Orange=EV, Green=Solar, Purple=EV+Solar, Red=Data Center")
    plt.show()


def solve_specific_hour_and_capture(row, portfolio):
    result = solve_one_timestep_portfolio(row, portfolio, capture_details=True)
    return (
        result["bus_status_df"],
        result["overloaded_lines_df"],
        result["overloaded_transformers_df"]
    )


def plot_breakdown_map(row, portfolio, title=None):
    G = build_feeder_graph()
    pos = nx.spring_layout(G, seed=42)

    bus_status_df, overloaded_lines_df, _ = solve_specific_hour_and_capture(row, portfolio)
    bus_status_map = dict(zip(bus_status_df["bus"], bus_status_df["status"]))

    overloaded_line_set = set(overloaded_lines_df["line"]) if not overloaded_lines_df.empty else set()

    node_colors = []
    for node in G.nodes():
        status = bus_status_map.get(node, "normal")
        if status == "undervoltage":
            node_colors.append("red")
        elif status == "overvoltage":
            node_colors.append("yellow")
        elif status == "unknown":
            node_colors.append("gray")
        else:
            node_colors.append("lightgreen")

    edge_colors = []
    for _, _, data in G.edges(data=True):
        line_name = data.get("element")
        edge_colors.append("red" if line_name in overloaded_line_set else "gray")

    plt.figure(figsize=(18, 12))
    nx.draw(
        G, pos,
        with_labels=True,
        node_color=node_colors,
        edge_color=edge_colors,
        node_size=230,
        font_size=8
    )
    plt.title(title or f"Breakdown Map\n{portfolio_name(portfolio)}")
    plt.show()


def plot_breakdown_comparison(row, base_portfolio, alt_portfolio, base_title="Base Case", alt_title="Alternative"):
    G = build_feeder_graph()
    pos = nx.spring_layout(G, seed=42)

    base_bus_df, base_line_df, _ = solve_specific_hour_and_capture(row, base_portfolio)
    alt_bus_df, alt_line_df, _ = solve_specific_hour_and_capture(row, alt_portfolio)

    def get_node_colors(bus_df):
        bus_status_map = dict(zip(bus_df["bus"], bus_df["status"]))
        colors = []
        for node in G.nodes():
            status = bus_status_map.get(node, "normal")
            if status == "undervoltage":
                colors.append("red")
            elif status == "overvoltage":
                colors.append("yellow")
            elif status == "unknown":
                colors.append("gray")
            else:
                colors.append("lightgreen")
        return colors

    def get_edge_colors(line_df):
        overloaded_line_set = set(line_df["line"]) if not line_df.empty else set()
        colors = []
        for _, _, data in G.edges(data=True):
            line_name = data.get("element")
            colors.append("red" if line_name in overloaded_line_set else "gray")
        return colors

    fig, axes = plt.subplots(1, 2, figsize=(22, 10))

    nx.draw(
        G, pos, ax=axes[0], with_labels=True,
        node_color=get_node_colors(base_bus_df),
        edge_color=get_edge_colors(base_line_df),
        node_size=220, font_size=7
    )
    axes[0].set_title(base_title)

    nx.draw(
        G, pos, ax=axes[1], with_labels=True,
        node_color=get_node_colors(alt_bus_df),
        edge_color=get_edge_colors(alt_line_df),
        node_size=220, font_size=7
    )
    axes[1].set_title(alt_title)

    plt.tight_layout()
    plt.show()


def compare_intervention_impact(base_results_df, alt_results_df, alt_name):
    comparison = pd.DataFrame({
        "time": base_results_df["time"],
        "base_undervoltage_buses": base_results_df["undervoltage_buses"],
        "alt_undervoltage_buses": alt_results_df["undervoltage_buses"],
        "base_overloaded_lines": base_results_df["num_overloaded_lines"],
        "alt_overloaded_lines": alt_results_df["num_overloaded_lines"],
        "base_overloaded_transformers": base_results_df["num_overloaded_transformers"],
        "alt_overloaded_transformers": alt_results_df["num_overloaded_transformers"],
    })

    comparison["uv_improvement"] = comparison["base_undervoltage_buses"] - comparison["alt_undervoltage_buses"]
    comparison["line_improvement"] = comparison["base_overloaded_lines"] - comparison["alt_overloaded_lines"]
    comparison["xf_improvement"] = comparison["base_overloaded_transformers"] - comparison["alt_overloaded_transformers"]

    print(f"\nImpact comparison for: {alt_name}")
    print(comparison.head())
    return comparison


def plot_top_ranked_bar(ranking_df, top_n=10):
    top = ranking_df.head(top_n).copy()
    plt.figure(figsize=(14, 6))
    plt.barh(top["portfolio_name"][::-1], top["final_score"][::-1])
    plt.xlabel("Final Score")
    plt.title(f"Top {top_n} Ranked Portfolios")
    plt.tight_layout()
    plt.show()


def plot_cost_vs_technical(ranking_df, top_n=50):
    df = ranking_df.head(top_n).copy()
    plt.figure(figsize=(10, 6))
    plt.scatter(df["cost_score"], df["technical_improvement_pct"], s=60)
    for _, r in df.iterrows():
        plt.annotate(r["portfolio_name"][:18], (r["cost_score"], r["technical_improvement_pct"]), fontsize=7)
    plt.xlabel("Cost Score (higher is better / lower cost)")
    plt.ylabel("Technical Improvement %")
    plt.title(f"Cost vs Technical Improvement (Top {top_n})")
    plt.tight_layout()
    plt.show()





# Print a compact report for the ranked portfolio results.
def print_report(report):
    print("\n" + "=" * 100)
    print("GRID PLANNING PORTFOLIO REPORT")
    print("=" * 100)

    print("\nScenario")
    for k, v in report["scenario"].items():
        print(f"  {k}: {v}")

    print("\nBase Case Summary")
    for k, v in report["base_summary"].items():
        print(f"  {k}: {v}")

    print("\nTop 10 Ranked Portfolios")
    cols = [
        "portfolio_name",
        "technical_improvement_pct",
        "technical_score",
        "cost_score",
        "feasibility_score",
        "deployment_score",
        "final_score"
    ]
    print(report["ranking"][cols].head(10).to_string(index=False))

    print("\nTop Recommendation")
    if report["top_recommendation"]:
        for k, v in report["top_recommendation"].items():
            print(f"  {k}: {v}")

    print("\nSecond Best Option")
    if report["second_best"]:
        for k, v in report["second_best"].items():
            print(f"  {k}: {v}")

    print("=" * 100)




# Example execution block that runs the study, writes CSV outputs, and renders visuals.
if __name__ == "__main__":
    ensure_master_exists()
    # inspect_feeder()

    scenario = {
        "horizon_label": "12m",
        "ev_level": "High",
        "solar_level": "Base",
        "dc_level": "Moderate",
        "dc_timeline_label": "12m"
    }

    outputs, report = run_portfolio_planning_study(
        **scenario,
        max_active_measures=3,   # prune combinations
        max_portfolios=120,      # set None to run all generated portfolios
        progress_every=20
    )

    print_report(report)

    out_dir = Path("./outputs2")
    out_dir.mkdir(exist_ok=True)

    report["ranking"].to_csv(out_dir / "portfolio_ranking.csv", index=False)

    summary_rows = []
    for name, data in outputs.items():
        row = {"portfolio_name": name}
        row.update(data["summary"])
        if "score" in data:
            row.update(data["score"])
        summary_rows.append(row)

    pd.DataFrame(summary_rows).to_csv(out_dir / "portfolio_summaries.csv", index=False)

    # Save top 5 detailed outputs
    top_names = ["BaseCase"] + report["ranking"]["portfolio_name"].head(5).tolist()
    for name in top_names:
        if name in outputs:
            outputs[name]["profiles"].to_csv(out_dir / f"{name.replace('|','_').replace(':','_')}_profiles.csv", index=False)
            outputs[name]["results"].to_csv(out_dir / f"{name.replace('|','_').replace(':','_')}_results.csv", index=False)

    # --------------------------------------------------------
    # VISUALS
    # --------------------------------------------------------

    base_profiles = outputs["BaseCase"]["profiles"]
    base_results = outputs["BaseCase"]["results"]

    plot_profiles(base_profiles, title="Base Case Synthetic Profiles")
    plot_results(base_results, title="Base Case Time-Series Results")

    # Asset table / asset map for a representative peak hour
    peak_idx = int(base_profiles["ev_mw"].idxmax())
    peak_row = base_profiles.loc[peak_idx]
    asset_table = create_bus_asset_table(peak_row)
    asset_table.to_csv(out_dir / "bus_asset_table_peak_hour.csv", index=False)
    plot_bus_asset_map(peak_row)

    # Breakdown map for base case
    base_portfolio = {k: 0 for k in INTERVENTION_KEYS}
    plot_breakdown_map(peak_row, base_portfolio, title="Base Case Breakdown Map at Peak EV Hour")

    # Breakdown comparison for top recommendation
    if report["top_recommendation"] is not None:
        top_portfolio = {k: int(report["top_recommendation"][k]) for k in INTERVENTION_KEYS}
        plot_breakdown_comparison(
            peak_row,
            base_portfolio=base_portfolio,
            alt_portfolio=top_portfolio,
            base_title="Base Case Breakdown",
            alt_title=f"Top Portfolio Breakdown\n{portfolio_name(top_portfolio)}"
        )

        top_name = report["top_recommendation"]["portfolio_name"]
        top_results = outputs[top_name]["results"]
        impact_df = compare_intervention_impact(base_results, top_results, top_name)
        impact_df.to_csv(out_dir / "top_portfolio_impact_comparison.csv", index=False)

    plot_top_ranked_bar(report["ranking"], top_n=10)
    plot_cost_vs_technical(report["ranking"], top_n=min(30, len(report["ranking"])))
