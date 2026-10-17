# Evolutionary Game-Theoretic Model of Tax Evasion with Adaptive Auditing

A complete simulation suite and analytical toolkit modeling the evolutionary dynamics between taxpayers and an adaptive tax authority.

Developed for **Semester 5 Game Theory (SEM 5 GT PROJECT)**.

---

## 📁 Repository Structure

```
d:/SEM 5/GT PROJECT/
├── model/
│   ├── __init__.py               # Package exports
│   ├── payoff.py                 # 2x2 Inspection Game, payoffs, thresholds (α*, x*)
│   ├── enforcement_policies.py   # 5 Policies: Static, Proportional, PID, Targeted, Budget
│   ├── continuous_dynamics.py    # Continuous Replicator Dynamics ODE solver (SciPy RK45)
│   └── agent_based_model.py      # Micro Agent-Based Monte Carlo simulator with Fermi rule
│
├── experiments/
│   ├── run_comparison.py         # Monte Carlo multi-policy benchmark & trajectory plots
│   ├── phase_portrait.py         # 2D Phase space vector fields & streamplots
│   └── sensitivity_analysis.py   # Parameter sweep heatmaps (fine vs audit cost)
│
├── web/
│   ├── index.html                # Interactive modern web dashboard
│   ├── styles.css                # Glassmorphic dark-mode CSS design system
│   └── app.js                    # In-browser live evolutionary simulation engine & Chart.js
│
├── output/
│   ├── policy_comparison_trajectories.png  # Time-series trajectories
│   ├── policy_bar_metrics.png              # Summary metric bar charts
│   ├── policy_comparison_summary.csv       # Experiment raw statistics
│   ├── phase_portraits.png                 # Lotka-Volterra orbits vs Adaptive sink
│   └── sensitivity_analysis.png            # 2D parameter heatmaps
│
├── PROJECT_REPORT.md             # Complete academic submission report
└── README.md                     # Overview & Quick Start Guide
```

---

## 🚀 Quick Start

### 1. Run Python Simulations
```powershell
# 1. Run comparative policy benchmark (generates summary table & trajectory plots)
python experiments/run_comparison.py

# 2. Generate phase portraits & vector fields
python experiments/phase_portrait.py

# 3. Run parameter sensitivity heatmaps
python experiments/sensitivity_analysis.py
```

### 2. Launch Interactive Web Dashboard
```powershell
python -m http.server 8085 --directory web
```
Open **[http://localhost:8085](http://localhost:8085)** in your browser to interact with live sliders, adjust tax and fine rates, switch enforcement policies, and observe dynamic convergence in real time.
