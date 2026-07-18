# FeederIQ - Assumptions Rationale & Market Benchmarks

## Purpose

This document provides defensible justification for the assumptions, scoring heuristics, and intervention levels used in FeederIQ. Each assumption is grounded in publicly available industry data from DOE, EPRI, NREL, EIA, FERC filings, and utility rate cases.

---

## 1. Deployment Levels (0%, 33%, 66%, 100%)

### Rationale

The four-level framework maps to EPRI's technology deployment maturity stages used across US utilities:

| Level | Label | EPRI Equivalent | Industry Context |
|-------|-------|----------------|------------------|
| 0% | Not deployed | N/A | Status quo - no intervention |
| 33% | Pilot / early adoption | Stage 1: Demonstration | Aligns with DOE-funded NWA pilot programs (typically 25–35% penetration). E.g., ConEdison BQDM project started at ~30% of target capacity. |
| 66% | Moderate-scale rollout | Stage 2: Early deployment | Matches utility programs at midpoint maturity. E.g., California's SGIP achieved ~60% of planned DER capacity by Year 3. |
| 100% | Full deployment | Stage 3: Full commercial | Represents full planned capacity. Rare within planning horizons < 5 years for physical infrastructure. |

**Source**: EPRI "Grid Modernization: Metrics Analysis" (2023); DOE Grid Deployment Office NWA Pilot Reports (2022–2024).

---

## 2. Intervention Cost Scores

### Methodology

Cost scores are **relative planning heuristics** (0-10 scale) derived from NREL ATB 2024, Lazard LCOE+ v17.0, and FERC Form 1 filings. Higher raw score = higher cost burden.

| Intervention | Level | Cost Score | Benchmark Source |
|---|---|---|---|
| **Capacity Upgrade** | Low (33%) | 5 | Single transformer replacement: $150–$500K (PG&E 2023 GRC). Includes procurement, installation, outage management. Lead time: 12–36 months due to global supply constraints. |
| | Medium (66%) | 8 | Multiple transformer replacements + line reconductoring: $500K–$2M. Requires engineering studies, environmental review, outage coordination. |
| | High (100%) | 10 | Full substation capacity upgrade: $2–$5M (FERC Form 1 median for 4kV feeders). Major capital project requiring PUC approval, 18–36 month procurement cycles. |
| **Battery Storage** | Low (33%) | 3 | NREL ATB 2024: 4-hr BESS at $280/kWh installed (1 MW pilot = ~$1.1M) |
| | Medium (66%) | 5 | Moderate fleet: 2–3 MW at ~$250/kWh (volume discount) |
| | High (100%) | 8 | Full deployment: 5+ MW, containerized BESS |
| **Managed EV Charging** | Low (33%) | 1 | Software + comms: $50–$150/charger (EPRI EV Pilot, 2023) |
| | Medium (66%) | 2 | Expanded program + incentives: $100–$300/charger |
| | High (100%) | 3 | Full fleet management: ~$500K total program cost for 5-bus deployment |
| **Staged Load Connection** | Low (33%) | 1 | Administrative: interconnection study + metering ($25–$75K) |
| | Medium (66%) | 2 | Partial connection + grid reinforcement: $100–$200K |
| | High (100%) | 3 | Full staged connection with DER controls: $200–$400K |
| **Dynamic Tariffs** | Low (33%) | 1 | Tariff design + AMI analytics: $50–$100K program cost |
| | Medium (66%) | 2 | Moderate TOU/CPP program: $100–$250K (customer outreach + billing) |
| | High (100%) | 3 | Full dynamic pricing: $200–$400K (requires AMI + DERMS integration) |

**Key insight**: Capacity upgrades (transformer replacement) are 5–50× more expensive than NWA solutions for equivalent load management, AND have 3–10× longer deployment timelines due to supply chain constraints (DOE Transmission Need Study 2023 reported 2–3 year lead times for power transformers).

**Sources**: NREL Annual Technology Baseline 2024; Lazard LCOE+ v17.0 (2024); PG&E General Rate Case 2023; EPRI "Costs and Benefits of EV Managed Charging" (2023).

---

## 3. Feasibility Scores

### Methodology

Feasibility reflects regulatory, operational, and implementation complexity. Scale: 10 = trivial, 1 = extremely complex. Based on US utility planning timelines from FERC/state PUC proceedings.

| Intervention | Level | Score | Justification |
|---|---|---|---|
| **Capacity Upgrade** | 33% | 8 | Standard utility planning process; lead times 6–12 months |
| | 66% | 6 | Multiple assets; supply chain risk (transformer shortage 2022–2025) |
| | 100% | 4 | Major capital project; board/PUC approval, 18–36 month lead times |
| **Battery Storage** | 33% | 8 | Proven technology; interconnection study required |
| | 66% | 7 | Siting + permitting for multiple installations |
| | 100% | 6 | Large-scale; environmental review, fire code compliance |
| **Managed EV Charging** | 33% | 9 | Software deployment; opt-in program, minimal regulatory hurdle |
| | 66% | 8 | Requires customer enrollment at scale |
| | 100% | 7 | Full program requires AMI + EVSE communication standards |
| **Staged Load Connection** | 33% | 8 | Initial phase within utility's delegated authority |
| | 66% | 7 | Requires updated interconnection agreement |
| | 100% | 6 | Full staged plan needs PUC review in many jurisdictions |
| **Dynamic Tariffs** | 33% | 8 | Pilot tariff within existing rate authority |
| | 66% | 7 | Expanded TOU/CPP; customer communication program needed |
| | 100% | 6 | Full dynamic pricing; tariff filing + PUC approval cycle (12–18 months) |

**Context**: The DOE Transmission Need Study (2023) reported transformer lead times of 1–3 years post-COVID, making traditional upgrades less feasible for near-term planning horizons.

---

## 4. Deployment Speed Scores

### Methodology

Measures time-to-benefit. Scale: 10 = immediate, 1 = multiple years. Based on DOE NWA case studies and utility IRP timelines.

| Intervention | Level | Score | Time to Deploy |
|---|---|---|---|
| **Capacity Upgrade** | 33% | 7 | 6–12 months (single unit, if available) |
| | 66% | 5 | 12–18 months (multi-unit, procurement lag) |
| | 100% | 3 | 18–36 months (full substation work, outage scheduling) |
| **Battery Storage** | 33% | 8 | 3–6 months (containerized BESS, pre-engineered) |
| | 66% | 6 | 6–12 months (siting + civil works for multiple units) |
| | 100% | 5 | 12–18 months (large fleet, phased commissioning) |
| **Managed EV Charging** | 33% | 9 | 1–3 months (software rollout to enrolled customers) |
| | 66% | 8 | 3–6 months (expanded enrollment + EVSE firmware updates) |
| | 100% | 7 | 6–9 months (full fleet, all eligible customers) |
| **Staged Load Connection** | 33% | 8 | 2–4 months (administrative phase, metering) |
| | 66% | 7 | 4–8 months (partial energization + monitoring) |
| | 100% | 6 | 8–14 months (full staged ramp-up with grid studies) |
| **Dynamic Tariffs** | 33% | 8 | 2–4 months (pilot, existing billing system) |
| | 66% | 7 | 4–8 months (expanded program, customer onboarding) |
| | 100% | 6 | 8–14 months (full dynamic pricing, AMI integration) |

**Source**: DOE "Non-Wires Alternatives: Case Studies from Leading US Utilities" (2022); EPRI Distribution Resource Plan reports.

---

## 5. Scoring Weights

| Criterion | Weight | Justification |
|---|---|---|
| Grid Relief (technical) | 40% | Must resolve reliability issues — NERC TPL standards require N-1 compliance |
| Cost Efficiency | 25% | PUC prudency review requires cost-benefit demonstration |
| Speed to Value | 20% | Merged feasibility + deployment. Deferral value increases with faster deployment |
| ESG Alignment | 15% | Sustainability mandate — PwC ESG practice, SEC climate disclosure rule, utility IRPs |

**Source**: Aligned with California CPUC IRP scoring framework (D.22-02-004), New York REV benefit-cost analysis methodology (BCA Handbook, 2024), and SEC Final Rule on Climate-Related Disclosures (2024).

---

## 5a. ESG Alignment Scoring

### Why ESG Is a Scoring Dimension

US utilities face increasing ESG reporting obligations:
- **SEC Climate Rule (2024)**: Requires disclosure of climate-related risks and GHG emissions for public companies.
- **State mandates**: CA SB 253/261, NY Climate Leadership Act — require Scope 1-3 emissions tracking.
- **PUC proceedings**: CPUC, NYPSC, and MPUC now include carbon/environmental metrics in IRP and rate case evaluation.
- **PwC ESG practice**: Largest Big4 ESG advisory practice; clients expect sustainability-aligned recommendations.

### ESG Score Methodology

Scores are based on **lifecycle carbon intensity** and **material intensity** of each intervention, derived from:
- IEA "The Role of Critical Minerals in Clean Energy Transitions" (2023)
- EPRI "Lifecycle Emissions of Grid Technologies" (2022)
- NREL "Life Cycle Greenhouse Gas Emissions from Electricity Generation" (2021)
- DOE "Pathways to Commercial Liftoff: Virtual Power Plants" (2023)

| Intervention | Level | ESG Score | Rationale |
|---|---|---|---|
| **Capacity Upgrade** | 33% | 7 | Single unit: ~15-25 tonnes CO2e embodied (steel, copper, mineral oil). Source: EPRI LCA 2022 |
| | 66% | 5 | Multiple units: 30-50 tonnes CO2e + construction emissions + SF6 risk in older switchgear |
| | 100% | 3 | Full substation: 50-100+ tonnes CO2e, significant material extraction, 20+ year asset lock-in |
| **Battery Storage** | 33% | 8 | Li-ion mining impact offset by enabling renewable integration and reducing curtailment |
| | 66% | 7 | Greater mining/manufacturing footprint; still net-positive via fossil peaker displacement |
| | 100% | 6 | Large-scale BESS: ~40-60 tonnes CO2e per MWh capacity (NREL 2021), but avoids gas peakers |
| **Managed EV Charging** | 33% | 9 | Pure software/controls: near-zero additional carbon, reduces peak fossil generation |
| | 66% | 9 | Same: behavioral/software intervention, shifts load from peak fossil hours to off-peak/renewable |
| | 100% | 9 | Maximum demand shifting: estimated 0.3-0.5 tonnes CO2 avoided per EV annually (DOE VPP 2023) |
| **Staged Load Connection** | 33% | 9 | Administrative controls; reduces peak demand without new physical assets |
| | 66% | 8 | Some monitoring equipment; still primarily operational/contractual |
| | 100% | 7 | Staged connection requires some grid-side reinforcement, but far less than full upgrade |
| **Dynamic Tariffs** | 33% | 9 | Price signals via existing AMI: zero additional carbon, behavioral demand reduction |
| | 66% | 9 | Expanded program: leverages existing infrastructure, reduces peak fossil dispatch |
| | 100% | 9 | Full dynamic pricing: DOE estimates 10-15% peak reduction → proportional carbon savings |

### Key Insight

**Software/behavioral interventions** (Managed Charging, Dynamic Tariffs) achieve ESG scores of 9/10 at all deployment levels because they:
1. Require no new physical materials or manufacturing
2. Actively reduce peak demand → displaces marginal fossil generation (typically gas CT)
3. Leverage existing infrastructure (AMI, smart chargers, billing systems)

**Physical infrastructure** (Capacity Upgrade) scores lowest because:
1. High embodied carbon: steel (1.8 tCO2/tonne), copper (3.5 tCO2/tonne), mineral oil
2. Manufacturing and transport emissions
3. 20-40 year asset lock-in with no flexibility to adapt to changing load patterns
4. Land use and construction site impacts

**Battery** scores in-between because while mining/manufacturing has environmental impact, batteries provide net-positive sustainability outcomes by:
1. Enabling higher renewable penetration (reduced curtailment)
2. Displacing fossil peaker plants during peak hours
3. Providing frequency regulation (reduces system-wide emissions)

---

## 6. Scenario Growth Rates

### EV Growth

| Level | Annual Rate | Source |
|---|---|---|
| Low | 15% | EIA AEO 2024 "Low Oil Price" case |
| Base | 20% | EIA AEO 2024 "Reference" case; BloombergNEF EVO 2024 |
| High | 25% | EIA AEO 2024 "High ZEV" case; reflects IRA/state incentive acceleration |

### Solar Adoption

| Level | Feeder-Equivalent MW | Source |
|---|---|---|
| Low | 1 MW | Scaled from SEIA Q1 2024 regional data. For a 4.16 kV feeder serving ~5,000 customers, 1 MW DER solar is consistent with bottom-quartile penetration. |
| Base | 2 MW | SEIA Q1 2024 median US utility territory, scaled to single-feeder equivalent. Consistent with IEEE 1547-2018 hosting capacity studies. |
| High | 3 MW | Top-quartile DER penetration (CA, TX, FL). Approaches hosting capacity limits for 4 kV class feeders per EPRI DER integration studies. |

### Data Center Demand

| Level | MW | Source |
|---|---|---|
| Low | 1.0 MW | Small edge facility / enterprise colocation. Typical of 10-20 rack deployments. Source: Uptime Institute 2024 Global Data Center Survey. |
| Moderate | 1.75 MW | Mid-size campus, typical new interconnection request at distribution level. Source: DOE Grid Deployment Office 2023 — median distribution-connected DC request. |
| High | 3.0 MW | Large campus phase or AI/ML training cluster. Source: DOE "Transmission Needs Study" 2023 reports 35+ GW pipeline; distribution-level requests typically 1-5 MW per FERC interconnection queue data. |

**Note on IEEE 123-bus context**: The IEEE 123-bus feeder is rated at ~4.16 kV with peak load of approximately 3.5 MW. Data center requests of 1-3 MW represent 28-85% of total feeder capacity — a realistic stress scenario for distribution planning.

**Sources**: EIA Annual Energy Outlook 2024; SEIA/Wood Mackenzie Solar Market Insight Q1 2024; DOE Grid Deployment Office "Transmission Needs Study" (2023); BloombergNEF Electric Vehicle Outlook 2024.

---

## 7. Base Feeder Growth

- **Annual growth rate**: 3%
- **Source**: FERC Form 1 data shows US distribution load growth averaging 2.5–3.5% annually (2020–2024), driven by electrification tailwinds.

---

## 8. Voltage Thresholds

| Threshold | Value | Source |
|---|---|---|
| Undervoltage | < 0.95 pu | ANSI C84.1 Range A (service voltage) |
| Overvoltage | > 1.05 pu | ANSI C84.1 Range A (service voltage) |
| Overload | > 100% rated | IEEE C57.91 (transformer loading guide) / utility N-1 planning criteria |

---

## 9. Grid Stress Score Formula

```
Stress = 20 × convergence_failures
       +  5 × total_line_overloads
       +  6 × total_transformer_overloads
       +  2 × undervoltage_buses
       +  2 × overvoltage_buses
```

### Weight Rationale

| Component | Weight | Why |
|---|---|---|
| Convergence failures | 20 | Indicates the network may be infeasible — most severe |
| Transformer overloads | 6 | Asset damage risk, costly to replace (18–36 month lead times) |
| Line overloads | 5 | Thermal risk, but lines are more accessible for repair/upgrade |
| Voltage violations | 2 | Customer quality-of-service issue, regulated by ANSI C84.1 |

---

## 10. Why This Framework Is Defensible for PwC US Engagements

1. **Regulatory alignment**: Scoring weights match CPUC IRP and NY REV BCA frameworks actually used in US utility proceedings.
2. **Industry benchmarks**: All cost/timeline assumptions cite published DOE, EPRI, NREL, or EIA sources.
3. **Accepted standards**: Voltage thresholds follow ANSI C84.1; overload criteria follow IEEE C57.91.
4. **NWA-first logic**: Consistent with FERC Order 2222, state NWA mandates (NY, CA, MA), and PwC US power advisory practice.
5. **Reproducibility**: Fixed scoring framework with configurable weights allows sensitivity analysis in client engagements.
6. **Audit trail**: Every run stores inputs, outputs, and scoring breakdown — essential for PUC filing support.
