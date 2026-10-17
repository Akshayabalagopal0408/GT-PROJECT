"""
payoff.py - Game-Theoretic Payoff Matrix and Expected Utility Calculations
for Taxpayer vs. Tax Authority Inspection Game.
"""

import numpy as np


class TaxEvasionGame:
    """
    Formal 2x2 Inspection Game between Taxpayers (Population) and Tax Authority.
    
    Parameters:
    -----------
    W : float
        Gross taxable income (default = 100.0).
    t : float
        Tax rate, t in (0, 1) (default = 0.30).
    f : float
        Fine / penalty multiplier on evaded tax (default = 1.5).
        Caught evaders pay owed tax (t*W) plus fine (f*t*W).
    c_a : float
        Cost incurred by the tax authority per audit (default = 8.0).
    """

    def __init__(self, W: float = 100.0, t: float = 0.30, f: float = 1.5, c_a: float = 8.0):
        if not (0 < t < 1):
            raise ValueError("Tax rate 't' must be in (0, 1).")
        if f <= 0:
            raise ValueError("Fine rate 'f' must be greater than 0.")
        if c_a <= 0:
            raise ValueError("Audit cost 'c_a' must be greater than 0.")
        if W <= 0:
            raise ValueError("Income 'W' must be greater than 0.")

        self.W = float(W)
        self.t = float(t)
        self.f = float(f)
        self.c_a = float(c_a)

    @property
    def owed_tax(self) -> float:
        """Standard tax liability: t * W."""
        return self.t * self.W

    @property
    def penalty_amount(self) -> float:
        """Penalty on detected evasion: f * t * W."""
        return self.f * self.t * self.W

    @property
    def total_caught_liability(self) -> float:
        """Total paid by caught evader: owed tax + penalty = (1 + f) * t * W."""
        return (1.0 + self.f) * self.t * self.W

    # -------------------------------------------------------------
    # 2x2 Payoff Matrix: (Taxpayer Payoff, Authority Net Revenue)
    # -------------------------------------------------------------
    def payoff_matrix(self):
        """
        Returns the 2x2 strategic payoff matrix:
        Rows: Taxpayer strategies [Comply (C), Evade (E)]
        Cols: Authority strategies [Audit (A), No Audit (NA)]
        
        Returns:
            dict of {(Taxpayer_Strat, Authority_Strat): (payoff_T, payoff_A)}
        """
        return {
            ("C", "A"):  (self.W * (1.0 - self.t), self.owed_tax - self.c_a),
            ("C", "NA"): (self.W * (1.0 - self.t), self.owed_tax),
            ("E", "A"):  (self.W - self.total_caught_liability, self.total_caught_liability - self.c_a),
            ("E", "NA"): (self.W, 0.0),
        }

    # -------------------------------------------------------------
    # Expected Payoffs given compliance rate x and audit intensity alpha
    # -------------------------------------------------------------
    def expected_taxpayer_payoffs(self, alpha: float):
        """
        Expected payoff for Taxpayer strategies given audit probability alpha:
        U_C = W * (1 - t)
        U_E(alpha) = alpha * (W - (1 + f)*t*W) + (1 - alpha) * W
                   = W - alpha * (1 + f) * t * W
        """
        alpha = np.clip(alpha, 0.0, 1.0)
        u_c = self.W * (1.0 - self.t)
        u_e = self.W - alpha * self.total_caught_liability
        delta_u = u_c - u_e  # Positive => Comply is fitter
        return u_c, u_e, delta_u

    def average_taxpayer_payoff(self, x: float, alpha: float):
        """Average population fitness bar{U} = x * U_C + (1 - x) * U_E."""
        u_c, u_e, _ = self.expected_taxpayer_payoffs(alpha)
        return x * u_c + (1.0 - x) * u_e

    def expected_authority_payoff(self, x: float, alpha: float):
        """
        Expected Authority net revenue per taxpayer:
        Gross Revenue = x * t * W + (1 - x) * alpha * (1 + f) * t * W
        Enforcement Cost = alpha * c_a
        Net Revenue = Gross Revenue - Enforcement Cost
        """
        x = np.clip(x, 0.0, 1.0)
        alpha = np.clip(alpha, 0.0, 1.0)

        # Revenue from compliant taxpayers
        rev_compliant = x * self.owed_tax
        # Revenue from audited evaders (back taxes + fines)
        rev_evaders = (1.0 - x) * alpha * self.total_caught_liability
        gross_rev = rev_compliant + rev_evaders
        cost = alpha * self.c_a
        net_rev = gross_rev - cost
        return gross_rev, cost, net_rev

    # -------------------------------------------------------------
    # Theoretical Thresholds & Nash Equilibrium
    # -------------------------------------------------------------
    @property
    def alpha_star(self) -> float:
        """
        Deterrence Audit Threshold (alpha*):
        The audit probability where taxpayer is indifferent between Comply and Evade:
        alpha* = 1 / (1 + f).
        If alpha > alpha*, Compliance strictly dominates in fitness.
        """
        return 1.0 / (1.0 + self.f)

    @property
    def x_star(self) -> float:
        """
        Indifference Compliance Threshold (x*):
        The compliance share where authority marginal gain of audit equals audit cost:
        (1 - x*) * (1 + f) * t * W = c_a
        x* = 1 - c_a / [(1 + f) * t * W]
        """
        threshold = 1.0 - (self.c_a / self.total_caught_liability)
        return float(np.clip(threshold, 0.0, 1.0))

    def summary(self) -> str:
        return (
            f"Tax Evasion Inspection Game Parameters:\n"
            f"  Income (W)                 : {self.W:.2f}\n"
            f"  Tax Rate (t)               : {self.t:.2%}\n"
            f"  Fine Multiplier (f)        : {self.f:.2f}\n"
            f"  Audit Cost (c_a)           : {self.c_a:.2f}\n"
            f"  Owed Tax (t*W)             : {self.owed_tax:.2f}\n"
            f"  Total Caught Fine+Tax      : {self.total_caught_liability:.2f}\n"
            f"  Critical Audit Rate (alpha*) : {self.alpha_star:.4f} ({self.alpha_star:.2%})\n"
            f"  Critical Compliance (x*)   : {self.x_star:.4f} ({self.x_star:.2%})\n"
        )
