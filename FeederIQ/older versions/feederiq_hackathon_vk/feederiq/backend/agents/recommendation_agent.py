class RecommendationAgent:
    """Merges NWA and capex results, ranks, and generates decision narrative."""

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

        memo = self._generate_memo(top, second, base_summary, assumptions, nwa_resolved)

        return {
            "ranking": ranking,
            "top_recommendation": top,
            "second_best": second,
            "nwa_resolved_all": nwa_resolved,
            "memo": memo,
        }

    def _generate_memo(self, top, second, base_summary, assumptions, nwa_resolved):
        lines = []
        lines.append("# FeederIQ Planning Decision Memo")
        lines.append("")
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
