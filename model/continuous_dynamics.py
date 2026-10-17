"""
continuous_dynamics.py - Continuous ODE Replicator Dynamics Solver and Phase Field Analysis.
"""

import numpy as np
from scipy.integrate import solve_ivp
from .payoff import TaxEvasionGame


class ReplicatorDynamicsSimulation:
    """
    Simulates continuous evolutionary game dynamics for Taxpayer compliance share x(t)
    and Authority audit intensity alpha(t).
    
    System Equations:
    -----------------
    dx/dt = x * (1 - x) * [U_C - U_E(alpha)]
          = x * (1 - x) * [t * W * (alpha * (1 + f) - 1)]
    
    For Co-evolutionary inspection game:
    d(alpha)/dt = alpha * (1 - alpha) * [(1 - x) * t * W * (1 + f) - c_a]
    """

    def __init__(self, game: TaxEvasionGame = None, learning_rate: float = 1.0):
        self.game = game or TaxEvasionGame()
        self.learning_rate = learning_rate

    def ode_system_coevolution(self, t_eval, state):
        """Standard 2D co-evolutionary replicator dynamics (Lotka-Volterra type)."""
        x, alpha = state
        x = np.clip(x, 1e-6, 1.0 - 1e-6)
        alpha = np.clip(alpha, 1e-6, 1.0 - 1e-6)

        # Taxpayer payoff difference
        delta_u_taxpayer = self.game.owed_tax * (alpha * (1.0 + self.game.f) - 1.0)
        dxdt = self.learning_rate * x * (1.0 - x) * delta_u_taxpayer

        # Authority marginal audit payoff
        delta_u_authority = (1.0 - x) * self.game.total_caught_liability - self.game.c_a
        dalphadt = self.learning_rate * alpha * (1.0 - alpha) * delta_u_authority

        return [dxdt, dalphadt]

    def ode_system_adaptive_proportional(self, t_eval, state, target_evasion=0.05, speed=1.5):
        """Replicator dynamics with proportional feedback control on audit rate."""
        x, alpha = state
        x = np.clip(x, 1e-6, 1.0 - 1e-6)
        alpha = np.clip(alpha, 0.01, 0.99)

        # Taxpayer replicator equation
        delta_u_taxpayer = self.game.owed_tax * (alpha * (1.0 + self.game.f) - 1.0)
        dxdt = self.learning_rate * x * (1.0 - x) * delta_u_taxpayer

        # Adaptive authority: increases alpha if evasion (1 - x) > target_evasion
        evasion = 1.0 - x
        dalphadt = speed * (evasion - target_evasion)
        # Boundary damping
        if (alpha >= 0.95 and dalphadt > 0) or (alpha <= 0.05 and dalphadt < 0):
            dalphadt = 0.0

        return [dxdt, dalphadt]

    def solve_trajectory(
        self,
        x0: float = 0.50,
        alpha0: float = 0.30,
        t_span: tuple = (0, 50),
        num_points: int = 1000,
        mode: str = "coevolution",
        target_evasion: float = 0.05,
    ):
        """
        Integrates the system of ODEs from initial condition (x0, alpha0).
        
        Returns:
            dict containing time array, x array, alpha array, revenue, and cost.
        """
        t_eval = np.linspace(t_span[0], t_span[1], num_points)

        if mode == "coevolution":
            func = self.ode_system_coevolution
        elif mode == "adaptive":
            func = lambda t, s: self.ode_system_adaptive_proportional(t, s, target_evasion=target_evasion)
        else:
            raise ValueError(f"Unknown mode '{mode}'. Choose 'coevolution' or 'adaptive'.")

        sol = solve_ivp(
            func,
            t_span,
            [x0, alpha0],
            t_eval=t_eval,
            method="RK45",
            rtol=1e-6,
            atol=1e-8
        )

        x_traj = np.clip(sol.y[0], 0.0, 1.0)
        alpha_traj = np.clip(sol.y[1], 0.0, 1.0)

        gross_rev, cost, net_rev = self.game.expected_authority_payoff(x_traj, alpha_traj)

        return {
            "t": sol.t,
            "compliance": x_traj,
            "evasion": 1.0 - x_traj,
            "alpha": alpha_traj,
            "gross_revenue": gross_rev,
            "enforcement_cost": cost,
            "net_revenue": net_rev,
        }

    def compute_phase_field(self, grid_points: int = 25, mode: str = "coevolution"):
        """
        Computes 2D vector field (dx/dt, dalpha/dt) across [0, 1] x [0, 1] grid.
        Useful for quiver plots, streamplots, and phase portraits.
        """
        x_vals = np.linspace(0.01, 0.99, grid_points)
        alpha_vals = np.linspace(0.01, 0.99, grid_points)
        X, Alpha = np.meshgrid(x_vals, alpha_vals)

        U = np.zeros_like(X)
        V = np.zeros_like(Alpha)

        for i in range(grid_points):
            for j in range(grid_points):
                state = [X[i, j], Alpha[i, j]]
                if mode == "coevolution":
                    derivs = self.ode_system_coevolution(0, state)
                else:
                    derivs = self.ode_system_adaptive_proportional(0, state)
                U[i, j] = derivs[0]
                V[i, j] = derivs[1]

        return X, Alpha, U, V
