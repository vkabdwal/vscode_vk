from ..simulation.portfolios import summarize_results


class ConstraintAgent:
    """Analyzes simulation results and detects violations."""

    def analyze(self, results: list) -> dict:
        summary = summarize_results(results)
        violations_detected = (
            summary["total_undervoltage_buses"] > 0 or
            summary["total_overvoltage_buses"] > 0 or
            summary["total_line_overloads"] > 0 or
            summary["total_transformer_overloads"] > 0 or
            summary["convergence_failures"] > 0
        )
        return {
            "summary": summary,
            "violations_detected": violations_detected,
            "severity": self._classify_severity(summary),
        }

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
