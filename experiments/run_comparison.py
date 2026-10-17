"""
run_comparison.py - Comprehensive Comparative Analysis of 5 Enforcement Policies.
Evaluates Compliance, Evasion, Gross Revenue, Enforcement Cost, and Net Government Revenue.
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from model.payoff import TaxEvasionGame
from model.enforcement_policies import (
    StaticAuditPolicy,
    ProportionalAdaptivePolicy,
    PIDAdaptivePolicy,
    RiskTargetedPolicy,
    BudgetConstrainedPolicy,
)
from model.agent_based_model import AgentBasedTaxModel


def run_comparative_experiment(
    n_agents: int = 1000,
    n_steps: int = 150,
    n_runs: int = 5,
    seed: int = 42,
    output_dir: str = "output"
):
    os.makedirs(output_dir, exist_ok=True)
    game = TaxEvasionGame(W=100.0, t=0.30, f=1.5, c_a=8.0)
    print(game.summary())

    policies = [
        StaticAuditPolicy(fixed_alpha=0.35),
        ProportionalAdaptivePolicy(initial_alpha=0.35, k_p=0.35, target_evasion=0.05),
        PIDAdaptivePolicy(base_alpha=0.35, k_p=0.45, k_i=0.08, k_d=0.20, target_evasion=0.02),
        RiskTargetedPolicy(alpha_clean=0.12, alpha_flagged=0.85, probation_periods=5),
        BudgetConstrainedPolicy(budget_fraction=0.25, target_desired_alpha=0.60, c_a=8.0),
    ]

    results_summary = []
    policy_trajectories = {}

    print("\n" + "=" * 80)
    print(f"RUNNING MONTE CARLO COMPARISON ({n_runs} runs per policy, {n_steps} steps, N={n_agents})")
    print("=" * 80)

    for pol in policies:
        print(f"--> Simulating: {pol.name} ...")
        runs_compliance = []
        runs_alpha = []
        runs_net_rev = []
        runs_cost = []
        runs_gross_rev = []

        for r in range(n_runs):
            run_seed = seed + (r * 100)
            model = AgentBasedTaxModel(
                n_agents=n_agents,
                game=game,
                policy=pol,
                initial_compliance=0.50,
                temperature=8.0,
                mutation_rate=0.005,
                seed=run_seed,
            )
            hist = model.run_simulation(n_steps=n_steps)
            runs_compliance.append(hist["compliance_rate"])
            runs_alpha.append(hist["audit_intensity"])
            runs_net_rev.append(hist["net_revenue"])
            runs_cost.append(hist["enforcement_cost"])
            runs_gross_rev.append(hist["gross_revenue"])

        mean_compliance = np.mean(runs_compliance, axis=0)
        mean_alpha = np.mean(runs_alpha, axis=0)
        mean_net_rev = np.mean(runs_net_rev, axis=0)
        mean_cost = np.mean(runs_cost, axis=0)
        mean_gross_rev = np.mean(runs_gross_rev, axis=0)

        # Store for trajectory plotting
        policy_trajectories[pol.name] = {
            "compliance": mean_compliance,
            "alpha": mean_alpha,
            "net_revenue": mean_net_rev,
            "cost": mean_cost,
            "gross_revenue": mean_gross_rev,
        }

        # Calculate steady-state / cumulative statistics
        final_compliance = float(np.mean(mean_compliance[-30:]))
        compliance_volatility = float(np.std(mean_compliance[-30:]))
        avg_audit_intensity = float(np.mean(mean_alpha))
        total_gross_revenue = float(np.sum(mean_gross_rev))
        total_cost = float(np.sum(mean_cost))
        total_net_revenue = float(np.sum(mean_net_rev))
        cost_benefit_ratio = total_net_revenue / total_cost if total_cost > 0 else 0.0

        results_summary.append({
            "Enforcement Policy": pol.name,
            "Final Compliance": f"{final_compliance:.1%}",
            "Volatility (std)": f"{compliance_volatility:.3f}",
            "Avg Audit Rate": f"{avg_audit_intensity:.1%}",
            "Total Gross Rev": f"{total_gross_revenue:,.0f}",
            "Total Audit Cost": f"{total_cost:,.0f}",
            "Total Net Revenue": f"{total_net_revenue:,.0f}",
            "Enforcement ROI": f"{cost_benefit_ratio:.2f}x",
            # Raw numbers for plotting
            "_final_comp": final_compliance,
            "_total_net": total_net_revenue,
            "_total_cost": total_cost,
            "_avg_alpha": avg_audit_intensity,
            "_roi": cost_benefit_ratio,
        })

    # Display comparison table
    df_summary = pd.DataFrame(results_summary)
    display_cols = [c for c in df_summary.columns if not c.startswith("_")]
    print("\n" + "=" * 95)
    print("POLICY COMPARISON SUMMARY TABLE")
    print("=" * 95)
    print(df_summary[display_cols].to_string(index=False))
    print("=" * 95)

    # Save summary CSV
    df_summary[display_cols].to_csv(os.path.join(output_dir, "policy_comparison_summary.csv"), index=False)

    # -------------------------------------------------------------
    # Plot Trajectories
    # -------------------------------------------------------------
    _plot_trajectories(policy_trajectories, n_steps, output_dir)
    _plot_bar_comparison(df_summary, output_dir)

    print(f"\n[OK] Results and figures successfully saved to '{output_dir}/'.")
    return df_summary, policy_trajectories


def _plot_trajectories(trajectories, n_steps, output_dir):
    """Plots multi-panel time-series dynamics for all policies."""
    palette = {
        "Static Audit Policy": "#e74c3c",          # Red
        "Proportional Adaptive Policy": "#e67e22",  # Orange
        "PID Adaptive Policy": "#2ecc71",           # Emerald Green
        "Risk-Targeted Policy": "#9b59b6",          # Amethyst Purple
        "Budget-Constrained Policy": "#3498db",     # Blue
    }

    steps = np.arange(n_steps)
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=True)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # 1. Compliance Rate
    ax1 = axes[0]
    for name, data in trajectories.items():
        ax1.plot(steps, data["compliance"], label=name, color=palette.get(name, "black"), lw=2.2)
    ax1.set_ylabel("Compliance Rate (x)", fontsize=12, fontweight="bold")
    ax1.set_title("Evolutionary Taxpayer Compliance Dynamics Under Different Policies", fontsize=14, fontweight="bold", pad=10)
    ax1.set_ylim(-0.02, 1.05)
    ax1.axhline(1.0, color="gray", linestyle=":", alpha=0.5)
    ax1.legend(loc="lower right", frameon=True, framealpha=0.9)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # 2. Audit Intensity
    ax2 = axes[1]
    for name, data in trajectories.items():
        ax2.plot(steps, data["alpha"], label=name, color=palette.get(name, "black"), lw=2.0)
    ax2.set_ylabel("Audit Intensity (α)", fontsize=12, fontweight="bold")
    ax2.set_title("Tax Authority Adaptive Audit Intensity Over Time", fontsize=13, fontweight="bold")
    ax2.set_ylim(0.0, 1.0)
    ax2.grid(True, linestyle="--", alpha=0.6)

    # 3. Net Revenue per Period
    ax3 = axes[2]
    for name, data in trajectories.items():
        ax3.plot(steps, data["net_revenue"], label=name, color=palette.get(name, "black"), lw=2.0)
    ax3.set_ylabel("Net Gov Revenue ($)", fontsize=12, fontweight="bold")
    ax3.set_xlabel("Evolutionary Time Steps (t)", fontsize=12, fontweight="bold")
    ax3.set_title("Net Government Revenue (Taxes + Fines - Enforcement Cost)", fontsize=13, fontweight="bold")
    ax3.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, "policy_comparison_trajectories.png")
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {fig_path}")


def _plot_bar_comparison(df_summary, output_dir):
    """Plots comparative bar charts of key metrics."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    names = df_summary["Enforcement Policy"].apply(lambda s: s.replace(" Policy", "")).tolist()
    colors = ["#e74c3c", "#e67e22", "#2ecc71", "#9b59b6", "#3498db"]

    # 1. Final Compliance
    axes[0].bar(names, df_summary["_final_comp"] * 100, color=colors, edgecolor="black", alpha=0.85)
    axes[0].set_title("Steady-State Compliance (%)", fontsize=12, fontweight="bold")
    axes[0].set_ylabel("Compliance Rate (%)", fontsize=11)
    axes[0].set_ylim(0, 105)
    axes[0].tick_params(axis="x", rotation=30)
    for i, v in enumerate(df_summary["_final_comp"] * 100):
        axes[0].text(i, v + 2, f"{v:.1f}%", ha="center", fontweight="bold", fontsize=10)

    # 2. Total Net Revenue
    axes[1].bar(names, df_summary["_total_net"] / 1000, color=colors, edgecolor="black", alpha=0.85)
    axes[1].set_title("Cumulative Net Revenue ($k)", fontsize=12, fontweight="bold")
    axes[1].set_ylabel("Net Revenue ($ in thousands)", fontsize=11)
    axes[1].tick_params(axis="x", rotation=30)
    for i, v in enumerate(df_summary["_total_net"] / 1000):
        axes[1].text(i, v + 15, f"${v:,.0f}k", ha="center", fontweight="bold", fontsize=10)

    # 3. Enforcement Cost
    axes[2].bar(names, df_summary["_total_cost"] / 1000, color=colors, edgecolor="black", alpha=0.85)
    axes[2].set_title("Cumulative Enforcement Cost ($k)", fontsize=12, fontweight="bold")
    axes[2].set_ylabel("Cost ($ in thousands)", fontsize=11)
    axes[2].tick_params(axis="x", rotation=30)
    for i, v in enumerate(df_summary["_total_cost"] / 1000):
        axes[2].text(i, v + 5, f"${v:,.0f}k", ha="center", fontweight="bold", fontsize=10)

    plt.tight_layout()
    bar_path = os.path.join(output_dir, "policy_bar_metrics.png")
    fig.savefig(bar_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {bar_path}")


if __name__ == "__main__":
    run_comparative_experiment()
