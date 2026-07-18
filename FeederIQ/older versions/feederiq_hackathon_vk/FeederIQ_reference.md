# FeederIQ Project Reference

## 1. Project Summary

FeederIQ is an AI-assisted planning copilot for electric distribution utilities. It helps planners forecast where feeder-level congestion, voltage issues, transformer overloads, or line overloads may emerge under future load-growth scenarios.

The core idea is to move distribution planning from static, periodic, single-scenario studies toward repeatable multi-scenario analysis. The system compares traditional wires upgrades against flexible alternatives such as batteries, managed EV charging, demand response, dynamic tariffs, and phased interconnection.

FeederIQ is designed as a planning decision-support layer. It is not a real-time grid-control platform.

## 2. Problem Statement

Distribution feeders are facing fast-changing load and generation patterns due to:

- EV charging growth
- Rooftop solar adoption
- Prosumer batteries
- Large flexible loads
- Data center interconnections
- Aging grid infrastructure
- Transformer and cable supply constraints

Traditional feeder planning is often static, siloed, and periodic. Utilities may struggle to predict where congestion will appear and may default to expensive wires upgrades even when faster or cheaper non-wires alternatives could defer or reduce capital spending.

The planning question FeederIQ addresses is:

> Where will the feeder break under future scenarios, and what is the best defensible fix — balancing technical effectiveness, cost, feasibility, and deployment speed — that still satisfies reliability constraints?

The system does **not** simply recommend the cheapest option. It uses multi-criteria weighted scoring so planners can evaluate trade-offs across dimensions and select based on their operational priority (e.g., fastest to deploy, most technically effective, or lowest cost).

## 3. MVP Objective

The MVP should demonstrate an end-to-end feeder planning workflow:

1. Select a feeder and planning horizon.
2. Define future scenarios for EV, solar, and data center growth.
3. Generate synthetic feeder-level load and generation profiles.
4. Inject those profiles into an IEEE 123-bus OpenDSS feeder model.
5. Run time-series power-flow simulations.
6. Detect overloads and voltage issues.
7. Generate intervention portfolios.
8. Re-simulate the feeder under each portfolio.
9. Score and rank portfolios.
10. Produce engineering and business-oriented visualizations and recommendations.

The MVP should show how an AI-assisted planning system can support utility planners with structured scenario analysis and decision support.

## 4. Prototype Scope

The current prototype concept is a representative 24-hour future-day planning study.

This means:

- The simulation duration is one day.
- The model runs 24 hourly time steps.
- The selected planning horizon does not simulate every month or year directly.
- The planning horizon scales future load and generation magnitudes.
- The planning horizon determines whether the data center load is online by the simulated future date.

Example interpretation:

- A 12-month horizon means simulate a representative day one year in the future.
- A 5-year horizon means simulate a representative day five years in the future.

This keeps runtime manageable while still demonstrating future-state planning logic.

## 5. Target Users

The MVP is intended for:

- Distribution planning teams
- Grid modernization teams
- Asset planning teams
- Capital planning teams
- Interconnection screening teams

The system should help users compare urgent versus deferrable upgrades, evaluate interconnection requests faster, and test flexibility-first alternatives before defaulting to capital-heavy grid upgrades.

## 6. Core Architecture

Recommended MVP architecture:

```text
User Interface
    |
    v
Scenario Configuration Layer
    |
    v
Synthetic Profile Generator
    |
    v
Power Flow Simulation Layer
    |
    v
Violation Detection Layer
    |
    v
Intervention Portfolio Generator
    |
    v
Portfolio Re-Simulation Layer
    |
    v
Scoring and Ranking Layer
    |
    v
Recommendation Memo and Visual Outputs
```

Suggested technical stack:

- UI: Streamlit
- Agent workflow: LangGraph or a simple Python orchestration layer for MVP
- Simulation: OpenDSS
- Optional network analysis: pandapower
- Data processing: pandas, numpy
- Visualization: plotly, matplotlib, networkx
- Feeder model: IEEE 123-bus feeder
- Scenario data: synthetic load, EV, solar, and data center profiles
- Runtime: local machine, no external cloud dependency required

## 7. Agent-Based Workflow

The MVP can be implemented as modular agents or as plain Python services. Agent names are useful for separating responsibilities.

### 7.1 Scenario Agent

Responsibilities:

- Read user-selected planning horizon.
- Read EV, solar, and data center growth scenarios.
- Convert scenario choices into numerical assumptions.
- Produce hourly load and generation multipliers.

Example inputs:

- Planning horizon: 6 months, 12 months, 18 months, 3 years, 5 years
- EV demand: Low, Base, High
- Solar adoption: Low, Base, High
- Data center demand: Low, Moderate, High
- Data center connection timeline: 6 months, 12 months, 18 months

### 7.2 Constraint Agent

Responsibilities:

- Define engineering thresholds.
- Detect voltage and loading violations.
- Identify overloaded lines and transformers.
- Identify undervoltage and overvoltage buses.
- Track convergence failures.

Typical metrics:

- Minimum bus voltage
- Maximum bus voltage
- Number of undervoltage buses
- Number of overvoltage buses
- Number of overloaded lines
- Number of overloaded transformers
- Simulation convergence status

### 7.3 Simulation Agent

Responsibilities:

- Compile the OpenDSS feeder.
- Apply hourly feeder load multipliers.
- Add EV loads at selected buses.
- Add solar generation at selected buses.
- Add data center load at selected bus.
- Run hourly power-flow simulations.
- Store time-series results.

### 7.4 Capex / Wires Agent

Responsibilities:

- Generate traditional infrastructure upgrade options.
- Estimate cost and impact of wires solutions.
- Model transformer upgrades, feeder reconductoring, or capacity increases.
- Rank wires options by cost versus violation reduction.

### 7.5 Flexibility / NWA Agent

Responsibilities:

- Generate non-wires alternative portfolios.
- Model flexible demand and storage options.
- Estimate effect of batteries, managed charging, demand tariffs, and phased connection.
- Compare flexibility options against wires upgrades.

NWA means non-wires alternative.

### 7.6 Orchestrator / Recommendation Agent

Responsibilities:

- Coordinate scenario, simulation, constraint, capex, and flexibility outputs.
- Compare all candidate portfolios.
- Apply weighted scoring.
- Rank recommendations.
- Generate planner-facing explanation.
- Produce a decision memo.

## 8. Scenario Inputs

The MVP should expose the following configurable inputs:

| Input | Example Values |
|---|---|
| Feeder | IEEE 123-bus feeder |
| Planning horizon | 6m, 12m, 18m, 3yr, 5yr |
| EV growth | Low, Base, High |
| Solar growth | Low, Base, High |
| Data center demand | Low, Moderate, High |
| Data center connection timeline | 6m, 12m, 18m |
| Battery option | None, 33%, 66%, 100% |
| Managed charging option | None, 33%, 66%, 100% |
| Phased interconnection option | None, 33%, 66%, 100% |
| Demand tariff option | None, 33%, 66%, 100% |
| Transformer upgrade option | None, 33%, 66%, 100% |

## 9. Synthetic Profile Generation

The MVP should generate 24-hour profiles for:

- Baseline feeder load
- EV charging demand
- Solar generation
- Data center load

Suggested profile shapes:

- Feeder load: morning and evening demand peaks
- EV charging: evening-heavy pattern
- Solar generation: bell-shaped daytime output
- Data center load: mostly flat profile

The scenario choices should scale these profiles.

Example:

- High EV scenario increases evening charging load.
- High solar scenario increases midday generation.
- High data center scenario adds a larger flat load.
- Longer planning horizons increase future load assumptions.

## 10. Feeder Simulation Logic

For each hourly time step:

1. Compile the IEEE 123-bus feeder model in OpenDSS.
2. Scale baseline feeder loads.
3. Add EV loads at selected buses.
4. Add solar generators at selected buses.
5. Add data center load at selected bus if the connection timeline is active.
6. Solve power flow.
7. Extract voltage and loading results.
8. Store violation metrics.

The baseline simulation creates the before-intervention case.

## 11. Violation Detection

The system should detect and summarize:

- Undervoltage buses
- Overvoltage buses
- Overloaded lines
- Overloaded transformers
- Minimum hourly voltage
- Maximum hourly voltage
- Worst hour of system stress
- Convergence failures

Suggested thresholds:

- Undervoltage: below 0.95 per unit
- Overvoltage: above 1.05 per unit
- Overload: above 100% loading

These thresholds can be made configurable.

## 12. Intervention Portfolios

The MVP should test combinations of interventions, not only single actions.

Candidate intervention categories:

- Transformer upgrade
- Battery storage
- Managed EV charging
- Phased interconnection
- Demand tariff

Each intervention can be modeled at multiple intensity levels:

- 0%
- 33%
- 66%
- 100%

Example portfolio:

```text
Transformer upgrade: 33%
Battery: 66%
Managed charging: 33%
Phased interconnection: 0%
Demand tariff: 0%
```

Each portfolio should modify either network capacity assumptions, load profiles, generation profiles, or load timing.

## 13. Portfolio Re-Simulation

For every candidate portfolio:

1. Apply the portfolio assumptions.
2. Modify load, generation, or capacity logic.
3. Re-run the 24-hour simulation.
4. Measure violation reduction.
5. Estimate cost and feasibility.
6. Store portfolio-level outputs.

This creates a ranked decision set rather than a single deterministic answer.

## 14. Scoring Framework

Each portfolio should be scored using weighted criteria:

| Criterion | Weight | Purpose |
|---|---|---|
| Technical improvement | 40% | Measures reduction in violations and system stress |
| Cost attractiveness | 25% | Rewards lower-cost options |
| Feasibility | 20% | Rewards implementable and operationally realistic options |
| Deployment speed | 15% | Rewards faster-to-deploy interventions |

**Key design decision**: The system exposes all dimension scores in the ranking table, allowing planners to sort/filter by any criterion — not just the weighted total. This means a planner who prioritizes speed can pick the fastest-to-deploy option even if it's not the overall highest-scoring portfolio.

Example scoring formula:

```text
Total Score =
  40% Technical Improvement
+ 25% Cost Attractiveness
+ 20% Feasibility
+ 15% Deployment Speed
```

The exact weights should be configurable in the MVP.

## 15. Expected Outputs

The MVP should produce:

- Scenario summary
- Synthetic load and generation profile charts
- Baseline simulation results
- Violation summary
- Worst-hour feeder stress summary
- Bus-level asset table
- Network map or simplified feeder visualization
- Before/after comparison
- Ranked portfolio table
- Recommended intervention
- Second-best option
- Explanation of why the recommendation was selected
- Decision memo in Markdown or PDF format

## 16. Suggested Repository Structure

```text
feederiq-mvp/
  app.py
  requirements.txt
  README.md
  data/
    feeders/
      ieee123/
        Master.dss
        ...
    profiles/
      sample_profiles.csv
  src/
    config/
      assumptions.py
      thresholds.py
    agents/
      scenario_agent.py
      constraint_agent.py
      simulation_agent.py
      capex_agent.py
      flexibility_agent.py
      orchestrator_agent.py
    simulation/
      opendss_runner.py
      profile_generator.py
      violation_detector.py
    portfolios/
      portfolio_generator.py
      portfolio_scorer.py
    reporting/
      charts.py
      decision_memo.py
    utils/
      data_loader.py
      constants.py
  outputs/
    runs/
  tests/
    test_profiles.py
    test_scoring.py
    test_portfolios.py
```

## 17. MVP Build Plan

### Phase 1: Feeder Simulation

Build:

- Load IEEE 123-bus feeder.
- Compile OpenDSS model.
- Run one baseline power flow.
- Extract bus voltages and equipment loading.

Exit criteria:

- Feeder compiles successfully.
- A simple result table is produced.

### Phase 2: Scenario Profiles

Build:

- Generate 24-hour baseline load profile.
- Generate EV load profile.
- Generate solar generation profile.
- Generate data center load profile.
- Scale profiles by planning horizon and scenario level.

Exit criteria:

- Charts show all 24-hour profiles.
- Scenario assumptions are visible in the UI.

### Phase 3: Time-Series Simulation

Build:

- Run 24 hourly simulations.
- Inject EV, solar, and data center profiles.
- Store hourly voltage and loading metrics.

Exit criteria:

- Baseline future scenario produces violation summary.
- Worst-hour stress is identified.

### Phase 4: Portfolio Engine

Build:

- Generate intervention combinations.
- Apply portfolio effects.
- Re-run simulation for each candidate.
- Score and rank options.

Exit criteria:

- Ranked portfolio table is produced.
- Top recommendation is explainable.

### Phase 5: Decision UI and Memo

Build:

- Streamlit workflow.
- Scenario controls.
- Charts and tables.
- Recommendation panel.
- Exportable Markdown decision memo.

Exit criteria:

- User can run an end-to-end planning study locally.

## 18. Local MVP Dependencies

Suggested Python packages:

```text
streamlit
pandas
numpy
plotly
matplotlib
networkx
opendssdirect.py
pandapower
langgraph
langchain
pydantic
pytest
```

For a simpler MVP, LangGraph can be skipped initially and the workflow can be implemented as plain Python functions. Agent orchestration can be added after the simulation and scoring logic works.

## 19. Development Priorities

Build in this order:

1. Make OpenDSS simulation work.
2. Generate synthetic profiles.
3. Run 24-hour baseline simulation.
4. Detect violations.
5. Generate intervention portfolios.
6. Re-simulate portfolios.
7. Score and rank options.
8. Build Streamlit UI.
9. Add memo generation.
10. Add agent orchestration if needed.

The simulation and scoring logic should be stable before investing heavily in UI or agent abstractions.

## 20. Key Design Principles

- Keep the MVP local-first.
- Use public feeder data and synthetic load profiles.
- Avoid real-time control claims.
- Keep the output planner-reviewable.
- Show assumptions clearly.
- Prefer explainable recommendations over black-box optimization.
- Compare flexibility options before defaulting to wires upgrades.
- Make scoring weights configurable.
- Store each run's inputs and outputs for reproducibility.
- Ground all assumptions in published industry benchmarks (DOE, EPRI, NREL, EIA).
- Align scoring framework with US regulatory methodologies (CPUC IRP, NY REV BCA).
- Expose all scoring dimensions to support multi-criteria decision-making.

## 20a. Assumptions Defensibility

All model assumptions are documented and defensible:

- **Deployment levels** (0/33/66/100%) map to EPRI technology maturity stages.
- **Cost scores** derived from NREL ATB 2024, Lazard LCOE+ v17.0, and FERC Form 1 filings.
- **Feasibility scores** based on PUC proceeding timelines and utility implementation experience.
- **Deployment speed** sourced from DOE NWA case studies and utility IRP data.
- **Scoring weights** aligned with CPUC IRP (D.22-02-004) and NY REV BCA Handbook (2024).
- **Voltage thresholds** follow ANSI C84.1 Range A.
- **Overload criteria** follow IEEE C57.91.

Full details: see `assumptions_rationale.md`

## 21. One-Line MVP Description

FeederIQ is a local planning copilot that stress-tests a distribution feeder under future EV, solar, and data center scenarios, compares wires and non-wires intervention portfolios, and produces a ranked recommendation with engineering evidence.
