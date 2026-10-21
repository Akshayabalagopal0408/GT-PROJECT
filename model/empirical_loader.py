"""
empirical_loader.py - Empirical Calibration Engine for Real-World Tax Administrations.
Loads official empirical benchmarks from OECD ISORA, World Bank, and IRS datasets.
"""

import os
import pandas as pd
from typing import Dict, Any, List
from .payoff import TaxEvasionGame


DEFAULT_DATA_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "empirical_tax_benchmarks.csv")
)


class EmpiricalTaxDataLoader:
    """
    Manages empirical calibration data for real-world tax compliance simulations.
    """

    def __init__(self, csv_path: str = DEFAULT_DATA_PATH):
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Empirical dataset not found at: {csv_path}")
        self.csv_path = csv_path
        self.df = pd.read_csv(csv_path)

    def list_countries(self) -> List[Dict[str, str]]:
        """Returns list of available countries with codes and names."""
        return [
            {"code": row["country_code"], "name": row["country_name"], "source": row["data_source"]}
            for _, row in self.df.iterrows()
        ]

    def get_country_row(self, country_code: str) -> pd.Series:
        """Retrieves raw data row for a specific country code."""
        matches = self.df[self.df["country_code"].str.upper() == country_code.upper()]
        if matches.empty:
            available = self.df["country_code"].tolist()
            raise ValueError(f"Country code '{country_code}' not found. Available: {available}")
        return matches.iloc[0]

    def build_game_for_country(
        self,
        country_code: str,
        benchmark_income: float = 100.0
    ) -> Dict[str, Any]:
        """
        Builds a calibrated TaxEvasionGame instance and behavioral parameters for a country.

        Returns:
            Dictionary containing:
            - 'country_name': str
            - 'country_code': str
            - 'game': TaxEvasionGame instance
            - 'declared_beta': float (fraction declared by cheaters)
            - 'evaded_fraction': float (1 - beta)
            - 'audit_coverage_pi': float (real-world observed audit rate)
            - 'detection_efficacy_alpha': float
            - 'raw_metrics': dict
        """
        row = self.get_country_row(country_code)

        tau = float(row["statutory_tax_rate_tau"])
        phi = float(row["penalty_multiplier_phi"])
        cost_ratio = float(row["cost_of_collection_pct_C"])
        beta = float(row["declared_share_beta"])
        alpha_efficacy = float(row["audit_detection_efficacy_alpha"])
        obs_pi = float(row["audit_coverage_rate_pi"])

        # Cost per audit: scaled to typical per-taxpayer administrative expenditure
        # Using cost ratio (e.g. 0.01 * tau * W * scaling factor)
        audit_cost = max(cost_ratio * tau * benchmark_income * 8.0, 2.0)

        game = TaxEvasionGame(
            W=benchmark_income,
            t=tau,
            f=phi,
            c_a=audit_cost
        )

        return {
            "country_code": row["country_code"],
            "country_name": row["country_name"],
            "data_source": row["data_source"],
            "game": game,
            "declared_beta": beta,
            "evaded_fraction": 1.0 - beta,
            "real_audit_coverage": obs_pi,
            "detection_efficacy": alpha_efficacy,
            "cost_of_collection_pct": cost_ratio * 100.0,
            "notes": row["notes"],
        }
