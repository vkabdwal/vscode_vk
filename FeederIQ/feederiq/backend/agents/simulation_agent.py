from ..simulation.engine import run_24hr_simulation
from ..simulation.engine_epri import run_epri_24hr_simulation
from ..simulation.portfolios import apply_portfolio_to_profiles, line_capacity_multiplier, transformer_capacity_multiplier
from ..config import INTERVENTION_KEYS


class SimulationAgent:
    """Runs 24-hour power flow simulation for a given portfolio."""

    def __init__(self, use_epri=False):
        self.use_epri = use_epri

    def _run_sim(self, profiles, portfolio, cap_mult_line=1.0, cap_mult_xf=1.0):
        if self.use_epri:
            return run_epri_24hr_simulation(profiles, portfolio, cap_mult_line=cap_mult_line, cap_mult_xf=cap_mult_xf)
        return run_24hr_simulation(profiles, portfolio, cap_mult_line=cap_mult_line, cap_mult_xf=cap_mult_xf)

    def run_baseline(self, profiles) -> list:
        base_portfolio = {k: 0 for k in INTERVENTION_KEYS}
        return self._run_sim(profiles, base_portfolio)

    def run_portfolio(self, profiles, portfolio: dict) -> list:
        modified = apply_portfolio_to_profiles(profiles, portfolio)
        cap_line = line_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))
        cap_xf = transformer_capacity_multiplier(portfolio.get("TransformerUpgrade", 0))
        return self._run_sim(modified, portfolio, cap_mult_line=cap_line, cap_mult_xf=cap_xf)
