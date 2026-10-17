"""
agent_based_model.py - Agent-Based Monte Carlo Simulation of Taxpayer Population
with Evolutionary Strategy Learning (Fermi Rule) and Adaptive Auditing.
"""

import numpy as np
from typing import Dict, Any, Optional
from .payoff import TaxEvasionGame
from .enforcement_policies import BaseEnforcementPolicy, RiskTargetedPolicy


class AgentBasedTaxModel:
    """
    Micro-founded Agent-Based Evolutionary Model.
    
    Each agent represents a taxpayer who chooses to either Comply (1) or Evade (0).
    Taxpayers learn and evolve their strategies over time using the Fermi update rule
    (pairwise comparison / social imitation).
    
    Parameters:
    -----------
    n_agents : int
        Number of taxpayers in the population (default = 1000).
    game : TaxEvasionGame
        Core game payoff instance.
    policy : BaseEnforcementPolicy
        Enforcement policy deployed by the Tax Authority.
    initial_compliance : float
        Initial fraction of compliant taxpayers in [0, 1] (default = 0.50).
    temperature : float
        Noise / selection temperature for Fermi imitation rule (default = 10.0).
    mutation_rate : float
        Probability of spontaneous strategy experimentation (default = 0.01).
    heterogeneous_income : bool
        If True, taxpayer incomes follow a LogNormal distribution; else homogeneous W.
    seed : Optional[int]
        Random seed for reproducibility.
    """

    def __init__(
        self,
        n_agents: int = 1000,
        game: Optional[TaxEvasionGame] = None,
        policy: Optional[BaseEnforcementPolicy] = None,
        initial_compliance: float = 0.50,
        temperature: float = 10.0,
        mutation_rate: float = 0.01,
        heterogeneous_income: bool = False,
        seed: Optional[int] = None,
    ):
        self.n_agents = n_agents
        self.game = game or TaxEvasionGame()
        self.policy = policy
        self.initial_compliance = float(initial_compliance)
        self.temperature = float(temperature)
        self.mutation_rate = float(mutation_rate)
        self.heterogeneous_income = heterogeneous_income
        self.rng = np.random.default_rng(seed)

        self._initialize_population()

    def _initialize_population(self):
        """Initializes agent strategies, incomes, and audit states."""
        # 1 = Comply, 0 = Evade
        n_comply = int(self.initial_compliance * self.n_agents)
        strategies = np.zeros(self.n_agents, dtype=np.int32)
        strategies[:n_comply] = 1
        self.rng.shuffle(strategies)
        self.strategies = strategies

        # Incomes
        if self.heterogeneous_income:
            # LogNormal with mean ~ W
            sigma = 0.35
            mu = np.log(self.game.W) - 0.5 * (sigma ** 2)
            self.incomes = self.rng.lognormal(mean=mu, sigma=sigma, size=self.n_agents)
        else:
            self.incomes = np.full(self.n_agents, self.game.W, dtype=np.float64)

        # Risk-Targeted state tracking
        self.is_flagged = np.zeros(self.n_agents, dtype=bool)
        self.flag_timer = np.zeros(self.n_agents, dtype=np.int32)

        # Individual statistics
        self.lifetime_audits = np.zeros(self.n_agents, dtype=np.int32)
        self.lifetime_caught = np.zeros(self.n_agents, dtype=np.int32)

        # Payoffs in the current step
        self.payoffs = np.zeros(self.n_agents, dtype=np.float64)

        if self.policy:
            self.policy.reset()

    def step(self, current_step: int, prev_metrics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Executes one full evolutionary period:
        1. Tax authority determines audit probabilities.
        2. Audits are executed and payoffs realized.
        3. Taxpayers update strategies via social imitation (Fermi rule).
        4. Performance metrics are recorded.
        """
        observed_evasion = 1.0 - (np.sum(self.strategies) / self.n_agents)
        flagged_fraction = float(np.mean(self.is_flagged))
        prev_rev = prev_metrics["gross_revenue"] if prev_metrics else (self.n_agents * self.game.owed_tax * 0.5)

        # 1. Determine audit intensity per agent
        if isinstance(self.policy, RiskTargetedPolicy):
            # Individual risk-based audit probabilities
            p_audit = np.where(
                self.is_flagged,
                self.policy.alpha_flagged,
                self.policy.alpha_clean
            )
            audit_intensity = float(np.mean(p_audit))
        elif self.policy is not None:
            audit_intensity = self.policy.get_audit_intensity(
                step=current_step,
                observed_evasion=observed_evasion,
                flagged_fraction=flagged_fraction,
                prev_revenue=prev_rev,
                n_taxpayers=self.n_agents
            )
            p_audit = np.full(self.n_agents, audit_intensity)
        else:
            audit_intensity = 0.35
            p_audit = np.full(self.n_agents, audit_intensity)

        # 2. Realize Audits (Monte Carlo sampling)
        audited_mask = self.rng.random(self.n_agents) < p_audit
        self.lifetime_audits += audited_mask.astype(np.int32)

        # 3. Compute Payoffs and Government Collections
        # Tax liabilities
        owed_taxes = self.game.t * self.incomes
        penalty_multipliers = 1.0 + self.game.f

        # Taxpayers who comply
        comply_mask = (self.strategies == 1)
        evade_mask = (self.strategies == 0)

        # Caught evaders: evaded AND audited
        caught_mask = evade_mask & audited_mask
        self.lifetime_caught += caught_mask.astype(np.int32)

        # Uncaught evaders: evaded AND NOT audited
        uncaught_mask = evade_mask & (~audited_mask)

        # Taxpayer payoff allocation
        # Comply: W_i * (1 - t)
        self.payoffs[comply_mask] = self.incomes[comply_mask] - owed_taxes[comply_mask]
        # Caught: W_i - owed_tax - fine = W_i - (1+f)*t*W_i
        self.payoffs[caught_mask] = self.incomes[caught_mask] - (owed_taxes[caught_mask] * penalty_multipliers)
        # Uncaught: keeps full W_i
        self.payoffs[uncaught_mask] = self.incomes[uncaught_mask]

        # Government revenue calculation
        rev_compliant = np.sum(owed_taxes[comply_mask])
        rev_caught = np.sum(owed_taxes[caught_mask] * penalty_multipliers)
        gross_revenue = float(rev_compliant + rev_caught)
        total_audits = int(np.sum(audited_mask))
        enforcement_cost = float(total_audits * self.game.c_a)
        net_revenue = gross_revenue - enforcement_cost

        # Update flag states for Risk-Targeted policy
        if isinstance(self.policy, RiskTargetedPolicy):
            # Newly caught become flagged
            self.is_flagged[caught_mask] = True
            self.flag_timer[caught_mask] = self.policy.probation_periods

            # Decrement timer for clean rounds
            clean_audit = comply_mask & audited_mask
            self.flag_timer[clean_audit] = np.maximum(0, self.flag_timer[clean_audit] - 1)
            # Expire flag if timer hits 0
            self.is_flagged[self.flag_timer <= 0] = False

        # 4. Evolutionary Strategy Update: Fermi Pairwise Imitation
        self._evolutionary_update()

        # 5. Record round results
        compliance_rate = float(np.sum(self.strategies) / self.n_agents)
        return {
            "step": current_step,
            "compliance_rate": compliance_rate,
            "evasion_rate": 1.0 - compliance_rate,
            "audit_intensity": float(total_audits / self.n_agents),
            "audits_conducted": total_audits,
            "evaders_caught": int(np.sum(caught_mask)),
            "gross_revenue": gross_revenue,
            "enforcement_cost": enforcement_cost,
            "net_revenue": net_revenue,
            "average_taxpayer_payoff": float(np.mean(self.payoffs)),
        }

    def _evolutionary_update(self):
        """
        Fermi update rule:
        Each agent i pairs with a random neighbor j.
        If pi_j > pi_i, agent i adopts j's strategy with probability:
        P(i <- j) = 1 / (1 + exp((pi_i - pi_j) / tau))
        """
        # Random peer matching
        peers = self.rng.integers(0, self.n_agents, size=self.n_agents)

        payoff_self = self.payoffs
        payoff_peer = self.payoffs[peers]
        strategy_peer = self.strategies[peers]

        # Payoff delta
        delta_pi = payoff_peer - payoff_self

        # Fermi probability: P(switch) = 1 / (1 + exp(-delta_pi / tau))
        # Protect against overflow in exp
        exponent = np.clip(-delta_pi / self.temperature, -50.0, 50.0)
        p_switch = 1.0 / (1.0 + np.exp(exponent))

        # Perform imitation switch
        rand_draws = self.rng.random(self.n_agents)
        switch_mask = rand_draws < p_switch
        self.strategies[switch_mask] = strategy_peer[switch_mask]

        # Mutation / spontaneous experimentation
        if self.mutation_rate > 0:
            mutate_mask = self.rng.random(self.n_agents) < self.mutation_rate
            self.strategies[mutate_mask] = 1 - self.strategies[mutate_mask]

    def run_simulation(self, n_steps: int = 150) -> Dict[str, np.ndarray]:
        """Runs the agent-based simulation for n_steps and returns trajectories."""
        self._initialize_population()

        history = {
            "step": np.zeros(n_steps),
            "compliance_rate": np.zeros(n_steps),
            "evasion_rate": np.zeros(n_steps),
            "audit_intensity": np.zeros(n_steps),
            "gross_revenue": np.zeros(n_steps),
            "enforcement_cost": np.zeros(n_steps),
            "net_revenue": np.zeros(n_steps),
            "average_taxpayer_payoff": np.zeros(n_steps),
        }

        metrics = None
        for step_idx in range(n_steps):
            metrics = self.step(step_idx, prev_metrics=metrics)
            for key in history.keys():
                history[key][step_idx] = metrics[key]

        return history
