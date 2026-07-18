import math
import numpy as np
import pandas as pd
from ..config import (
    PLANNING_HORIZONS, EV_GROWTH, SOLAR_ADOPTION,
    DATA_CENTER_MW, DATA_CENTER_TIMELINE_MONTHS,
    BASE_FEEDER_ANNUAL_GROWTH,
)


def growth_multiplier(rate, years):
    return (1 + rate) ** years


def synthetic_base_feeder_profile(horizon_years):
    hours = np.arange(24)
    shape = 0.80 + 0.10 * np.sin((hours - 7) / 24 * 2 * np.pi) + 0.18 * np.sin((hours - 18) / 24 * 2 * np.pi)
    shape = np.clip(shape, 0.60, None)
    shape = shape / np.mean(shape)
    return shape * growth_multiplier(BASE_FEEDER_ANNUAL_GROWTH, horizon_years)


def synthetic_ev_profile(horizon_years, ev_growth_rate):
    hours = np.arange(24)
    profile = np.array([
        math.exp(-((h - 19) ** 2) / 8) + 0.7 * math.exp(-((h - 22) ** 2) / 5) + 0.10 * math.exp(-((h - 7) ** 2) / 10)
        for h in hours
    ])
    profile = profile / profile.max()
    return profile * 0.6 * growth_multiplier(ev_growth_rate, horizon_years)


def synthetic_solar_profile(horizon_years, solar_adoption_mw):
    hours = np.arange(24)
    profile = np.array([math.sin((h - 6) / 12 * math.pi) if 6 <= h <= 18 else 0.0 for h in hours])
    profile = profile / max(profile.max(), 1e-6)
    feeder_mw = (solar_adoption_mw / 100.0) * (1 + 0.02 * horizon_years)
    return profile * feeder_mw


def synthetic_data_center_profile(horizon_years, dc_mw, dc_timeline_months):
    if (horizon_years * 12) < dc_timeline_months:
        return np.zeros(24)
    hours = np.arange(24)
    shape = 0.97 + 0.03 * np.sin((hours - 2) / 24 * 2 * np.pi)
    return (shape / np.mean(shape)) * dc_mw


def generate_profiles(horizon_label, ev_level, solar_level, dc_level, dc_timeline_label):
    horizon_years = PLANNING_HORIZONS[horizon_label]
    return pd.DataFrame({
        "time": pd.date_range("2025-01-01", periods=24, freq="h"),
        "feeder_mult": synthetic_base_feeder_profile(horizon_years),
        "ev_mw": synthetic_ev_profile(horizon_years, EV_GROWTH[ev_level]),
        "solar_mw": synthetic_solar_profile(horizon_years, SOLAR_ADOPTION[solar_level]),
        "dc_mw": synthetic_data_center_profile(horizon_years, DATA_CENTER_MW[dc_level], DATA_CENTER_TIMELINE_MONTHS[dc_timeline_label]),
    })
