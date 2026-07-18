# Intervention Explainer

## Purpose
FeederIQ evaluates intervention portfolios that reduce feeder stress caused by EV growth, solar adoption, and data center demand. The interventions below are modeled as planning levers so teams can compare options quickly, consistently, and transparently.

## Intervention Levels
All interventions use the same level scale.

| Level | Label | Meaning |
|---|---|---|
| 0 | Off | Intervention is not applied. |
| 33 | Low | Partial or limited deployment. |
| 66 | Medium | Scaled deployment. |
| 100 | High | Aggressive deployment. |

## 1) Battery Storage
### What it represents
Battery Storage represents feeder-level or distributed battery energy storage dispatch used for peak shaving.

### How it is modeled
- 17:00-21:00: battery discharge reduces feeder demand.
- 11:00-14:00: battery charging slightly increases feeder demand.
- Effect is applied through feeder load scaling.

### Modeled level effects
| Level | Evening peak effect | Midday effect | Practical interpretation |
|---|---|---|---|
| Low (33) | -4% feeder load | +1% feeder load | Small storage footprint, modest peak shaving |
| Medium (66) | -8% feeder load | +2% feeder load | Meaningful dispatchable support |
| High (100) | -12% feeder load | +3% feeder load | Strongest storage-driven mitigation |

## 2) Managed EV Charging
### What it represents
Managed EV Charging represents utility or aggregator control that shifts charging away from the evening peak into lower-stress hours.

### How it is modeled
- EV charging energy is shifted from 18:00-21:00 to 00:00-05:00.
- Total EV charging energy is conserved; only timing changes.

### Modeled level effects
| Level | Evening EV charging shifted | Practical interpretation |
|---|---|---|
| Low (33) | 15% shifted off-peak | Early program participation |
| Medium (66) | 30% shifted off-peak | Broader participation and controls |
| High (100) | 50% shifted off-peak | Strong program coverage and response |

## 3) Staged Load Connection
### What it represents
Staged Load Connection represents phased energization of large new demand (for example, data center blocks) instead of full immediate interconnection.

### How it is modeled
- Near-term large-load demand is reduced by a level-dependent percentage.
- Deferred load is treated as later-stage connection outside the immediate planning window.

### Modeled level effects
| Level | Data center demand reduction | Practical interpretation |
|---|---|---|
| Low (33) | -20% | Mild commissioning phasing |
| Medium (66) | -40% | Moderate ramp deferral |
| High (100) | -60% | Aggressive staged commissioning |

## 4) Dynamic Tariffs
### What it represents
Dynamic Tariffs represent tariff and price-signal programs that reduce peak consumption from flexible demand.

### How it is modeled
- During 17:00-20:00, feeder demand is reduced by a level-dependent percentage.

### Modeled level effects
| Level | Peak-hour feeder demand effect | Practical interpretation |
|---|---|---|
| Low (33) | -3% | Weak price signal and response |
| Medium (66) | -6% | Moderate elasticity response |
| High (100) | -10% | Strong peak-demand response |

## 5) Capacity Upgrade
### What it represents
Capacity Upgrade represents conventional network reinforcement that increases effective thermal headroom.

### How it is modeled
- Effective transformer and line loading limits are increased.
- This intervention increases serving capability rather than reducing demand.

### Modeled level effects
| Level | Transformer capacity factor | Line capacity factor | Practical interpretation |
|---|---|---|---|
| Low (33) | x1.10 | x1.08 | Selective reinforcement |
| Medium (66) | x1.20 | x1.15 | Meaningful infrastructure uplift |
| High (100) | x1.30 | x1.25 | Highest reinforcement effect |

## How to Interpret Portfolio Results
- Higher levels indicate larger deployment scale, not guaranteed operational performance.
- Non-wires interventions primarily reduce or shift demand.
- Capacity Upgrade primarily increases thermal headroom.
- Mixed portfolios can combine demand-side relief with reinforcement benefits.

## Scope Notes
- These effects are planning abstractions used for comparative screening.
- Utility-specific studies should calibrate percentages and windows to local telemetry, tariffs, and interconnection constraints.
