"""
empirical_country_comparison.py - Cross-National Simulation of Real Tax Administrations.
Calibrated using OECD ISORA, World Bank Enterprise Surveys, and IRS Tax Gap Data.
Compares Static / Observed Audit Coverage vs. PID Adaptive Feedback Enforcement.
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from model.empirical_loader import EmpiricalTaxDataLoader
from model.enforcement_policies import StaticAuditPolicy, PIDAdaptivePolicy
from model.agent_based_model import AgentBasedTaxModel


def run_empirical_country_study(
    countries: list = None,
    n_agents: int = 1000,
    n_steps: int = 120,
    n_runs: int = 3,
    output_dir: str = "output"
):
    os.makedirs(output_dir, exist_ok=True)
    loader = EmpiricalTaxDataLoader()

    if countries is None:
        countries = ["USA", "DEU", "ITA", "IND", "BRA", "OECD_AVG"]

    print("=" * 85)
    print("EMPIRICAL COUNTRY SIMULATION: REAL-WORLD OECD & WORLD BANK CALIBRATIONS")
    print("=" * 85)

    records = []
    country_trajectories = {}

    for ccode in countries:
        cdata = loader.build_game_for_country(ccode)
        cname = cdata["country_name"]
        game = cdata["game"]
        real_pi = cdata["real_audit_coverage"]
        beta = cdata["declared_beta"]
        alpha_eff = cdata["detection_efficacy"]

        print(f"\n--> Simulating Country: {cname} ({ccode})")
        print(f"    Tax Rate (tau)={game.t:.1%}, Declared (beta)={beta:.1%}, Fine (phi)={game.f:.2f}x, Obs Audit={real_pi:.1%}")
        print(f"    Critical Indifference Threshold alpha*: {game.alpha_star:.1%}")

        # Policy 1: Real-World Observed / Static Audit Intensity
        pol_observed = StaticAuditPolicy(fixed_alpha=real_pi)

        # Policy 2: PID Adaptive Control Policy (Country-Calibrated)
        pol_pid = PIDAdaptivePolicy(
            base_alpha=max(real_pi, 0.10),
            k_p=0.45,
            k_i=0.08,
            k_d=0.20,
            target_evasion=max(1.0 - beta, 0.05) * 0.3  # Ambition: cut evasion gap by 70%
        )

        country_trajectories[ccode] = {"name": cname, "observed": [], "pid": []}

        for pol_type, pol in [("Observed / Static", pol_observed), ("PID Adaptive", pol_pid)]:
            runs_comp = []
            runs_rev = []
            runs_cost = []

            for r in range(n_runs):
                model = AgentBasedTaxModel(
                    n_agents=n_agents,
                    game=game,
                    policy=pol,
                    initial_compliance=beta,  # Initial compliance set to real declared fraction
                    temperature=8.0,
                    mutation_rate=0.005,
                    seed=42 + (r * 100)
                )
                hist = model.run_simulation(n_steps=n_steps)
                runs_comp.append(hist["compliance_rate"])
                runs_rev.append(hist["net_revenue"])
                runs_cost.append(hist["enforcement_cost"])

            mean_comp = np.mean(runs_comp, axis=0)
            mean_rev = np.mean(runs_rev, axis=0)
            mean_cost = np.mean(runs_cost, axis=0)

            final_compliance = float(np.mean(mean_comp[-20:]))
            volatility = float(np.std(mean_comp[-20:]))
            total_net_rev = float(np.sum(mean_rev))
            total_cost = float(np.sum(mean_cost))

            country_trajectories[ccode]["observed" if "Observed" in pol_type else "pid"] = mean_comp

            records.append({
                "Country": cname,
                "Code": ccode,
                "Statutory Tax": f"{game.t:.1%}",
                "Declared Share": f"{beta:.1%}",
                "Observed Audit": f"{real_pi:.1%}",
                "Policy Mode": pol_type,
                "Final Compliance": f"{final_compliance:.1%}",
                "Stability (std)": f"{volatility:.3f}",
                "Total Net Revenue ($)": f"{total_net_rev:,.0f}",
                "Total Audit Cost ($)": f"{total_cost:,.0f}",
                "_final_comp": final_compliance,
                "_net_rev": total_net_rev,
                "_policy": pol_type,
                "_code": ccode
            })

    df_summary = pd.DataFrame(records)
    display_cols = [c for c in df_summary.columns if not c.startswith("_")]

    print("\n" + "=" * 95)
    print("EMPIRICAL COUNTRY SIMULATION SUMMARY TABLE")
    print("=" * 95)
    print(df_summary[display_cols].to_string(index=False))
    print("=" * 95)

    csv_out = os.path.join(output_dir, "empirical_country_comparison.csv")
    df_summary[display_cols].to_csv(csv_out, index=False)
    print(f"\n[OK] Empirical summary table saved to: {csv_out}")

    # Generate Visualization
    _plot_empirical_results(country_trajectories, df_summary, output_dir)
    return df_summary


def _plot_empirical_results(trajectories, df_summary, output_dir):
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    axes = axes.flatten()

    codes = list(trajectories.keys())
    for idx, ccode in enumerate(codes):
        ax = axes[idx]
        data = trajectories[ccode]
        cname = data["name"]

        ax.plot(data["observed"], label="Observed Status Quo Audit", color="#e74c3c", lw=2.5, linestyle="--")
        ax.plot(data["pid"], label="Calibrated PID Adaptive Audit", color="#2ecc71", lw=2.5)

        ax.set_title(f"{cname} ({ccode})", fontsize=13, fontweight="bold")
        ax.set_xlabel("Simulation Rounds", fontsize=10)
        ax.set_ylabel("Tax Compliance Rate", fontsize=10)
        ax.set_ylim(-0.05, 1.05)
        ax.axhline(0.5, color="#bdc3c7", linestyle=":", alpha=0.6)
        ax.legend(loc="lower right" if np.mean(data["pid"][-20:]) > 0.5 else "upper right", fontsize=8.5)
        ax.grid(True, linestyle="--", alpha=0.5)

    plt.suptitle("Empirical Cross-National Tax Evasion Simulations\nStatus Quo Audit Coverage vs. Calibrated PID Adaptive Control", fontsize=15, fontweight="bold", y=1.02)
    plt.tight_layout()

    fig_path = os.path.join(output_dir, "empirical_country_comparison.png")
    fig.savefig(fig_path, dpi=300, bbox_inches="tight")
    print(f"[OK] Empirical multi-country plot saved to: {fig_path}")


if __name__ == "__main__":
    run_empirical_country_study()
