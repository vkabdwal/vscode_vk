from pathlib import Path
from ..llm_client import invoke_llm

INSTRUCTIONS_PATH = Path(__file__).parent / "instructions" / "recommendation_agent.md"


class RecommendationAgent:
    """Merges NWA and capex results, ranks, and generates decision narrative.
    Uses LLM (AWS Bedrock) for memo generation when available; falls back to template."""

    def __init__(self):
        self.instructions = INSTRUCTIONS_PATH.read_text() if INSTRUCTIONS_PATH.exists() else ""

    def run(self, nwa_scored: list, capex_scored: list, base_summary: dict, assumptions: dict) -> dict:
        # Merge and rank all portfolios
        all_scored = nwa_scored + capex_scored
        all_scored.sort(key=lambda x: x["final_score"], reverse=True)

        # Remove internal summary from output
        ranking = []
        for s in all_scored:
            row = {k: v for k, v in s.items() if k != "alt_summary"}
            ranking.append(row)

        top = ranking[0] if ranking else None
        second = ranking[1] if len(ranking) > 1 else None

        # Check if NWA-only resolved all violations
        nwa_resolved = False
        if nwa_scored:
            best_nwa = nwa_scored[0]
            if "alt_summary" in best_nwa and best_nwa["alt_summary"]["grid_stress_score"] == 0:
                nwa_resolved = True

        # Use instant template for study response; LLM memo is generated on-demand via /memo endpoint
        memo = self._generate_memo_template(top, second, base_summary, assumptions, nwa_resolved)

        return {
            "ranking": ranking,
            "top_recommendation": top,
            "second_best": second,
            "nwa_resolved_all": nwa_resolved,
            "memo": memo,
        }

    def _generate_memo_llm(self, top, second, base_summary, assumptions, nwa_resolved, top5):
        """Generate decision memo using LLM (AWS Bedrock). Returns empty string if unavailable."""
        system_prompt = self.instructions + """

You are a senior distribution planning consultant at PwC.
Generate a professional planning decision memo in Markdown format.
Include: Executive Summary, Planning Scenario (table), Baseline Assessment (table), 
Recommended Solution with score breakdown, and Alternative Options (comparison table).
Do NOT include an 'Implementation Next Steps' section.
Use tables where appropriate. Be specific with numbers. Target 500-700 words.
Do NOT include a top-level title (the UI already has one).
Start directly with ## Executive Summary.
"""
        context = f"""
SCENARIO:
- Planning horizon: {assumptions.get('horizon_years', 1)} years
- Peak EV demand: {assumptions.get('peak_ev_mw', 0):.2f} MW
- Peak solar generation: {assumptions.get('peak_solar_mw', 0):.2f} MW
- Data center: {'Active' if assumptions.get('dc_active') else 'Not online'} ({assumptions.get('dc_mw', 0)} MW)

BASELINE GRID ASSESSMENT:
- Grid stress score: {base_summary.get('grid_stress_score', 0):.0f}
- Line overloads (24h total): {base_summary.get('total_line_overloads', 0)}
- Transformer overloads (24h total): {base_summary.get('total_transformer_overloads', 0)}
- Undervoltage events: {base_summary.get('total_undervoltage_buses', 0)}

NWA RESOLVES ALL: {nwa_resolved}

TOP RECOMMENDATION: {top.get('portfolio_name', 'N/A') if top else 'N/A'}
- Score: {top.get('final_score', 0) if top else 0:.2f}/10
- Grid Relief: {top.get('technical_improvement_pct', 0) if top else 0:.1f}%
- Cost Score: {top.get('cost_score', 0) if top else 0:.1f}/10
- Speed to Value: {top.get('speed_to_value_score', 0) if top else 0:.1f}/10
- ESG: {top.get('esg_score', 0) if top else 0:.1f}/10

RUNNER-UP: {second.get('portfolio_name', 'N/A') if second else 'N/A'} (Score: {second.get('final_score', 0) if second else 0:.2f})

TOP 5 RANKED:
""" + "\n".join([f"  {i+1}. {r.get('portfolio_name','?')} (score={r.get('final_score',0):.2f}, improvement={r.get('technical_improvement_pct',0):.1f}%)" for i, r in enumerate(top5)])

        return invoke_llm(system_prompt, context, max_tokens=1200)

    def _generate_memo_template(self, top, second, base_summary, assumptions, nwa_resolved):
        """Fallback template-based memo when LLM is unavailable."""
        lines = []
        lines.append("## Executive Summary")
        lines.append("")
        if nwa_resolved:
            lines.append("Non-wires alternatives **fully resolve all identified violations**. No traditional capital expenditure is required within the planning horizon.")
        elif top and top.get("TransformerUpgrade", 0) == 0:
            lines.append("The recommended solution uses **non-wires alternatives only**, achieving significant grid stress reduction without capital infrastructure investment.")
        else:
            lines.append("A **hybrid approach** combining non-wires alternatives with targeted infrastructure upgrades is recommended to address identified violations.")
        lines.append("")
        lines.append("## Planning Scenario")
        lines.append("")
        lines.append(f"| Parameter | Value |")
        lines.append(f"|-----------|-------|")
        lines.append(f"| Planning Horizon | {assumptions['horizon_years']} years |")
        lines.append(f"| Peak EV Demand | {assumptions['peak_ev_mw']:.2f} MW |")
        lines.append(f"| Peak Solar Generation | {assumptions['peak_solar_mw']:.2f} MW |")
        lines.append(f"| Data Center | {'Active' if assumptions['dc_active'] else 'Not yet online'} ({assumptions['dc_mw']} MW) |")
        lines.append("")
        lines.append("## Baseline Grid Assessment")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Grid Stress Score | {base_summary['grid_stress_score']:.0f} |")
        lines.append(f"| Line Overloads (24h) | {base_summary['total_line_overloads']} |")
        lines.append(f"| Transformer Overloads (24h) | {base_summary['total_transformer_overloads']} |")
        lines.append(f"| Undervoltage Events | {base_summary['total_undervoltage_buses']} |")
        lines.append(f"| Overvoltage Events | {base_summary['total_overvoltage_buses']} |")
        lines.append("")

        if top:
            lines.append("## Recommended Solution")
            lines.append("")
            lines.append(f"**{top['portfolio_name']}**")
            lines.append("")
            lines.append(f"| Scoring Dimension | Score |")
            lines.append(f"|-------------------|-------|")
            lines.append(f"| Overall Score | **{top['final_score']:.2f}** / 10 |")
            lines.append(f"| Grid Relief | {top.get('grid_relief_score', top.get('technical_score', 0)):.1f} / 10 |")
            lines.append(f"| Cost Efficiency | {top['cost_score']:.1f} / 10 |")
            lines.append(f"| Speed to Value | {top.get('speed_to_value_score', 0):.1f} / 10 |")
            lines.append(f"| ESG Alignment | {top.get('esg_score', 0):.1f} / 10 |")
            lines.append(f"| Technical Improvement | {top['technical_improvement_pct']:.1f}% stress reduction |")
            lines.append("")

        if second:
            lines.append("## Alternative Option")
            lines.append("")
            lines.append(f"**{second['portfolio_name']}** (Score: {second['final_score']:.2f})")
            lines.append("")
            lines.append(f"Technical improvement: {second['technical_improvement_pct']:.1f}%")
            lines.append("")

        lines.append("## Methodology")
        lines.append("")
        lines.append("Portfolios are evaluated using a four-dimension weighted scoring framework:")
        lines.append("")
        lines.append("- **Grid Relief (40%)** → Percentage reduction in grid stress score (violations, overloads)")
        lines.append("- **Cost Efficiency (25%)** → Relative cost advantage vs. full capex alternatives")
        lines.append("- **Speed to Value (20%)** → Combined feasibility and deployment timeline")
        lines.append("- **ESG Alignment (15%)** → Sustainability benefit (lower-carbon, less material intensity)")
        lines.append("")
        lines.append("*Scoring framework aligned with CPUC IRP (D.22-02-004) and NY REV BCA methodology.*")

        return "\n".join(lines)
