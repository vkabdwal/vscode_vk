# Q-Log (Panel Interview Prep)

Purpose: Keep a running list of interview questions and polished answers.

How to use:
- Add each new question as a new section.
- Keep answers in plain language first, then add technical detail.
- Add 3-6 key terms under each answer so you sound technical without overexplaining.
- End with a one-line version you can say quickly.

---

## Q1. OpenDSS: Is it a phasor-domain simulation or a discrete-domain simulation?

Short answer:
OpenDSS in our project works like this: one power-flow solve per time slot. So it is phasor-based solving, repeated at discrete time steps.

Interview-safe explanation:
- **What QSTS means (simple).**
	QSTS means we run many steady-state snapshots in time order, like a day split into time slots.

- **What phasor-domain means (simple).**
	In each snapshot, OpenDSS calculates voltage and current in normal AC steady state (not fast waveform transients).

- **What discrete-time means (simple).**
	We move time step by step (for example hourly). At each step, we use the values for that time and solve once.

- **What is a profile row (simple).**
	A profile is a table. One row = one time slot. That row contains feeder load, EV, solar, and data center values for that time.

- **Important clarification.**
	We do not sample the sine wave itself. We sample operating conditions over time, then run one power-flow solve for each sampled time slot.

What it is not (for clarity):
- It is not a full EMT/time-domain waveform simulator for sub-cycle switching transients.

One-line response:
"We run one phasor power-flow solve per time slot using that slot's demand and generation values."

Key terms to mention:
- QSTS (Quasi-Static Time Series)
- Phasor-domain
- Steady-state snapshot
- Time-series profiles
- Voltage violations / thermal overloads

20-second panel version:
"We use OpenDSS in QSTS mode. That means we take time-series demand and generation values, then run one phasor power-flow snapshot per time slot. This lets us track voltage and loading issues over time without doing full EMT waveform simulation."

Panel fallback answer (even simpler):
"Think of it as a flipbook: each frame is a phasor power flow snapshot, and QSTS is the ordered sequence of those frames over the day."

If asked "So is it phase distribution sampled discretely?":
"Almost. It is phasor-based network solving at each step, and discrete sampling of system operating states over time, not direct waveform sampling."

If asked "Sample from where and how?":
- **From where.**
	The sampled states come from time-series profile inputs. In this MVP, that is either synthetic 24-hour profiles (feeder multiplier, EV MW, solar MW, data center MW) or hourly profiles derived from openEDI CSV data.

- **How.**
	For each time index (for example, each hour), we read one row, apply those values to OpenDSS loads/generators, run one solve, record outputs, and move to the next row.

- **What is discretized.**
	The operating point trajectory is discretized in time (row-by-row). The network physics in each row is solved as a phasor steady-state power flow.

---

## Q2. Is this good enough as a hackathon MVP, and can it be defended as real-world and sellable?

Short answer:
Yes. For an MVP, this is a strong and credible architecture: OpenDSS + time-series profiles + intervention logic + explainable outputs. It is realistic for utility advisory use cases and can be positioned as a decision-support product, not a protection-grade real-time controller.

Interview-safe explanation:
- **Why this is a good MVP.**
	It uses an industry-recognized engine (OpenDSS), not a toy simulator. It addresses a real utility pain point by testing DER/load impacts and intervention options before field deployment. It is explainable because recommendations can be traced to voltage/loading results at specific times and nodes. It is also modular, so data ingestion, simulation, and recommendation logic can evolve independently.

- **Why this is defensible for real-world application.**
	Utilities and consulting firms already run planning and scenario analysis in quasi-static snapshot workflows, so this aligns with existing operating models. A Big4-style offering can package this as "grid planning analytics + what-if intervention assessment + executive reporting." The near-term commercial value is planning decisions, program design, and capex prioritization where explainability matters.

- **Honest limitation to acknowledge (and control).**
	It is not yet a production digital twin or SCADA-integrated closed-loop optimizer. That does not weaken the MVP claim; it clarifies scope and maturity.

- **Best defense sentence.**
	"This MVP is production-relevant for planning analytics today, and roadmap-ready for deeper operational integration tomorrow."

One-line response:
"For a hackathon MVP, this is exactly the right level: technically credible, business-relevant, and directly extensible into a client-facing planning analytics product."

Key terms to mention:
- Decision-support analytics
- Explainable recommendations
- Scenario analysis / what-if analysis
- DER integration planning
- Capex prioritization
- Roadmap to digital twin

20-second panel version:
"This MVP is strong because it uses an industry-standard simulation engine and produces explainable, scenario-based planning outputs. It is immediately useful for decision-support and capex prioritization, and it has a clear roadmap toward deeper operational integration."

---

## Q3. This is an AI hackathon. Where is the AI value in FeederIQ?

Short answer:
The simulator (OpenDSS) is the physics engine, and AI is the decision-support layer that turns scenarios and simulation outputs into ranked, explainable intervention recommendations.

Interview-safe explanation:
- **How to frame it correctly.**
	We are not claiming AI replaces power-system physics. We use AI to translate planning context into scenarios, compare intervention portfolios, and generate explainable recommendations from simulation outputs.

- **Where AI is used in the workflow.**
	AI helps convert user/planning inputs into structured assumptions, supports portfolio recommendation logic, and produces readable executive-level rationale tied to technical results.

- **Why this is valuable in an AI hackathon.**
	The value is AI + domain engine integration. AI accelerates decision quality and communication, while OpenDSS ensures technical credibility. This is stronger than a pure chatbot and stronger than a physics-only dashboard.

- **How to defend against "this is just rules" feedback.**
	Say the product is an AI-assisted decision system: simulation creates evidence, AI creates prioritization and explanation, and the combined system improves speed, consistency, and usability for planners.

Key terms to mention:
- AI-assisted decision support
- Explainable recommendations
- Scenario-to-action pipeline
- Human-in-the-loop
- Physics-informed AI workflow
- Portfolio ranking and rationale generation

Terms to avoid (or use carefully):
- "Fully autonomous grid control"
- "Real-time closed-loop operations" (unless you clearly say "future roadmap")
- "AI replaces engineering"
- "Black-box recommendation"

20-second panel version:
"OpenDSS is our physics truth layer, and AI is our decision layer. AI helps structure scenarios, prioritize intervention portfolios, and generate explainable recommendations linked to voltage and loading results. So this is an AI-assisted, physics-grounded planning product, not a generic chatbot."

One-line response:
"Our differentiator is physics-grounded AI decision support: credible simulation outputs plus explainable AI-driven planning recommendations."

If they ask "Is this really AI or just simulation?":
"It is both by design: simulation provides system truth, and AI converts that truth into prioritized, explainable actions for planners and executives."

If they ask "Can this be sold by a Big4 team?":
"Yes, as an AI-enabled grid planning advisory product: faster scenario analysis, transparent recommendations, and board-ready reporting with a clear roadmap to deeper utility integration."

---

## Q4. What is your competitive moat?

Short answer:
Our moat is not just AI and not just simulation. It is the combination: physics-grounded outputs, AI-assisted prioritization, and client-ready explainability in one workflow.

Interview-safe explanation:
- **Moat layer 1: Credibility.**
	Recommendations are tied to power-system outputs (voltage, loading, violations), so stakeholders can trust and audit decisions.

- **Moat layer 2: Speed.**
	The platform converts scenario inputs into ranked intervention options faster than manual spreadsheet + engineering handoffs.

- **Moat layer 3: Explainability for decision makers.**
	We do not stop at metrics. We provide clear recommendation narratives and trade-offs that planners, managers, and executives can act on.

- **Moat layer 4: Delivery fit for consulting teams.**
	This can be packaged as repeatable advisory accelerators: scenario workshop, quantified options, prioritized roadmap, and executive memo.

- **Moat layer 5: Expandable architecture.**
	Today: planning decision support. Tomorrow: deeper integration with utility data systems and richer optimization methods.

Key terms to mention:
- Physics-grounded AI
- Explainable decision intelligence
- Scenario-to-recommendation engine
- Auditability and trust
- Advisory accelerator
- Land-and-expand roadmap

20-second panel version:
"Our moat is the integration of three things most tools separate: physics credibility, AI-driven prioritization, and executive-ready explainability. That combination makes the product trusted by engineers, usable by business teams, and commercially deployable by consulting organizations."

One-line response:
"We win by turning technically correct simulation outputs into fast, explainable, and client-ready decisions."

If they ask "What stops others from copying this?":
"Code can be copied, but integrated workflow quality is harder to copy: domain calibration, decision logic, explainability design, and delivery playbooks built with client feedback."

If they ask "Is the moat data, model, or workflow?":
"Primarily workflow and trust architecture today, with data and model advantages compounding over time as deployments grow."

---

## Q5. How big is your dataset and how long does the AI take to run?

Short answer:
In synthetic mode, 24 rows. In real-data mode, 3.7M source points reduced to 24 hourly values at runtime. Full study runs in under 30 seconds.

Interview-safe explanation:
- **Dataset size.**
  Synthetic mode generates 24 rows × 4 columns (feeder load, EV, solar, data center) — intentionally lightweight for fast iteration. Real-data mode loads 91 load CSVs × 35,040 rows + 14 PV CSVs from DOE openEDI, then selects the peak-stress day and averages to 24 hourly values.

- **Simulation speed.**
  Each study evaluates up to 120 intervention portfolios, each running 24 OpenDSS power-flow solves. That takes about 5–15 seconds depending on portfolio count.

- **AI layer overhead.**
  LLM calls for recommendation narratives, implementation plans, and executive memos add 3–8 seconds depending on API latency.

- **Total end-to-end.**
  Roughly 10–25 seconds for a complete study, including simulation and AI generation.

Key terms to mention:
- 24-hour time-series resolution
- 120 candidate portfolios
- Sub-30-second turnaround
- Peak-day selection from full-year data

20-second panel version:
"Each study evaluates up to 120 portfolios across 24 hourly time steps in under 30 seconds — simulation plus AI-generated recommendations. In real-data mode we start from 3.7 million data points and reduce to the peak-stress day automatically."

One-line response:
"Full study in under 30 seconds: 120 portfolios, 24 time steps, simulation plus AI recommendations."

---

## Q6. Why did you anchor the GIS view at Loudoun County, VA?

Short answer:
Loudoun County is the world's largest data center corridor, has active EV charging expansion, and is under Virginia's clean energy mandate — all three scenarios we model.

Interview-safe explanation:
- **Data centers.**
  Ashburn / Loudoun County hosts 100+ data center facilities (AWS, Microsoft, Google, Equinix, Digital Realty). This is the most relevant US location for our data center interconnection scenario.

- **EV growth.**
  Northern Virginia has among the highest EV adoption rates in the state. VDOT is expanding charging infrastructure along I-66 and Route 7.

- **Solar mandate.**
  The Virginia Clean Economy Act (2020) mandates 100% clean energy by 2050. Dominion Energy has a large-scale solar buildout program underway.

- **Why this matters for credibility.**
  We are not placing our feeder on a random map. We chose a location where all three of our scenario drivers (EV, solar, data center) are real and actively growing.

Key terms to mention:
- HIFLD (federal open dataset)
- Dominion Energy service territory
- Virginia Clean Economy Act
- Data Center Alley
- Georeferenced anchor

20-second panel version:
"We anchored at Loudoun County, Virginia — the world's largest data center cluster, served by Dominion Energy, with active EV growth and a state solar mandate. All three of our scenario drivers are real there."

One-line response:
"Loudoun County has data centers, EV growth, and a solar mandate — exactly the scenario our tool models."

---

## Q7. How many customers will actually be willing to let their utility see and control their EV charging?

Short answer:
Industry data shows 50–70% of residential EV owners opt in to managed charging programs when offered meaningful incentives (bill credits, TOU savings, or free charger hardware). Enrollment scales with trust, simplicity, and tangible value.

Interview-safe explanation:
- **Current opt-in rates from real programs.**
	Utilities running managed charging pilots consistently report 50–70% enrollment among eligible EV owners. Examples: Con Edison's SmartCharge program, Duke Energy's Park & Plug, Pacific Gas & Electric's EV Charge Network, and GM Energy / PG&E V2H pilots. These are voluntary programs with financial incentives.

- **What drives willingness.**
	Three factors dominate: (1) **Financial incentive** — bill credits of $5–$15/month or TOU rate savings make participation rational. (2) **Convenience and override ability** — customers enroll more when they can override or set departure-time guarantees ("my car is full by 7 AM"). (3) **Trust in the utility** — transparent communication about what is controlled, when, and why.

- **What suppresses willingness.**
	Lack of awareness (many EV owners do not know programs exist), privacy concerns about charging data, and fear of losing control ("will my car be dead when I need it?"). Programs that offer clear opt-out or override mechanisms address the control concern directly.

- **Why this matters for our product.**
	FeederIQ models managed EV charging as an intervention. We do not assume 100% participation. Our simulation can parameterize adoption rate (e.g., 30%, 50%, 70%) and show planners the grid impact at each level. This makes the recommendation honest and actionable: planners see what adoption rate is needed to avoid a capacity upgrade, and what the fallback is if adoption is lower.

- **How to defend the managed charging intervention.**
	Say: "We model managed charging at realistic adoption levels, not 100%. The value of the tool is showing planners the tipping point — what participation rate avoids a $2M transformer upgrade versus what rate only delays it."

Key terms to mention:
- Opt-in rate / enrollment rate
- Time-of-use (TOU) shifting
- Demand response (DR) for EVs
- Override / departure-time guarantee
- Parameterized adoption sensitivity
- Incentive design (bill credit, free hardware)

20-second panel version:
"Real utility programs see 50–70% opt-in for managed EV charging when incentives are clear and customers can override. Our tool does not assume 100% — we let planners set the adoption rate and see how grid impacts change at 30%, 50%, or 70%, so recommendations are realistic and defensible."

One-line response:
"50–70% opt-in is typical in incentivized programs, and our tool lets planners test sensitivity across adoption levels rather than assuming full participation."

If they ask "What if customers refuse?":
"That is exactly what our sensitivity analysis shows. If adoption is too low to avoid violations, the tool recommends the next-best intervention — like targeted infrastructure upgrades — so the planner always has a fallback."

If they ask "Is managed charging actually deployed anywhere?":
"Yes. Con Edison SmartCharge NY, Duke Energy Park & Plug, PG&E EV Charge Network, and multiple California CCAs run active managed charging programs today. Several have moved from pilot to full program status."

If they ask "How is this different from simple TOU rates?":
"TOU shifts behavior with price signals but gives the utility no direct control. Managed charging adds utility-dispatchable load reduction — the utility can actively curtail or shift charging during grid stress events, not just hope the price signal works."
