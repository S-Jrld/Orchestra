"""Predefined task tier budget profiles."""

from __future__ import annotations

from typing import Dict

from orchestra.models import BudgetLimit, Tier


class BudgetProfileManager:
    """Provides standard tier budget quotas calibrated for token efficiency."""

    DEFAULTS: Dict[str, BudgetLimit] = {
        Tier.TINY.value: BudgetLimit(
            max_calls=3,
            max_input_tokens=2500,
            max_output_tokens=1000,
            max_total_tokens=3500,
            max_duration_seconds=60,
            max_parallel_workers=1,
            max_cost_usd=0.02,
        ),
        Tier.NORMAL.value: BudgetLimit(
            max_calls=8,
            max_input_tokens=15000,
            max_output_tokens=4000,
            max_total_tokens=19000,
            max_duration_seconds=300,
            max_parallel_workers=2,
            max_cost_usd=0.10,
        ),
        Tier.COMPLEX.value: BudgetLimit(
            max_calls=20,
            max_input_tokens=50000,
            max_output_tokens=15000,
            max_total_tokens=65000,
            max_duration_seconds=900,
            max_parallel_workers=4,
            max_cost_usd=0.40,
        ),
        Tier.ARCHITECTURAL.value: BudgetLimit(
            max_calls=35,
            max_input_tokens=100000,
            max_output_tokens=30000,
            max_total_tokens=130000,
            max_duration_seconds=1800,
            max_parallel_workers=4,
            max_cost_usd=1.00,
        ),
    }

    @classmethod
    def get_profile(cls, tier: str) -> BudgetLimit:
        return cls.DEFAULTS.get(tier, cls.DEFAULTS[Tier.NORMAL.value])
