# Academic Project Defense Guide: Explaining the Project to Sir

This guide provides a **rigorous, academically sound, and crystal-clear explanation** of our project. It explicitly separates the **baseline theoretical model from the published literature (Fedeli & Costarelli, 2026)** from **our proposed extensions (Agent-Based Modeling, Social Imitation, and Adaptive Control Policies)**.

---

## 1. Academic Framing & 1-Minute Pitch

### When Sir asks: *"Tell me in 2–3 lines what your project is about and its contribution."*

> *"Sir, our project investigates tax evasion as an evolutionary co-governance game between taxpayers and a tax authority.*  
> *We first study the baseline model by **Fedeli & Costarelli (2026)**, which proves that under standard replicator dynamics, tax compliance and enforcement inevitably fall into **unstable, perpetual cycles**.*  
> *We then **extend** this work by introducing an **individual-level agent-based model (1,000 citizens with Fermi social imitation)** and comparing **five alternative enforcement mechanisms (Static, Reactive, PID Adaptive, Risk-Targeted, and Budget-Constrained)** to analyze how active feedback control can break these cycles and stabilize compliance."*

---

## 2. Does Our Project Address the Original Paper's Limitations?

The table below provides an honest academic audit of what the original paper left open, what our project implements, and the precise academic verdict:

| Original Paper's Limitation (Fedeli & Costarelli 2026) | What Our Project Implements | Academic Verdict |
| :--- | :--- | :--- |
| **No individual-level taxpayer simulation** (Uses macro infinite-population differential equations) | Simulates 1,000 individual citizens using an Agent-Based Model (`model/agent_based_model.py`) | **Addressed at the modeling level**: Captures individual histories, flags, and discrete interactions. |
| **No social learning or peer imitation** (Assumes deterministic population-level replicator dynamics) | Taxpayers update strategies via the **Fermi update rule** (pairwise payoff comparison) | **Partly addressed**: This introduces a bounded-rationality behavioral assumption, though it remains a theoretical imitation model rather than an empirically verified human decision rule. |
| **No adaptive audit policy comparison** (Authority follows a fixed evolutionary replicator rule) | Implements and compares 5 distinct audit policies (Static, Proportional, PID, Risk-Targeted, Budget-Constrained) | **Addressed at the design level**: Explores how engineering feedback control alters evolutionary stability. |
| **Illustrative parameters, not estimated from real tax data** (Assumes $\tau=0.30, \beta=0.75, C=0.50$) | Uses assumed parameters ($W=100, t=0.30, f=1.5, c_a=8.0$) | **Not addressed**: Our project remains simulation-based; parameters are illustrative benchmarks. |
| **No empirical validation** (No real-world tax audit dataset used) | Reports Monte Carlo simulation metrics | **Not addressed**: No empirical dataset has been fitted yet (a recognized limitation for future work). |
| **No risk-based audit targeting** (Audits are strictly random matching) | Implements a **Risk-Targeted Policy** (flagged watchlist with 85% audit rate for 5 periods) | **Addressed at the model level**: Evaluates the trade-off of audit memory vs. moral hazard among clean citizens. |
| **No explicit budget constraint** (Authority assumed to have infinite funds) | Implements a **Budget-Constrained Policy** (audit budget capped at 25% of collected revenue) | **Addressed at the model level**: Successfully captures the "fiscal poverty trap" where low initial revenue prevents deterrence. |
| **No active feedback controller** | Designs a **PID (Proportional-Integral-Derivative) Adaptive Controller** | **New Extension**: Demonstrates how classical control theory dampens evolutionary game-theoretic cycles. |

> **Important Distinction:** Adding a feature to a simulation addresses a *modeling limitation*, but does not automatically mean it reflects *real-world behavior*. We must present our ABM as an exploratory computational laboratory, not empirical proof.

---

## 3. Resolving the Three Critical Issues

### Issue 1: Clarifying the 40% Deterrence Threshold ($\alpha^*$)

* **The Common Misconception:** Stating that *"if audit rate $\alpha > 40\%$, everyone is guaranteed to comply."*
* **The Correct Academic Explanation:**
  $$\alpha^* = \frac{1}{1 + f} = \frac{1}{1 + 1.5} = 0.40 \quad (40\%)$$
  $\alpha^* = 40\%$ is the **risk-neutral expected payoff indifference threshold**:
  * Payoff from Complying: $U_C = W(1 - t) = 100(1 - 0.30) = \$70$.
  * Payoff from Evading under audit probability $\alpha$:  
    $$U_E(\alpha) = (1 - \alpha) \cdot W + \alpha \cdot [W - (1 + f)tW] = 100 - \alpha \cdot 75$$
  * At $\alpha = 0.40$: $U_E(0.40) = 100 - (0.40 \times 75) = \$70 = U_C$.
  * **Why it is NOT an instant guarantee in our simulation:**
    In our agent-based model, citizens update strategies via the **Fermi Rule**:
    $$P(S_i \leftarrow S_j) = \frac{1}{1 + e^{-(\pi_j - \pi_i) / T}}$$
    Because of the selection temperature $T$ (noise) and random pairwise matching, individuals do not instantly flip to compliance the moment $\alpha$ crosses $40\%$. Instead, $\alpha > 40\%$ gives compliance a **statistical fitness advantage**, causing compliance to spread gradually across rounds through peer imitation.

---

### Issue 2: Distinguishing the Original Paper's Equations vs. Our Project's Equations

We must clearly separate the mathematical framework of Fedeli & Costarelli (2026) from our computational extensions:

```
+-------------------------------------------------------------+-------------------------------------------------------------+
|          PART A: Original Paper (Fedeli & Costarelli 2026)   |             PART B: Our SEM 5 Project Extensions            |
+-------------------------------------------------------------+-------------------------------------------------------------+
| • Players: Two infinite, well-mixed populations             | • Players: 1,000 discrete agents + 1 Central Tax Authority  |
|   (Taxpayers x and Audit Units y)                           |                                                             |
| • Payoffs: Includes under-declaration fraction β and        | • Payoffs: All-or-nothing evasion (W, t, f, c_a)            |
|   institutional accountability loss λ on unrecovered taxes  |                                                             |
| • Dynamics: Canonical continuous Replicator ODEs:           | • Dynamics: Discrete-time Agent-Based Model with            |
|   dx/dt = x(1-x)(1-β)Y [α(τ+φ)y - τ]                        |   Fermi imitation rule: P = 1 / [1 + exp(-Δπ / T)]          |
|   dy/dt = y(1-y)Y {α(1-β)[φ+(1+λ)τ](1-x) - Cτ}              |                                                             |
| • Result: Purely imaginary eigenvalues (±iω),               | • Policies: Replaces passive replicator audit unit with     |
|   Jacobian trace = 0, permanent undamped center cycles      |   5 active control policies (Static, PID, Watchlist, etc.)  |
+-------------------------------------------------------------+-------------------------------------------------------------+
```

---

### Issue 3: Verifying Numerical Results & Clarifying Cost Claims

In earlier drafts, it was claimed that PID achieves the *"lowest enforcement cost."* **That claim was factually inaccurate and must be corrected.**

#### Corrected Metrics Table (5 Monte Carlo Runs, $N=1000$, 150 Steps):

| Policy Name | Final Steady Compliance | Volatility ($\sigma$) | Average Audit Rate | Total Enforcement Cost | Total Net Revenue | Correct Evaluation |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Static Audit ($\alpha=35\%$)** | **1.8%** | 0.003 | **34.9%** | **$418,800** | $3,523,790 | Lowest cost, but complete system failure |
| **Budget-Constrained** | **19.9%** | 0.009 | 47.7% | $572,400 | $4,622,056 | Trapped in under-enforcement poverty trap |
| **Risk-Targeted (Watchlist)** | **49.6%** | 0.032 | 58.1% | $697,200 | $4,359,020 | High fine collection, but 50% evading |
| **Proportional Reactive** | **95.1%** | 0.008 | 58.3% | $699,600 | $3,914,527 | High compliance, but exhibits persistent swings |
| **PID Adaptive** | **97.8%** | **0.003** | **60.7%** | **$728,400** | **$3,867,758** | **Highest compliance & stability, but higher audit cost** |

#### Why PID is "Optimal Under a Specific Objective":
* **If the objective is pure budget minimization:** Static Audit has the lowest cost ($418k), but it completely destroys compliance (1.8%).
* **If the objective is maximizing gross penalties:** Risk-Targeted generates high revenue from caught evaders, but permits chronic evasion (49.6%).
* **If the objective is Maximizing Long-Term Compliance Stability (Deterrence):** **PID Adaptive is superior**. It eliminates cycle oscillations ($\sigma = 0.003$) and maintains 97.8% voluntary compliance. The authority deliberately invests in a higher average audit rate (60.7%) to suppress evasion permanently.

---

## 4. How to Frame Our Contribution Academically

When presenting slides or writing the final report, use this formal abstract statement:

> *"Our work extends the baseline evolutionary tax-compliance model by introducing individual-level taxpayer imitation and comparing fixed, reactive, feedback-based, risk-targeted, and budget-constrained audit policies. We investigate how these alternative enforcement mechanisms affect compliance, government revenue, audit expenditure, and the stability of the system. The model remains simulation-based and uses illustrative parameters, so its findings are not yet empirically validated against real tax-administration data."*

---

## 5. Summary of the Original Model (Fedeli & Costarelli, 2026)

To demonstrate mastery to Sir, be ready to explain the original paper's mathematics:

### 1. The Two Populations:
* **Taxpayers:** Share $x = q_H$ are Honest; share $(1 - x) = q_C$ are Cheaters (declaring fraction $\beta$ of income).
* **Tax Authority Units:** Share $y = p_I$ Inspect; share $(1 - y) = p_{NI}$ Do Not Inspect.

### 2. Payoff Differences:
* Taxpayer: $\Delta_T(y) = (1 - \beta)Y [\alpha(\tau + \phi)y - \tau]$
* Authority: $\Delta_A(x) = Y \{\alpha(1 - \beta)[\phi + (1 + \lambda)\tau](1 - x) - C\tau\}$

### 3. The Stationary Interior Benchmark:
$$p_I^* = \frac{\tau}{\alpha(\tau + \phi)}, \qquad q_C^* = \frac{C\tau}{\alpha(1 - \beta)[\phi + (1 + \lambda)\tau]}$$

### 4. Mathematical Center & Invariant:
* The Jacobian matrix evaluated at $(x^*, y^*)$ has $\text{Trace} = 0$ and $\text{Determinant} > 0$.
* Eigenvalues are purely imaginary: $\mu_{1,2} = \pm i \sqrt{x^*(1 - x^*)y^*(1 - y^*)AB}$.
* A first integral $H(x, y)$ is strictly conserved ($dH/dt = 0$), proving the trajectories are **closed concentric cycles**.

---

## 6. Top 5 Questions Sir Might Ask & How to Answer

### Q1: *"Why does the original paper predict cycles rather than a stable equilibrium?"*
> **Answer:** *"Sir, because of two-sided incentive feedback. High evasion makes inspections fiscally rewarding, so audits increase. High audits deter cheating, so compliance rises. But once compliance is high, auditing honest citizens yields no recoveries and wastes administrative resources ($C\tau Y$), so the authority scales back audits. This opens room for cheating to re-emerge. Under continuous replicator dynamics, the Jacobian has zero real eigenvalues, creating perpetual closed orbits."*

### Q2: *"Is your 1,000-agent ABM an empirical validation of the paper?"*
> **Answer:** *"No, Sir. Our ABM is a computational modeling extension, not an empirical validation. It replaces the infinite-population assumption with 1,000 discrete agents and tests the Fermi imitation rule. However, our parameters ($W=100, t=0.30$) are illustrative benchmarks. Validating the model empirically would require calibrating parameters against administrative tax datasets such as OECD ISORA or World Bank Enterprise surveys."*

### Q3: *"Why did the Static Audit policy crash to 1.8% compliance in your ABM?"*
> **Answer:** *"Sir, because the static audit rate was set to 35%, which is below the risk-neutral indifference threshold of $\alpha^* = \frac{1}{1 + f} = 40\%$. Evading had a higher expected payoff than complying. Through the Fermi imitation process, evaders earned more on average, and honest citizens gradually copied their strategy until compliance almost completely collapsed."*

### Q4: *"Why do you claim PID control is beneficial if its audit cost is higher?"*
> **Answer:** *"Sir, PID control is optimal if the policy objective is system stability and high compliance rather than raw expenditure minimization. Static auditing costs less but allows 98% evasion. PID uses feedback on current evasion (P), accumulated past evasion (I), and evasion momentum (D) to eliminate cycles ($\sigma = 0.003$) and maintain 97.8% compliance, preventing the boom-and-bust enforcement crises demonstrated in the original paper."*

### Q5: *"What would be the next step to turn this into a published paper?"*
> **Answer:** *"Sir, three concrete steps: First, calibrate parameters ($t, f, c_a$) using real audit datasets from OECD or the IRS. Second, conduct sensitivity sweeps across the Fermi selection temperature $T$ to test robustness against behavioral noise. Third, formally formulate the tax authority's objective as a constrained optimization problem to solve for Pareto-optimal control gains."*
