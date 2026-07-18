from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "ai_synthetic_data"
MASTER_DSS_PATH = DATA_DIR / "master_lite.dss"
OUTPUTS_DIR = REPO_ROOT / "outputs"

# Feeder voltages
PRIMARY_KV_LL = 4.16
SINGLE_PHASE_KV_LN = 2.402

# Violation thresholds
VOLTAGE_MIN_PU = 0.95
VOLTAGE_MAX_PU = 1.05

# Bus assignments
EV_BUSES = ["60", "83", "90", "92", "114"]
SOLAR_BUSES = ["66", "80", "92", "104", "110"]
DATA_CENTER_BUS = "67"

BUS_PHASE_MAP_EV = {"60": ".1", "83": ".1", "90": ".2", "92": ".3", "114": ".1"}
BUS_PHASE_MAP_SOLAR = {"66": ".1", "80": ".1", "92": ".3", "104": ".3", "110": ".1"}

# Scenario options
PLANNING_HORIZONS = {"3m": 0.25, "6m": 0.5, "12m": 1.0, "18m": 1.5, "3yr": 3.0, "5yr": 5.0}
EV_GROWTH = {"Low": 0.15, "Base": 0.20, "High": 0.25}
SOLAR_ADOPTION = {"Low": 100, "Base": 200, "High": 300}
DATA_CENTER_MW = {"Low": 1.0, "Moderate": 1.75, "High": 3.0}
DATA_CENTER_TIMELINE_MONTHS = {"6m": 6, "12m": 12, "18m": 18}
BASE_FEEDER_ANNUAL_GROWTH = 0.03

# Intervention definitions
INTERVENTION_KEYS = [
    "TransformerUpgrade", "Battery", "ManagedCharging",
    "PhasedInterconnection", "DemandTariff"
]
LEVELS = [0, 33, 66, 100]

# Human-friendly level labels
LEVEL_LABELS = {0: "None", 33: "Low", 66: "Medium", 100: "High"}

# Human-friendly intervention labels
INTERVENTION_LABELS = {
    "TransformerUpgrade": "Capacity Upgrade",
    "Battery": "Battery Storage",
    "ManagedCharging": "Managed EV Charging",
    "PhasedInterconnection": "Staged Load Connection",
    "DemandTariff": "Dynamic Tariffs",
}

COST_BY_LEVEL = {
    "TransformerUpgrade": {0: 0, 33: 5, 66: 8, 100: 10},
    "Battery": {0: 0, 33: 3, 66: 5, 100: 8},
    "ManagedCharging": {0: 0, 33: 1, 66: 2, 100: 3},
    "PhasedInterconnection": {0: 0, 33: 1, 66: 2, 100: 3},
    "DemandTariff": {0: 0, 33: 1, 66: 2, 100: 3},
}
FEASIBILITY_BY_LEVEL = {
    "TransformerUpgrade": {0: 10, 33: 8, 66: 6, 100: 4},
    "Battery": {0: 10, 33: 8, 66: 7, 100: 6},
    "ManagedCharging": {0: 10, 33: 9, 66: 8, 100: 7},
    "PhasedInterconnection": {0: 10, 33: 8, 66: 7, 100: 6},
    "DemandTariff": {0: 10, 33: 8, 66: 7, 100: 6},
}
DEPLOYMENT_BY_LEVEL = {
    "TransformerUpgrade": {0: 10, 33: 7, 66: 5, 100: 3},
    "Battery": {0: 10, 33: 8, 66: 6, 100: 5},
    "ManagedCharging": {0: 10, 33: 9, 66: 8, 100: 7},
    "PhasedInterconnection": {0: 10, 33: 8, 66: 7, 100: 6},
    "DemandTariff": {0: 10, 33: 8, 66: 7, 100: 6},
}
# ESG Alignment: software/behavioral solutions score highest, physical infra lowest
ESG_BY_LEVEL = {
    "TransformerUpgrade": {0: 10, 33: 7, 66: 5, 100: 3},
    "Battery": {0: 10, 33: 8, 66: 7, 100: 6},
    "ManagedCharging": {0: 10, 33: 9, 66: 9, 100: 9},
    "PhasedInterconnection": {0: 10, 33: 9, 66: 8, 100: 7},
    "DemandTariff": {0: 10, 33: 9, 66: 9, 100: 9},
}

# Scoring weights (4 dimensions)
# Grid Relief = technical violation reduction
# Cost Efficiency = lower cost is better
# Speed to Value = merged feasibility + deployment speed
# ESG Alignment = sustainability / carbon benefit
SCORING_WEIGHTS = {
    "technical": 0.40,
    "cost": 0.25,
    "speed_to_value": 0.20,
    "esg": 0.15,
}

