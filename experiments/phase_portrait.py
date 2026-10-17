"""
phase_portrait.py - Phase Plane Analysis and Vector Field Visualization
for Continuous Replicator Dynamics (Inspection Game vs. Adaptive Auditing).
"""

import os
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
import matplotlib.pyplot as plt
from model.payoff import TaxEvasionGame
from model.continuous_dynamics import ReplicatorDynamicsSimulation


def generate_phase_portraits(output_dir: str = "output"):
    os.makedirs(output_dir, exist_ok=True)
    game = TaxEvasionGame(W=100.0, t=0.30, f=1.5, c_a=8.0)
    sim = ReplicatorDynamicsSimulation(game=game, learning_rate=0.8)

    x_star = game.x_star
    alpha_star = game.alpha_star

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    # =========================================================================
    # Panel 1: Classic Co-evolutionary Inspection Game (Undamped Periodic Cycles)
    # =========================================================================
    ax1 = axes[0]
    X, Alpha, U, V = sim.compute_phase_field(grid_points=24, mode="coevolution")

    # Normalize vectors for clear directional quiver/stream
    speed = np.sqrt(U**2 + V**2)
    speed[speed == 0] = 1.0
    ax1.streamplot(
        X[0, :], Alpha[:, 0], U, V,
        color="#7f8c8d", density=1.2, linewidth=1.0, arrowsize=1.2
    )

    # Plot sample trajectory cycles from various starting points
    initial_conditions = [
        (0.60, 0.20),
        (0.75, 0.25),
        (0.85, 0.15),
        (0.50, 0.50),
    ]
    colors = ["#e74c3c", "#e67e22", "#3498db", "#9b59b6"]
    for idx, (x0, a0) in enumerate(initial_conditions):
        sol = sim.solve_trajectory(x0=x0, alpha0=a0, t_span=(0, 60), num_points=1200, mode="coevolution")
        ax1.plot(sol["compliance"], sol["alpha"], color=colors[idx], lw=2.2, label=f"Trajectory (x0={x0}, a0={a0})")
        ax1.plot(x0, a0, "o", color=colors[idx], markersize=6)

    # Mark Interior Equilibrium (x*, alpha*)
    ax1.plot(x_star, alpha_star, "r*", markersize=14, label=f"Center (x*={x_star:.2f}, alpha*={alpha_star:.2f})")
    ax1.axvline(x_star, color="crimson", linestyle="--", alpha=0.5, label="x* Nullcline")
    ax1.axhline(alpha_star, color="navy", linestyle="--", alpha=0.5, label="alpha* Nullcline")

    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.set_xlabel("Taxpayer Compliance Share (x)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Authority Audit Intensity (alpha)", fontsize=12, fontweight="bold")
    ax1.set_title("A. Standard Inspection Game\n(Periodic Lotka-Volterra Closed Orbits)", fontsize=13, fontweight="bold")
    ax1.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
    ax1.grid(True, linestyle="--", alpha=0.6)

    # =========================================================================
    # Panel 2: Adaptive Auditing Policy (Stabilizing Spiral / Sink)
    # =========================================================================
    ax2 = axes[1]
    X2, Alpha2, U2, V2 = sim.compute_phase_field(grid_points=24, mode="adaptive")
    ax2.streamplot(
        X2[0, :], Alpha2[:, 0], U2, V2,
        color="#7f8c8d", density=1.2, linewidth=1.0, arrowsize=1.2
    )

    for idx, (x0, a0) in enumerate(initial_conditions):
        sol = sim.solve_trajectory(x0=x0, alpha0=a0, t_span=(0, 60), num_points=1200, mode="adaptive")
        ax2.plot(sol["compliance"], sol["alpha"], color=colors[idx], lw=2.2, label=f"Adaptive Path (x0={x0}, a0={a0})")
        ax2.plot(x0, a0, "o", color=colors[idx], markersize=6)
        # End point
        ax2.plot(sol["compliance"][-1], sol["alpha"][-1], "s", color=colors[idx], markersize=7)

    target_compliance = 0.95
    ax2.axvline(target_compliance, color="green", linestyle="--", alpha=0.7, label=f"Target Compliance ({target_compliance:.0%})")
    ax2.axhline(alpha_star, color="navy", linestyle="--", alpha=0.5, label="alpha* Deterrence Level")

    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.set_xlabel("Taxpayer Compliance Share (x)", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Authority Audit Intensity (alpha)", fontsize=12, fontweight="bold")
    ax2.set_title("B. Adaptive Enforcement Policy\n(Asymptotic Convergence to High Compliance)", fontsize=13, fontweight="bold")
    ax2.legend(loc="upper left", fontsize=8.5, framealpha=0.9)
    ax2.grid(True, linestyle="--", alpha=0.6)

    plt.tight_layout()
    fig_path = os.path.join(output_dir, "phase_portraits.png")
    fig.savefig(fig_path, dpi=300)
    plt.close(fig)
    print(f"[OK] Phase portraits saved to: {fig_path}")


if __name__ == "__main__":
    generate_phase_portraits()
