from pathlib import Path
from ..simulation.portfolios import summarize_results
from ..llm_client import invoke_llm

INSTRUCTIONS_PATH = Path(__file__).parent / "instructions" / "constraint_agent.md"


class ConstraintAgent:
    """Analyzes simulation results and detects violations.
    Uses LLM to generate human-readable interpretation of grid issues."""

    def __init__(self):
        self.instructions = INSTRUCTIONS_PATH.read_text() if INSTRUCTIONS_PATH.exists() else ""

    def analyze(self, results: list) -> dict:
        summary = summarize_results(results)
        violations_detected = (
            summary["total_undervoltage_buses"] > 0 or
            summary["total_overvoltage_buses"] > 0 or
            summary["total_line_overloads"] > 0 or
            summary["total_transformer_overloads"] > 0 or
            summary["convergence_failures"] > 0
        )
        severity = self._classify_severity(summary)

        # Use LLM to interpret violations
        interpretation = self._interpret_violations(summary, severity)

        return {
            "summary": summary,
            "violations_detected": violations_detected,
            "severity": severity,
            "interpretation": interpretation,
        }

    def _interpret_violations(self, summary: dict, severity: str) -> str:
        """Use LLM to generate plain-English explanation of grid violations."""
        system_prompt = self.instructions + """

You are a distribution grid engineer. Explain the violations in 2-3 sentences
that a utility planner can understand. Be specific about WHAT is overloaded and
WHEN (based on the counts). No jargon. No markdown formatting."""

        context = f"""Grid stress score: {summary['grid_stress_score']:.0f} (severity: {severity})
Line overloads: {summary['total_line_overloads']} instances across 24 hours
Transformer overloads: {summary['total_transformer_overloads']} instances across 24 hours
Undervoltage buses: {summary['total_undervoltage_buses']}
Overvoltage buses: {summary['total_overvoltage_buses']}
Convergence failures: {summary['convergence_failures']}
Worst minimum voltage: {summary['worst_vmin']:.4f} pu
Worst maximum voltage: {summary['worst_vmax']:.4f} pu"""

        result = invoke_llm(system_prompt, context, max_tokens=200)
        return result if result else f"Grid stress level: {severity}. {summary['total_line_overloads']} line overloads and {summary['total_transformer_overloads']} transformer overloads detected."

    def _classify_severity(self, summary: dict) -> str:
        stress = summary["grid_stress_score"]
        if stress == 0:
            return "none"
        elif stress < 100:
            return "low"
        elif stress < 1000:
            return "moderate"
        elif stress < 5000:
            return "high"
        else:
            return "critical"
