"""
Real data loader for FeederIQ.
Loads actual load profiles and PV profiles from openEDI/oedisi-ieee123 CSVs.
Each CSV has 35,040 rows (15-min intervals × 365 days).
"""
import numpy as np
import pandas as pd
from pathlib import Path

from ..config import (
    DATA_DIR, PLANNING_HORIZONS, EV_GROWTH, SOLAR_ADOPTION,
    DATA_CENTER_MW, DATA_CENTER_TIMELINE_MONTHS, BASE_FEEDER_ANNUAL_GROWTH,
)

LOAD_PROFILES_DIR = DATA_DIR / "profiles" / "load_profiles"
PV_PROFILES_DIR = DATA_DIR / "profiles" / "pv_profiles"


def _load_csv_as_hourly(filepath: Path) -> np.ndarray:
    """Load a 35040-point CSV and reshape to (365, 24) hourly averages."""
    data = pd.read_csv(filepath, header=None).values.flatten()
    if len(data) != 35040:
        return None
    daily = data.reshape(365, 96)
    hourly = daily.reshape(365, 24, 4).mean(axis=2)
    return hourly


def _find_peak_day(hourly_profiles: list) -> int:
    """Find the day with highest total load across all profiles."""
    total = np.zeros(365)
    for h in hourly_profiles:
        if h is not None:
            total += h.sum(axis=1)
    return int(total.argmax())


def generate_profiles_real_data(horizon_label, ev_level, solar_level, dc_level, dc_timeline_label):
    """
    Generate 24-hour profiles using REAL openEDI data for the feeder load and solar.
    EV and DC profiles remain synthetic (no real EV/DC data in the dataset).
    """
    horizon_years = PLANNING_HORIZONS[horizon_label]
    ev_growth_rate = EV_GROWTH[ev_level]
    solar_mw = SOLAR_ADOPTION[solar_level]
    dc_mw = DATA_CENTER_MW[dc_level]
    dc_timeline_months = DATA_CENTER_TIMELINE_MONTHS[dc_timeline_label]

    # Load real feeder profiles
    load_files = sorted(LOAD_PROFILES_DIR.glob("loadshape_*.csv"))
    load_profiles = []
    for f in load_files[:20]:  # Sample first 20 for speed
        h = _load_csv_as_hourly(f)
        if h is not None:
            load_profiles.append(h)

    if not load_profiles:
        return None  # Fall back to synthetic

    # Load real PV profiles
    pv_files = sorted(PV_PROFILES_DIR.glob("pvshape_*.csv"))
    pv_profiles = []
    for f in pv_files[:5]:  # Sample first 5
        h = _load_csv_as_hourly(f)
        if h is not None:
            pv_profiles.append(h)

    # Find peak day across all load profiles
    peak_day = _find_peak_day(load_profiles)

    # Average all load profiles for peak day → feeder multiplier
    feeder_mult = np.mean([p[peak_day] for p in load_profiles], axis=0)
    # Apply growth scaling
    feeder_mult *= (1 + BASE_FEEDER_ANNUAL_GROWTH) ** horizon_years

    # PV profile for peak day
    if pv_profiles:
        solar_shape = np.mean([p[peak_day] for p in pv_profiles], axis=0)
    else:
        # Fallback bell curve
        hours = np.arange(24)
        solar_shape = np.where((hours >= 6) & (hours <= 18), np.sin((hours - 6) / 12 * np.pi), 0)

    feeder_equiv_mw = (solar_mw / 100.0) * (1 + 0.02 * horizon_years)
    solar_mw_profile = solar_shape * feeder_equiv_mw

    # EV profile (synthetic - no real EV data in dataset)
    hours = np.arange(24)
    ev_shape = np.exp(-((hours - 19) ** 2) / 8) + 0.7 * np.exp(-((hours - 22) ** 2) / 5)
    ev_shape = ev_shape / ev_shape.max()
    base_ev_mw = 0.6
    ev_mw_profile = ev_shape * base_ev_mw * (1 + ev_growth_rate) ** horizon_years

    # DC profile (synthetic - flat baseload)
    dc_active = (horizon_years * 12) >= dc_timeline_months
    if dc_active:
        dc_shape = 0.97 + 0.03 * np.sin((hours - 2) / 24 * 2 * np.pi)
        dc_mw_profile = (dc_shape / dc_shape.mean()) * dc_mw
    else:
        dc_mw_profile = np.zeros(24)

    time_index = pd.date_range("2025-01-01 00:00:00", periods=24, freq="h")

    return pd.DataFrame({
        "time": time_index,
        "feeder_mult": feeder_mult,
        "ev_mw": ev_mw_profile,
        "solar_mw": solar_mw_profile,
        "dc_mw": dc_mw_profile,
    })


def is_real_data_available() -> bool:
    """Check if real profile data exists."""
    return LOAD_PROFILES_DIR.exists() and len(list(LOAD_PROFILES_DIR.glob("*.csv"))) > 0
