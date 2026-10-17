"""
enforcement_policies.py - Adaptive Auditing Enforcement Policies for Tax Authority.
"""

from abc import ABC, abstractmethod
import numpy as np


class BaseEnforcementPolicy(ABC):
    """Abstract base class for Tax Authority enforcement policies."""

    def __init__(self, name: str, alpha_min: float = 0.02, alpha_max: float = 0.95):
        self.name = name
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max

    @abstractmethod
    def get_audit_intensity(self, step: int, observed_evasion: float, **kwargs) -> float:
        """Computes audit intensity alpha in [alpha_min, alpha_max] for the current step."""
        pass

    def reset(self):
        """Resets any internal states for a fresh simulation run."""
        pass


class StaticAuditPolicy(BaseEnforcementPolicy):
    """
    Policy 1: Static / Fixed Audit Intensity (Benchmark).
    Maintains a constant audit probability regardless of evasion rate.
    """

    def __init__(self, fixed_alpha: float = 0.35, **kwargs):
        super().__init__(name="Static Audit Policy", **kwargs)
        self.fixed_alpha = float(fixed_alpha)

    def get_audit_intensity(self, step: int, observed_evasion: float, **kwargs) -> float:
        return np.clip(self.fixed_alpha, self.alpha_min, self.alpha_max)


class ProportionalAdaptivePolicy(BaseEnforcementPolicy):
    """
    Policy 2: Proportional / Reactive Adaptive Audit.
    Auditing intensity increases when observed evasion rises and decreases
    when evasion falls:
    alpha_{t+1} = clip(alpha_t + k_p * (observed_evasion - target_evasion), alpha_min, alpha_max)
    """

    def __init__(self, initial_alpha: float = 0.35, k_p: float = 0.30, target_evasion: float = 0.05, **kwargs):
        super().__init__(name="Proportional Adaptive Policy", **kwargs)
        self.initial_alpha = initial_alpha
        self.current_alpha = initial_alpha
        self.k_p = k_p
        self.target_evasion = target_evasion

    def reset(self):
        self.current_alpha = self.initial_alpha

    def get_audit_intensity(self, step: int, observed_evasion: float, **kwargs) -> float:
        if step == 0:
            return self.current_alpha

        error = observed_evasion - self.target_evasion
        self.current_alpha = np.clip(
            self.current_alpha + self.k_p * error,
            self.alpha_min,
            self.alpha_max
        )
        return float(self.current_alpha)


class PIDAdaptivePolicy(BaseEnforcementPolicy):
    """
    Policy 3: PID (Proportional-Integral-Derivative) Control Policy.
    Eliminates steady-state error and dampens inspection game limit cycles:
    u(t) = K_p * e(t) + K_i * sum(e(tau)) + K_d * (e(t) - e(t-1))
    """

    def __init__(
        self,
        base_alpha: float = 0.35,
        k_p: float = 0.40,
        k_i: float = 0.08,
        k_d: float = 0.15,
        target_evasion: float = 0.02,
        **kwargs
    ):
        super().__init__(name="PID Adaptive Policy", **kwargs)
        self.base_alpha = base_alpha
        self.k_p = k_p
        self.k_i = k_i
        self.k_d = k_d
        self.target_evasion = target_evasion
        self.reset()

    def reset(self):
        self.integral_error = 0.0
        self.prev_error = 0.0

    def get_audit_intensity(self, step: int, observed_evasion: float, **kwargs) -> float:
        error = observed_evasion - self.target_evasion
        self.integral_error += error
        # Anti-windup clamping on integral term
        self.integral_error = np.clip(self.integral_error, -5.0, 5.0)

        derivative = (error - self.prev_error) if step > 0 else 0.0
        self.prev_error = error

        control = self.base_alpha + (self.k_p * error) + (self.k_i * self.integral_error) + (self.k_d * derivative)
        return float(np.clip(control, self.alpha_min, self.alpha_max))


class RiskTargetedPolicy(BaseEnforcementPolicy):
    """
    Policy 4: Risk-Targeted / Memory-Based Audit Policy.
    Audits flagged individuals (those caught evading recently) with higher intensity
    alpha_flagged, while clean/compliant individuals face baseline alpha_clean.
    Aggregate alpha is dynamically computed as:
    alpha_agg = (n_flagged * alpha_flagged + n_clean * alpha_clean) / N
    """

    def __init__(
        self,
        alpha_clean: float = 0.10,
        alpha_flagged: float = 0.85,
        probation_periods: int = 5,
        **kwargs
    ):
        super().__init__(name="Risk-Targeted Policy", **kwargs)
        self.alpha_clean = alpha_clean
        self.alpha_flagged = alpha_flagged
        self.probation_periods = probation_periods

    def get_audit_intensity(self, step: int, observed_evasion: float, **kwargs) -> float:
        flagged_fraction = kwargs.get("flagged_fraction", observed_evasion)
        flagged_fraction = np.clip(flagged_fraction, 0.0, 1.0)

        aggregate_alpha = (flagged_fraction * self.alpha_flagged) + ((1.0 - flagged_fraction) * self.alpha_clean)
        return float(np.clip(aggregate_alpha, self.alpha_min, self.alpha_max))

    def get_individual_audit_prob(self, is_flagged: bool) -> float:
        return self.alpha_flagged if is_flagged else self.alpha_clean


class BudgetConstrainedPolicy(BaseEnforcementPolicy):
    """
    Policy 5: Budget-Constrained Revenue-Allocated Audit Policy.
    The audit authority allocates a proportion of its collected tax and fine revenue
    into the audit enforcement budget:
    Max Audits = Budget / Cost_per_audit
    Ensures the enforcement apparatus never incurs a net fiscal deficit.
    """

    def __init__(
        self,
        budget_fraction: float = 0.25,
        target_desired_alpha: float = 0.60,
        c_a: float = 8.0,
        **kwargs
    ):
        super().__init__(name="Budget-Constrained Policy", **kwargs)
        self.budget_fraction = budget_fraction
        self.target_desired_alpha = target_desired_alpha
        self.c_a = c_a
        self.prev_revenue = 1000.0  # Initial warm-up revenue buffer

    def reset(self):
        self.prev_revenue = 1000.0

    def get_audit_intensity(self, step: int, observed_evasion: float, **kwargs) -> float:
        prev_gross_revenue = kwargs.get("prev_revenue", self.prev_revenue)
        n_taxpayers = kwargs.get("n_taxpayers", 1000)

        # Budget available for audits
        budget = max(prev_gross_revenue * self.budget_fraction, 50.0)
        max_affordable_audits = budget / self.c_a
        max_affordable_alpha = max_affordable_audits / n_taxpayers

        # Evasion-responsive desired alpha
        desired_alpha = self.alpha_min + (self.target_desired_alpha - self.alpha_min) * observed_evasion

        # Actual alpha is constrained by budget
        actual_alpha = min(desired_alpha, max_affordable_alpha)
        return float(np.clip(actual_alpha, self.alpha_min, self.alpha_max))
