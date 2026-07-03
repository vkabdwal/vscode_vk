from ..config import PLANNING_HORIZONS, EV_GROWTH, SOLAR_ADOPTION, DATA_CENTER_MW, DATA_CENTER_TIMELINE_MONTHS
from ..simulation.profiles import generate_profiles


class ScenarioAgent:
    """Converts user scenario selections into numeric assumptions and 24-hour profiles."""

    def run(self, scenario: dict) -> dict:
        horizon_years = PLANNING_HORIZONS[scenario["horizon_label"]]
        profiles = generate_profiles(
            scenario["horizon_label"],
            scenario["ev_level"],
            scenario["solar_level"],
            scenario["dc_level"],
            scenario["dc_timeline_label"],
        )
        assumptions = {
            "horizon_years": horizon_years,
            "ev_growth_rate": EV_GROWTH[scenario["ev_level"]],
            "solar_mw": SOLAR_ADOPTION[scenario["solar_level"]],
            "dc_mw": DATA_CENTER_MW[scenario["dc_level"]],
            "dc_timeline_months": DATA_CENTER_TIMELINE_MONTHS[scenario["dc_timeline_label"]],
            "dc_active": (horizon_years * 12) >= DATA_CENTER_TIMELINE_MONTHS[scenario["dc_timeline_label"]],
            "peak_ev_mw": float(profiles["ev_mw"].max()),
            "peak_solar_mw": float(profiles["solar_mw"].max()),
            "peak_dc_mw": float(profiles["dc_mw"].max()),
        }
        return {"profiles": profiles, "assumptions": assumptions}
