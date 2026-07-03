from ..simulation.portfolios import generate_portfolios, score_portfolio, summarize_results
from ..simulation.engine import run_24hr_simulation
from ..simulation.portfolios import apply_portfolio_to_profiles, line_capacity_multiplier, transformer_capacity_multiplier
from ..config import INTERVENTION_KEYS


class NWAAgent:
    """Generates and evaluates Non-Wires Alternative portfolios (no TransformerUpgrade)."""

    def run(self, profiles, base_summary: dict, max_portfolios: int = 30) -> list:
        # Generate NWA-only portfolios (TransformerUpgrade forced to 0)
        all_portfolios = generate_portfolios(max_active_measures=3)
        nwa_portfolios = [p for p in all_portfolios if p["TransformerUpgrade"] == 0]
        nwa_portfolios = nwa_portfolios[:max_portfolios]

        scored = []
        base_stress = max(base_summary["grid_stress_score"], 1e-6)

        for portfolio in nwa_portfolios:
            modified = apply_portfolio_to_profiles(profiles, portfolio)
            cap_line = line_capacity_multiplier(0)
            cap_xf = transformer_capacity_multiplier(0)
            results = run_24hr_simulation(modified, portfolio, cap_mult_line=cap_line, cap_mult_xf=cap_xf)
            alt_summary = summarize_results(results)
            improvement = max(0.0, (base_stress - alt_summary["grid_stress_score"]) / base_stress * 100.0)
            score_row = score_portfolio(portfolio, improvement)
            score_row["alt_summary"] = alt_summary
            scored.append(score_row)

        scored.sort(key=lambda x: x["final_score"], reverse=True)
        return scored
