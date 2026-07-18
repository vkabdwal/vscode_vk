"""
EPRI ckt5 simulation engine.
Full 24-hour QSTS simulation on the real EPRI Test Circuit 5 (981 primary buses, 2998 total buses).

Performance: compile-once pattern eliminates redundant DSS re-compilations across portfolios.
"""
import math
import numpy as np
import opendssdirect as dss
from pathlib import Path

# EPRI ckt5 paths
EPRI_DIR = Path(__file__).resolve().parent.parent.parent.parent / "ai_synthetic_data" / "epri_ckt5"
EPRI_MASTER = EPRI_DIR / "Master_ckt5.dss"

# Asset placement on EPRI ckt5 primary buses
# Selected from 3-phase primary buses suitable for large loads
EV_BUSES_EPRI = ["8163", "8164", "829", "834", "44582", "8160"]
SOLAR_BUSES_EPRI = ["6584", "8113", "8124", "14880", "63707", "63657"]
DATA_CENTER_BUS_EPRI = "8163"

# Voltage thresholds (ANSI C84.1)
VOLTAGE_MIN_PU = 0.95
VOLTAGE_MAX_PU = 1.05
PRIMARY_KV_LN = 7.2  # 12.47 kV line-to-line / sqrt(3)
PRIMARY_KV_LL = 12.47


def compile_epri_feeder():
    """Compile EPRI ckt5 model."""
    if not EPRI_MASTER.exists():
        raise FileNotFoundError(f"EPRI Master DSS not found: {EPRI_MASTER}")
    dss.Basic.ClearAll()
    dss.Text.Command(f"Compile [{EPRI_MASTER.as_posix()}]")
    dss.Solution.Mode(0)
    dss.Solution.MaxIterations(100)


def prepare_epri_simulation():
    """Compile feeder once and return cached context for fast repeated runs.
    
    Returns a dict with baseline load data and cached equipment ratings.
    Call this once before looping over portfolios.
    """
    compile_epri_feeder()

    # Capture baseline load values
    baseline_kw = {}
    baseline_kvar = {}
    for load_name in dss.Loads.AllNames():
        dss.Loads.Name(load_name)
        baseline_kw[load_name] = dss.Loads.kW()
        baseline_kvar[load_name] = dss.Loads.kvar()

    # Pre-add placeholder devices (once)
    for i, bus in enumerate(EV_BUSES_EPRI):
        dss.Text.Command(
            f"New Load.EV_{i+1} Bus1={bus}.1 "
            f"Phases=1 Conn=Wye kV={PRIMARY_KV_LN} kW=0 kvar=0"
        )
    for i, bus in enumerate(SOLAR_BUSES_EPRI):
        dss.Text.Command(
            f"New Generator.SOLAR_{i+1} Bus1={bus}.1 "
            f"Phases=1 kV={PRIMARY_KV_LN} kW=0 PF=1.0"
        )
    dss.Text.Command(
        f"New Load.DATACENTER Bus1={DATA_CENTER_BUS_EPRI}.1.2.3 "
        f"Phases=3 Conn=Wye kV={PRIMARY_KV_LL} kW=0 kvar=0"
    )

    # Cache line ratings (names + NormAmps don't change between solves)
    line_names = dss.Lines.AllNames() or []
    line_norm_amps = {}
    for ln in line_names:
        dss.Lines.Name(ln)
        line_norm_amps[ln] = dss.Lines.NormAmps()

    # Cache transformer ratings
    xf_names = dss.Transformers.AllNames() or []
    xf_rated_amps = {}
    for xf in xf_names:
        dss.Transformers.Name(xf)
        kva = dss.Transformers.kVA()
        kv = dss.Transformers.kV()
        if kva > 0 and kv > 0:
            xf_rated_amps[xf] = (kva * 1000) / (math.sqrt(3) * kv * 1000)
        else:
            xf_rated_amps[xf] = 0.0

    return {
        "baseline_kw": baseline_kw,
        "baseline_kvar": baseline_kvar,
        "line_names": line_names,
        "line_norm_amps": line_norm_amps,
        "xf_names": xf_names,
        "xf_rated_amps": xf_rated_amps,
    }


def run_epri_24hr_fast(ctx, modified_profiles, portfolio, cap_mult_line=1.0, cap_mult_xf=1.0):
    """Run 24-hour simulation reusing an already-compiled feeder context.
    
    ctx: dict returned by prepare_epri_simulation()
    """
    baseline_kw = ctx["baseline_kw"]
    baseline_kvar = ctx["baseline_kvar"]
    line_names = ctx["line_names"]
    line_norm_amps = ctx["line_norm_amps"]
    xf_names = ctx["xf_names"]
    xf_rated_amps = ctx["xf_rated_amps"]

    results = []
    for _, row in modified_profiles.iterrows():
        # Scale existing loads
        mult = row["feeder_mult"]
        for load_name in baseline_kw:
            dss.Loads.Name(load_name)
            dss.Loads.kW(baseline_kw[load_name] * mult)
            dss.Loads.kvar(baseline_kvar[load_name] * mult)

        # Update EV
        ev_kw = (row["ev_mw"] * 1000) / len(EV_BUSES_EPRI) if EV_BUSES_EPRI else 0
        for i in range(len(EV_BUSES_EPRI)):
            dss.Loads.Name(f"EV_{i+1}")
            dss.Loads.kW(ev_kw)
            dss.Loads.kvar(0.20 * ev_kw)

        # Update solar
        solar_kw = (row["solar_mw"] * 1000) / len(SOLAR_BUSES_EPRI) if SOLAR_BUSES_EPRI else 0
        for i in range(len(SOLAR_BUSES_EPRI)):
            dss.Text.Command(f"Generator.SOLAR_{i+1}.kW={solar_kw:.2f}")

        # Update data center
        dc_kw = row["dc_mw"] * 1000
        dss.Loads.Name("DATACENTER")
        dss.Loads.kW(dc_kw)
        dss.Loads.kvar(0.25 * dc_kw)

        # Solve
        dss.Solution.Solve()
        converged = bool(dss.Solution.Converged())

        bus_v = dss.Circuit.AllBusMagPu()
        vmin = min(bus_v) if bus_v else float("nan")
        vmax = max(bus_v) if bus_v else float("nan")
        underv = sum(v < VOLTAGE_MIN_PU for v in bus_v)
        overv = sum(v > VOLTAGE_MAX_PU for v in bus_v)

        # Line overloads (using cached ratings)
        num_overloaded_lines = 0
        for ln in line_names:
            norm_amps = line_norm_amps[ln] * cap_mult_line
            if norm_amps <= 0:
                continue
            dss.Circuit.SetActiveElement(f"Line.{ln}")
            currents = dss.CktElement.CurrentsMagAng()
            mags = currents[0::2] if currents else []
            if mags and max(mags) > norm_amps:
                num_overloaded_lines += 1

        # Transformer overloads (using cached ratings)
        num_overloaded_xf = 0
        for xf in xf_names:
            rated = xf_rated_amps[xf] * cap_mult_xf
            if rated <= 0:
                continue
            dss.Circuit.SetActiveElement(f"Transformer.{xf}")
            currents = dss.CktElement.CurrentsMagAng()
            mags = currents[0::2] if currents else []
            if mags and max(mags) > rated:
                num_overloaded_xf += 1

        results.append({
            "time": str(row["time"]),
            "converged": converged,
            "vmin_pu": round(vmin, 5),
            "vmax_pu": round(vmax, 5),
            "undervoltage_buses": underv,
            "overvoltage_buses": overv,
            "num_overloaded_lines": num_overloaded_lines,
            "num_overloaded_transformers": num_overloaded_xf,
        })

    return results


def run_epri_24hr_simulation(modified_profiles, portfolio, cap_mult_line=1.0, cap_mult_xf=1.0):
    """Run 24-hour simulation on EPRI ckt5 feeder (standalone, compiles each time).
    
    For batch evaluation of multiple portfolios, use prepare_epri_simulation() + run_epri_24hr_fast() instead.
    """
    ctx = prepare_epri_simulation()
    return run_epri_24hr_fast(ctx, modified_profiles, portfolio, cap_mult_line, cap_mult_xf)
