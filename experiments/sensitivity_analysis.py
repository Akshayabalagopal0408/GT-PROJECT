"""
sensitivity_analysis.py - Parameter Sweeps for Fine Multiplier, Audit Cost, and Tax Rate.
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from model.payoff import TaxEvasionGame
from model.enforcement_policies import ProportionalAdaptivePolicy, PIDAdaptivePolicy
from model.agent_based_model import AgentBasedTaxModel


def run_sensitivity_sweep(output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 80)
    print("RUNNING PARAMETER SENSITIVITY ANALYSIS (Fine Multiplier vs. Audit Cost)")
    print("=" * 80)

    fine_values = np.linspace(0.5, 3.0, 6)    # [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
    audit_costs = np.linspace(4.0, 16.0, 5)   # [4.0, 7.0, 10.0, 13.0, 16.0]

    compliance_grid = np.zeros((len(audit_costs), len(fine_values)))
    net_rev_grid = np.zeros((len(audit_costs), len(fine_values)))

    n_agents = 500
    n_steps = 100

    for i, ca in enumerate(audit_costs):
        for j, f in enumerate(fine_values):
            print(f"Testing ca={ca:.1f}, fine={f:.1f} ...", end="\r")
            game = TaxEvasionGame(W=100.0, t=0.30, f=f, c_a=ca)
            policy = PIDAdaptivePolicy(base_alpha=game.alpha_star, k_p=0.40, k_i=0.06, k_d=0.15)
            model = AgentBasedTaxModel(
                n_agents=n_agents,
                game=game,
                policy=policy,
                initial_compliance=0.50,
                temperature=8.0,
                mutation_rate=0.005,
                seed=42
            )
            hist = model.run_simulation(n_steps=n_steps)
            compliance_grid[i, j] = np.mean(hist["compliance_rate"][-20:])
            net_rev_grid[i, j] = np.mean(hist["net_revenue"][-20:])

    print("\n[OK] Grid sweep completed. Generating heatmaps...")

    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Heatmap 1: Compliance
    sns.heatmap(
        compliance_grid * 100,
        xticklabels=[f"{f:.1f}" for f in fine_values],
        yticklabels=[f"${ca:.1f}" for ca in audit_costs],
        annot=True,
        fmt=".1f",
        cmap="YlGn",
        cbar_kws={'label': 'Steady-State Compliance (%)'},
        ax=axes[0]
    )
    axes[0].set_title("Steady-State Compliance vs. Fine Multiplier & Audit Cost", fontsize=12, fontweight="bold")
    axes[0].set_xlabel("Fine Multiplier (f on evaded tax)", fontsize=11, fontweight="bold")
    axes[0].set_ylabel("Audit Cost per Taxpayer ($c_a)", fontsize=11, fontweight="bold")

    # Heatmap 2: Net Revenue
    sns.heatmap(
        net_rev_grid,
        xticklabels=[f"{f:.1f}" for f in fine_values],
        yticklabels=[f"${ca:.1f}" for ca in audit_costs],
        annot=True,
        fmt=".0f",
        cmap="Blues",
        cbar_kws={'label': 'Net Gov Revenue per Period ($)'},
        ax=axes[1]
    )
    axes[1].set_title("Net Government Revenue vs. Fine Multiplier & Audit Cost", fontsize=12, fontweight="bold")
    axes[1].set_xlabel("Fine Multiplier (f on evaded tax)", fontsize=11, fontweight="bold")
    axes[1].set_ylabel("Audit Cost per Taxpayer ($c_a)", fontsize=11, fontweight="bold")

    plt.tight_layout()
    fig_path = os.path.join(output_dir, "sensitivity_analysis.png")
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    print(f"[OK] Sensitivity heatmaps saved to: {fig_path}")


if __name__ == "__main__":
    run_sensitivity_sweep()
