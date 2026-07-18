import re
from pathlib import Path
from ..simulation.portfolios import generate_portfolios, score_portfolio, summarize_results
from ..simulation.portfolios import apply_portfolio_to_profiles, line_capacity_multiplier, transformer_capacity_multiplier
from ..simulation.engine import run_24hr_simulation, prepare_simulation, run_24hr_fast
from ..simulation.engine_epri import run_epri_24hr_simulation, prepare_epri_simulation, run_epri_24hr_fast
from ..config import INTERVENTION_KEYS

INSTRUCTIONS_PATH = Path(__file__).parent / "instructions" / "nwa_agent.md"


def _parse_config(text: str) -> dict:
    """Extract CONFIG yaml block from instruction markdown."""
    config = {}
    match = re.search(r"```yaml\n(.*?)```", text, re.DOTALL)
    if match:
        for line in match.group(1).strip().split("\n"):
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                # Parse list values
                if val.startswith("[") and val.endswith("]"):
                    val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
                elif val.isdigit():
                    val = int(val)
                config[key] = val
    return config


class NWAAgent:
    """Generates and evaluates Non-Wires Alternative portfolios.
    Behavior is driven by the instruction file at instructions/nwa_agent.md.
    Edit the CONFIG section in that file to change which interventions are excluded."""

    def __init__(self):
        self.instructions = INSTRUCTIONS_PATH.read_text() if INSTRUCTIONS_PATH.exists() else ""
        self.config = _parse_config(self.instructions)
        # These come from the instruction file CONFIG block
        self.exclude = self.config.get("exclude_interventions", ["TransformerUpgrade"])
        self.max_measures = self.config.get("max_active_measures", 3)

    def run(self, profiles, base_summary: dict, max_portfolios: int = 30, required_interventions: list = None, min_active_measures: int = 1, use_epri: bool = False) -> list:
        # Generate portfolios excluding interventions specified in instructions
        all_portfolios = generate_portfolios(
            max_active_measures=self.max_measures,
            min_active_measures=min_active_measures,
            required_interventions=required_interventions
        )
        # Filter out excluded interventions (from instruction config)
        nwa_portfolios = [p for p in all_portfolios
                          if all(p.get(k, 0) == 0 for k in self.exclude)]
        nwa_portfolios = nwa_portfolios[:max_portfolios]

        scored = []
        base_stress = max(base_summary["grid_stress_score"], 1e-6)

        # Compile feeder once for all portfolios (avoids redundant recompilation)
        epri_ctx = prepare_epri_simulation() if use_epri else None
        ieee_ctx = prepare_simulation() if not use_epri else None

        for portfolio in nwa_portfolios:
            modified = apply_portfolio_to_profiles(profiles, portfolio)
            cap_line = line_capacity_multiplier(0)
            cap_xf = transformer_capacity_multiplier(0)
            if use_epri:
                results = run_epri_24hr_fast(epri_ctx, modified, portfolio, cap_mult_line=cap_line, cap_mult_xf=cap_xf)
            else:
                results = run_24hr_fast(ieee_ctx, modified, portfolio, cap_mult_line=cap_line, cap_mult_xf=cap_xf)
            alt_summary = summarize_results(results)
            improvement = max(0.0, (base_stress - alt_summary["grid_stress_score"]) / base_stress * 100.0)
            score_row = score_portfolio(portfolio, improvement)
            score_row["alt_summary"] = alt_summary
            scored.append(score_row)

        scored.sort(key=lambda x: x["final_score"], reverse=True)
        return scored
